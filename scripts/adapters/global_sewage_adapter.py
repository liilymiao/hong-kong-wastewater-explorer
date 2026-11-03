#!/usr/bin/env python3
"""Build a source-checked Global Sewage 3 count subset, never the huge browser matrix.

Default: use local original files. --refresh retrieves and verifies the fixed Zenodo
version and ENA metadata. Requires pandas and pyarrow for the actual Parquet read.
"""
import argparse
import collections
import csv
import datetime
import hashlib
import json
import pathlib
import sys
import urllib.request
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[2]
SITE = ROOT / "site" if (ROOT / "site/datasets").is_dir() else ROOT
RAW = ROOT / 'work/data_sources/global-sewage'
OUT = SITE / 'datasets'
QA = ROOT / 'qa'
RECORD = 'https://zenodo.org/api/records/14652833'
ENA_FIELDS = 'run_accession,sample_accession,sample_alias,study_accession,scientific_name,country,location,collection_date,lat,lon,fastq_ftp,fastq_md5,read_count,base_count'
VERSION = 'global-sewage-adapter-1.0.0'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def md5(path):
    h = hashlib.md5()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def fetch(url, path):
    req = urllib.request.Request(url, headers={'User-Agent': 'HKWastewaterExplorer/1.0 research data adapter'})
    with urllib.request.urlopen(req, timeout=60) as r:
        path.write_bytes(r.read())


def fetch_large(url, path, size):
    """Bounded HTTP Range requests survive the host's five-minute transfer cutoff."""
    tmp = path.with_suffix(path.suffix + '.part')
    if tmp.exists() and tmp.stat().st_size > size:
        raise ValueError('Unexpected partial-file length')
    offset = tmp.stat().st_size if tmp.exists() else 0
    while offset < size:
        end = min(offset + 8 * 1024 * 1024, size) - 1
        req = urllib.request.Request(url, headers={'Range': f'bytes={offset}-{end}',
            'User-Agent': 'HKWastewaterExplorer/1.0 research data adapter'})
        with urllib.request.urlopen(req, timeout=90) as r:
            assert r.status == 206 and r.headers.get('Content-Range', '').startswith(f'bytes {offset}-{end}/')
            data = r.read()
        assert len(data) == end - offset + 1
        with tmp.open('ab') as f:
            f.write(data)
        offset += len(data)
    tmp.replace(path)


def ena_url(run):
    return 'https://www.ebi.ac.uk/ena/portal/api/filereport?accession=' + run + '&result=read_run&fields=' + ENA_FIELDS + '&format=json'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--sample-limit', type=int, default=16)
    args = parser.parse_args()
    assert 1 <= args.sample_limit <= 100, 'Use an explicitly bounded subset (1–100 samples).'
    RAW.mkdir(parents=True, exist_ok=True)
    if args.refresh:
        fetch(RECORD, RAW / 'record.json')
    record = json.loads((RAW / 'record.json').read_text())
    original_files = {r['key']: r for r in record['files']}
    for name in ['gs3.parquet', 'tot_counts.csv', 'counts_clusters.csv']:
        p = RAW / name
        upstream = original_files[name]
        if not p.exists() and p.with_suffix(p.suffix + '.part').exists():
            part = p.with_suffix(p.suffix + '.part')
            if part.stat().st_size == upstream['size'] and md5(part) == upstream['checksum'].split(':')[1]:
                part.replace(p)
        if args.refresh:
            if name == 'counts_clusters.csv':
                if not (p.exists() and md5(p) == upstream['checksum'].split(':')[1]):
                    fetch_large(upstream['links']['self'], p, upstream['size'])
            else:
                fetch(upstream['links']['self'], p)
        assert p.exists(), f'Missing complete original {name}; use --refresh.'
        assert p.stat().st_size == upstream['size']
        assert md5(p) == upstream['checksum'].split(':')[1], f'Upstream checksum mismatch: {name}'
    deps = ROOT / 'work/adapter-deps'
    if deps.exists():
        sys.path.insert(0, str(deps))
    import pandas as pd
    geo = pd.read_parquet(RAW / 'gs3.parquet')
    assert set(['country', 'city', 'lat', 'lon']).issubset(geo.columns)
    # This file is a geography table: it has no complete_name or genepid key.
    assert 'genepid' not in geo.columns and 'complete_name' not in geo.columns
    geography = []
    for i, row in geo.iterrows():
        obj = {'source_row': int(i) + 1}
        for k in ['country', 'city', 'lat', 'lon', 'city_fixed']:
            v = row.get(k)
            obj[k] = None if pd.isna(v) else v
        geography.append(obj)

    selected = []
    selected_set = set()
    counts = []
    all_names, all_genepids, all_genes = set(), set(), set()
    source_row_count = 0
    with (RAW / 'counts_clusters.csv').open(newline='') as f:
        for source_row, r in enumerate(csv.DictReader(f), 2):
            source_row_count += 1
            name = r['complete_name']
            if name not in all_names and len(selected) < args.sample_limit:
                selected.append(name)
                selected_set.add(name)
            all_names.add(name)
            all_genepids.add(r['genepid'])
            all_genes.add(r['cluster_representative_98'])
            if name in selected_set:
                counts.append((source_row, r))
    assert len(selected) == args.sample_limit
    selected_ids = {r['genepid'] for _, r in counts}
    assert len(selected_ids) == len(selected), 'Selected technical runs share genepid; adjust scope/counts.'
    assert len({(r['complete_name'], r['cluster_representative_98'], r['group']) for _, r in counts}) == len(counts)

    totals = list(csv.DictReader((RAW / 'tot_counts.csv').open(newline='')))
    # bindCol repeats per-run metadata. Collapse identical run/complete-name/total
    # tuples and never sum the repeated rows as sequencing depth.
    by_name = collections.defaultdict(dict)
    for source_row, r in enumerate(totals, 2):
        if r['complete_name'] in selected_set:
            key = (r['sample_name'], r['complete_name'], r['total_fragments'])
            by_name[r['complete_name']].setdefault(key, {'run_accession': r['sample_name'],
                'total_fragments': int(r['total_fragments']), 'source_rows': []})['source_rows'].append(source_row)
    assert set(by_name) == selected_set, 'Count subset lacks total-count linkage'
    samples, sequence_manifest = [], []
    source_urls = {name: original_files[name]['links']['self'] for name in ['gs3.parquet', 'tot_counts.csv', 'counts_clusters.csv']}
    for name in selected:
        matches = list(by_name[name].values())
        assert len(matches) == 1, 'Ambiguous sequencing run/denominator; do not arbitrarily choose.'
        match = matches[0]
        run = match['run_accession']
        if args.refresh or not (RAW / (run + '.json')).exists():
            fetch(ena_url(run), RAW / (run + '.json'))
        records = json.loads((RAW / (run + '.json')).read_text())
        assert len(records) == 1 and records[0]['run_accession'] == run
        ena = records[0]
        accession = ena['sample_accession']
        xml_url = 'https://www.ebi.ac.uk/ena/browser/api/xml/' + accession
        if args.refresh or not (RAW / (accession + '.xml')).exists():
            fetch(xml_url, RAW / (accession + '.xml'))
        xml = ET.parse(RAW / (accession + '.xml'))
        attrs = {x.findtext('TAG'): x.findtext('VALUE') for x in xml.findall('.//SAMPLE_ATTRIBUTE')}
        assert attrs.get('collection date') == ena['collection_date']
        count_row = next(r for _, r in counts if r['complete_name'] == name)
        sample = {'sample_id': count_row['genepid'], 'genepid': count_row['genepid'], 'complete_name': name,
            'sample_accession': accession, 'run_accession': run, 'study_accession': ena['study_accession'],
            'country': ena.get('country') or None, 'city': None,
            'date': ena.get('collection_date') or None,
            'latitude': float(ena['lat']) if ena.get('lat') else None,
            'longitude': float(ena['lon']) if ena.get('lon') else None,
            'sample_alias': ena.get('sample_alias'), 'scientific_name': ena.get('scientific_name'),
            'total_fragments': match['total_fragments'], 'total_count_source_rows': ';'.join(map(str, match['source_rows'])),
            'ena_read_count': int(ena['read_count']) if ena.get('read_count') else None,
            'ena_base_count': int(ena['base_count']) if ena.get('base_count') else None,
            'public_date': attrs.get('ENA-FIRST-PUBLIC'),
            'metadata_link_rule': 'counts.complete_name = tot_counts.complete_name; unique sample_name = ENA run_accession',
            'metadata_source_url': ena_url(run), 'sample_url': 'https://www.ebi.ac.uk/ena/browser/view/' + accession}
        samples.append(sample)
        source_urls[run + '.json'] = ena_url(run)
        source_urls[accession + '.xml'] = xml_url
        urls = (ena.get('fastq_ftp') or '').split(';')
        hashes = (ena.get('fastq_md5') or '').split(';')
        assert len(urls) == len(hashes)
        for url, checksum in zip(urls, hashes):
            if url:
                sequence_manifest.append({'sample_id': sample['sample_id'], 'complete_name': name,
                    'sample_accession': accession, 'run_accession': run,
                    'download_url': 'https://' + url, 'md5': checksum,
                    'availability': 'Public ENA file manifest; FASTQ not downloaded'})
    sample_map = {s['complete_name']: s for s in samples}
    rows = []
    for source_row, raw in counts:
        s = sample_map[raw['complete_name']]
        count = int(raw['fragmentCountAln'])
        assert count >= 0 and str(count) == raw['fragmentCountAln']
        rows.append({'id': raw['complete_name'] + '|' + raw['cluster_representative_98'] + '|' + raw['group'],
            'sample_id': raw['genepid'], 'complete_name': raw['complete_name'],
            'country': s['country'], 'city': None, 'date': s['date'],
            'gene': raw['cluster_representative_98'], 'cluster_representative_98': raw['cluster_representative_98'],
            'group': raw['group'], 'value': count, 'unit': 'aligned fragments (raw count)',
            'fragmentCountAln': count, 'raw_fragmentCountAln': raw['fragmentCountAln'],
            'fragmentCountAln_adj': raw['fragmentCountAln_adj'],
            'fragmentCountAln_adj_kb': raw['fragmentCountAln_adj_kb'],
            'resfinder': raw['resfinder'], 'functional_amr': raw['functional_amr'], 'csabapal': raw['csabapal'],
            'run_accession': s['run_accession'], 'sample_accession': s['sample_accession'],
            'source_file': 'counts_clusters.csv', 'source_row': source_row})
    source_urls.update({'record.json': RECORD,
        'code-README.md': 'https://raw.githubusercontent.com/genomicepidemiology/gs3_acquired_vs_FG/main/README.md',
        'Diversities_Abundances.ipynb': 'https://raw.githubusercontent.com/genomicepidemiology/gs3_acquired_vs_FG/main/notebooks/Diversities_Abundances.ipynb',
        'PanRes-record.json': 'https://zenodo.org/api/records/8055116'})
    sources = []
    for name, url in source_urls.items():
        p = RAW / name
        if p.exists():
            sources.append({'file': name, 'url': url, 'sha256': sha(p), 'bytes': p.stat().st_size,
                'retrieved_at_utc': datetime.datetime.fromtimestamp(p.stat().st_mtime, datetime.timezone.utc).isoformat(),
                'upstream_md5': original_files[name]['checksum'].split(':')[1] if name in original_files else None})
    source_sha = hashlib.sha256(json.dumps(sources, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    stats = {'source_count_row_count': source_row_count, 'source_complete_name_count': len(all_names),
        'source_genepid_count': len(all_genepids), 'source_cluster_count': len(all_genes),
        'geography_row_count': len(geography), 'total_count_source_row_count': len(totals),
        'row_count': len(rows), 'sample_count': len(samples),
        'biological_accession_count': len({s['sample_accession'] for s in samples}),
        'run_count': len({s['run_accession'] for s in samples}), 'gene_cluster_count': len({r['gene'] for r in rows}),
        'country_count': len({s['country'] for s in samples}),
        'date_min': min(s['date'] for s in samples if s['date']),
        'date_max': max(s['date'] for s in samples if s['date'])}
    dictionary = {k: {'label': k.replace('_', ' ').capitalize()} for k in rows[0]}
    dictionary.update({
        'gene': {'label': 'PanRes 98% cluster', 'definition': 'Original cluster_representative_98 identifier; no unverified gene-symbol mapping.'},
        'value': {'label': 'Raw fragment count', 'unit': 'aligned fragments', 'definition': 'Exact integer fragmentCountAln from the upstream cluster-count file; no normalization applied.'},
        'fragmentCountAln_adj': {'label': 'Upstream adjusted count', 'definition': 'Original decimal text retained. This field is not used as the query value or as a cross-study abundance metric.'},
        'fragmentCountAln_adj_kb': {'label': 'Upstream adjusted count per kb', 'definition': 'Original source field retained verbatim; no new normalization or denominator calculation is performed.'},
        'group': {'label': 'Source database group', 'definition': 'Original ResFinder/Functional group assignment.'},
        'date': {'label': 'Collection date', 'definition': 'ENA collection_date, independently checked against the ENA sample XML collection date.'},
        'country': {'label': 'Country', 'definition': 'Reported country from the matched ENA run.'},
        'city': {'label': 'City', 'definition': 'Unavailable in the matched run/sample metadata. The unlinked Parquet geography table is not used to infer a sample city.'},
        'sample_id': {'label': 'Source sample ID', 'definition': 'Original genepid identifier, connected to one complete_name and one ENA sample accession within this subset.'},
        'total_fragments': {'label': 'Reported total fragments', 'definition': 'tot_counts.csv total_fragments for the unique matched run after removing repeated bindCol joins. It is retained without a derived abundance calculation.'}})
    meta = {'dataset_id': 'global-sewage', 'title': f'Global Sewage 3: verified {args.sample_limit}-sample count subset',
        'provider': 'Martiny, Munk, Fuschi and Aarestrup / Zenodo', 'status': 'connected',
        'source_url': 'https://zenodo.org/records/14652833', 'source_version': '10.5281/zenodo.14652833 (v1, 2025-01-21)',
        'source_sha256': source_sha, 'checksum_scope': 'SHA256 of canonical source-manifest JSON; complete Zenodo files also checked against repository MD5.',
        'retrieved_at_utc': max(s['retrieved_at_utc'] for s in sources), 'adapter_version': VERSION,
        'observation_unit': 'One sample × PanRes gene-cluster × database-group reported count',
        'scope_note': f'All reported cluster-count rows for the first {args.sample_limit} distinct complete_name identifiers in the fixed v1 counts_clusters.csv file. The entire source file is scanned and checksum-verified; this subset is not a representative global sample.',
        'scope': {'sample_limit': args.sample_limit, 'selected_complete_names': selected,
                  'selection_rule': 'First distinct complete_name values in source-file row order; retain every matching row from the complete verified file.'},
        'counts': stats, 'sources': sources,
        'terms': {'name': 'Creative Commons Attribution 4.0', 'url': 'https://creativecommons.org/licenses/by/4.0/',
                  'summary': 'Zenodo record 14652833 declares CC BY 4.0. Credit the data creators and fixed version. ENA metadata/sequence records retain their original accession provenance.'},
        'citation': 'Martiny, H.-M., Munk, P., Fuschi, A., & Aarestrup, F. (2025). Data for Global Sewage 3 (v1). Zenodo. https://doi.org/10.5281/zenodo.14652833',
        'methods': {'pipeline': 'ARGprofiler', 'mapper': 'KMA 1.4.12a',
                    'database': 'PanRes 1.0.0, Zenodo 8055116, linked by the author code README',
                    'clustering': 'USEARCH 11.0.66, 98% nucleotide identity and query coverage as documented by author code',
                    'displayed_measure': 'Original fragmentCountAln; no normalization performed'},
        'dictionary': dictionary,
        'notes': [
            'The complete gs3.parquet was read and contains geography records without a sample key. Its locations are retained separately and are not assigned to count samples.',
            'The author notebook references metadata_fixed.csv, which is not among the Zenodo files; the checked repository-relative path returns HTTP 404. Country/date/accessions here come from the directly linked ENA run and sample records.',
            'Repeated tot_counts rows caused by bindCol are collapsed for run linkage; reported total_fragments are never summed across those duplicates.',
            'Unlisted sample/cluster combinations remain absent, not zero. No positivity threshold, risk score, copies/L or relative abundance is derived.',
            'panres_counts.csv, motus_counts.zip and the rest of the global count matrix are not served by the browser. Original file links and the adapter preserve the next-step retrieval path.'],
        'ui': {'filters': ['country', 'date', 'gene', 'group', 'sample_id'],
               'columns': ['sample_id', 'country', 'date', 'gene', 'group', 'value', 'unit', 'run_accession', 'source_row']}}
    data = {'meta': meta, 'rows': rows, 'samples': samples, 'sequence_manifest': sequence_manifest,
            'geography': geography, 'excluded': []}
    OUT.mkdir(parents=True, exist_ok=True)
    packed = {'meta': meta}
    for name in ['rows', 'samples', 'sequence_manifest', 'geography', 'excluded']:
        cols = list(dict.fromkeys(k for r in data[name] for k in r))
        packed[name] = {'columns': cols, 'values': [[r.get(k) for k in cols] for r in data[name]]}
    output = OUT / 'global-sewage-data.js'
    staged = output.with_suffix('.js.tmp')
    staged.write_text('(function(){const d=' + json.dumps(packed, ensure_ascii=False, separators=(',', ':')) +
        ';for(const k of ["rows","samples","sequence_manifest","geography","excluded"]){const p=d[k];d[k]=p.values.map(v=>Object.fromEntries(p.columns.map((c,i)=>[c,v[i]])));}window.EXT_GLOBAL_DATA=d;})();\n')
    restored = json.loads(json.dumps(packed, ensure_ascii=False))
    restored_rows = [dict(zip(restored['rows']['columns'], v)) for v in restored['rows']['values']]
    for (_, raw), r in zip(counts, restored_rows):
        assert str(r['value']) == raw['fragmentCountAln']
        assert r['fragmentCountAln_adj'] == raw['fragmentCountAln_adj']
        assert r['fragmentCountAln_adj_kb'] == raw['fragmentCountAln_adj_kb']
    staged.replace(output)
    dump(OUT / 'global-sewage-provenance.json', meta)
    (OUT / 'global-sewage-NOTICE.txt').write_text(meta['citation'] + '\n\nCC BY 4.0\n' + meta['terms']['url'] +
        '\n\n' + meta['scope_note'] + '\n\n' + '\n'.join(meta['notes']) + '\n')
    QA.mkdir(exist_ok=True, parents=True)
    dump(QA / 'global-sewage-verification.json', {'status': 'passed', 'counts': stats,
        'checks': ['three complete Zenodo files match repository MD5 and sizes', 'actual Parquet schema read',
            'complete count-file scan for every selected identifier', 'unique sample/cluster/group keys',
            'exact complete_name to unique run linkage after bindCol de-duplication',
            'all ENA run IDs and sample XML collection dates verified', 'raw counts and adjusted-text fields preserved',
            'unlinked geography is never imputed onto samples'],
        'output_bytes': output.stat().st_size, 'output_sha256': sha(output), 'source_manifest_sha256': source_sha})
    print(json.dumps(stats, indent=2))
    print('Output bytes:', output.stat().st_size)


if __name__ == '__main__':
    main()

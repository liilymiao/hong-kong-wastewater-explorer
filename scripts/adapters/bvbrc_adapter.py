#!/usr/bin/env python3
"""Offline BV-BRC E. coli/ciprofloxacin experimental AST snapshot adapter.

Run with --refresh to retrieve a new, fully paginated snapshot. The default reads
the archived API responses. A failed refresh never replaces the public dataset.
Only Python's standard library is required.
"""
import argparse
import collections
import concurrent.futures
import hashlib
import json
import pathlib
import re
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
SITE = ROOT / "site" if (ROOT / "site/datasets").is_dir() else ROOT
RAW = ROOT / 'work/data_sources/bvbrc'
OUT = SITE / 'datasets'
QA = ROOT / 'qa'
API = 'https://www.bv-brc.org/api/'
QUERY = 'eq(taxon_id,562)&eq(antibiotic,ciprofloxacin)&eq(evidence,Laboratory%20Method)&sort(%2Bid)'
GENOME_FIELDS = 'genome_id,genome_name,taxon_id,biosample_accession,assembly_accession,sra_accession,bioproject_accession,genbank_accessions,refseq_accessions,collection_date,collection_year,isolation_country,isolation_source,host_name,body_sample_site,genome_status,genome_quality,genome_length,contigs,strain,publication,date_modified,sequencing_platform'
POLICY = 'https://www.bv-brc.org/docs/system_documentation/data_management_sharing.html'
VERSION = 'bvbrc-adapter-1.0.0'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def fetch(url, path, extra=None):
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={
                'Accept': 'application/solr+json',
                'User-Agent': 'HKWastewaterExplorer/1.0 (research public-data snapshot adapter)'})
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read()
            data = json.loads(raw)
            assert data['responseHeader']['status'] == 0
            path.write_bytes(raw)
            dump(path.with_suffix('.source.json'), dict(
                url=url, retrieved_at_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                **(extra or {})))
            return data['response']
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))


def pages(prefix):
    return sorted(f for f in RAW.glob(prefix + '-*.json') if not f.name.endswith('.source.json'))


def refresh():
    RAW.mkdir(parents=True, exist_ok=True)
    first = fetch(API + 'genome_amr/?' + QUERY + '&limit(1000,0)', RAW / 'ast-00000.json')
    total = first['numFound']
    offsets = list(range(1000, total, 1000))
    def ast_page(off):
        r = fetch(API + 'genome_amr/?' + QUERY + f'&limit(1000,{off})', RAW / f'ast-{off:05}.json')
        assert r['numFound'] == total and r['start'] == off
    with concurrent.futures.ThreadPoolExecutor(3) as pool:
        list(pool.map(ast_page, offsets))
    expected = {f'ast-{off:05}.json' for off in range(0, total, 1000)}
    for f in pages('ast'):
        if f.name not in expected:
            f.unlink()
            f.with_suffix('.source.json').unlink(missing_ok=True)
    rows = [r for f in pages('ast') for r in json.loads(f.read_text())['response']['docs']]
    ids = sorted({r['genome_id'] for r in rows})
    def genome_page(off):
        part = ids[off:off+300]
        url = API + 'genome/?in(genome_id,(' + ','.join(part) + '))&select(' + GENOME_FIELDS + ')&limit(1000,0)&sort(%2Bgenome_id)'
        r = fetch(url, RAW / f'genomes-{off:05}.json', {'requested_ids': part})
        assert r['numFound'] == len(r['docs'])
    with concurrent.futures.ThreadPoolExecutor(3) as pool:
        list(pool.map(genome_page, range(0, len(ids), 300)))
    expected = {f'genomes-{off:05}.json' for off in range(0, len(ids), 300)}
    for f in pages('genomes'):
        if f.name not in expected:
            f.unlink()
            f.with_suffix('.source.json').unlink(missing_ok=True)


def accessions(value):
    if isinstance(value, list):
        return sorted(set(str(x) for x in value if x))
    return sorted(set(x for x in re.split(r'[;,\s]+', str(value or '')) if x))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh', action='store_true')
    args = parser.parse_args()
    if args.refresh:
        refresh()
    files = pages('ast') + pages('genomes')
    assert files, 'No archived API snapshot; use --refresh.'
    ast = []
    totals = set()
    for f in pages('ast'):
        r = json.loads(f.read_text())['response']
        totals.add(r['numFound'])
        assert r['start'] == len(ast), 'Non-contiguous API pagination'
        ast.extend(r['docs'])
    assert len(totals) == 1 and len(ast) == next(iter(totals)), 'Incomplete AST pagination'
    assert len({r['id'] for r in ast}) == len(ast), 'Repeated API record ID'
    assert [r['id'] for r in ast] == sorted(r['id'] for r in ast), 'Unstable API ordering'
    genomes = [r for f in pages('genomes') for r in json.loads(f.read_text())['response']['docs']]
    gm = {r['genome_id']: r for r in genomes}
    assert len(gm) == len(genomes), 'Duplicate genome metadata response'
    for r in ast:
        assert r['taxon_id'] == 562 and r['antibiotic'] == 'ciprofloxacin'
        assert r['evidence'] == 'Laboratory Method'
        assert r.get('laboratory_typing_method') != 'Computational Prediction'

    # A shared exact BioSample, SRA accession, or assembly accession groups genome
    # versions; never merge on strain names, geography, collection year or labels.
    parent = {g: g for g in gm}
    def find(g):
        while parent[g] != g:
            parent[g] = parent[parent[g]]
            g = parent[g]
        return g
    def union(a, b):
        a, b = find(a), find(b)
        parent[max(a, b)] = min(a, b)
    seen = {}
    for g, r in sorted(gm.items()):
        for field in ['biosample_accession', 'sra_accession', 'assembly_accession']:
            for a in accessions(r.get(field)):
                a = re.sub(r'\.\d+$', '', a) if field == 'assembly_accession' else a
                key = (field, a)
                if key in seen:
                    union(g, seen[key])
                else:
                    seen[key] = g
    members = collections.defaultdict(list)
    for g in sorted(gm):
        members[find(g)].append(g)
    groups = {}
    for ids in members.values():
        bios = sorted({a for g in ids for a in accessions(gm[g].get('biosample_accession'))})
        runs = sorted({a for g in ids for a in accessions(gm[g].get('sra_accession'))})
        assemblies = sorted({re.sub(r'\.\d+$', '', a) for g in ids for a in accessions(gm[g].get('assembly_accession'))})
        key = ('biosample:' + bios[0] if bios else 'sra:' + runs[0] if runs else
               'assembly:' + assemblies[0] if assemblies else 'genome:' + ids[0])
        for g in ids:
            groups[g] = {'sample_group_id': key, 'sample_group_basis': key.split(':')[0],
                         'identifier_conflict': len(bios) > 1, 'genome_versions_in_group': len(ids)}
    labels = collections.defaultdict(set)
    for r in ast:
        key = groups.get(r['genome_id'], {}).get('sample_group_id', 'genome:' + r['genome_id'])
        if r.get('resistant_phenotype'):
            labels[key].add(r['resistant_phenotype'])
    keep = ['id', 'genome_id', 'taxon_id', 'antibiotic', 'evidence', 'resistant_phenotype',
            'measurement', 'measurement_sign', 'measurement_value', 'measurement_unit',
            'laboratory_typing_method', 'testing_standard', 'testing_standard_year',
            'source', 'pmid', 'date_modified']
    rows, excluded, duplicate_signatures = [], [], {}
    for raw in ast:
        r = {k: raw.get(k) for k in keep}
        r['pmid'] = ';'.join(map(str, raw.get('pmid') or []))
        g = gm.get(raw['genome_id'], {})
        group = groups.get(raw['genome_id'], {'sample_group_id': 'genome:' + raw['genome_id'],
                                             'sample_group_basis': 'genome', 'identifier_conflict': False,
                                             'genome_versions_in_group': 1})
        r.update(group)
        r['genome_linked'] = bool(g)
        r['country'] = g.get('isolation_country')
        r['collection_date'] = g.get('collection_date')
        r['raw_collection_year'] = g.get('collection_year')
        r['collection_year'] = g.get('collection_year')
        r['collection_year_basis'] = 'reported collection_year' if r['collection_year'] is not None else None
        date = str(g.get('collection_date') or '')
        year_range = re.fullmatch(r'(\d{4})-(\d{4})', date)
        r['year_start'], r['year_end'] = None, None
        if year_range:
            r['collection_year'] = None
            r['year_start'], r['year_end'] = map(int, year_range.groups())
            r['collection_year_basis'] = 'range in reported collection_date; no single year assigned'
        elif r['collection_year'] is None and re.fullmatch(r'\d{4}(?:-(?:0[1-9]|1[0-2])(?:-(?:0[1-9]|[12]\d|3[01]))?)?', date):
            r['collection_year'] = int(g['collection_date'][:4])
            r['collection_year_basis'] = 'year extracted from reported collection_date'
        r['host_name'] = g.get('host_name')
        r['isolation_source'] = g.get('isolation_source')
        r['body_sample_site'] = g.get('body_sample_site')
        r['method'] = raw.get('laboratory_typing_method')
        r['sequence_available'] = any(g.get(k) for k in ['sra_accession', 'assembly_accession', 'genbank_accessions', 'refseq_accessions'])
        r['conflict_label'] = len(labels[group['sample_group_id']]) > 1
        r['study_group_id'] = 'pmid:' + (r['pmid'] or str(g.get('publication') or 'unreported'))
        value = str(raw.get('measurement_value') or '')
        numeric = bool(re.fullmatch(r'(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?', value))
        method, unit = r['method'], raw.get('measurement_unit')
        if unit == 'mg/L' and method in ['MIC', 'Broth dilution', 'Agar dilution'] and numeric:
            r['measurement_type'] = 'MIC'
        elif unit == 'mm' and method == 'Disk diffusion' and numeric:
            r['measurement_type'] = 'zone_diameter'
        elif unit == 'mg/L' and method == 'Disk diffusion':
            r['measurement_type'] = 'method_unit_conflict'
        elif unit == 'mg/L':
            r['measurement_type'] = 'unclassified_concentration'
        elif not value and raw.get('resistant_phenotype'):
            r['measurement_type'] = 'phenotype_only'
        else:
            r['measurement_type'] = 'unclassified'
        r['mic_eligible'] = r['measurement_type'] == 'MIC'
        r['censored'] = str(raw.get('measurement_sign') or '') in ['<', '>', '<=', '>=', '≤', '≥']
        signature = json.dumps([raw.get(k) for k in keep if k not in ['id', 'date_modified']], sort_keys=True)
        r['duplicate_of'] = duplicate_signatures.get(signature)
        duplicate_signatures.setdefault(signature, raw['id'])
        reasons = []
        if not r['genome_linked']: reasons.append('genome_metadata_not_found')
        if not r['sequence_available']: reasons.append('sequence_accession_not_reported')
        if r['identifier_conflict']: reasons.append('multiple_biosample_identifiers_in_group')
        if r['conflict_label']: reasons.append('conflicting_phenotype_labels_in_sample_group')
        if r['duplicate_of']: reasons.append('duplicate_ast_payload')
        if not (r.get('resistant_phenotype') or r['mic_eligible']): reasons.append('no_interpretable_phenotype_or_method_verified_MIC')
        r['cohort_eligible'] = not reasons
        r['exclusion_reason'] = ';'.join(reasons) or None
        if reasons:
            excluded.append({'id': r['id'], 'genome_id': r['genome_id'],
                             'sample_group_id': r['sample_group_id'], 'reason': r['exclusion_reason'],
                             'duplicate_of': r['duplicate_of']})
        rows.append(r)

    samples, manifest = [], []
    for g in sorted(genomes, key=lambda x: x['genome_id']):
        clean = {k: v for k, v in g.items() if k != '_version_'}
        clean.update(groups[g['genome_id']])
        clean['conflict_label'] = len(labels[clean['sample_group_id']]) > 1
        clean['source_api_url'] = API + 'genome/' + g['genome_id']
        samples.append(clean)
        gid = g['genome_id']
        manifest.append({'genome_id': gid, 'sample_group_id': clean['sample_group_id'],
            'biosample_accession': g.get('biosample_accession'), 'assembly_accession': g.get('assembly_accession'),
            'sra_accession': g.get('sra_accession'), 'genbank_accessions': g.get('genbank_accessions'),
            'refseq_accessions': g.get('refseq_accessions'),
            'genome_url': 'https://www.bv-brc.org/view/Genome/' + gid,
            'sequence_download_url': f'ftp://ftp.bv-brc.org/genomes/{gid}/{gid}.fna',
            'transport': 'Explicit FTPS (TLS required)',
            'availability': 'Public genome indexed; documented FASTA path; sequence file not downloaded'})
    sources = []
    for f in files:
        info = json.loads(f.with_suffix('.source.json').read_text())
        sources.append({'file': f.name, 'sha256': sha(f), 'bytes': f.stat().st_size,
                        'url': info['url'], 'retrieved_at_utc': info['retrieved_at_utc']})
    source_sha = hashlib.sha256(json.dumps(sources, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    stats = {'raw_ast_record_count': len(ast), 'experimental_record_count': len(rows),
        'linked_ast_record_count': sum(r['genome_linked'] for r in rows), 'linked_genome_count': len(samples),
        'sample_group_count': len({r['sample_group_id'] for r in rows}),
        'biosample_accession_count': len({a for g in genomes for a in accessions(g.get('biosample_accession'))}),
        'genome_fallback_group_count': len({r['sample_group_id'] for r in rows if r['sample_group_basis'] == 'genome'}),
        'eligible_ast_record_count': sum(r['cohort_eligible'] for r in rows),
        'eligible_sample_group_count': len({r['sample_group_id'] for r in rows if r['cohort_eligible']}),
        'method_verified_MIC_record_count': sum(r['mic_eligible'] for r in rows),
        'method_unit_conflict_count': sum(r['measurement_type'] == 'method_unit_conflict' for r in rows),
        'conflicting_label_group_count': len({r['sample_group_id'] for r in rows if r['conflict_label']}),
        'duplicate_ast_record_count': sum(bool(r['duplicate_of']) for r in rows),
        'censored_record_count': sum(r['censored'] for r in rows), 'excluded_record_count': len(excluded)}
    dictionary = {k: {'label': k.replace('_', ' ').capitalize()} for k in rows[0]}
    dictionary.update({
        'measurement': {'label': 'Original measurement', 'definition': 'Original API text retained verbatim; use the separate sign and value fields together.'},
        'measurement_sign': {'label': 'Measurement sign', 'definition': 'Original censoring/equality operator; blank remains blank.'},
        'measurement_value': {'label': 'Measurement value', 'definition': 'Original value text; no threshold replacement or imputation.'},
        'measurement_unit': {'label': 'Unit', 'definition': 'Original reported unit (mg/L or mm); missing remains null.'},
        'mic_eligible': {'label': 'Method-verified MIC', 'definition': 'Numeric mg/L result with MIC, broth dilution, or agar dilution method. This flag alone does not establish an independent training sample.'},
        'sample_group_id': {'label': 'Sample group', 'definition': 'Connected exact BioSample/SRA/assembly-accession groups; genome-ID fallback if no shared external identifier. Not all groups are proven independent isolates.'},
        'conflict_label': {'label': 'Label conflict', 'definition': 'More than one reported S/I/R phenotype in the same sample group; no majority label is invented.'},
        'cohort_eligible': {'label': 'Eligible cohort record', 'definition': 'Genome and external sequence accession available, phenotype or method-verified MIC present, no duplicate payload, no label/identifier conflict.'},
        'collection_year': {'label': 'Collection year', 'definition': 'Reported API collection_year; when absent, a year is extracted only from YYYY, YYYY-MM or YYYY-MM-DD collection_date. Year ranges remain null with separate year_start/year_end. raw_collection_year and collection_year_basis preserve provenance.'},
        'raw_collection_year': {'label': 'Original collection year', 'definition': 'Original API collection_year, including null; not filled from collection_date.'},
        'year_start': {'label': 'Reported range start', 'definition': 'First year of an explicitly reported YYYY-YYYY collection_date range; not an exact sampling year.'},
        'year_end': {'label': 'Reported range end', 'definition': 'Last year of an explicitly reported YYYY-YYYY collection_date range; not an exact sampling year.'},
        'sequence_available': {'label': 'Sequence accession reported', 'definition': 'At least one SRA, assembly, GenBank or RefSeq accession is reported; file contents have not been mirrored.'}})
    meta = {'dataset_id': 'bvbrc-ast', 'title': 'E. coli × ciprofloxacin: experimental AST cohort',
        'provider': 'BV-BRC', 'status': 'connected', 'source_url': API + 'genome_amr/?' + QUERY,
        'source_version': 'public-api-snapshot-' + max(s['retrieved_at_utc'] for s in sources)[:10] + '+' + source_sha[:12],
        'source_sha256': source_sha, 'checksum_scope': 'SHA256 of canonical source-manifest JSON; individual response hashes are included.',
        'retrieved_at_utc': max(s['retrieved_at_utc'] for s in sources), 'adapter_version': VERSION,
        'observation_unit': 'One experimental antimicrobial susceptibility record',
        'scope_note': 'All public API records matching taxon_id 562, ciprofloxacin and Laboratory Method in this frozen snapshot. International mixed clinical, animal and environmental sources; collection fields retain reported precision.',
        'terms': {'name': 'BV-BRC public-data use policy', 'url': POLICY,
                  'summary': 'BV-BRC states that public data are freely available without restriction on use. Retain BV-BRC and original-study provenance. Third-party records are separate from the application MIT licence.'},
        'citation': 'BV-BRC public genome_amr and genome API snapshot; original study PMIDs retained per record.',
        'dictionary': dictionary, 'counts': stats, 'sources': sources,
        'notes': [
            'All candidate records remain queryable. Exclusion flags apply to the derived conservative cohort; original experiments are not deleted.',
            'Disk diffusion records reported in mg/L are flagged as method/unit conflicts and are not classified as MIC.',
            'Shared BioSample, SRA, or assembly accessions group genome versions. Genome-ID fallbacks are unresolved sample identities.',
            'Repeated measurements are retained; conflicting S/I/R labels are flagged and excluded from the default conservative cohort.',
            'The sequence manifest uses documented explicit-FTPS paths; genome sequence files have not been downloaded.'],
        'ui': {'filters': ['country', 'collection_year', 'method', 'measurement_type', 'resistant_phenotype', 'host_name', 'isolation_source', 'mic_eligible', 'cohort_eligible', 'conflict_label', 'sequence_available'],
               'columns': ['id', 'genome_id', 'country', 'collection_year', 'resistant_phenotype', 'measurement', 'measurement_sign', 'measurement_value', 'measurement_unit', 'method', 'measurement_type', 'conflict_label', 'cohort_eligible']}}
    data = {'meta': meta, 'rows': rows, 'samples': samples, 'sequence_manifest': manifest, 'excluded': excluded}
    OUT.mkdir(exist_ok=True, parents=True)
    output = OUT / 'bvbrc-data.js'
    staged = output.with_suffix('.js.tmp')
    # Column encoding removes repeated JSON field names in this static asset.
    # At load time it reconstructs the same public array-of-flat-objects contract.
    packed = {'meta': meta}
    for name in ['rows', 'samples', 'sequence_manifest', 'excluded']:
        cols = list(dict.fromkeys(k for row in data[name] for k in row))
        packed[name] = {'columns': cols, 'values': [[row.get(k) for k in cols] for row in data[name]]}
    staged.write_text('(function(){const d=' + json.dumps(packed, ensure_ascii=False, separators=(',', ':')) +
        ';for(const k of ["rows","samples","sequence_manifest","excluded"]){const p=d[k];d[k]=p.values.map(v=>Object.fromEntries(p.columns.map((c,i)=>[c,v[i]])));}window.EXT_BVBRC_DATA=d;})();\n')
    # Safeguard raw fields through the exact output serialization round trip.
    serialized = json.loads(json.dumps(packed, ensure_ascii=False))
    restored = {'rows': [dict(zip(serialized['rows']['columns'], v)) for v in serialized['rows']['values']]}
    for raw, r in zip(ast, restored['rows']):
        for key in ['measurement', 'measurement_sign', 'measurement_value', 'measurement_unit', 'resistant_phenotype']:
            assert r[key] == raw.get(key), (raw['id'], key)
        assert not (r['mic_eligible'] and r['method'] == 'Disk diffusion')
    assert len(restored['rows']) == len(ast)
    staged.replace(output)
    dump(OUT / 'bvbrc-provenance.json', meta)
    (OUT / 'bvbrc-NOTICE.txt').write_text('BV-BRC experimental AST snapshot\n\nData policy: ' + POLICY + '\n' + meta['terms']['summary'] + '\n\n' + '\n'.join(meta['notes']) + '\n')
    QA.mkdir(exist_ok=True, parents=True)
    dump(QA / 'bvbrc-verification.json', {'status': 'passed', 'counts': stats,
        'api_pages': len(pages('ast')), 'genome_batches': len(pages('genomes')),
        'evidence_values': dict(collections.Counter(r['evidence'] for r in rows)),
        'measurement_type_counts': dict(collections.Counter(r['measurement_type'] for r in rows)),
        'units': dict(collections.Counter(str(r['measurement_unit']) for r in rows)),
        'signs': dict(collections.Counter(str(r['measurement_sign']) for r in rows)),
        'checks': ['complete, ordered pagination', 'unique API record IDs', 'exact taxon/drug/evidence filter',
                   'all original measurement fields serialized unchanged', 'no disk diffusion classified as MIC',
                   'genome linkage and exact external-identifier grouping', 'conflicts retained and cohort exclusions explicit'],
        'output_bytes': output.stat().st_size, 'output_sha256': sha(output), 'source_manifest_sha256': source_sha})
    print(json.dumps(stats, indent=2))
    print('Output bytes:', output.stat().st_size)


if __name__ == '__main__':
    main()

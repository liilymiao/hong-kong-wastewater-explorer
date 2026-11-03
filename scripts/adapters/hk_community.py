"""Read public supplemental QC cells and a separately sourced ENA index.

No matching between workbook Sample IDs and ENA aliases is inferred.
Only XML cell values are read; the source workbook is copied byte-for-byte.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import csv
import hashlib
import json
import re
import shutil
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT/"site" if (ROOT/"site/datasets").is_dir() else ROOT
HERE = ROOT/"work/data_sources/hk-community"
OUT = SITE / 'datasets'
QA = ROOT / 'qa'
OUT.mkdir(exist_ok=True)
SOURCE = HERE / 'ADVS-13-e08389-s002.xlsx'
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
DOI = 'https://doi.org/10.1002/advs.202508389'
SUPP_URL = 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13067863/supplementaryFiles'
XML_URL = 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13067863/fullTextXML'
ENA_URL = (HERE / 'ena-url.txt').read_text().strip()
POLICY_URL = 'https://ena-browser-docs.readthedocs.io/en/latest/about/policies.html'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def retrieved(path):
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(timespec='seconds')


def value(raw):
    if raw in (None, '/', ''):
        return None
    if re.fullmatch(r'-?\d+', raw):
        return int(raw)
    try:
        return float(raw)
    except ValueError:
        return raw


def read_sheet(z, path, shared):
    rows = []
    for element in ET.fromstring(z.read(path)).findall('s:sheetData/s:row', NS):
        cells = {}
        for c in element:
            col = re.match(r'[A-Z]+', c.get('r')).group()
            raw = c.findtext('s:v', None, NS)
            if c.get('t') == 's' and raw is not None:
                raw = shared[int(raw)]
            elif c.get('t') == 'inlineStr':
                raw = ''.join(c.find('s:is', NS).itertext())
            cells[col] = raw
        rows.append((int(element.get('r')), cells))
    return rows


S1_FIELDS = ['sample_id', 'illumina_number_of_reads', 'illumina_total_bases',
             'nanopore_number_of_reads', 'nanopore_total_bases', 'nanopore_min_read_length',
             'nanopore_max_read_length', 'nanopore_n50_length', 'nanopore_mean_read_quality']
S2_FIELDS = ['sample_id', 'illumina_number_of_reads', 'illumina_total_bases',
             'illumina_min_read_length', 'illumina_max_read_length', 'illumina_n50_length',
             'nanopore_number_of_reads', 'nanopore_total_bases', 'nanopore_min_read_length',
             'nanopore_max_read_length', 'nanopore_n50_length']
TABLES = []
with zipfile.ZipFile(SOURCE) as z:
    shared = [''.join(s.itertext()) for s in ET.fromstring(z.read('xl/sharedStrings.xml'))]
    for tid, sheet, path, fields in [
        ('table_s1', 'Table S1', 'xl/worksheets/sheet2.xml', S1_FIELDS),
        ('table_s2', 'Table S2', 'xl/worksheets/sheet3.xml', S2_FIELDS),
    ]:
        all_rows = read_sheet(z, path, shared)
        width = len(fields)
        raw_rows = [{'source_row': rn, 'values': [cells.get(chr(65+i)) for i in range(width)]}
                    for rn, cells in all_rows if rn >= 4 and cells.get('A')]
        rows = [dict(zip(fields, [r['values'][0]] + [value(v) for v in r['values'][1:]]))
                for r in raw_rows]
        TABLES.append({
            'id': tid, 'title': all_rows[0][1]['A'], 'sheet_name': sheet,
            'fields': fields, 'row_count': len(rows), 'rows': rows, 'raw_rows': raw_rows,
            'header_rows': [{'source_row': rn, 'values': [cells.get(chr(65+i)) for i in range(width)]}
                            for rn, cells in all_rows if rn <= 3],
            'missing_marker': '/', 'source_sha256': sha(SOURCE),
            'download_url': 'datasets/hk-community-' + tid.replace('_', '-') + '.csv',
            'measurement_type': 'sequencing_qc' if tid == 'table_s1' else 'assembly_qc',
        })

s1, s2 = TABLES
assert len(s1['rows']) == len(s2['rows']) == 189
assert len({r['sample_id'] for r in s1['rows']}) == 189
assert [r['sample_id'] for r in s1['rows']] == [r['sample_id'] for r in s2['rows']]
samples = []
for index, (seq, assembly) in enumerate(zip(s1['rows'], s2['rows'])):
    sample_id = seq['sample_id']
    season = sample_id.split('_', 1)[0]
    assert season in ('Summer', 'Winter')
    iqc = seq['illumina_number_of_reads'] is not None
    nqc = seq['nanopore_number_of_reads'] is not None
    platforms = (['Illumina'] if iqc else []) + (['Oxford Nanopore'] if nqc else [])
    samples.append({
        'sample_id': sample_id, 'season': season,
        'season_basis': 'Literal prefix of the published Sample identifier',
        'collection_date': None, 'area_id': None, 'district': None,
        'latitude': None, 'longitude': None,
        'platforms': platforms, 'platform': '; '.join(platforms),
        'illumina_qc_available': iqc, 'nanopore_qc_available': nqc,
        'available_qc': platforms, 'has_sequencing_qc': iqc or nqc,
        'has_assembly_qc': any(v is not None for k, v in assembly.items() if k != 'sample_id'),
        'sequencing_qc': {k: v for k, v in seq.items() if k != 'sample_id'},
        'assembly_qc': {k: v for k, v in assembly.items() if k != 'sample_id'},
        'source_row_s1': s1['raw_rows'][index]['source_row'],
        'source_row_s2': s2['raw_rows'][index]['source_row'],
        'source_sha256': sha(SOURCE), 'source_url': DOI,
    })

archive = list(csv.DictReader((HERE / 'ena-runs.tsv').open(), delimiter='\t'))
assert len(archive) == len({r['run_accession'] for r in archive}) == 406
assert not ({r['sample_id'] for r in samples} & {r['sample_alias'] for r in archive})
article = ET.parse(HERE / 'article.xml').getroot()
title = ''.join(article.find('.//article-title').itertext())
license_url = 'https://creativecommons.org/licenses/by/4.0/'
assert license_url in (HERE / 'article.xml').read_text()
meta = {
    'dataset_id': 'hk-community', 'schema_version': '1.0',
    'title': 'Hong Kong community sewage metagenomics',
    'citation': f'Ding J et al. (2026). {title} Advanced Science, 13(20), e08389. doi:10.1002/advs.202508389.',
    'doi': '10.1002/advs.202508389', 'pmcid': 'PMC13067863', 'bioproject': 'PRJNA1207805',
    'source_url': DOI, 'retrieval_url': SUPP_URL,
    'source_sha256': sha(SOURCE), 'source_bytes': SOURCE.stat().st_size,
    'retrieved': retrieved(HERE / 'supplements.zip'),
    'license': 'CC BY 4.0', 'license_url': license_url,
    'attribution': 'Jiahui Ding and coauthors, 2026. Advanced Science / Wiley-VCH GmbH. Supporting Information II, Tables S1–S2.',
    'license_basis': 'The article XML states CC BY 4.0; the workbook is the article Supporting File 2. Original attribution is retained.',
    'adaptation': 'Two supplementary QC tables parsed to JSON and CSV. Original cell text is retained in raw_rows; normalized missing values are null. Season is the literal Sample prefix. No QC threshold or ARG quantity is inferred.',
    'download_url': 'datasets/hk-community-source.xlsx',
    'samples_download_url': 'datasets/hk-community-samples.csv',
    'archive_download_url': 'datasets/hk-community-archive-runs.tsv',
    'measurement_scope': 'Published sample identifiers, sequencing quality metrics and assembly statistics',
    'study_counts': {'collected_samples': 190, 'sites': 95, 'districts': 18,
                     'figure_1_resistome_samples': 185, 'public_qc_samples': 189},
    'study_campaigns': [{'period': '2021-05', 'precision': 'month'}, {'period': '2022-01', 'precision': 'month'}],
    'sample_count': len(samples), 'table_row_counts': {'Table S1': 189, 'Table S2': 189},
    'season_counts': dict(Counter(r['season'] for r in samples)),
    'platform_qc_counts': {'Illumina': sum(r['illumina_qc_available'] for r in samples),
                           'Oxford Nanopore': sum(r['nanopore_qc_available'] for r in samples)},
    'missing_illumina_samples': [r['sample_id'] for r in samples if not r['illumina_qc_available']],
    'sample_metadata_missing': ['collection_date', 'area_id', 'district', 'latitude', 'longitude'],
    'availability': {'sample_index': True, 'sequencing_qc': True, 'assembly_qc': True,
                     'arg_abundance_matrix': False, 'clinical_pairing_matrix': False, 'clinical_ast': False},
    'count_explanation': 'The study reports 190 collected samples. Each public QC table contains 189 identifiers: 95 Summer and 94 Winter. Illumina metrics are unavailable (/) for four of these identifiers; Nanopore metrics are present for all 189. Figure 1 reports 185 samples in its resistome analysis.',
    'sample_location_explanation': 'The QC workbook does not provide a date, district, coordinate or accession crosswalk for individual Sample identifiers. These fields are left empty.',
    'archive_index': {
        'row_count': len(archive), 'record_type': 'ENA sequencing-run record',
        'platform_counts': dict(Counter(r['instrument_platform'] for r in archive)),
        'collection_date_min': min(r['collection_date'] for r in archive),
        'collection_date_max': max(r['collection_date'] for r in archive),
        'location_missing_count': sum(not r['location'] for r in archive),
        'crosswalk_available': False,
        'explanation': 'PRJNA1207805 currently exposes 406 ENA run records, with archive aliases and dates extending beyond the two paper campaigns. No verified crosswalk to the 189 published QC identifiers was obtained. Archive runs remain a separate index; they are not counted as 406 paper study samples or merged into QC rows.',
        'terms': 'ENA / INSDC free and unrestricted data-record access and redistribution, with appropriate citation',
        'terms_url': POLICY_URL,
    },
    'author_scripts': {
        'url': 'https://github.com/dingjiahui123/Sewage_ARG',
        'commit': 'cd16f411b900cf2b44028bef73cb0580d8ac7684',
        'files': ['README.md', 'Scripts'], 'contains_sample_matrix': False,
        'license': None, 'distributed': False,
        'note': 'The repository contains processing commands and no explicit license file. It is linked for method provenance; its code is not included in the application MIT grant.',
    },
    'sources': [
        {'id': 'supplement_qc', 'url': SUPP_URL, 'publisher_url': 'https://advanced.onlinelibrary.wiley.com/doi/10.1002/advs.202508389',
         'archive_member': 'ADVS-13-e08389-s002.xlsx', 'sha256': sha(SOURCE), 'bytes': SOURCE.stat().st_size,
         'retrieved': retrieved(HERE / 'supplements.zip'), 'license': 'CC BY 4.0'},
        {'id': 'article_xml', 'url': XML_URL, 'sha256': sha(HERE / 'article.xml'),
         'retrieved': retrieved(HERE / 'article.xml'), 'license': 'CC BY 4.0'},
        {'id': 'ena_run_index', 'url': ENA_URL, 'sha256': sha(HERE / 'ena-runs.tsv'),
         'bytes': (HERE / 'ena-runs.tsv').stat().st_size, 'retrieved': retrieved(HERE / 'ena-runs.tsv'),
         'terms_url': POLICY_URL},
    ],
}
data = {'meta': meta, 'samples': samples, 'tables': TABLES, 'archive_runs': archive}
(OUT / 'hk-community.js').write_text(
    '/* Published QC tables: Ding et al. (2026), CC BY 4.0. See meta for sources and changes. */\n'
    '(function(root){"use strict";const data=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) +
    ';root.HK_COMMUNITY_DATA=data;if(typeof module==="object"&&module.exports)module.exports=data;'
    '})(typeof globalThis!=="undefined"?globalThis:this);\n')
shutil.copyfile(SOURCE, OUT / 'hk-community-source.xlsx')
shutil.copyfile(HERE / 'ena-runs.tsv', OUT / 'hk-community-archive-runs.tsv')
for table in TABLES:
    with (OUT / ('hk-community-' + table['id'].replace('_', '-') + '.csv')).open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(table['fields'])
        writer.writerows(row['values'] for row in table['raw_rows'])
flat_samples = [{k: r[k] for k in ['sample_id', 'season', 'collection_date', 'area_id', 'district',
                'platform', 'illumina_qc_available', 'nanopore_qc_available', 'source_row_s1', 'source_row_s2', 'source_sha256']}
                for r in samples]
with (OUT / 'hk-community-samples.csv').open('w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(flat_samples[0])); w.writeheader(); w.writerows(flat_samples)
(HERE / 'source-manifest.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({'samples': len(samples), 'table_rows': [len(t['rows']) for t in TABLES],
                  'archive_runs': len(archive), 'source_sha256': sha(SOURCE),
                  'module_bytes': (OUT / 'hk-community.js').stat().st_size}, indent=2))

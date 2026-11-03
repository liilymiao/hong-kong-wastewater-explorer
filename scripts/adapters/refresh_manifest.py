"""Refresh the separately scoped public research-dataset index; no model runs."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / 'site' if (ROOT / 'site/datasets').is_dir() else ROOT


def read(rel):
    return json.loads((SITE / rel).read_text())


def sha(rel):
    return hashlib.sha256((SITE / rel).read_bytes()).hexdigest()


p = read('datasets/phlsb-metadata.json')
e = read('datasets/europe-provenance.json')
# Metadata are embedded in the standalone browser file as plain JSON.
hk_js = (SITE / 'datasets/hk-community.js').read_text()
h = json.loads(hk_js.split('const data=', 1)[1].split(';root.HK_COMMUNITY_DATA=', 1)[0])['meta']

datasets = [
    {
        'dataset_id': p['dataset_id'],
        'title': p['title']['en'],
        'js_file': 'datasets/phlsb.js',
        'js_sha256': sha('datasets/phlsb.js'),
        'source_raw_sha256': p['source_sha256'],
        'source_url': p['source_url'],
        'source_raw_file': 'datasets/phlsb-source.csv',
        'metadata_file': 'datasets/phlsb-metadata.json',
        'retrieved_at_utc': p['retrieved_at_utc'],
        'unit_of_observation': p['unit_of_observation'],
        'unit': ['reported count', 'reported percentage'],
        'temporal_resolution': 'annual',
        'source_years': p['source_years'],
        'counts': {k: p[k] for k in ['record_count', 'specimen_count', 'organism_count',
                                  'drug_analyte_count', 'marker_analyte_count',
                                  'reported_percent_count', 'count_only_record_count', 'not_reported_record_count']},
        'data_availability': {
            'official_annual_clinical_records': True, 'reported_percentages': True,
            'raw_source_cells': True, 'drug_resistance_separated_from_marker_positive': True,
            'independently_verified_drug_specific_ast_denominators': False,
            'clinical_wastewater_pairing': False, 'weekly_clinical_observations': False,
        },
        'third_party_terms': {
            'name': 'DATA.GOV.HK Terms of Use ' + p['terms']['version'],
            'url': p['terms']['url'], 'notice': 'THIRD_PARTY_NOTICES.md#phlsb-outpatient-resistance',
            'detail_notice': 'datasets/phlsb-README.txt',
        },
    },
    {
        'dataset_id': e['dataset_id'], 'title': e['title'],
        'js_file': 'datasets/europe-arg.js', 'js_sha256': sha('datasets/europe-arg.js'),
        'source_raw_sha256': e['source_sha256'], 'source_url': e['source_url'],
        'source_raw_filename': e['source_file'], 'source_raw_file': None,
        'source_raw_bundled': False, 'metadata_file': 'datasets/europe-provenance.json',
        'retrieved_at_utc': e['retrieved_at_utc'],
        'unit_of_observation': 'Biological sewage sample × ResFinder gene',
        'unit': e['unit'], 'normalization': e['normalization_status'],
        'start_date': e['start_date'], 'end_date': e['end_date'],
        'counts': {k: e[k] for k in ['independent_sample_count', 'gene_count', 'count_cell_count',
                                  'sequencing_run_count', 'count_linked_run_count', 'metadata_run_count',
                                  'metadata_biological_sample_count', 'city_count', 'plant_count']},
        'data_availability': {
            'gene_count_matrix': True, 'sample_metadata': True, 'exact_join_key': True,
            'normalized_abundance': False, 'clinical_ast': False,
            'clinical_wastewater_pairing': False,
        },
        'third_party_terms': {
            'name': e['license'], 'url': e['license_url'],
            'scope': e['license_scope'],
            'notice': 'THIRD_PARTY_NOTICES.md#european-sewage-resfinder-counts',
            'detail_notice': 'datasets/europe-NOTICE.txt',
        },
    },
    {
        'dataset_id': h['dataset_id'], 'title': h['title'],
        'js_file': 'datasets/hk-community.js', 'js_sha256': sha('datasets/hk-community.js'),
        'source_raw_sha256': h['source_sha256'], 'source_url': h['retrieval_url'],
        'article_url': h['source_url'], 'source_raw_file': 'datasets/hk-community-source.xlsx',
        'retrieved_at_utc': h['retrieved'],
        'unit_of_observation': 'Published Sample identifier × sequencing/assembly QC metric',
        'unit': ['read count', 'base count', 'read length', 'mean read quality'],
        'study_campaigns': h['study_campaigns'],
        'counts': {
            'published_qc_samples': h['sample_count'], 'table_row_counts': h['table_row_counts'],
            'season_counts': h['season_counts'], 'platform_qc_counts': h['platform_qc_counts'],
            'study_counts': h['study_counts'], 'separate_ena_run_records': h['archive_index']['row_count'],
        },
        'data_availability': dict(h['availability'], individual_qc_collection_dates=False,
                                 individual_qc_districts=False, qc_ena_accession_crosswalk=False,
                                 separate_ena_run_index=True),
        'third_party_terms': {
            'name': h['license'], 'url': h['license_url'],
            'notice': 'THIRD_PARTY_NOTICES.md#hong-kong-community-sewage-study',
            'detail_notice': 'datasets/hk-community-NOTICE.txt',
        },
        'additional_sources': [{
            'id': 'ena_run_index',
            'source_raw_file': 'datasets/hk-community-archive-runs.tsv',
            'source_raw_sha256': next(s['sha256'] for s in h['sources'] if s['id'] == 'ena_run_index'),
            'source_url': next(s['url'] for s in h['sources'] if s['id'] == 'ena_run_index'),
            'counts': h['archive_index']['platform_counts'],
            'third_party_terms_url': h['archive_index']['terms_url'],
            'linkage_status': 'Separate index; no verified crosswalk to the 189 QC identifiers',
        }],
    },
]
extension_files = ['ha-data.js','supply-data.js','bvbrc-data.js','rainfall-data.js','flu-data.js','global-sewage-data.js']
node = os.environ.get('NODE') or shutil.which('node')
if not node:
    candidate = Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
    if candidate.is_file(): node = str(candidate)
if not node: raise RuntimeError('Set NODE to a Node.js executable to inspect browser metadata')
for name in extension_files:
    js_file = 'datasets/' + name
    if not (SITE/js_file).is_file(): raise FileNotFoundError('Dataset not ready: '+js_file)
    m = json.loads(subprocess.check_output([node, '-e',
        'const fs=require("fs"),vm=require("vm"),c={window:{}};vm.createContext(c);vm.runInContext(fs.readFileSync(process.argv[1],"utf8"),c);const d=Object.values(c.window).find(x=>x&&x.meta);if(!d)throw Error("No dataset metadata");process.stdout.write(JSON.stringify(d.meta));',
        str(SITE/js_file)], text=True))
    count_fields = {k:v for k,v in m.items() if k.endswith('_count') or k.endswith('_counts')}
    counts = dict(m.get('counts', {}), **count_fields)
    terms = m.get('terms', {})
    if isinstance(terms,str): terms = {'name':terms}
    unit = m.get('unit') or ('Source units: mg/L, mm or missing; method/unit conflicts flagged' if m['dataset_id']=='bvbrc-ast' else m.get('dictionary',{}).get('value',{}).get('unit','Source-specific; see embedded dictionary'))
    metadata_candidates=[name.replace('-data.js','-metadata.json'),name.replace('-data.js','-provenance.json')]
    metadata_file=next(('datasets/'+n for n in metadata_candidates if (SITE/'datasets'/n).is_file()),js_file)
    datasets.append({
        'dataset_id':m['dataset_id'],'title':m['title'],'status':m.get('status'),
        'js_file':js_file,'js_sha256':sha(js_file),'source_raw_sha256':m['source_sha256'],
        'source_checksum_scope':m.get('checksum_scope','Complete source file bytes'),
        'source_url':m['source_url'],'source_raw_file':None,'source_raw_bundled':False,
        'metadata_file':metadata_file,'source_version':m.get('source_version'),
        'retrieved_at_utc':m.get('retrieved_at_utc'),'processing_version':m.get('processing_version',m.get('adapter_version')),
        'unit_of_observation':m.get('unit_of_observation',m.get('observation_unit',m.get('observation_grain'))),
        'unit':unit,'temporal_resolution':m.get('temporal_resolution'),
        'source_years':m.get('source_years',m.get('years')),
        'start_date':m.get('start_date',counts.get('date_min')),'end_date':m.get('end_date',counts.get('date_max')),'counts':counts,
        'scope_note':m.get('scope_note',m.get('notes')),
        'data_availability':m.get('data_availability',{'structured_observations':True}),
        'third_party_terms':dict(terms,notice='THIRD_PARTY_NOTICES.md'),
    })
assert len(datasets)==9
for d in datasets:
    d.setdefault('source_checksum_scope','Complete source file bytes')
manifest = {
    'schema_version': 1, 'release_version': '1.6.0',
    'scope': 'Additional public research datasets with independent source identities and terms. They do not alter the frozen COVID-19 scientific configuration 1.1 or its forecasts.',
    'frozen_covid_manifest': 'source_manifest.json', 'dataset_count': len(datasets), 'datasets': datasets,
}
(SITE / 'research-datasets.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({'datasets': len(datasets), 'path': 'site/research-datasets.json'}))

#!/usr/bin/env python3
"""Read the unmodified Becsei et al. supplementary workbook into factual query tables."""
from pathlib import Path
from collections import Counter,defaultdict
import datetime,hashlib,json,math,zipfile
from openpyxl import load_workbook
from openpyxl.utils.cell import get_column_letter
ROOT=Path(__file__).resolve().parents[2]
SITE = ROOT / "site" if (ROOT / "site/datasets").is_dir() else ROOT
SOURCE=ROOT/'work/data_sources/europe/41467_2024_51957_MOESM4_ESM.xlsx'
OUT=SITE/'datasets';QA=ROOT/'qa';OUT.mkdir(parents=True,exist_ok=True);QA.mkdir(parents=True,exist_ok=True)
SOURCE_URL='https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11364805/supplementaryFiles'
ARTICLE='https://www.nature.com/articles/s41467-024-51957-8'
DOI='10.1038/s41467-024-51957-8'
SHA=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
with zipfile.ZipFile(SOURCE) as z: assert z.testzip() is None
wb=load_workbook(SOURCE,read_only=True,data_only=True)
def clean(v):
 if isinstance(v,(datetime.date,datetime.datetime)):return v.date().isoformat() if isinstance(v,datetime.datetime) else v.isoformat()
 if isinstance(v,float) and v.is_integer():return int(v)
 return v

def read_sheet(name):
 return [(i,[clean(v) for v in r]) for i,r in enumerate(wb[name].values,1) if any(v is not None for v in r)]
mr=read_sheet('Supplementary Data 1');headers=mr[0][1][:13]
runs=[];by_key={};by_bio=defaultdict(list)
for rn,row in mr[1:]:
 r=dict(zip(headers,row[:13]));assert all(r[k] is not None for k in headers)
 r['sample_id']=str(r['ENA_ALIAS'])+'_'+str(r['REPLICA']);r['source_sheet']='Supplementary Data 1';r['source_row']=rn;r['source_cell_range']=f'A{rn}:M{rn}';r['source_file']=SOURCE.name;r['source_sha256']=SHA
 r['run_url']='https://www.ebi.ac.uk/ena/browser/view/'+r['ENA_RUN_ACCESSION'];r['sample_url']='https://www.ebi.ac.uk/ena/browser/view/'+r['ENA_SAMPLE_ACCESSION']
 assert r['sample_id'] not in by_key
 by_key[r['sample_id']]=r;by_bio[r['ENA_SAMPLE_ACCESSION']].append(r);runs.append(r)
cr=read_sheet('Supplementary Data 3');genes=[v for v in cr[0][1][1:] if v is not None];assert len(genes)==len(set(genes))
samples=[];counts=[];matrix_ids=[];cell_count=0;zero_count=0;noninteger=[];missing_count=0
for rn,row in cr[1:]:
 sid=row[0];assert sid not in matrix_ids;matrix_ids.append(sid);assert sid in by_key
 original=by_key[sid];ar=by_bio[original['ENA_SAMPLE_ACCESSION']]
 sample={'sample_id':sid,'city':original['CITY'],'plant':original['PLANT'],'date':original['COLLECTION_DATE'],'country':original['COUNTRY'],'latitude':original['LATITUDE'],'longitude':original['LONGITUDE'],'ENA_ALIAS':original['ENA_ALIAS'],'REPLICA':original['REPLICA'],'ENA_SAMPLE_ACCESSION':original['ENA_SAMPLE_ACCESSION'],'sampling_type':original['SAMPLING TYPE'],'sewage_type':original['SEWAGE TYPE'],'complete_name':original['COMPLETE_NAME'],'run_accessions':[r['ENA_RUN_ACCESSION'] for r in ar],'count_linked_run_accessions':[original['ENA_RUN_ACCESSION']],'metadata_source_rows':[r['source_row'] for r in ar],'count_linked_metadata_row':original['source_row'],'source_sheet':'Supplementary Data 3','source_row':rn,'source_cell_range':f'B{rn}:{get_column_letter(len(genes)+1)}{rn}','source_file':SOURCE.name,'source_sha256':SHA,'sample_url':original['sample_url']}
 vals=[]
 for gi,v in enumerate(row[1:len(genes)+1]):
  if v is None or v=='':vals.append(None);missing_count+=1;continue
  n=float(v);assert math.isfinite(n) and n>=0 and n.is_integer(),(sid,genes[gi],v)
  n=int(n);assert str(n)==str(v) or float(v)==n;vals.append(n);cell_count+=1;zero_count+=n==0
 assert len(vals)==len(genes)
 samples.append(sample);counts.append(vals)
assert len(samples)==235 and len(genes)==554
assert len(set(s['ENA_SAMPLE_ACCESSION'] for s in samples))==len(samples)
unique_runs=sorted({x for s in samples for x in s['run_accessions']});direct_runs=sorted({x for s in samples for x in s['count_linked_run_accessions']})
not_counted=[r for r in runs if r['sample_id'] not in set(matrix_ids)]
no_matrix_bio=sorted(set(by_bio)-set(s['ENA_SAMPLE_ACCESSION'] for s in samples))
dictionary_source=read_sheet('Supplementary Data 5')
dictionary_index=[{'table':r[0],'column':r[1],'source_sheet':'Supplementary Data 5','source_row':rn} for rn,r in dictionary_source[1:] if r[0] is not None and r[1] is not None]
meta={'dataset_id':'europe-arg','dataset_version':'2024-supplement-v1','title':'European sewage ResFinder gene counts','citation':'Becsei A, Fuschi A, Otani S, et al. Nature Communications 15, 7551 (2024).','doi':DOI,'article_url':ARTICLE,'project_accession':'PRJEB68319','project_url':'https://www.ebi.ac.uk/ena/browser/view/PRJEB68319','source_url':SOURCE_URL,'source_file':SOURCE.name,'source_sha256':SHA,'source_bytes':SOURCE.stat().st_size,'retrieved_at_utc':datetime.datetime.fromtimestamp(SOURCE.stat().st_mtime,datetime.timezone.utc).isoformat(),'source_date':'2024-08-30','license':'CC BY-NC-ND 4.0 (article notice; no separate data licence found in the checked workbook or article XML)','license_url':'https://creativecommons.org/licenses/by-nc-nd/4.0/','license_scope':'Third-party source data; not covered by the application MIT licence. Exact factual counts and sample fields are extracted; source values are unchanged. No article figures or prose are included.','independent_sample_count':len(samples),'gene_count':len(genes),'count_cell_count':len(samples)*len(genes),'sequencing_run_count':len(unique_runs),'count_linked_run_count':len(direct_runs),'metadata_run_count':len(runs),'metadata_biological_sample_count':len(by_bio),'metadata_only_biological_samples':no_matrix_bio,'start_date':min(s['date'] for s in samples),'end_date':max(s['date'] for s in samples),'city_count':len(set(s['city'] for s in samples)),'plant_count':len(set(s['plant'] for s in samples)),'unit':'raw gene counts','normalization_status':'Not normalized for cross-sample abundance comparison','clinical_pairing':'No clinical susceptibility pair table in this workbook','join_rule':'Supplementary Data 3.sample_id = string(Supplementary Data 1.ENA_ALIAS) + "_" + string(REPLICA)','run_count_rule':'Count-linked runs use the exact alias/replica key. Associated run counts include all metadata runs with the same ENA_SAMPLE_ACCESSION as a selected matrix row; their contribution to a count value is not inferred.','measurement_method':'Sequence-fragment counts mapped with KMA v1.2.8 to ResFinder commit 3eedbde; related alleles grouped at 90% identity and coverage in the source analysis.','changes':'Typed numeric count strings as non-negative integers; dates formatted ISO 8601; metadata joined by the reported key. No values were normalized, imputed or averaged.'}
dictionary={'sample_id':'Published matrix identifier; ENA_ALIAS_REPLICA, not a new isolate identifier.','date':'Collection date, ISO 8601; source COLLECTION_DATE.','city':'Source CITY.','plant':'Source PLANT; do not infer a clinical service area.','counts':'Rows align with samples; columns align with genes. Counts are raw sequence-fragment counts and zero is a reported zero.','run_accessions':'Every metadata run sharing the selected biological ENA_SAMPLE_ACCESSION.','count_linked_run_accessions':'Metadata run matching the matrix alias/replica key exactly.','source_row':'One-based spreadsheet row in source_sheet.','gene_source_column':'gene index + 2, one-based; header row 1 in Supplementary Data 3.','normalization':'No concentration or relative abundance is derived. Source workbook lacks the full depth/length inputs needed for normalization.'}
data={'meta':meta,'genes':genes,'samples':samples,'counts':counts,'runs':runs,'dictionary':dictionary,'dictionary_source_index':dictionary_index}
script='/* Factual source values extracted from the attributed supplementary workbook. */\nwindow.EUROPE_ARG_DATA='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n'
(OUT/'europe-arg.js').write_text(script)
(OUT/'europe-provenance.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
# Re-open the written JSON and compare every numerical value against its exact workbook cell.
parsed=json.loads(script.split('window.EUROPE_ARG_DATA=',1)[1].rstrip(';\n'))
assert parsed['counts']==counts and parsed['genes']==genes and len(parsed['runs'])==278
for i,(rn,row) in enumerate(cr[1:]):
 for j,v in enumerate(row[1:len(genes)+1]):
  assert parsed['counts'][i][j]==(None if v in [None,''] else int(v))
assert len(unique_runs)==274 and len(direct_runs)==235
proof={'status':'passed','source_file':str(SOURCE.relative_to(ROOT)),'source_sha256':SHA,'source_xlsx_crc':'passed','all_matrix_cells_compared':cell_count,'reported_zero_count':zero_count,'missing_count':missing_count,'matrix_rows':len(samples),'genes':len(genes),'unique_biological_samples':len(set(s['ENA_SAMPLE_ACCESSION'] for s in samples)),'unmatched_matrix_rows':0,'ambiguous_matrix_keys':0,'count_linked_runs':len(direct_runs),'associated_runs_for_matrix_samples':len(unique_runs),'all_metadata_runs':len(runs),'all_metadata_biological_samples':len(by_bio),'metadata_only_biological_samples':no_matrix_bio,'metadata_keys_without_count_rows':len(not_counted),'cities':dict(Counter(s['city'] for s in samples)),'plants':dict(Counter(s['plant'] for s in samples)),'date_range':[meta['start_date'],meta['end_date']],'output_bytes':len(script.encode()),'output_sha256':hashlib.sha256(script.encode()).hexdigest(),'first_cell':{'sample_id':samples[0]['sample_id'],'gene':genes[0],'count':counts[0][0],'source_cell':'B2'},'last_cell':{'sample_id':samples[-1]['sample_id'],'gene':genes[-1],'count':counts[-1][-1],'source_cell':get_column_letter(len(genes)+1)+str(cr[-1][0])}}
(QA/'europe-ingestion-verification.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(proof,ensure_ascii=False,indent=2))

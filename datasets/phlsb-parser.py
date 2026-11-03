#!/usr/bin/env python3
"""Parse the downloaded PHLSB annual wide CSV; retain reported values and raw cells."""
from pathlib import Path
import argparse,csv,hashlib,json,re,shutil,datetime
ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source',type=Path,default=ROOT/'work/data_sources/phlsb-source.csv')
parser.add_argument('--metadata',type=Path,default=ROOT/'work/data_sources/phlsb-download.json')
parser.add_argument('--out',type=Path,default=ROOT/'site/datasets')
parser.add_argument('--report',type=Path,default=ROOT/'qa/phlsb-verification.json')
args=parser.parse_args()
SRC=args.source
OUT=args.out;OUT.mkdir(parents=True,exist_ok=True)
SOURCE_URL='https://www.chp.gov.hk/files/misc/bac_path_isolation_and_antimicrobial_resistance_en.csv'
PAGE_URL='https://www.chp.gov.hk/en/statistics/data/10/641/697/7145.html'
RESOURCE_URL='https://data.gov.hk/en-data/dataset/hk-dh-dh_phlsb-phlsb-bac-path-isolation-antimicrobial-resistance/resource/cc032b80-99f7-4116-8205-3e019829113b'
download=json.loads(args.metadata.read_text())
if 'source' in download:
 info=download['source'];download={'sha256':info['source_sha256'],'bytes':info['source_bytes'],'retrieved_at_utc':info['retrieved_at_utc'],'headers':{'Last-Modified':info.get('http_last_modified')}}
assert hashlib.sha256(SRC.read_bytes()).hexdigest()==download['sha256'], 'Source digest does not match metadata'
raw_rows=list(csv.reader(SRC.read_text(encoding='utf-8-sig').splitlines()))
raw_footnotes={str(i):r[0] for i,r in enumerate(raw_rows,1) if i>=73 and r and r[0]}
notes={'*':'Klebsiella pneumoniae complex is intrinsically resistant to ampicillin (source reports 100%).','^':'Proteus mirabilis is intrinsically resistant to nitrofurantoin (source reports 100%).','#':'One isolate was negative for the CPE genes tested.'}
specimen_map={'Throat swab specimens':'Throat swab','Sputum specimens':'Sputum','Urine specimens':'Urine','Enteric specimens':'Enteric','Soft tissue specimens':'Soft tissue'}
markers={'BL+':'BL','ESBL+':'ESBL','KPC+':'KPC','NDM+':'NDM','OXA-48-like+':'OXA-48-like'}
clean=lambda x:re.sub(r'\s+',' ',x.replace('?',' ')).strip()
blocks=[];block=None;specimen=None;years=None
for i,r in enumerate(raw_rows,1):
 r=r+['']*(8-len(r))
 if r[0] in specimen_map:specimen=r[0];block=None;continue
 if r[0]=='Organism':
  years=[int(x) for x in r[2:8]];assert years==list(range(2020,2026));continue
 if i>=72:break
 if not specimen or not any(r) or r[1]=='Resistance phenotype':continue
 if r[0]:
  block={'specimen_raw':specimen,'organism_raw':r[0],'organism_row':i,'values':[],'totals':None,'total_row':None};blocks.append(block)
 if block is None:continue
 if r[1]=='No.':block['totals']=r[2:8];block['total_row']=i;continue
 if r[1]=='[MRSA]':
  assert block['values'][-1]['analyte_raw']=='Oxacillin'
  block['values'][-1]['annotation']='MRSA';block['values'][-1]['annotation_row']=i;continue
 if r[1]:block['values'].append({'analyte_raw':r[1],'row':i,'values':r[2:8],'annotation':'','annotation_row':None})
rows=[];parsed=missing=integer_only=0;arithmetic=[]
for b in blocks:
 assert b['totals'] is not None and len(b['totals'])==6
 organism=clean(b['organism_raw']).rstrip('*^').strip()
 for v in b['values']:
  marker=v['analyte_raw'] in markers
  for j,year in enumerate(years):
   cell=v['values'][j];token=cell.strip();total_raw=b['totals'][j]
   total=int(total_raw) if re.fullmatch(r'\d+',total_raw) else None
   count=percent=None;status='reported';decimals=None
   m=re.fullmatch(r'(\d+)\s*\??\s*\((\d+(?:\.\d+)?)%\)\s*(#?)',token)
   if m:count=int(m[1]);percent=float(m[2]);decimals=len(m[2].split('.')[1]) if '.' in m[2] else 0;parsed+=1
   elif re.fullmatch(r'\d+',token):count=int(token);status='count_only';integer_only+=1
   elif token in {'','-'}:status='not_reported';missing+=1
   else:raise ValueError(f'Unrecognized cell at CSV row {v["row"]} year {year}: {token!r}')
   footnote_keys=[x for x in '*^#' if (x in b['organism_raw'] if x!='#' else x in cell)]
   source_rows=[v['row'],b['total_row']]
   if v['annotation_row']:source_rows.append(v['annotation_row'])
   analyte=markers.get(v['analyte_raw'],clean(v['analyte_raw']))
   row={'record_id':f'phlsb-{year}-r{v["row"]}','year':year,'specimen':specimen_map[b['specimen_raw']],'organism':organism,'analyte':analyte,'measure_type':'marker_positivity' if marker else 'drug_resistance','result_definition':'positive' if marker else 'R','result_label':'Marker-positive proportion' if marker else 'Resistant proportion (R)','count':count,'reported_total':total,'reported_percent':percent,'reported_percent_decimals':decimals,'reported_percent_text':m[2]+'%' if m else None,'value_status':status,'annotation':v['annotation'],'footnote':' '.join(notes[x] for x in footnote_keys),'footnote_markers':''.join(footnote_keys),'raw_specimen':b['specimen_raw'],'raw_organism':b['organism_raw'],'raw_analyte':v['analyte_raw'],'raw_value':cell,'raw_reported_total':total_raw,'source_rows':source_rows,'source_data_row':v['row'],'source_total_row':b['total_row'],'source_column':j+3,'source_url':SOURCE_URL,'source_file':'phlsb-source.csv','source_sha256':download['sha256'],'source_snapshot_utc':download['retrieved_at_utc']}
   rows.append(row)
   assert count is None or 0<=count<=total
   assert percent is None or 0<=percent<=100
   if percent is not None and total:
    difference=abs(100*count/total-percent);tolerance=.5*10**(-decimals)+1e-9
    arithmetic.append({'record_id':row['record_id'],'difference_pp':difference,'rounding_tolerance_pp':tolerance,'consistent':difference<=tolerance})
meta={'dataset_id':'phlsb-outpatient','title':{'en':'Hong Kong PHLSB outpatient antimicrobial resistance','zh':'香港 PHLSB 门诊细菌耐药统计'},'dataset_version':'2026-11-03-'+download['sha256'][:12],'status':'loaded','years':years,'temporal_resolution':'annual','region':'Hong Kong','unit_of_observation':'Year × specimen type × organism × drug or resistance marker','record_count':len(rows),'specimen_count':len(specimen_map),'organism_count':len({r['organism'] for r in rows}),'drug_analyte_count':len({r['analyte'] for r in rows if r['measure_type']=='drug_resistance'}),'marker_analyte_count':len(markers),'reported_percent_count':parsed,'count_only_record_count':integer_only,'not_reported_record_count':missing,'source':{'url':SOURCE_URL,'resource_url':RESOURCE_URL,'detail_2025_url':PAGE_URL,'provider':'Department of Health, Hong Kong SAR Government; Public Health Laboratory Services Branch','retrieved_at_utc':download['retrieved_at_utc'],'source_sha256':download['sha256'],'source_bytes':download['bytes'],'http_last_modified':download['headers'].get('Last-Modified'),'resource_last_updated':'2026-04-22','resource_update_frequency':'Quarterly','observation_frequency':'Annual'},'terms':{'url':'https://data.gov.hk/en/terms-and-conditions','version':'1.2 (26 May 2025)','attribution':'Source: Department of Health, Hong Kong SAR Government, via DATA.GOV.HK. Source data remain the intellectual property of the Government and relevant organisations.','scope':'Data are redistributed and restructured with attribution under the DATA.GOV.HK Terms of Use; project MIT license applies to the parser and interface, not the source data.'},'definitions':{'R':'Resistant. The 2025 detailed PHLSB table reports R and I separately; these merged CSV drug values match the R rows.','I':'Intermediate. I is not present as separate rows in this merged CSV and is not added to R.','positive':'Marker-positive count. BL, ESBL, KPC, NDM and OXA-48-like are distinguished from drug resistance.','reported_total':'The source No. row for that organism, specimen and year. Retained as reported; it is not re-labelled as an independently verified drug-specific AST denominator.','reported_percent':'Official reported percentage, retained with its source precision. Percentages are never reconstructed for count-only cells.','not_reported':'A source dash or blank remains null; a missing result is not changed to zero.','question_mark':'The source CSV contains literal question marks in place of separators in names and numeric cells. The raw strings are retained; normalized labels use spaces and the numeric parser accepts only the observed count?(percent%) pattern.','source_rows':'1-based logical CSV row numbers; source_data_row holds the observation and source_total_row holds its No. row.'},'normalization_rules':['Forward-fill organism only inside its specimen block.','Attach each block’s No. row by year; retain it separately as reported_total.','Preserve raw labels and cells, footnote symbols, cell coordinates and source digest.','Remove * and ^ from normalized organism labels while retaining their source footnotes.','Keep plus-labelled resistance markers separate from drug_resistance.','Do not create rows for intrinsic-resistance footnotes; no drug result cell exists for them.','Carry [MRSA] as an annotation to Oxacillin.','No clinical–wastewater pairing or predictive analysis is included.'],'source_footnotes':raw_footnotes,'acceptance_example':{'year':2025,'specimen':'Urine','organism':'Escherichia coli','analyte':'Levofloxacin','count':3038,'reported_total':8171,'reported_percent':37.2,'result_definition':'R','separate_2025_intermediate_count':355,'separate_2025_intermediate_percent':4.3,'intermediate_source':PAGE_URL,'intermediate_added_to_dataset':False}}
meta.update(source_sha256=download['sha256'],retrieved_at_utc=download['retrieved_at_utc'],source_url=SOURCE_URL,license_url='https://data.gov.hk/en/terms-and-conditions',source_years=years)
obj={'meta':meta,'rows':rows}
(OUT/'phlsb.json').write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':'))+'\n')
(OUT/'phlsb.js').write_text('/* Official PHLSB annual data; source attribution and definitions are in meta. */\nwindow.PHLSB_DATA='+json.dumps(obj,ensure_ascii=False,separators=(',',':'))+';\n')
(OUT/'phlsb-metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
if SRC.resolve()!=(OUT/'phlsb-source.csv').resolve():shutil.copyfile(SRC,OUT/'phlsb-source.csv')
with (OUT/'phlsb-long.csv').open('w',newline='',encoding='utf-8-sig') as f:
 writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader()
 for row in rows:writer.writerow({k:json.dumps(v) if isinstance(v,list) else v for k,v in row.items()})
(OUT/'phlsb-README.txt').write_text('PHLSB outpatient antimicrobial resistance · 2020–2025\n\nSource: Department of Health, Hong Kong SAR Government, via DATA.GOV.HK.\n'+SOURCE_URL+'\n'+RESOURCE_URL+'\n\nphlsb-source.csv is the byte-identical official download. phlsb-long.csv and phlsb.json are derived annual long tables. phlsb.js exposes the same object as window.PHLSB_DATA.\n\nOne row represents a year, specimen type, organism and drug or resistance marker. Drug R and marker-positive results are separate. The official percentages and No. organism totals are retained; the totals are not independently verified drug-specific AST denominators. Count-only markers have null reported_percent, and dashes remain missing.\n\nThe provider updates the resource quarterly; observations in this snapshot are annual. Raw values, symbols, source row/column coordinates and SHA256 accompany each record. Details and transformation rules are in phlsb-metadata.json.\n\nSource terms: https://data.gov.hk/en/terms-and-conditions\nReproduce the long table with: python3 phlsb-parser.py --source phlsb-source.csv --metadata phlsb-metadata.json --out regenerated --report regenerated/verification.json\n\nProject-owned parser and interface: MIT. Source-data ownership remains with the Government and relevant organisations.\n')
example=[r for r in rows if (r['year'],r['specimen'],r['organism'],r['analyte'])==(2025,'Urine','Escherichia coli','Levofloxacin')]
assert len(example)==1 and tuple(example[0][k] for k in ['count','reported_total','reported_percent','result_definition'])==(3038,8171,37.2,'R')
assert len({r['record_id'] for r in rows})==len(rows)
assert not [r for r in rows if r['measure_type']=='marker_positivity' and r['result_definition']=='R']
assert all(r['reported_percent'] is None for r in rows if r['value_status']!='reported')
assert all(r['count'] is None for r in rows if r['value_status']=='not_reported')
assert all(a['consistent'] for a in arithmetic),[a for a in arithmetic if not a['consistent']]
assert len(rows)==sum(len(b['values'])*6 for b in blocks)
# Independent raw-cell lookup and total lookup for every derived row.
for r in rows:
 assert raw_rows[r['source_data_row']-1][r['source_column']-1]==r['raw_value']
 assert raw_rows[r['source_total_row']-1][r['source_column']-1]==r['raw_reported_total']
files={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in OUT.glob('phlsb*') if p.is_file()}
report={'status':'passed','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256':download['sha256'],'years':years,'blocks':len(blocks),'rows':len(rows),'reported_percent_records':parsed,'count_only_records':integer_only,'not_reported_records':missing,'source_rows_reconciled':len(rows),'arithmetic_reconciliation_to_reported_total_not_ast_denominator_validation':{'records':len(arithmetic),'all_within_reported_rounding_precision':all(a['consistent'] for a in arithmetic)},'acceptance_example':example[0],'official_detail_evidence':{'url':PAGE_URL,'R_count':3038,'I_count':355,'R_percent':37.2,'I_percent':4.3,'reported_total':8171},'checks':['all original measure cells parsed once per year','source row/column and reported total reconciled for every record','year range and specimen blocks verified','numeric ranges valid','no synthesized percentages for count-only cells','source dashes remain null','drug R and marker positivity distinct','footnotes retained','source file byte-identical','unique record IDs','acceptance record matches official 2025 detailed R table'],'public_files':files}
args.report.parent.mkdir(parents=True,exist_ok=True)
args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['status','rows','blocks','reported_percent_records','count_only_records','not_reported_records']},indent=2))

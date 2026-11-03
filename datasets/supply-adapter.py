#!/usr/bin/env python3
"""Fetch/parse CHP annual wholesale supply tables. Python standard library only.

python3 scripts/adapters/supply.py --fetch
python3 scripts/adapters/supply.py --source work/data_sources/supply-source.html \
  --retrieval work/data_sources/supply-source.html.retrieval.json

Validation precedes output replacement. A failed refresh retains the last usable data.
The extracted factual values retain source attribution; no source open licence is inferred.
"""
import argparse, csv, datetime, hashlib, io, json, os, re, tempfile, urllib.request
from html.parser import HTMLParser
from pathlib import Path

SOURCE_URL='https://www.chp.gov.hk/en/statistics/data/10/100044/6960.html'
TERMS_URL='https://www.chp.gov.hk/en/static/24027.html'
ADAPTER_VERSION='1.0.0'
TITLES=['Overall antimicrobial supply','Private doctors','Hospital Authority','Community pharmacies','Private hospitals','Veterinary surgeons']
HUMAN_SECTORS={'Private doctors','Hospital Authority','Private hospitals','Dentists','Community pharmacies','Department of Health','Total'}
GROUPS={'Tetracyclines','Beta-lactam antibacterials, penicillins','Other beta-lactam antibacterials','Macrolides, lincosamides and streptogramins','Aminoglycoside antibacterials','Quinolone antibacterials'}

def clean(s): return ' '.join(s.split())
class Tables(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.tables=[];self.heading='';self.h2=None;self.table=None;self.row=None;self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=='h2':self.h2=[]
        if tag=='table':
            if self.table is not None:raise ValueError('Nested table schema unsupported')
            self.table={'title':self.heading,'rows':[]}
        elif tag=='tr' and self.table is not None:self.row=[]
        elif tag in ('th','td') and self.row is not None:
            if any(k in ('rowspan','colspan') and v!='1' for k,v in attrs):raise ValueError('Merged cell schema unsupported')
            self.cell=[]
    def handle_data(self,data):
        if self.h2 is not None:self.h2.append(data)
        if self.cell is not None:self.cell.append(data)
    def handle_endtag(self,tag):
        if tag=='h2' and self.h2 is not None:self.heading=clean(''.join(self.h2));self.h2=None
        if tag in ('th','td') and self.cell is not None:self.row.append(clean(''.join(self.cell)));self.cell=None
        elif tag=='tr' and self.row is not None:self.table['rows'].append(self.row);self.row=None
        elif tag=='table' and self.table is not None:self.tables.append(self.table);self.table=None

def parse(source,retrieval):
    text=source.decode('utf-8-sig');parser=Tables();parser.feed(text);tables=parser.tables
    if [t['title'] for t in tables]!=TITLES:raise ValueError('Expected six named supply tables; source schema changed')
    if 'defined daily doses per 1,000 inhabitants per day' not in text.lower():raise ValueError('DID definition missing')
    if 'Non-human use antimicrobials supplied to veterinary surgeons and farmers are excluded' not in text:raise ValueError('Human-use scope footnote missing')
    provisional=sorted({int(x) for x in re.findall(r'Data for (\d{4}) is provisional',text)})
    source_sha=hashlib.sha256(source).hexdigest()
    if retrieval.get('sha256') and retrieval['sha256']!=source_sha:raise ValueError('Retrieval/source digest mismatch')
    revision=re.search(r"last_revision_date=['\"]([^'\"]+)",text)
    revision=revision.group(1).replace('/','-') if revision else None
    version=(revision or 'undated')+'-'+source_sha[:12]
    rows=[];table_audit=[];all_years=set()
    for ti,table in enumerate(tables,1):
        header=table['rows'][0]
        if header[0] not in ('Sector*','Antimicrobial'):raise ValueError('Unrecognized first column')
        years=[int(v) if re.fullmatch(r'\d{4}',v) else None for v in header[1:]]
        if any(y is None or not 1900<=y<=2100 for y in years) or years!=sorted(set(years)):raise ValueError('Invalid/duplicate/year column order')
        all_years.update(years)
        labels=[r[0] for r in table['rows'][1:]]
        if len(labels)!=len(set(labels)):raise ValueError('Duplicate measure row')
        if ti==1 and set(labels)!=HUMAN_SECTORS:raise ValueError('Overall sector schema changed')
        if ti>1 and set(labels)!=GROUPS:raise ValueError('Antimicrobial group schema changed')
        for ri,row in enumerate(table['rows'][1:],2):
            if len(row)!=len(header):raise ValueError('Ragged source row')
            sector=row[0] if ti==1 else table['title'];group='All antimicrobials' if ti==1 else row[0]
            for ci,(year,raw) in enumerate(zip(years,row[1:]),2):
                if re.fullmatch(r'\d+(?:\.\d+)?',raw):value=float(raw);status='reported'
                elif raw in ('','-','—','N/A'):value=None;status='not_reported'
                else:raise ValueError('Unknown source value '+repr(raw))
                rows.append({'record_id':f'supply-t{ti}-r{ri}-y{year}','source_id':'antimicrobial-supply','year':year,'sector':sector,'antimicrobial_group':group,'measure':'wholesale_supply','value':value,'unit':'DID','human_use_flag':sector!='Veterinary surgeons','provisional':year in provisional,'value_status':status,'reported_precision':len(raw.split('.')[1]) if '.' in raw else 0 if value is not None else None,'aggregation_level':'human_total' if sector=='Total' else 'sector_total' if ti==1 else 'sector_drug_group','source_url':SOURCE_URL,'source_version':version,'source_sha256':source_sha,'source_table':ti,'source_table_title':table['title'],'source_row':ri,'source_column':ci,'raw_cell':raw,'raw_sector':sector,'raw_group':row[0] if ti>1 else None,'footnote':('Human-use total excludes veterinary surgeons and farmers. ' if ti==1 else 'Veterinary supply is separate from the human-use total. ' if sector=='Veterinary surgeons' else '')+('Provisional and subject to revision.' if year in provisional else '')})
        table_audit.append({'source_table':ti,'title':table['title'],'years':years,'measure_rows':len(labels),'observation_count':len(labels)*len(years)})
    if not set(provisional).issubset(all_years):raise ValueError('Provisional year is absent from data')
    dictionary={
      'year':'Annual survey/statistical year; no artificial observation date is assigned.',
      'sector':'Original supply recipient sector. Total is the published human-use aggregate; veterinary surgeons and farmers are excluded from this aggregate.',
      'antimicrobial_group':'Original broad pharmacological group or All antimicrobials. Six selected classes are supplied per detailed sector table; their sum is not the full sector total.',
      'measure':'Wholesale supply reported by licensed wholesalers; an indirect use indicator, not a dispensing, prescribing or consumption measurement.',
      'value':'Original reported numeric value; no recomputation from rounded sector rows.',
      'unit':'DID = defined daily doses per 1,000 inhabitants per day. DDD is a technical unit and does not equal a prescribed dose.',
      'human_use_flag':'False for Veterinary surgeons. True for the six human sectors and the published human Total. Never sum human Total with its component sectors.',
      'provisional':'True only for years explicitly marked provisional by the source footnotes.',
      'raw_cell':'Source text retains its decimal precision; a printed 0.000 is a reported rounded value, not a missing value or proof of absence.',
      'source_table/source_row/source_column':'1-based HTML table, row (including header), and column, respectively.',
      'aggregation_level':'human_total, sector_total, or sector_drug_group. Totals and detail groups overlap and must not be added together.',
      'value_status':'reported or not_reported. Missing tokens stay null and are never replaced by zero.'}
    meta={'dataset_id':'antimicrobial-supply','title':'Hong Kong antimicrobial wholesale supply','provider':'Department of Health, Hong Kong SAR Government / Drug Office','region':'Hong Kong','study_type':'Annual licensed drug wholesaler survey','temporal_resolution':'annual','unit_of_observation':'Year × supply recipient sector × antimicrobial group','update_frequency':'Annual','source_url':SOURCE_URL,'source_sha256':source_sha,'source_version':version,'dataset_version':version,'retrieved_at_utc':retrieval['retrieved_at_utc'],'source_last_revision':revision,'status':'loaded','record_count':len(rows),'source_years':sorted(all_years),'years':sorted(all_years),'provisional_years':provisional,'unit':'DID','terms':{'url':TERMS_URL,'copyright':'Government of the Hong Kong Special Administrative Region','open_license':None,'status':'No open data licence inferred from the checked CHP page','scope':'Factual numeric values are extracted with attribution; original HTML/PDF remain linked rather than redistributed. CHP copyright permission explicitly covers complete, unmodified copies for personal/internal use. Public reuse permission for the table compilation is not established. Source material is outside the application MIT licence.'},'dictionary':dictionary,'notes':['This snapshot uses only the current HTML tables; historical report values are not spliced into it.','The December 2025 report gives 2024 total as 18.33 DID (PDF page 4); this HTML snapshot reports 18.34 DID. Keep the source version attached.','Quinolone antibacterials are a drug class. A comparison with PHLSB levofloxacin resistance is annual background comparison with different endpoints.'],'audit':{'adapter_version':ADAPTER_VERSION,'tables':table_audit,'source_bytes':len(source),'independent_sample_count':None,'statistical_record_count':len(rows),'human_use_records':sum(r['human_use_flag'] for r in rows),'veterinary_records':sum(not r['human_use_flag'] for r in rows),'missing_records':sum(r['value'] is None for r in rows),'method_report_url':'https://www.chp.gov.hk/files/pdf/wholesale_result_2024.pdf','method_report_sha256':'bb1f3a5306d4271a72096e9629b2b27cb231346d05c67bd905f4ce0db10de219','method_pages':[4,26,27],'processing':'All six tables unpivoted without interpolation, normalization or imputation. Original decimal cells and table positions retained.'}}
    if len({r['record_id'] for r in rows})!=len(rows):raise ValueError('Duplicate record ID')
    return {'meta':meta,'rows':rows}

def atomic(path,content):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('wb',dir=path.parent,delete=False) as f:f.write(content if isinstance(content,bytes) else content.encode());name=f.name
    os.replace(name,path)
def main():
    p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');p.add_argument('--source',default='work/data_sources/supply-source.html');p.add_argument('--retrieval',default='work/data_sources/supply-source.html.retrieval.json');p.add_argument('--out',default='site/datasets');p.add_argument('--report',default='qa/supply-validation.json');a=p.parse_args()
    if a.fetch:
        req=urllib.request.Request(SOURCE_URL,headers={'User-Agent':'HongKongWastewaterExplorerResearch/1.6'})
        with urllib.request.urlopen(req,timeout=60) as response:source=response.read();headers=dict(response.headers)
        retrieval={'url':SOURCE_URL,'sha256':hashlib.sha256(source).hexdigest(),'bytes':len(source),'retrieved_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'headers':headers}
    else:source=Path(a.source).read_bytes();retrieval=json.loads(Path(a.retrieval).read_text())
    data=parse(source,retrieval)
    out=Path(a.out);serialized=json.dumps(data,ensure_ascii=False,separators=(',',':'))
    s=io.StringIO(newline='');w=csv.DictWriter(s,fieldnames=list(data['rows'][0]));w.writeheader();w.writerows(data['rows'])
    files={'supply-data.js':'/* Factual wholesale statistics; source terms and definitions retained in meta. */\nwindow.EXT_SUPPLY_DATA='+serialized+';\n','supply-data.json':serialized+'\n','supply-data.csv':'\ufeff'+s.getvalue(),'supply-metadata.json':json.dumps(data['meta'],ensure_ascii=False,indent=2)+'\n','supply-adapter.py':Path(__file__).read_bytes(),'supply-NOTICE.txt':'Source: Department of Health, Hong Kong SAR Government; Drug Office annual licensed wholesaler survey.\n'+SOURCE_URL+'\nSource figures retain Government rights; no source open licence is inferred. The application MIT licence does not apply to source data.\nOriginal HTML and PDF are linked, not included in this public dataset directory. See meta.terms.\nUnit: DID. Human-use totals exclude veterinary surgeons and farmers. 2025 is provisional.\nRebuild: python3 supply-adapter.py --fetch --out regenerated --source downloaded-source.html --retrieval downloaded-source.retrieval.json --report regenerated/validation.json\n'}
    for name,content in files.items():atomic(out/name,content)
    if a.fetch:atomic(Path(a.source),source);atomic(Path(a.retrieval),json.dumps(retrieval,indent=2)+'\n')
    report={'status':'passed','dataset_id':data['meta']['dataset_id'],'source_sha256':data['meta']['source_sha256'],'records':len(data['rows']),'tables':data['meta']['audit']['tables'],'source_years':data['meta']['years'],'provisional_years':data['meta']['provisional_years'],'source_cell_reconciliation':len(data['rows']),'outputs':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in files}}
    atomic(Path(a.report),json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','records','source_years','provisional_years']}))
if __name__=='__main__':main()

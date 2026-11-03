#!/usr/bin/env python3
"""Flu Express adapter. --fetch refreshes both CSV and dictionary identity.
An unknown schema, value or dictionary revision stops replacement of the snapshot.
"""
import argparse, csv, datetime as dt, hashlib, io, json, re, tempfile, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site" if (ROOT / "site/datasets").is_dir() else ROOT
SOURCE = 'https://www.chp.gov.hk/files/misc/flux_data.csv'
DICTIONARY_URL = 'https://www.chp.gov.hk/files/pdf/flux_spec_en.pdf'
DICTIONARY_SHA256 = 'b2fde8698d95413345e61d2b72b098d023678eb1f9e73155d6749798c71375cf'
TERMS = 'https://data.gov.hk/en/terms-and-conditions'
VERSION = 'flu-express-dictionary-1.0'
FIELDS = 'Year,Week,From,To,ILI_FMC,ILI_PMP,H1,H3,B,AandB,H1_proportion,H3_proportion,B_proportion,AandB_proportion,ILI_School,ILI_NonSchool,Adm_0_5,Adm_6_11,Adm_12_17,Adm_18_49,Adm_50_64,Adm_65_higher,Adm_All,ILI_AED,Fever_CCCKG,Fever_RCHE,ILI_CMP,SevereCase_0_17,SevereCase_18_49,SevereCase_50_64,SevereCase_65_higher'.split(',')
NUMERIC = FIELDS[4:]
COUNTS = {'H1','H3','B','AandB','ILI_School','ILI_NonSchool','SevereCase_0_17','SevereCase_18_49','SevereCase_50_64','SevereCase_65_higher'}
PROPORTIONS = {'H1_proportion','H3_proportion','B_proportion','AandB_proportion','Fever_CCCKG','Fever_RCHE'}
DICT = {
 'Year':{'label':'Surveillance year','unit':'year','description':'Source surveillance year; the first week can begin in December of the preceding year.'},
 'Week':{'label':'Surveillance week','unit':'week number','description':'Source week number retained.'},
 'From':{'label':'Week starts','unit':'date','description':'Original DD/MM/YYYY start date.'},
 'To':{'label':'Week ends','unit':'date','description':'Original DD/MM/YYYY end date.'},
 'ILI_FMC':{'label':'ILI: family medicine clinics','unit':'per 1,000 consultations'},
 'ILI_PMP':{'label':'ILI: private medical practitioners','unit':'per 1,000 consultations'},
 'H1':{'label':'Influenza A(H1) detections','unit':'positive detections'},
 'H3':{'label':'Influenza A(H3) detections','unit':'positive detections'},
 'B':{'label':'Influenza B detections','unit':'positive detections'},
 'AandB':{'label':'All influenza A/B detections','unit':'positive detections'},
 'H1_proportion':{'label':'Influenza A(H1) positivity','unit':'proportion (0–1)','denominator':'All respiratory specimens'},
 'H3_proportion':{'label':'Influenza A(H3) positivity','unit':'proportion (0–1)','denominator':'All respiratory specimens'},
 'B_proportion':{'label':'Influenza B positivity','unit':'proportion (0–1)','denominator':'All respiratory specimens'},
 'AandB_proportion':{'label':'All influenza A/B positivity','unit':'proportion (0–1)','denominator':'All respiratory specimens'},
 'ILI_School':{'label':'School ILI outbreaks','unit':'outbreaks'},
 'ILI_NonSchool':{'label':'Other institution ILI outbreaks','unit':'outbreaks'},
 'ILI_AED':{'label':'Public hospital emergency ILI syndrome','unit':'per 1,000 coded cases'},
 'Fever_CCCKG':{'label':'Fever at child care/kindergarten','unit':'proportion (0–1)','denominator':'Children at sentinel child care centres/kindergartens'},
 'Fever_RCHE':{'label':'Fever at elderly care homes','unit':'proportion (0–1)','denominator':'Residents at sentinel residential care homes for the elderly'},
 'ILI_CMP':{'label':'ILI: Chinese medicine practitioners','unit':'per 1,000 consultations'},
}
for field,age in [('Adm_0_5','0–5'),('Adm_6_11','6–11'),('Adm_12_17','12–17'),('Adm_18_49','18–49'),('Adm_50_64','50–64'),('Adm_65_higher','65+'),('Adm_All','all ages')]:
    DICT[field]={'label':'Influenza admission rate: '+age,'unit':'per 10,000 population','denominator':'Population of the corresponding age group','description':'Public hospital admission with principal diagnosis of influenza.'}
for field,age in [('SevereCase_0_17','0–17'),('SevereCase_18_49','18–49'),('SevereCase_50_64','50–64'),('SevereCase_65_higher','65+')]:
    DICT[field]={'label':'Severe influenza cases: '+age,'unit':'cases'}
for f in NUMERIC:
    DICT[f].setdefault('description',DICT[f]['label']+'. Values retain the units stated in the official dictionary.')
    DICT[f]['missing']='Empty source cell remains null; not assigned zero.'
DICT={f:DICT[f]for f in FIELDS}

def digest(b):return hashlib.sha256(b).hexdigest()

def parse_number(field, raw):
    text=raw.strip()
    if text=='':return None
    if not re.fullmatch(r'\d+(?:\.\d+)?',text):raise ValueError('Unknown numerical code '+field+': '+raw)
    v=float(text)
    if field in COUNTS:
        if not v.is_integer():raise ValueError('Fractional count '+field)
        return int(v)
    if field in PROPORTIONS and v>1:raise ValueError('Proportion outside 0–1: '+field)
    return v

def parse(b):
    reader=csv.DictReader(io.StringIO(b.decode('utf-8-sig')))
    if reader.fieldnames!=FIELDS:raise ValueError('Flu Express 31-column schema changed')
    rows=[];seen=set()
    for row_no,raw in enumerate(reader,2):
        if None in raw or any(v is None for v in raw.values()):raise ValueError('Wrong column count')
        start=dt.datetime.strptime(raw['From'],'%d/%m/%Y').date();end=dt.datetime.strptime(raw['To'],'%d/%m/%Y').date()
        if (end-start).days!=6:raise ValueError('Non-seven-day reporting interval at row '+str(row_no))
        year,week=int(raw['Year']),int(raw['Week'])
        if not 1<=week<=53:raise ValueError('Invalid week number')
        key=f'{year}W{week:02}'
        if key in seen:raise ValueError('Duplicate surveillance week '+key)
        seen.add(key)
        r={'record_id':'flu-'+key,'Year':year,'Week':week,'From':raw['From'],'To':raw['To'],
           'year':year,'week_key':key,'period_start':start.isoformat(),'period_end':end.isoformat(),'source_row':row_no}
        for f in NUMERIC:r[f]=parse_number(f,raw[f]);r['raw_'+f]=raw[f]
        r['missing_fields']=';'.join(f for f in NUMERIC if r[f]is None)
        rows.append(r)
    if not rows:raise ValueError('No observations')
    dates=[r['period_start']for r in rows]
    if dates!=sorted(set(dates)):raise ValueError('Duplicate or unsorted periods')
    return rows

def build(b,info,dictionary):
    if digest(dictionary)!=DICTIONARY_SHA256:raise ValueError('Dictionary revision requires field/unit review before updating')
    rows=parse(b);sha=digest(b)
    meta={'dataset_id':'flu-express','title':'Hong Kong Flu Express weekly surveillance','provider':'Department of Health, Hong Kong SAR Government',
          'source_sha256':sha,'source_bytes':len(b),'source_url':SOURCE,'source_version':'Flu-through-'+rows[-1]['week_key']+'-'+sha[:12],
          'retrieved_at_utc':info['retrieved_at_utc'],'source_last_modified':info.get('last_modified'),'status':'ready',
          'terms':{'name':'DATA.GOV.HK Terms of Use','url':TERMS,'attribution':'Source: Department of Health, Hong Kong SAR Government, via DATA.GOV.HK.'},
          'dictionary':DICT,'dictionary_url':DICTIONARY_URL,'dictionary_sha256':DICTIONARY_SHA256,
          'numeric_fields':NUMERIC,'source_field_count':len(FIELDS),'source_fields':FIELDS,
          'unit':'Indicator-specific; see dictionary','region':'Hong Kong',
          'unit_of_observation':'One surveillance week across 27 influenza/ILI indicators','temporal_resolution':'weekly','resource_update_frequency':'weekly',
          'processing_version':VERSION,'resource_url':'https://data.gov.hk/en-data/dataset/hk-dh-chpsebcddr-flu-express',
          'start_date':rows[0]['period_start'],'end_date':rows[-1]['period_end'],'first_week':rows[0]['week_key'],'last_week':rows[-1]['week_key'],
          'row_count':len(rows),'missing_by_field':{f:sum(r[f]is None for r in rows)for f in NUMERIC},
          'scope_note':'Weekly influenza clinical surveillance. Ratios stay on their original 0–1 scale; consultation and admission rates retain their source denominators. No wastewater field or influenza wastewater model is included.',
          'normalization':'No rescaling, imputation or cross-indicator aggregation.',
          'data_availability':{'weekly_clinical_surveillance':True,'original_31_fields':True,'wastewater_measurements':False,'clinical_wastewater_pairing':False,'historical_release_reconstruction':False},
          'ui':{'filters':[{'field':'year','label':'Surveillance year'}],
                'columns':['week_key','period_start','period_end','AandB_proportion','ILI_FMC','ILI_PMP','Adm_All']},
          'default_filters':{},'raw_source_download_url':SOURCE}
    return {'meta':meta,'rows':rows}

def output(data,out):
    out.mkdir(parents=True,exist_ok=True)
    stream=io.StringIO(newline='');w=csv.DictWriter(stream,fieldnames=list(data['rows'][0]));w.writeheader();w.writerows(data['rows'])
    rendered={'flu-data.json':json.dumps(data,ensure_ascii=False,indent=2)+'\n','flu-metadata.json':json.dumps(data['meta'],ensure_ascii=False,indent=2)+'\n',
              'flu-data.csv':stream.getvalue(),'flu-data.js':'window.EXT_FLU_DATA='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n'}
    staged=[]
    try:
        for name,text in rendered.items():
            with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=out,delete=False)as f:f.write(text);staged.append((Path(f.name),out/name))
        for tmp,target in staged:tmp.replace(target)
    finally:
        for tmp,_ in staged:tmp.unlink(missing_ok=True)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fetch',action='store_true');p.add_argument('--source',type=Path,default=ROOT/'work/data_sources/flu-source.csv');p.add_argument('--dictionary',type=Path,default=ROOT/'work/data_sources/flu-dictionary.pdf');p.add_argument('--out',type=Path,default=SITE/'datasets');a=p.parse_args()
    sidecar=Path(str(a.source)+'.source.json')
    if a.fetch:
        with urllib.request.urlopen(SOURCE,timeout=45)as r:b=r.read();info={'url':SOURCE,'retrieved_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'last_modified':r.headers.get('Last-Modified'),'sha256':digest(b),'bytes':len(b)}
        with urllib.request.urlopen(DICTIONARY_URL,timeout=45)as r:dictionary=r.read()
    else:
        b=a.source.read_bytes();info=json.loads(sidecar.read_text());dictionary=a.dictionary.read_bytes()
        if info.get('sha256')!=digest(b):raise ValueError('Acquisition hash mismatch')
    data=build(b,info,dictionary)
    if a.fetch:
        a.source.parent.mkdir(parents=True,exist_ok=True);a.source.write_bytes(b);sidecar.write_text(json.dumps(info,indent=2)+'\n');a.dictionary.write_bytes(dictionary)
    output(data,a.out);print(json.dumps({'dataset_id':data['meta']['dataset_id'],'rows':len(data['rows']),'source_fields':len(FIELDS),'source_sha256':data['meta']['source_sha256']}))

if __name__=='__main__':main()

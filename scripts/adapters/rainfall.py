#!/usr/bin/env python3
"""HKO daily rainfall adapter. --fetch refreshes; default rebuilds downloaded bytes.
Only validated records replace the last usable public snapshot.
"""
import argparse, csv, datetime as dt, hashlib, io, json, re, tempfile, urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site" if (ROOT / "site/datasets").is_dir() else ROOT
SOURCE = 'https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKO/ALL/daily_HKO_RF_ALL.csv'
RESOURCE = 'https://data.gov.hk/en-data/dataset/hk-hko-rss-daily-total-rainfall/resource/fe463867-cfe1-4566-aa3e-a7e60b5e3473'
TERMS = 'https://data.gov.hk/en/terms-and-conditions'
VERSION = 'hko-daily-rainfall-1.0'
DICT = {
 'date': {'label':'Observation date','unit':'date','description':'Daily date from the three source date columns.'},
 'station': {'label':'Station','unit':'station ID','description':'HKO: Hong Kong Observatory. This source is one station.'},
 'rainfall_mm': {'label':'Daily rainfall','unit':'mm','description':'Exact reported numerical amount. Trace and unavailable values remain null.'},
 'raw_value': {'label':'Original value','unit':'source text','description':'Unchanged Value column, including Trace and ***.'},
 'quality_flag': {'label':'Source completeness','unit':'source code','description':'C complete; # incomplete; empty unknown.'},
 'quality_status': {'label':'Completeness','unit':'category','description':'complete, incomplete or unknown; independent of trace/missing status.'},
 'value_status': {'label':'Measurement status','unit':'category','description':'observed, trace or unavailable.'},
 'rainfall_lower_bound_mm': {'label':'Rainfall lower bound','unit':'mm','description':'Observed value or 0 for Trace. Trace is not assigned an exact measured amount.'},
 'rainfall_upper_bound_mm': {'label':'Rainfall upper bound','unit':'mm','description':'Observed value or exclusive 0.05 mm for Trace, as stated in the source legend.'},
 'upper_bound_inclusive': {'label':'Upper bound included','unit':'boolean','description':'False for Trace; true for exact values; null if unavailable.'},
 'source_row': {'label':'Original CSV row','unit':'row number','description':'1-based row, including the two title rows and column header.'},
}

def digest(b): return hashlib.sha256(b).hexdigest()

def parse_value(raw, flag):
    text = raw.strip(); incomplete = '#' in text or flag.strip() == '#'
    text = text.replace('#','').strip()
    if flag.strip() not in {'','C','#'}: raise ValueError('Unknown completeness flag: '+flag)
    quality = 'incomplete' if incomplete else 'complete' if flag.strip() == 'C' else 'unknown'
    if text == 'Trace': return None, 'trace', 0, 0.05, False, quality
    if text in {'***',''}: return None, 'unavailable', None, None, None, quality
    if not re.fullmatch(r'\d+(?:\.\d+)?', text): raise ValueError('Unknown rainfall value: '+raw)
    v=float(text)
    return v, 'observed', v, v, True, quality

def parse(b, start='2019-01-01'):
    raw=list(csv.reader(io.StringIO(b.decode('utf-8-sig'))))
    if len(raw)<4 or raw[2] != ['年/Year','月/Month','日/Day','數值/Value','數據完整性/data Completeness']:
        raise ValueError('HKO header changed')
    if 'Hong Kong Observatory' not in ','.join(raw[1]): raise ValueError('Wrong station title')
    data=[]; excluded=[]; known_footer={'*** 沒有數據/unavailable','# 數據不完整/data incomplete','微量表示少於 0.05 毫米/Trace means rainfall less than 0.05 mm','C 數據完整/data Complete'}
    for row_no, r in enumerate(raw[3:],4):
        if not r: continue
        if len(r)==1 and r[0] in known_footer: continue
        if len(r)!=5 or not all(re.fullmatch(r'\d+',x) for x in r[:3]): raise ValueError(f'Unrecognized row {row_no}')
        try: date=dt.date(*map(int,r[:3])).isoformat()
        except ValueError:
            excluded.append({'source_row':row_no,'raw_year':r[0],'raw_month':r[1],'raw_day':r[2],'raw_value':r[3],'quality_flag':r[4],'reason':'Invalid Gregorian calendar date in source; date is not corrected or imputed.'})
            continue
        v,status,lo,hi,inclusive,quality=parse_value(r[3],r[4])
        data.append({'date':date,'year':int(r[0]),'station':'HKO','rainfall_mm':v,'raw_value':r[3],
                     'quality_flag':r[4],'quality_status':quality,'value_status':status,
                     'rainfall_lower_bound_mm':lo,'rainfall_upper_bound_mm':hi,'upper_bound_inclusive':inclusive,
                     'source_row':row_no})
    if not data: raise ValueError('No rainfall records')
    dates=[r['date']for r in data]
    if dates!=sorted(set(dates)): raise ValueError('Duplicate or unsorted dates')
    selected=[r for r in data if r['date']>=start]
    if not selected: raise ValueError('Empty selected period')
    return selected, {'source_record_count':len(data)+len(excluded),'source_valid_date_count':len(data),'source_excluded_record_count':len(excluded),'excluded_records':excluded,'source_start_date':dates[0],'source_end_date':dates[-1],
                     'source_value_status_counts':dict(Counter(r['value_status']for r in data)),
                     'source_quality_counts':dict(Counter(r['quality_status']for r in data))}

def build(b, info, start='2019-01-01'):
    rows, coverage=parse(b,start); sha=digest(b)
    meta={'dataset_id':'hko-rainfall','title':'Hong Kong Observatory daily rainfall','provider':'Hong Kong Observatory',
          'source_sha256':sha,'source_bytes':len(b),'source_url':SOURCE,'source_version':'HKO-through-'+coverage['source_end_date']+'-'+sha[:12],
          'retrieved_at_utc':info['retrieved_at_utc'],'source_last_modified':info.get('last_modified'),
          'status':'ready','terms':{'name':'DATA.GOV.HK Terms of Use','url':TERMS,'attribution':'Source: Hong Kong Observatory, Hong Kong SAR Government, via DATA.GOV.HK.'},
          'dictionary':DICT,'numeric_fields':['rainfall_mm'],'unit':'mm','region':'Hong Kong','station':'HKO',
          'unit_of_observation':'One daily observation at the Hong Kong Observatory station','temporal_resolution':'daily',
          'resource_update_frequency':'monthly','processing_version':VERSION,'resource_url':RESOURCE,
          'start_date':rows[0]['date'],'end_date':rows[-1]['date'],'row_count':len(rows),'loaded_start_filter':start,
          'value_status_counts':dict(Counter(r['value_status']for r in rows)),
          'quality_counts':dict(Counter(r['quality_status']for r in rows)),**coverage,
          'scope_note':'HKO station daily rainfall. Trace is below 0.05 mm and has no exact numeric value. The loaded period starts in 2019; the complete source starts in 1884. Weekly alignment is background context; catchment flow and historical publication availability have not been validated.',
          'quality_rules':{'Trace':'Keep null rainfall_mm and interval [0,0.05) mm','***':'Unavailable; null rainfall_mm','#':'Incomplete; preserve amount and flag','C':'Complete'},
          'data_availability':{'daily_rainfall':True,'station_metadata':True,'historical_release_reconstruction':False,'catchment_flow_correction':False},
          'ui':{'filters':[{'field':'station','label':'Station'},{'field':'quality_status','label':'Completeness'},{'field':'value_status','label':'Value status'}],
                'columns':['date','station','rainfall_mm','raw_value','quality_status','value_status']},
          'default_filters':{},'raw_source_download_url':SOURCE}
    return {'meta':meta,'rows':rows}

def output(data,out):
    out.mkdir(parents=True,exist_ok=True)
    stream=io.StringIO(newline='');w=csv.DictWriter(stream,fieldnames=list(data['rows'][0]));w.writeheader();w.writerows(data['rows'])
    rendered={'rainfall-data.json':json.dumps(data,ensure_ascii=False,indent=2)+'\n',
              'rainfall-metadata.json':json.dumps(data['meta'],ensure_ascii=False,indent=2)+'\n',
              'rainfall-data.csv':stream.getvalue(),
              'rainfall-data.js':'window.EXT_RAINFALL_DATA='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n'}
    staged=[]
    try:
        for name,text in rendered.items():
            with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=out,delete=False)as f:f.write(text);staged.append((Path(f.name),out/name))
        for tmp,target in staged:tmp.replace(target)
    finally:
        for tmp,_ in staged:tmp.unlink(missing_ok=True)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fetch',action='store_true');p.add_argument('--source',type=Path,default=ROOT/'work/data_sources/rainfall-source.csv');p.add_argument('--out',type=Path,default=SITE/'datasets');p.add_argument('--start',default='2019-01-01');a=p.parse_args()
    sidecar=Path(str(a.source)+'.source.json')
    if a.fetch:
        with urllib.request.urlopen(SOURCE,timeout=45)as r:b=r.read();info={'url':SOURCE,'retrieved_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'last_modified':r.headers.get('Last-Modified'),'sha256':digest(b),'bytes':len(b)}
    else:
        b=a.source.read_bytes();info=json.loads(sidecar.read_text())
        if info.get('sha256')!=digest(b):raise ValueError('Acquisition hash mismatch')
    data=build(b,info,a.start)
    if a.fetch:a.source.parent.mkdir(parents=True,exist_ok=True);a.source.write_bytes(b);sidecar.write_text(json.dumps(info,indent=2)+'\n')
    output(data,a.out);print(json.dumps({'dataset_id':data['meta']['dataset_id'],'rows':len(data['rows']),'source_sha256':data['meta']['source_sha256']}))

if __name__=='__main__':main()

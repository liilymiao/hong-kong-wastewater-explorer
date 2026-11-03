#!/usr/bin/env python3
"""Parse actual HA blood key-findings PDF. Requires pdfplumber; no OCR or imputation.

python3 scripts/adapters/ha_blood.py --fetch
python3 scripts/adapters/ha_blood.py --source work/data_sources/ha-blood-key-findings2024.pdf
Only validated output replaces the last usable dataset. Original source stays local.
"""
import argparse, csv, datetime as dt, hashlib, io, json, re, tempfile, urllib.request
from collections import Counter
from pathlib import Path
import pdfplumber

VERSION = 'ha-blood-coordinate-parser-1.0'
SOURCE = 'https://www.chp.gov.hk/files/pdf/haamr_blood_key_findings2024.pdf'
PUBLICATION = 'https://www.chp.gov.hk/en/static/109746.html'
TERMS = 'https://www.chp.gov.hk/en/static/24027.html'
ROOT = Path(__file__).resolve().parents[2]
NUM = r'([<>≤≥]?)([0-9]+(?:\.[0-9]+)?)'
PERCENT = re.compile('^'+NUM+r'%(††)?$')
CI = re.compile(r'^\('+NUM+r'%-'+NUM+r'%\)$')
COUNTS = re.compile(r'^\(([0-9,]+|§)/([0-9,]+|§)\)$')
NOTES = {
 'rounding':'Patient headcounts are rounded to the nearest 100. Percentages and confidence limits are retained at source precision; they are not recalculated from rounded counts.',
 'suppression':'The source symbol § identifies a positive patient count below 50; its numeric field is null and its literal symbol is retained.',
 'coverage':'A †† suffix marks AST coverage below 70%. Absence of the suffix is stored as not_flagged, without estimating an exact testing percentage.',
 'deduplication':'The source de-duplicates with location of onset considered. A patient can contribute an isolate to each onset group when available.',
 'confidence_intervals':'The source reports Wilson 95% confidence intervals. An inequality at a confidence bound is stored separately from the numeric boundary.',
 'small_denominator':'The report excludes non-susceptibility percentages based on fewer than 10 de-duplicated isolates. No result rows are invented for absent cells.',
 'metric':'The metric remains the official non-susceptibility percentage. The checked key-findings PDF does not separately enumerate R and I categories; no R-only or I+R relabelling is imposed.',
 'scope':'This PDF supplies E. coli hospital-onset records and K. pneumoniae community- and hospital-onset records. E. coli community-onset rows are not present in this file.',
}
BREAKPOINT = 'Source notes: CLSI revised fluoroquinolone criteria for Enterobacteriaceae except Salmonella in 2019, and piperacillin/tazobactam criteria in 2022; subsequent differences may reflect these changes. The source also notes a 2020 Acinetobacter colistin change, outside this two-organism extract.'
DICTIONARY = {
 'record_id':'Stable record key within this source layout: physical page, antimicrobial row and year.', 'source_id':'ha-amr dataset identifier.',
 'unit':'Percentage units, 0–100.', 'ci_method':'Wilson confidence interval, 95%.', 'value_status':'reported or reported_with_suppressed_count; the percentage can remain reported while its count is suppressed.',
 'trend_raw':'Original row-level trend direction and p-value label; source Cochran-Armitage test, no new trend test performed.',
 'source_url':'Official source PDF URL.', 'footnote_pages':'Physical PDF pages containing the shared notes.',
 'year':'Surveillance year; annual precision.', 'specimen_type':'Blood culture.',
 'organism':'Organism heading in the source PDF.', 'antimicrobial':'Source antimicrobial label with line-break hyphens joined; no drug-class-to-molecule substitutions.',
 'onset_setting':'Literal source stratum: Community or Hospital.',
 'metric_definition':'Official non-susceptibility percentage; retained separately from PHLSB R-only resistance.',
 'reported_percentage':'Source percentage (0–100), not recomputed.', 'reported_percentage_operator':'= for a reported number; <, >, ≤ or ≥ if shown.',
 'ci_lower':'Source lower 95% CI boundary in percentage points; read with ci_lower_operator.',
 'ci_upper':'Source upper 95% CI boundary in percentage points; read with ci_upper_operator.',
 'ci_lower_operator':'Inequality symbol retained for a censored lower limit; = otherwise.', 'ci_upper_operator':'Inequality symbol for upper boundary; = otherwise.',
 'reported_numerator':'Rounded reported patient numerator, or null when § suppressed.', 'reported_denominator':'Rounded reported AST denominator, or null when § suppressed.',
 'reported_numerator_text':'Literal numerator, including §.', 'reported_denominator_text':'Literal denominator.',
 'reported_total_headcount':'Separate organism-specific annual total in the table header. This is not the AST denominator.',
 'count_rounding':'nearest_100 for this source.', 'count_suppression':'none, numerator_gt0_lt50, denominator_gt0_lt50 or both_gt0_lt50.',
 'ast_coverage_flag':'lt70pct when †† is printed; not_flagged otherwise.',
 'breakpoint_note':'Source breakpoint-change context; no retrospective reinterpretation.',
 'source_page':'1-based physical PDF page.', 'source_row':'1-based antimicrobial row within the page.', 'source_column':'1-based surveillance-year column (excluding label and onset columns).',
 'source_bbox':'PDF cell bounding box (x0, top, x1, bottom), coordinates in points, stored as JSON text.',
 'raw_cell':'Three source text lines: percentage, CI and numerator/denominator.',
 'raw_antimicrobial':'Source antimicrobial text retaining line breaks.', 'source_sha256':'SHA256 of the complete source PDF.',
 'source_version':'Report year, generation month and PDF SHA prefix.',
}

def digest(b): return hashlib.sha256(b).hexdigest()
def now(): return dt.datetime.now(dt.timezone.utc).isoformat()
def center(w): return (w['x0']+w['x1'])/2
def tokens(words, x0, y0, x1, y1):
    return sorted([w for w in words if x0 <= center(w) < x1 and y0 <= (w['top']+w['bottom'])/2 < y1], key=lambda w:(round(w['top'],1),w['x0']))
def lines(words):
    groups=[]
    for w in words:
        if not groups or abs(groups[-1][0]-w['top'])>2: groups.append((w['top'],[]))
        groups[-1][1].append(w['text'])
    return '\n'.join(' '.join(g[1]) for g in groups)

def parse(source, acquisition):
    rows=[]; page_audit=[]; sha=digest(source.read_bytes())
    version='2024-generated-2025-12-'+sha[:12]
    with pdfplumber.open(source) as doc:
        for page_no,page in enumerate(doc.pages,1):
            text=page.extract_text() or ''
            heading=re.search(r'Non susceptibility percentage of (.+?) for different antimicrobials',text)
            if not heading: continue
            organism=heading.group(1); words=page.extract_words()
            headers=sorted([w for w in words if re.fullmatch(r'20[0-9]{2}',w['text']) and w['top']<115],key=lambda w:w['x0'])
            if len(headers)<2: raise ValueError(f'Page {page_no}: year header unavailable')
            years=[int(w['text'])for w in headers]
            if len(set(years))!=len(years) or years!=sorted(years):raise ValueError('Ambiguous year columns')
            cx=[center(w)for w in headers];half=min(b-a for a,b in zip(cx,cx[1:]))/2
            left=cx[0]-half; right=cx[-1]+half
            onsets=[w for w in words if w['text'] in ('Community','Hospital') and 115<center(w)<left and w['top']>headers[0]['bottom']]
            if not onsets:raise ValueError(f'Page {page_no}: no onset rows')
            counts=[]
            for x in cx:
                t=tokens(words,x-half,headers[0]['bottom'],x+half,onsets[0]['top']-10)
                found=[w['text']for w in t if re.fullmatch(r'\([0-9,]+\)',w['text'])]
                if len(found)!=1:raise ValueError('Annual total header changed')
                counts.append(int(found[0][1:-1].replace(',','')))
            for ri,onset in enumerate(onsets,1):
                y0=onset['top']-11;y1=onset['bottom']+12
                label=lines(tokens(words,0,y0,120,y1));analyte=re.sub(r'\s+',' ',label.replace('-\n','-')).strip()
                if not analyte or any(c.isdigit()for c in analyte):raise ValueError(f'Invalid drug row: {label}')
                trend=lines(tokens(words,right,y0,page.width,y1))
                for j,(year,x)in enumerate(zip(years,cx)):
                    cellwords=tokens(words,x-half,y0,x+half,y1);raw=lines(cellwords);parts=raw.splitlines()
                    if len(parts)!=3:raise ValueError(f'Page {page_no} {analyte} {year}: expected three source lines: {raw!r}')
                    pct=PERCENT.fullmatch(parts[0]);ci=CI.fullmatch(parts[1]);cnt=COUNTS.fullmatch(parts[2])
                    if not(pct and ci and cnt):raise ValueError(f'Unrecognized cell: {raw!r}')
                    num,den=cnt.groups(); suppressed=('both_gt0_lt50' if num==den=='§' else 'numerator_gt0_lt50' if num=='§' else 'denominator_gt0_lt50' if den=='§' else 'none')
                    rows.append({'record_id':f'ha-blood-p{page_no}-r{ri}-{year}','source_id':'ha-amr','year':year,'specimen_type':'Blood','organism':organism,'antimicrobial':analyte,'onset_setting':onset['text'],'metric_definition':'Non-susceptibility','unit':'percent','reported_percentage':float(pct[2]),'reported_percentage_operator':pct[1]or'=','ci_lower':float(ci[2]),'ci_lower_operator':ci[1]or'=','ci_upper':float(ci[4]),'ci_upper_operator':ci[3]or'=','ci_method':'Wilson 95%','reported_numerator':None if num=='§'else int(num.replace(',','')),'reported_denominator':None if den=='§'else int(den.replace(',','')),'reported_numerator_text':num,'reported_denominator_text':den,'reported_total_headcount':counts[j],'count_rounding':'nearest_100','count_suppression':suppressed,'ast_coverage_flag':'lt70pct'if pct[3]else'not_flagged','value_status':'reported_with_suppressed_count'if suppressed!='none'else'reported','breakpoint_note':BREAKPOINT,'trend_raw':trend,'raw_cell':raw,'raw_antimicrobial':label,'source_url':SOURCE,'source_page':page_no,'source_row':ri,'source_column':j+1,'source_bbox':json.dumps([round(x-half,3),round(y0,3),round(x+half,3),round(y1,3)]),'footnote_pages':'4,6,8','source_version':version,'source_sha256':sha})
            page_audit.append({'page':page_no,'organism':organism,'onset_settings':sorted({w['text']for w in onsets}),'antimicrobial_rows':len(onsets),'year_columns':years,'records':len(onsets)*len(years)})
    validate(rows)
    meta={'dataset_id':'ha-amr','title':'Hospital Authority blood-culture non-susceptibility','provider':'Centre for Health Protection / Hospital Authority, Hong Kong SAR Government','region':'Hong Kong','research_type':'Clinical surveillance aggregate','citation':'Centre for Health Protection. Hospital Authority AMR Data (2024): Blood key findings. Released 30 January 2026.','update_frequency':'Annual report; file revisions possible','data_level':'Clinical aggregate','available_fields':list(rows[0]),'observation_grain':'Year × organism × antimicrobial × onset setting, blood culture','temporal_resolution':'annual','source_url':SOURCE,'publication_url':PUBLICATION,'release_date':'2026-01-30','report_generated':'2025-12','source_version':version,'source_sha256':sha,'source_bytes':source.stat().st_size,'retrieved_at_utc':acquisition['retrieved_at_utc'],'http_last_modified':acquisition.get('http_last_modified'),'status':'connected','record_count':len(rows),'source_years':sorted({r['year']for r in rows}),'unit':'percent','terms':{'status':'source_rights_retained_no_open_licence_inferred','url':TERMS,'attribution':'Source: Centre for Health Protection / Hospital Authority, Hong Kong SAR Government. Source rights remain with the Government and other owners.','distribution_scope':'Structured factual statistics and provenance are extracted. The source PDF, figures, layout and explanatory prose are not redistributed; the application MIT licence does not cover source material.','notice_scope':'The CHP notice permits complete unmodified copies for personal/internal non-commercial use. It does not establish a general open-data licence for this adapted extract.'},'license_url':TERMS,'dictionary':DICTIONARY,'notes':NOTES,'processing_version':VERSION,'audit':{'pages':page_audit,'rows':len(rows),'groups':dict(Counter(r['organism']+' | '+r['onset_setting']for r in rows)),'coverage_flagged_rows':sum(r['ast_coverage_flag']=='lt70pct'for r in rows),'suppressed_numerator_rows':sum(r['reported_numerator']is None for r in rows),'inequality_ci_rows':sum(r['ci_lower_operator']!='='or r['ci_upper_operator']!='='for r in rows),'pdf_page_count':len(doc.pages),'excluded_scope':'Pages 1–2 contain culture sampling/positivity statistics, not antimicrobial non-susceptibility. No rows added for groups not printed.'}}
    return {'meta':meta,'rows':rows}

def validate(rows):
    if not rows:raise ValueError('No HA rows parsed; last snapshot retained')
    keys=[(r['year'],r['specimen_type'],r['organism'],r['antimicrobial'],r['onset_setting'])for r in rows]
    if len(set(keys))!=len(keys):raise ValueError('Duplicate HA key')
    for r in rows:
        if not 0<=r['ci_lower']<=r['reported_percentage']<=r['ci_upper']<=100:raise ValueError('Invalid CI ordering/range')
        for k in ['reported_numerator','reported_denominator']:
            if r[k]is not None and (r[k]<0 or r[k]%100):raise ValueError('Unexpected count rounding')
        if r['reported_numerator_text']=='§' and r['reported_numerator']is not None:raise ValueError('Suppression converted to number')
        if (r['ast_coverage_flag']=='lt70pct')!=('††'in r['raw_cell']):raise ValueError('AST flag lost')

def atomic(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.tmp');tmp.write_text(text,encoding='utf-8');tmp.replace(path)

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=ROOT/'work/data_sources/ha-blood-key-findings2024.pdf');p.add_argument('--fetch',action='store_true');p.add_argument('--out',type=Path,default=ROOT/'site/datasets');p.add_argument('--report',type=Path,default=ROOT/'qa/ha-ingestion-verification.json');args=p.parse_args()
    acquisition_path=args.source.with_suffix('.acquisition.json')
    try:
        if args.fetch:
            req=urllib.request.Request(SOURCE,headers={'User-Agent':'WastewaterExplorer/1.6 research adapter'})
            with urllib.request.urlopen(req,timeout=60)as response:b=response.read();modified=response.headers.get('Last-Modified')
            if not b.startswith(b'%PDF'):raise ValueError('Response is not PDF')
            acquired={'source_url':SOURCE,'source_sha256':digest(b),'source_bytes':len(b),'retrieved_at_utc':now(),'http_last_modified':modified}
            archive=args.source.parent/f'ha-blood-{acquired["source_sha256"][:16]}.pdf';archive.parent.mkdir(parents=True,exist_ok=True);archive.write_bytes(b)
            data=parse(archive,acquired)
            args.source.write_bytes(b);atomic(acquisition_path,json.dumps(acquired,indent=2)+'\n')
        else:
            if not acquisition_path.exists():raise ValueError('Provide source acquisition JSON with actual retrieved_at_utc')
            acquired=json.loads(acquisition_path.read_text())
            if digest(args.source.read_bytes())!=acquired['source_sha256']:raise ValueError('Local PDF hash differs from acquisition record')
            data=parse(args.source,acquired)
        data_json=json.dumps(data,ensure_ascii=False,separators=(',',':'))
        s=io.StringIO(newline='');writer=csv.DictWriter(s,fieldnames=list(data['rows'][0]));writer.writeheader();writer.writerows(data['rows'])
        outputs={'ha-data.js':'/* Source factual statistics and provenance; see meta.terms. */\nwindow.EXT_HA_DATA='+data_json+';\n','ha-data.json':data_json+'\n','ha-rows.csv':s.getvalue(),'ha-metadata.json':json.dumps(data['meta'],ensure_ascii=False,indent=2)+'\n'}
        for name,text in outputs.items():atomic(args.out/name,text)
        report={'status':'passed','source_sha256':data['meta']['source_sha256'],'source_version':data['meta']['source_version'],'audit':data['meta']['audit'],'outputs':{k:{'bytes':len(v.encode()),'sha256':digest(v.encode())}for k,v in outputs.items()},'tests':['Unique record grain','CI boundaries and percentage range','Hundred-rounded counts retained','Suppression stays null','AST coverage flags retain literal source markers','Year columns identified from source headers','Each antimicrobial/onset row has one source cell per year']}
        atomic(args.report,json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'passed','rows':len(data['rows']),'audit':data['meta']['audit']}))
    except Exception as exc:
        atomic(args.report,json.dumps({'status':'failed','at_utc':now(),'error':str(exc),'source_url':SOURCE,'last_successful_outputs_retained':True},indent=2)+'\n');raise

if __name__=='__main__':main()

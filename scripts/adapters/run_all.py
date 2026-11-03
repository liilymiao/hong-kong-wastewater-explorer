#!/usr/bin/env python3
"""Stage and validate a single data adapter or all nine before replacing snapshots.

python3 scripts/adapters/run_all.py --dataset rainfall --refresh
python3 scripts/adapters/run_all.py --dataset all --refresh
Without --refresh, original cached inputs are required (PHLSB is also bundled).
"""
import argparse, datetime as dt, hashlib, json, os, shutil, subprocess, sys, tempfile, urllib.request, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SITE=ROOT/'site' if (ROOT/'site/datasets').is_dir() else ROOT
RAW=ROOT/'work/data_sources'
SPECS={
 'phlsb':('phlsb.py','phlsb.js','phlsb-metadata.json',None),
 'europe':('europe_arg.py','europe-arg.js','europe-provenance.json',None),
 'hong-kong':('hk_community.py','hk-community.js',None,None),
 'ha':('ha_blood.py','ha-data.js','ha-metadata.json','--fetch'),
 'supply':('supply.py','supply-data.js','supply-metadata.json','--fetch'),
 'bvbrc':('bvbrc_adapter.py','bvbrc-data.js','bvbrc-provenance.json','--refresh'),
 'rainfall':('rainfall.py','rainfall-data.js','rainfall-metadata.json','--fetch'),
 'flu':('flu.py','flu-data.js','flu-metadata.json','--fetch'),
 'global':('global_sewage_adapter.py','global-sewage-data.js','global-sewage-provenance.json','--refresh'),
}
def get(url,target):
 target.parent.mkdir(parents=True,exist_ok=True)
 with urllib.request.urlopen(url,timeout=60)as response:
  b=response.read();headers=dict(response.headers)
 sha=hashlib.sha256(b).hexdigest();archive=RAW/'.snapshots'/(sha+target.suffix);archive.parent.mkdir(exist_ok=True)
 if not archive.exists():archive.write_bytes(b)
 target.write_bytes(b)
 return {'url':url,'sha256':sha,'bytes':len(b),'retrieved_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'headers':headers}

def legacy_refresh(name):
 if name=='phlsb':
  info=get('https://www.chp.gov.hk/files/misc/bac_path_isolation_and_antimicrobial_resistance_en.csv',RAW/'phlsb-source.csv')
  (RAW/'phlsb-download.json').write_text(json.dumps(info,indent=2)+'\n')
 elif name=='europe':
  p=RAW/'europe';get('https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11364805/supplementaryFiles',p/'supplementaryFiles.zip')
  with zipfile.ZipFile(p/'supplementaryFiles.zip')as z:
   name='41467_2024_51957_MOESM4_ESM.xlsx'
   member=next(n for n in z.namelist()if Path(n).name==name);(p/name).write_bytes(z.read(member))
 elif name=='hong-kong':
  p=RAW/'hk-community';get('https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13067863/supplementaryFiles',p/'supplements.zip')
  with zipfile.ZipFile(p/'supplements.zip')as z:
   name='ADVS-13-e08389-s002.xlsx';member=next(n for n in z.namelist()if Path(n).name==name);(p/name).write_bytes(z.read(member))
  get('https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13067863/fullTextXML',p/'article.xml')
  fields='study_accession,sample_accession,secondary_sample_accession,experiment_accession,run_accession,sample_alias,instrument_platform,instrument_model,library_strategy,library_source,library_layout,read_count,base_count,scientific_name,collection_date,country,location'
  from urllib.parse import urlencode
  url='https://www.ebi.ac.uk/ena/portal/api/filereport?'+urlencode({'accession':'PRJNA1207805','result':'read_run','fields':fields,'format':'tsv'})
  get(url,p/'ena-runs.tsv');(p/'ena-url.txt').write_text(url)

def update(name,refresh):
 script,main,metadata,flag=SPECS[name]
 RAW.mkdir(parents=True,exist_ok=True)
 if refresh and name in {'phlsb','europe','hong-kong'}:legacy_refresh(name)
 with tempfile.TemporaryDirectory(prefix='research-update-')as td:
  stage=Path(td);scripts=stage/'scripts/adapters';scripts.mkdir(parents=True)
  shutil.copyfile(SITE/'scripts/adapters'/script,scripts/script)
  (stage/'work').symlink_to(ROOT/'work',target_is_directory=True)
  (stage/'datasets').mkdir();(stage/'qa').mkdir()
  args=[sys.executable,str(scripts/script)]
  if refresh and flag:args.append(flag)
  if name=='phlsb':
   source=RAW/'phlsb-source.csv' if (RAW/'phlsb-source.csv').exists()else SITE/'datasets/phlsb-source.csv'
   info=RAW/'phlsb-download.json' if (RAW/'phlsb-download.json').exists()else SITE/'datasets/phlsb-metadata.json'
   args+=['--source',str(source),'--metadata',str(info)]
  subprocess.run(args,cwd=stage,check=True)
  outputs=list((stage/'datasets').iterdir())
  if not (stage/'datasets'/main).is_file():raise ValueError('Adapter did not produce its expected dataset')
  if metadata:
   m=json.loads((stage/'datasets'/metadata).read_text())
   if len(m.get('source_sha256',''))!=64:raise ValueError('Missing source identity')
  if not outputs or any(not p.is_file()for p in outputs):raise ValueError('Unexpected adapter output structure')
  target=SITE/'datasets';target.mkdir(exist_ok=True)
  previous={p.name:(target/p.name).read_bytes()if(target/p.name).exists()else None for p in outputs}
  try:
   for p in outputs:
    tmp=target/(p.name+'.updating');shutil.copyfile(p,tmp);tmp.replace(target/p.name)
  except Exception:
   for filename,b in previous.items():
    if b is None:(target/filename).unlink(missing_ok=True)
    else:(target/filename).write_bytes(b)
   raise
  return {'dataset':name,'status':'updated','files':[p.name for p in outputs]}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset',choices=['all',*SPECS],default='all')
    p.add_argument('--refresh',action='store_true')
    a=p.parse_args()
    node=os.environ.get('NODE')or shutil.which('node')
    if not node:
        raise RuntimeError('Node.js is required to rebuild the source indexes; set NODE or add node to PATH. No dataset has been changed.')
    report=[]
    for name in SPECS if a.dataset=='all'else[a.dataset]:
        try:report.append(update(name,a.refresh))
        except Exception as exc:report.append({'dataset':name,'status':'failed','error':str(exc),'last_usable_snapshot_retained':True})
    index_status='unchanged'
    if any(r['status']=='updated'for r in report):
        try:
            subprocess.run([node,str(SITE/'scripts/adapters/refresh_extension_index.cjs'),'--require-all'],check=True)
            env=dict(os.environ,NODE=node)
            subprocess.run([sys.executable,str(SITE/'scripts/adapters/refresh_manifest.py')],check=True,env=env)
            index_status='rebuilt'
        except Exception as exc:
            index_status='failed'
            report.append({'dataset':'indexes','status':'failed','error':str(exc),'publication_ready':False})
    status={'at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'refresh':a.refresh,'results':report,'indexes':index_status,'publication_performed':False}
    (ROOT/'work').mkdir(exist_ok=True)
    (ROOT/'work/last-update-status.json').write_text(json.dumps(status,indent=2)+'\n')
    print(json.dumps(status,indent=2))
    return int(any(r['status']=='failed'for r in report))
if __name__=='__main__':raise SystemExit(main())

from pathlib import Path
import json,os,subprocess,socket
B=Path(__file__).resolve().parents[2];q=B/'qa/browser'
for port in [8548,8549]:
 s=socket.socket();s.bind(('127.0.0.1',port));s.close()
env=dict(os.environ,PYTHONPATH=str(q/'network-guard')+os.pathsep+str(B/'course-candidate'),BROWSER_PYTHON_NETWORK_LOG=str(q/'candidate-python-network-attempts.jsonl'),PYTHONDONTWRITEBYTECODE='1',STREAMLIT_SERVER_HEADLESS='true',STREAMLIT_BROWSER_GATHER_USAGE_STATS='false')
(q/'candidate-python-network-attempts.jsonl').write_text('')
records=[]
with (q/'candidate-streamlit.log').open('w') as log:
 p=subprocess.Popen([str(B/'qa/clean-venv/bin/python'),'launch.py','--port','8548'],cwd=B/'course-candidate',env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);records.append({'pid':p.pid,'port':8548,'kind':'candidate-course'})
with (q/'site-server.log').open('w') as log:
 p=subprocess.Popen([str(B/'qa/clean-venv/bin/python'),'-m','http.server','8549','--bind','127.0.0.1'],cwd=B/'site',stdout=log,stderr=subprocess.STDOUT,start_new_session=True);records.append({'pid':p.pid,'port':8549,'kind':'candidate-site'})
(q/'candidate-servers.json').write_text(json.dumps(records,indent=2));print(records)

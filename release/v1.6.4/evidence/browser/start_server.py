from pathlib import Path
import json,subprocess,os,socket
B=Path(__file__).resolve().parents[2];q=B/'qa/browser'; guard=q/'network-guard';guard.mkdir(exist_ok=True)
(guard/'sitecustomize.py').write_text('''import sys,os,json\nfrom pathlib import Path\ndef guard(event,args):\n if event in {"socket.getaddrinfo","socket.gethostbyname","socket.gethostbyaddr"} and str(args[0]) in {"127.0.0.1","localhost","::1"}:return\n if event=="socket.connect" and isinstance(args[1],tuple) and str(args[1][0]) in {"127.0.0.1","::1"}:return\n if event in {"socket.connect","socket.sendto","socket.getaddrinfo","socket.gethostbyname","socket.gethostbyaddr"}:\n  with Path(os.environ["BROWSER_PYTHON_NETWORK_LOG"]).open("a") as f:f.write(json.dumps({"event":event})+"\\n")\n  raise RuntimeError("Network disabled for browser acceptance: "+event)\nsys.addaudithook(guard)\n''')
(q/'python-network-attempts.jsonl').write_text('')
s=socket.socket();s.bind(('127.0.0.1',8547));s.close()
env=dict(os.environ,PYTHONPATH=str(guard)+os.pathsep+str(B/'course'),BROWSER_PYTHON_NETWORK_LOG=str(q/'python-network-attempts.jsonl'),PYTHONDONTWRITEBYTECODE='1',STREAMLIT_SERVER_HEADLESS='true',STREAMLIT_BROWSER_GATHER_USAGE_STATS='false')
with (q/'streamlit.log').open('w') as log:
 p=subprocess.Popen([str(B/'qa/clean-venv/bin/python'),'launch.py','--port','8547'],cwd=B/'course',env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
(q/'server.json').write_text(json.dumps({'pid':p.pid,'port':8547,'command':['qa/clean-venv/bin/python','launch.py','--port','8547'],'cwd':'course','server_python_network_blocked':True},indent=2))
print(p.pid)

import sys,os,json
from pathlib import Path
def guard(event,args):
 if event in {"socket.getaddrinfo","socket.gethostbyname","socket.gethostbyaddr"} and str(args[0]) in {"127.0.0.1","localhost","::1"}:return
 if event=="socket.connect" and isinstance(args[1],tuple) and str(args[1][0]) in {"127.0.0.1","::1"}:return
 if event in {"socket.connect","socket.sendto","socket.getaddrinfo","socket.gethostbyname","socket.gethostbyaddr"}:
  with Path(os.environ["BROWSER_PYTHON_NETWORK_LOG"]).open("a") as f:f.write(json.dumps({"event":event})+"\n")
  raise RuntimeError("Network disabled for browser acceptance: "+event)
sys.addaudithook(guard)

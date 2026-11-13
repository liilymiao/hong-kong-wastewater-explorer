from pathlib import Path
import csv,json
B=Path(__file__).resolve().parents[2];out=B/'course/outputs'
def rows(n):
 with (out/n).open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))
d={'metrics':{},'bootstrap':{},'predictions':rows('predictions.csv'),'stages':{}}
for s,p in [('clipped',''),('raw','raw_')]:
 d['metrics'][s]=rows(p+'metrics.csv');d['bootstrap'][s]=rows(p+'bootstrap_sensitivity.csv');d['stages'][s]=rows(p+'stage_metrics.csv')
(B/'qa/browser/expected.json').write_text(json.dumps(d))

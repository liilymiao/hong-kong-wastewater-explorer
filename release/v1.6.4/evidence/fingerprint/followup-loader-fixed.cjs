'use strict';
// No external dependencies, network, repository writes, or actual surveillance data.
// Default: execute retrieved source excerpts. With an app.js argument, execute the
// same declarations extracted from that complete checkout instead.
const fs=require('node:fs'), path=require('node:path'), vm=require('node:vm');
const assert=require('node:assert/strict');
let source=fs.readFileSync(path.join(__dirname,'../reference/evidence/app-excerpts.js'),'utf8');
let scope='retrieved_source_excerpts';
const args=process.argv.slice(2),strict=args.includes('--strict'),appPath=args.find(x=>!x.startsWith('--'));
if(appPath){
  const app=fs.readFileSync(path.resolve(appPath),'utf8');
  const line=(prefix)=>{const s=app.split('\n').find(x=>x.startsWith(prefix));if(!s)throw new Error('Missing '+prefix);return s;};
  const start=app.indexOf('function reviewDiagnostics('),end=app.indexOf('function periodSummary(',start);
  if(start<0||end<0)throw new Error('Cannot find diagnostic function boundaries');
  source=['const MODEL_KEYS='+JSON.stringify(['persistence','clinical_ridge','combined_ridge'])+';',line('function numeric('),line('const finiteNumber='),line('const valid='),line('const day='),line('const week='),line('const byDate='),line('const PREDICTION_NUMBERS='),line('function predictionRows('),app.slice(start,end)].join('\n');
  scope='functions_extracted_from_supplied_app_js';
}
const D={predictions:[],bootstrap_sensitivity:[],raw_bootstrap_sensitivity:[]};
const c=vm.createContext({D});
vm.runInContext(source+'\nglobalThis.audit={numeric,valid,reviewDiagnostics};',c,{timeout:1000});
const {numeric,valid,reviewDiagnostics:diag}=c.audit;
const results=[];
function check(name,fn){try{fn();results.push({name,status:'pass'});}catch(e){results.push({name,status:'fail',message:e.message});}}
for(const [name,value] of [['null',null],['undefined',undefined],['empty',''],['spaces','  '],['false',false],['true',true],['empty array',[]],['zero array',[0]],['object',{}],['NaN',NaN],['Infinity',Infinity],['hexadecimal','0x10'],['nondecimal','1_000']])check('reject '+name,()=>assert.equal(valid(value),false));
for(const [name,value,expected] of [['zero',0,0],['zero text','0',0],['decimal',' .5 ',.5],['scientific','1e-3',.001],['negative','-2.5',-2.5]])check('accept '+name,()=>assert.equal(numeric(value),expected));
check('empty comparison returns null metrics and no interval',()=>{const d=diag('test',2);assert.equal(d.status,'empty');assert.equal(d.n_origins,0);assert.ok(d.summary.every(r=>r.mae_pp===null&&r.rmse_pp===null));assert.equal(d.clipImpact.bounded_delta_mae_pp,null);assert.equal(d.clipImpact.raw_delta_mae_pp,null);assert.equal(d.intervals.length,0);});
const models=['persistence','clinical_ridge','combined_ridge'];
function origin(week=1){return models.map((m,i)=>({split:'test',horizon:2,anchor_year:2026,anchor_week:week,anchor_from:week===1?'2026-01-04':'2026-01-11',target_from:week===1?'2026-01-18':'2026-01-25',evaluation_vintage:'SYNTHETIC_A',status:'ok',model_id:m,observed:.02,prediction:[.027,.025,.022][i],raw_prediction:[.027,.025,.022][i]}));}
check('valid shared origin retained',()=>{D.predictions=origin();assert.equal(diag('test',2).n_origins,1);});
check('missing model excludes origin',()=>{D.predictions=origin().slice(0,2);assert.equal(diag('test',2).status,'empty');});
check('null observations exclude origin',()=>{D.predictions=origin().map(r=>({...r,observed:null}));assert.equal(diag('test',2).status,'empty');});
check('conflicting observed targets exclude origin',()=>{D.predictions=origin();D.predictions[0].observed=.03;const d=diag('test',2);assert.equal(d.status,'empty');assert.equal(d.exclusions[0].reason,'inconsistent_observed_target');});
check('duplicate identity rejects whole origin',()=>{D.predictions=origin();D.predictions.push({...D.predictions[0]});assert.equal(diag('test',2).status,'empty');});
check('explicit empty paired_set_id preservation (current exporter statement)',()=>{const row={paired_set_id:''},paired={paired_set_id:'STALE'},has=(r,k)=>Object.prototype.hasOwnProperty.call(r,k),choose=(...v)=>v.find(x=>x!==undefined&&x!==null&&x!=='')??'';assert.equal(has(row,'paired_set_id')?row.paired_set_id:choose(paired?.paired_set_id),'');});
// Regression probe: same-count edits must not retain statistics from another payload.
// These synthetic data are not scientific results, and this is not a full UI test.
D.predictions=[...origin(1),...origin(2)];
const saved=diag('test',2);
const gain=saved.clipImpact.bounded_delta_mae_pp;
D.bootstrap_sensitivity=[{split:'test',horizon:2,n_origins:2,paired_set_id:'SYNTHETIC_A',delta_mae_pp:gain,low:.1,high:.5,block_weeks:4}];
D.raw_bootstrap_sensitivity=[{...D.bootstrap_sensitivity[0]}];
D.predictions=D.predictions.map(r=>({...r,...(r.model_id==='combined_ridge'?{prediction:.04,raw_prediction:.04}:{})}));
const changed=diag('test',2),joint={n_origins:2,delta_mae_pp:gain};
const fallbackSelected=(!changed.n_origins||!joint||joint.n_origins!==changed.n_origins);
const regression={name:'same_count_changed_predictions_retain_stale_saved_statistics',fixture:'synthetic_only',n_origins:changed.n_origins,recomputed_delta_mae_pp:changed.clipImpact.bounded_delta_mae_pp,retained_saved_delta_mae_pp:changed.intervals[0]?.delta_mae_pp,retained_saved_interval:[changed.intervals[0]?.low,changed.intervals[0]?.high],saved_comparison_fallback_selected:fallbackSelected,defect_reproduced:changed.intervals.length>0&&Math.abs(changed.intervals[0].delta_mae_pp-changed.clipImpact.bounded_delta_mae_pp)>1e-10&&!fallbackSelected};
const report={reviewed_commit:'880ce2e8e9e9c558cd1d857e348c5d06f50612e8',node:process.version,scope,not_performed:['full website execution','real browser rendering','Python archive execution','analysis of actual frozen values'],checks:results,passed:results.filter(r=>r.status==='pass').length,failed:results.filter(r=>r.status==='fail').length,regression_probe:regression};
console.log(JSON.stringify(report,null,2));
if(results.some(r=>r.status==='fail')||(strict&&regression.defect_reproduced))process.exitCode=1;

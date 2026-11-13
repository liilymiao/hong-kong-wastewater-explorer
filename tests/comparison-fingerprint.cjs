'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const site=path.resolve(__dirname,'..'),root=path.resolve(site,'..');
const plain=x=>JSON.parse(JSON.stringify(x)),proof=require(path.join(site,'comparison-fingerprint.js'));
let assertions=0;const check=(x,m)=>{assertions++;assert.ok(x,m)};
function load(dir=site,mutate=()=>{},appOverride=null){
 let active=null,controls=[],details=[];const attrs=text=>Object.fromEntries([...text.matchAll(/([\w-]+)(?:="([^"]*)")?/g)].map(m=>[m[1],m[2]??'']));
 function el(tag,at){return{tagName:tag.toUpperCase(),attributes:at,dataset:Object.fromEntries(Object.entries(at).filter(([k])=>k.startsWith('data-')).map(([k,v])=>[k.slice(5).replace(/-([a-z])/g,(_,x)=>x.toUpperCase()),v])),getAttribute(k){return this.attributes[k]??null},focus(){active=this},disabled:at.disabled!==undefined}}
 const app={html:'',clientWidth:1000,contains(e){return controls.includes(e)||details.includes(e)},querySelectorAll(sel){return sel==='details[data-detail-key]'?details:controls},get innerHTML(){return this.html},set innerHTML(s){this.html=s;controls=[...s.matchAll(/<(button|select|input)\b([^>]*)>/g)].map(m=>el(m[1],attrs(m[2])));details=[...s.matchAll(/<details\b([^>]*)>/g)].map(m=>{const n=el('details',attrs(m[1]));n.open=n.attributes.open!==undefined;return n});active=null}};
 const document={documentElement:{},title:'',body:{dataset:{}},get activeElement(){return active},getElementById:id=>id==='proposal-video'?null:app,addEventListener(){},querySelector(){return null}};
 const ctx={console,URL,URLSearchParams,Date,setTimeout:()=>0,clearTimeout(){},requestAnimationFrame:fn=>fn(),cancelAnimationFrame(){},location:{href:'http://localhost/?page=comparison'},history:{replaceState(s,t,u){ctx.location.href=String(u)},pushState(s,t,u){ctx.location.href=String(u)}},localStorage:{getItem(){return null},setItem(){}},document,window:{ResearchQuery:{render(){return '<section>Research query</section>'},weekActions(){return ''}},addEventListener(){},scrollTo(){}}};
 vm.createContext(ctx);vm.runInContext(fs.readFileSync(path.join(dir,'data.js'),'utf8'),ctx);mutate(ctx.window.WASTEWATER_DATA);
 for(const n of ['export-contract.js','analysis-state.js','coverage-sources.js',...(fs.existsSync(path.join(dir,'comparison-fingerprint.js'))?['comparison-fingerprint.js','comparison-manifest.js']:[]),'app.js'])vm.runInContext(fs.readFileSync(n==='app.js'&&appOverride?appOverride:path.join(dir,n),'utf8'),ctx,{filename:n});
 return {api:ctx.window.WastewaterExplorer,D:ctx.window.WASTEWATER_DATA,app,ctx};
}
for(const text of ['', 'abc', '香港污水','a'.repeat(1000), JSON.stringify({n:1e-10,x:[-0,null,true]})])check(proof.sha256(text)===crypto.createHash('sha256').update(text).digest('hex'),'SHA-256 matches independent Node crypto');
const orig=load(site,()=>{},path.join(__dirname,'fixtures/app-v1.6.3.js')),fixed=load();let numericalRows=0;
const strip=r=>Object.fromEntries(Object.entries(r).filter(([k])=>!['comparison_fingerprint','saved_match','saved_match_status','software_version','exported_at_utc','calendar_status_as_of_utc'].includes(k)));
const clean=rows=>plain(rows.map(strip));
for(const split of ['test','validation'])for(const horizon of [1,2])for(const score of ['clipped','raw']){
 const d=fixed.api.reviewDiagnostics(split,horizon),result=d.comparisons[score];
 check(result.saved_match&&result.saved_match_status==='verified','original scope verified');
 check(result.comparison_fingerprint.startsWith('comparison-content-v1:sha256:'),'content fingerprint present');
 const before=orig.api.reviewDiagnostics(split,horizon);
 for(const key of ['summary'])assert.deepEqual(clean(d[key]),clean(before[key]));
 for(const key of ['periods','weekly'])for(const mode of ['clipped','raw'])assert.deepEqual(clean(d[key][mode]),clean(before[key][mode]));
 assert.deepEqual(clean(d.intervals),clean(before.intervals));
 for(const language of ['en','zh']){
  const state={page:'comparison',compareSplit:split,compareHorizon:horizon,compareScore:score,language};orig.api.setState(state);fixed.api.setState(state);
  const a=orig.api.getExports(),b=fixed.api.getExports();assert.deepEqual(Object.keys(b),Object.keys(a));
  for(const id of Object.keys(a)){
   assert.deepEqual(clean(b[id].rows),clean(a[id].rows),id+' unchanged valid exports');numericalRows+=a[id].rows.length;
   for(const row of b[id].rows)check(row.comparison_fingerprint&&row.saved_match===true,id+' export verified fingerprint');
  }
 }
}
for(const h of [1,2])for(const score of ['clipped','raw'])for(const block of [2,4,8])check(fixed.api.reviewDiagnostics('test',h).comparisons[score].intervals.some(r=>r.block_weeks===block),'all12 test intervals retained');
const baselineFingerprint=fixed.api.reviewDiagnostics('test',2).comparisons.clipped.comparison_fingerprint;
const mutations={
 same_count_prediction:D=>{D.predictions.find(r=>r.split==='test'&&r.horizon===2&&r.model_id==='combined_ridge').prediction+=.02;},
 same_count_raw_prediction:D=>{D.predictions.find(r=>r.split==='test'&&r.horizon===2&&r.model_id==='combined_ridge').raw_prediction+=.02;},
 same_count_observation:D=>{for(const r of D.predictions.filter(r=>r.split==='test'&&r.horizon===2&&r.anchor_week===1))r.observed+=.01;},
 same_count_origin:D=>{for(const r of D.predictions.filter(r=>r.split==='test'&&r.horizon===2&&r.anchor_week===1))r.anchor_from='2025-12-21';},
 same_count_target:D=>{for(const r of D.predictions.filter(r=>r.split==='test'&&r.horizon===2&&r.anchor_week===1))r.target_from='2026-01-18';},
 evaluation_version:D=>{for(const r of D.predictions.filter(r=>r.split==='test'&&r.horizon===2))r.evaluation_vintage='synthetic-other-version';},
 source_version:D=>{for(const r of D.predictions.filter(r=>r.split==='test'&&r.horizon===2))r.source_version='synthetic-other-source';},
 configuration:D=>{D.config.forecast.lags=[0,1];},
 frozen_decision:D=>{D.frozen_config.synthetic_revision=true;},
 source_metadata:D=>{D.source_meta.snapshot_date='2026-10-24';},
 source_values:D=>{D.clean[0].SARSCoV2_proportion+=.01;},
 saved_metrics:D=>{D.metrics.find(r=>r.split==='test'&&r.horizon===2&&r.model_id==='combined_ridge').mae_pp+=1;},
 saved_paired:D=>{D.paired_errors.find(r=>r.split==='test'&&r.horizon===2).delta_error_pp+=1;},
 saved_bootstrap:D=>{D.bootstrap_sensitivity.find(r=>r.split==='test'&&r.horizon===2).low+=1;},
 saved_stage:D=>{D.stage_metrics.find(r=>r.split==='test'&&r.horizon===2).delta_mae_pp+=1;}
};
const cases=[];
for(const [name,mutate]of Object.entries(mutations)){
 const t=load(site,mutate),d=t.api.reviewDiagnostics('test',2),r=d.comparisons.clipped;
 check(d.n_origins===40,name+' retains same record count');check(!r.saved_match&&r.saved_match_status==='content_mismatch',name+' rejects old saved results');check(r.intervals.length===0,name+' no stale intervals');
 t.api.setState({page:'comparison',compareSplit:'test',compareHorizon:2,compareScore:'clipped'});
 const exp=t.api.getExports(),joint=exp.metrics.rows.find(r=>r.model_id==='combined_ridge');
 check(joint.mae_pp===d.summary.find(r=>r.model_id==='combined_ridge'&&r.score_mode==='clipped').mae_pp,name+' current metric exported');
 check(joint.delta_ci_low_pp===null&&joint.delta_ci_high_pp===null&&joint.paired_set_id==='',name+' CI blank and paired id not resurrected');
 check(joint.comparison_fingerprint===r.comparison_fingerprint&&joint.saved_match===false,name+' export matches result identity');
 check(t.app.html.includes('Saved intervals are unavailable'),'mismatch explained');
 for(const row of exp['compare-predictions'].rows){check(Math.abs(row.display_abs_error_pp-Math.abs(row.display_prediction-row.observed)*100)<1e-12,name+' exported error recomputed');check(Math.abs(row.squared_error_pp2-((row.prediction-row.observed)*100)**2)<1e-12,name+' squared error recomputed');check(Math.abs(row.raw_squared_error_pp2-((row.raw_prediction-row.observed)*100)**2)<1e-12,name+' raw squared error recomputed');check(row.was_clipped===(row.raw_prediction<0||row.raw_prediction>1),name+' bounds flag recomputed');}
 const plotted=t.api.getPlots().find(p=>p.id==='comparison-errors').data;for(const [i,trace] of plotted.entries()){const model=['persistence','clinical_ridge','combined_ridge'][i];check(trace.y.every((v,j)=>{const record=exp['compare-predictions'].rows.find(r=>r.model_id===model&&r.anchor_from.slice(0,10)===trace.x[j]);return record?Math.abs(v-record.display_abs_error_pp)<1e-12:v===null;}),name+' chart and export values agree');}
 cases.push({name,n_origins:d.n_origins,saved_match:r.saved_match,interval_rows:r.intervals.length});
}
const reorder=load(site,D=>{D.predictions.reverse();for(const key of ['metrics','raw_metrics','paired_errors','raw_paired_errors','bootstrap_sensitivity','raw_bootstrap_sensitivity','stage_metrics','raw_stage_metrics'])D[key].reverse();});
check(reorder.api.reviewDiagnostics('test',2).comparisons.clipped.comparison_fingerprint===baselineFingerprint,'input reordering stable');check(reorder.api.reviewDiagnostics('test',2).comparisons.clipped.saved_match,'saved payload reordering stable');
for(const [name,mutation] of Object.entries({empty:D=>D.predictions=[],duplicate:D=>D.predictions.push({...D.predictions.find(r=>r.split==='test'&&r.horizon===2)}),inconsistent:D=>D.predictions.find(r=>r.split==='test'&&r.horizon===2).observed+=.1})){
 const t=load(site,mutation),d=t.api.reviewDiagnostics('test',2);check(!d.comparisons.clipped.saved_match,name+' rejects old set');check(d.intervals.length===0,name+' no old intervals');if(name==='empty')check(d.summary.every(r=>r.mae_pp===null&&r.rmse_pp===null),'empty null metrics retained');else check(d.n_origins===39,name+' excluded entire origin');
}
const afterLoad=load(),prior=afterLoad.api.reviewDiagnostics('test',2).comparisons.clipped.comparison_fingerprint;afterLoad.D.predictions.find(r=>r.split==='test'&&r.horizon===2&&r.model_id==='combined_ridge').prediction+=.05;afterLoad.api.setState({page:'comparison',compareHorizon:2,compareSplit:'test',compareScore:'clipped'});check(afterLoad.api.getExports().metrics.rows.every(r=>r.saved_match===false&&r.comparison_fingerprint!==prior),'post-load mutation cannot reuse cached results');
const missingProof=load();delete missingProof.ctx.window.COMPARISON_MANIFEST;check(!missingProof.api.reviewDiagnostics('test',2).comparisons.clipped.saved_match,'missing manifest fails closed');
check(JSON.stringify(fixed.D)===JSON.stringify(orig.D),'runtime does not mutate frozen data');
const report={status:'passed',assertions,verified_original_scopes:8,retained_test_interval_states:12,unchanged_export_rows:numericalRows,mutation_cases:cases,sha256_verified_against_node_crypto:true,data_js_sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(site,'data.js'))).digest('hex'),scope:'Actual app functions and comparison render/export in a Node VM with a parsed DOM; not a real-browser claim'};
fs.writeFileSync(path.join(root,'qa/comparison-fingerprint-tests.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));

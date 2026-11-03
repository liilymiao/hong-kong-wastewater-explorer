/* Metadata added at download time. Frozen input rows are never mutated. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.ExportContract=api;})(typeof window==='undefined'?this:window,function(){'use strict';
const softwareVersion='1.6.0';
const present=x=>x!==undefined&&x!==null&&x!=='';
const has=(r,k)=>Object.prototype.hasOwnProperty.call(r,k);
const choose=(...values)=>values.find(present)??'';
function enrichRows(rows,context={},dataset={}){
 const meta=dataset.source_meta||{},config=dataset.config||{},evaluation=config.evaluation||{},timestamp=context.exportedAt||new Date().toISOString();
 return rows.map(row=>{
  const r={...row},horizon=choose(r.horizon,context.horizon),split=choose(r.split,context.split),score=choose(r.display_score_mode,r.score_mode,context.score);
  const paired=(dataset.metrics||[]).find(m=>m.horizon===Number(horizon)&&m.split===split);
  const interval=(present(r.delta_ci_low_pp)&&present(r.delta_ci_high_pp))||(present(r.low)&&present(r.high));
  const predictionFields=['prediction','raw_prediction','display_prediction'],observationFields=['observed','SARSCoV2_proportion','p','p_center'];
  const units={};for(const k of Object.keys(r)){
   if(predictionFields.includes(k)||observationFields.includes(k))units[k]='proportion (1 = 100%)';
   else if(k.endsWith('_pp2'))units[k]='percentage_points_squared';
   else if(k.endsWith('_pp')||interval&&['low','high'].includes(k))units[k]='percentage_points';
   else if(k.endsWith('_pct')||k.endsWith('_percent'))units[k]='percent';
   else if(['Sewage_viralload','w_center','w'].includes(k))units[k]='copy/L';
   else if(k.includes('log1p_w'))units[k]='natural_log(1 + wastewater_copy_per_L)';
  }
  Object.assign(r,{software_version:softwareVersion,analysis_version:choose(meta.project_version,config.project?.version),snapshot_date:choose(meta.snapshot_date,config.project?.snapshot_date_hkt),source_data_sha256:choose(config.data?.sha256),source_url:choose(meta.source_url),source_generated_at_utc:choose(meta.generated_at_utc),exported_at_utc:timestamp,export_kind:choose(context.kind),post_hoc_diagnostic:context.posthoc===true||r.analysis_type==='post_hoc_descriptive',horizon,score_mode:score,split,paired_set_id:choose(r.paired_set_id,paired?.paired_set_id),prediction_unit:predictionFields.some(k=>has(r,k))?'proportion (1 = 100%)':'',observed_unit:observationFields.some(k=>has(r,k))?'proportion (1 = 100%)':'',error_unit:Object.values(units).includes('percentage_points')?'percentage_points':'',field_units:JSON.stringify(units)});
  if(interval){r.block_weeks=choose(row.block_weeks,context.blockWeeks,evaluation.bootstrap_block_weeks);r.bootstrap_resamples=choose(row.bootstrap_resamples,evaluation.bootstrap_repeats);r.bootstrap_confidence_level=choose(row.bootstrap_confidence_level,row.confidence_level,evaluation.bootstrap_confidence_level);r.interval_quantity=choose(row.interval_quantity,'mean_paired_MAE_difference_clinical_minus_combined');r.interval_unit='percentage_points';}
  else{for(const k of ['block_weeks','bootstrap_resamples','bootstrap_confidence_level','interval_quantity','interval_unit'])if(!has(r,k))r[k]='';}
  if(has(row,'coverage')){r.coverage_kind='evaluable_origins';r.n_evaluable_origins=choose(row.n_origins);r.n_candidate_origins=Number(row.coverage)>0&&present(row.n_origins)?Math.round(Number(row.n_origins)/Number(row.coverage)):'';}
  return r;
 });
}
function filename(base,context={}){let stem=String(base||'records').replace(/\.csv$/i,'').replace(/[^a-zA-Z0-9_.-]+/g,'-');const tokens=stem.split(/[_-]/);for(const token of [present(context.horizon)?'h'+context.horizon:'',context.score,context.split])if(present(token)&&!tokens.includes(String(token)))stem+='-'+token;return stem+'-'+String(context.exportDate||context.exportedAt||new Date().toISOString()).slice(0,10)+'.csv';}
return{softwareVersion,enrichRows,filename};
});

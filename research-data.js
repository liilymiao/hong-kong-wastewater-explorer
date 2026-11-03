/* Pure research-table and import validation helpers. No network or model fitting. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.ResearchData=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){'use strict';
const SCHEMAS={
 wastewater:['sample_id','collection_date','area_id','indicator','value','unit','method','normalization'],
 clinical:['period_start','period_end','area_id','organism','antibiotic','endpoint','n_tested','n_positive','standard','dedup_rule','count_quality','evidence_type'],
 mapping:['wastewater_area_id','clinical_area_id','basis']
};
const COVID_FIELDS=['week_key','From','To_corrected','SARSCoV2_proportion','Sewage_viralload','source_version','source_row_key'];
const LINK_FIELDS=['period_start','period_end','clinical_area_id','organism','antibiotic','endpoint','n_tested','n_positive','rate','standard','dedup_rule','count_quality','evidence_type','source_reference','indicator','environment_mean','unit','method','normalization','n_samples','source_sample_ids','wastewater_area_ids','mapping_basis','aggregation','clinical_resolution','requested_resolution','purpose','weekly_resolution_compatible','prediction_feasibility','clinical_source_row','wastewater_source_rows'];
const clone=v=>v===undefined?undefined:JSON.parse(JSON.stringify(v));
const own=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
const issue=(severity,code,message,extra={})=>({severity,code,message,...extra});
const exclusion=(source,row,code,reason,record)=>({source,row:row??null,code,reason,record:clone(record)});
function dateValue(s){if(typeof s!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(s))return null;const t=Date.parse(s+'T00:00:00Z');return Number.isFinite(t)&&new Date(t).toISOString().slice(0,10)===s?t:null;}
function numeric(s){if(typeof s==='number')return Number.isFinite(s)?s:null;if(typeof s!=='string'||!s.trim()||!/^[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?$/i.test(s.trim()))return null;const n=Number(s);return Number.isFinite(n)?n:null;}
function parseCSV(text){
 if(typeof text!=='string')return{headers:[],records:[],errors:[issue('error','invalid_csv','CSV input must be text.')]};
 text=text.replace(/^\uFEFF/,'');let rows=[],cells=[],cell='',quoted=false,closed=false,line=1,startLine=1,errors=[];
 const pushCell=()=>{cells.push(cell);cell='';closed=false};
 const pushRow=()=>{pushCell();if(cells.some(x=>x!==''))rows.push({cells,line:startLine});cells=[];startLine=line+1};
 for(let i=0;i<text.length;i++){
  const c=text[i];
  if(quoted){if(c==='"'){if(text[i+1]==='"'){cell+='"';i++}else{quoted=false;closed=true}}else{cell+=c;if(c==='\n')line++}continue;}
  if(c==='"'){if(cell!==''||closed){errors.push(issue('error','malformed_quotes','Quote inside an unquoted field.',{row:line}));cell+=c;}else quoted=true;}
  else if(c===',')pushCell();
  else if(c==='\n'||c==='\r'){if(c==='\r'&&text[i+1]==='\n')i++;pushRow();line++;startLine=line;}
  else if(closed){if(!/\s/.test(c)){errors.push(issue('error','malformed_quotes','Unexpected text after a closing quote.',{row:line}));cell+=c;}}
  else cell+=c;
 }
 if(quoted)errors.push(issue('error','unterminated_quote','CSV contains an unterminated quoted field.',{row:startLine}));
 if(cell!==''||cells.length||closed)pushRow();
 if(!rows.length)return{headers:[],records:[],errors:[...errors,issue('error','empty_csv','CSV has no header or data.')]};
 const headers=rows.shift().cells.map(h=>h.trim());
 if(headers.some(h=>!h))errors.push(issue('error','empty_header','CSV headers must be non-empty.'));
 if(new Set(headers).size!==headers.length)errors.push(issue('error','duplicate_header','CSV contains duplicate column names.'));
 const records=[];
 for(const row of rows){if(row.cells.length!==headers.length){errors.push(issue('error','column_count','Row column count does not match the header.',{row:row.line,values:row.cells}));continue;}const record={};headers.forEach((h,i)=>Object.defineProperty(record,h,{value:row.cells[i],writable:true,enumerable:true,configurable:true}));records.push({row:row.line,record});}
 return{headers,records,errors};
}
function validateImport(kind,text){
 if(!own(SCHEMAS,kind))return{kind,valid:false,records:[],issues:[issue('error','unknown_import_kind','Expected wastewater, clinical or mapping CSV.')],excluded:[],headers:[],summary:{input:0,accepted:0,excluded:0}};
 const parsed=parseCSV(text),issues=[...parsed.errors],excluded=parsed.errors.filter(e=>e.code==='column_count').map(e=>exclusion(kind,e.row,e.code,e.message,{values:e.values})),candidates=[];
 const missing=SCHEMAS[kind].filter(k=>!parsed.headers.includes(k));
 if(missing.length)issues.push(issue('error','missing_columns','Required columns are missing.',{fields:missing}));
 if(missing.length||parsed.errors.some(e=>['empty_header','duplicate_header','unterminated_quote','malformed_quotes','invalid_csv','empty_csv'].includes(e.code)))return{kind,valid:false,records:[],issues,excluded:parsed.records.map(r=>exclusion(kind,r.row,'invalid_structure','CSV structure must be corrected before import.',r.record)),headers:parsed.headers,summary:{input:parsed.records.length,accepted:0,excluded:parsed.records.length}};
 for(const {row,record:raw} of parsed.records){
  const record={...raw};for(const k of SCHEMAS[kind])record[k]=String(raw[k]??'').trim();
  let reasons=[];const blanks=SCHEMAS[kind].filter(k=>!record[k]);if(blanks.length)reasons.push(['missing_value','Required values are empty: '+blanks.join(', ')]);
  if(kind==='wastewater'){
   if(dateValue(record.collection_date)===null)reasons.push(['invalid_date','collection_date must be a valid ISO date (YYYY-MM-DD).']);
   const n=numeric(record.value);if(n===null||n<0)reasons.push(['invalid_value','Wastewater value must be a finite non-negative number.']);else record.value=n;
  }else if(kind==='clinical'){
   const a=dateValue(record.period_start),b=dateValue(record.period_end);if(a===null||b===null||a>b)reasons.push(['invalid_period','Clinical period must have valid ISO dates with start no later than end.']);
   if(record.count_quality!=='exact')reasons.push(['non_exact_counts','count_quality must be exact; rounded, suppressed or unknown counts cannot enter rate analysis.']);
   if(record.evidence_type!=='experimental_ast')reasons.push(['unsupported_clinical_evidence','evidence_type must be experimental_ast; predicted susceptibility cannot be treated as measured AST counts.']);
   if(!['resistant','non_susceptible'].includes(record.endpoint))reasons.push(['invalid_endpoint','endpoint must be resistant or non_susceptible.']);
   const tested=numeric(record.n_tested),positive=numeric(record.n_positive);
   if(tested===null||positive===null||!Number.isSafeInteger(tested)||!Number.isSafeInteger(positive)||tested<0||positive<0||positive>tested)reasons.push(['invalid_denominator','n_tested and n_positive must be non-negative integers, with n_positive no greater than n_tested.']);
   else{record.n_tested=tested;record.n_positive=positive;}
  }
  if(reasons.length){for(const [code,message]of reasons)issues.push(issue('error',code,message,{row,source:kind}));excluded.push(exclusion(kind,row,reasons[0][0],reasons.map(x=>x[1]).join(' '),raw));continue;}
  record.source_row=row;record.source_values=clone(raw);candidates.push(record);
 }
 const key=r=>JSON.stringify((kind==='wastewater'?['sample_id','indicator']:kind==='clinical'?['period_start','period_end','area_id','organism','antibiotic','endpoint']:['wastewater_area_id','clinical_area_id']).map(k=>r[k]));
 const groups=new Map();for(const r of candidates){const k=key(r);if(!groups.has(k))groups.set(k,[]);groups.get(k).push(r);}
 const records=[];
 for(const group of groups.values()){
  if(group.length===1){records.push(group[0]);continue;}
  const signature=r=>JSON.stringify(SCHEMAS[kind].map(k=>r[k]));const exact=new Set(group.map(signature)).size===1;
  if(exact){records.push(group[0]);for(const r of group.slice(1)){excluded.push(exclusion(kind,r.source_row,'duplicate_exact','Identical duplicate removed; the first record is retained.',r.source_values));issues.push(issue('warning','duplicate_exact','Identical duplicate removed.',{source:kind,row:r.source_row}));}}
  else for(const r of group){excluded.push(exclusion(kind,r.source_row,'duplicate_conflict','Conflicting duplicate identity; all records with this identity are excluded until corrected.',r.source_values));issues.push(issue('error','duplicate_conflict','Conflicting duplicate identity; do not pool unrecorded strata.',{source:kind,row:r.source_row}));}
 }
 records.sort((a,b)=>a.source_row-b.source_row);
 return{kind,valid:!issues.some(i=>i.severity==='error'),records,issues,excluded,headers:parsed.headers,summary:{input:parsed.records.length,accepted:records.length,excluded:excluded.length,errors:issues.filter(i=>i.severity==='error').length,warnings:issues.filter(i=>i.severity==='warning').length}};
}
function rangeOptions(options={}){
 const from=options.from||'',to=options.to||'',errors=[];
 if(from&&dateValue(from)===null)errors.push(issue('error','invalid_from','Start date must be a valid ISO date.'));
 if(to&&dateValue(to)===null)errors.push(issue('error','invalid_to','End date must be a valid ISO date.'));
 if(from&&to&&from>to)errors.push(issue('error','reversed_range','Start date must not follow end date.'));
 const exclusions=[];
 for(const e of options.exclusions||[]){if(!e||dateValue(e.start)===null||dateValue(e.end)===null||e.start>e.end)errors.push(issue('error','invalid_exclusion','Excluded periods need valid ordered ISO dates.'));else exclusions.push({start:e.start,end:e.end,reason:String(e.reason||'User-selected excluded period')});}
 return{from,to,exclusions,errors};
}
function rangeReason(start,end,range){if(range.from&&start<range.from||range.to&&end>range.to)return['outside_date_range','The complete observation period is outside the selected date range.'];const hit=range.exclusions.find(e=>start<=e.end&&end>=e.start);return hit?['user_excluded_period',hit.reason]:null;}
function reasonCounts(excluded){return excluded.reduce((a,x)=>(a[x.code]=(a[x.code]||0)+1,a),{});}
function buildCovidTable(data,options={}){
 // Also accept (options, data) for callers whose data is already available separately.
 if(!Array.isArray(data)&&!data?.clean&&(Array.isArray(options)||options?.clean)){const swap=data;data=options;options=swap||{};}
 const input=Array.isArray(data)?data:data?.clean||[],range=rangeOptions(options),rows=[],excluded=[],issues=[...range.errors];
 if(!range.errors.length)for(const r of input){
  const start=r.From,end=r.To_corrected||r.To;let reason;
  if(dateValue(start)===null||dateValue(end)===null||start>end)reason=['invalid_source_period','Source week has no valid ordered ISO start/end dates.'];
  else reason=rangeReason(start,end,range);
  if(!reason){const p=numeric(r.SARSCoV2_proportion),w=numeric(r.Sewage_viralload);if(p===null)reason=['missing_clinical','Clinical specimen positivity is missing.'];else if(p<0||p>1)reason=['invalid_clinical','Clinical proportion is outside 0–1.'];else if(w===null)reason=['missing_wastewater','Wastewater value is missing; no value was imputed.'];else if(w<0)reason=['invalid_wastewater','Wastewater value is negative.'];}
  if(reason)excluded.push(exclusion('covid',r.source_row_key||r.week_key,reason[0],reason[1],r));else rows.push(clone(r));
 }
 return{rows,excluded,issues,blockers:issues.filter(i=>i.severity==='error').map(i=>i.message),summary:{input:input.length,selected:rows.length+excluded.filter(e=>!['outside_date_range','user_excluded_period'].includes(e.code)).length,eligible:rows.length,excluded:excluded.length,missingWastewater:excluded.filter(e=>e.code==='missing_wastewater').length,reasonCounts:reasonCounts(excluded),status:range.errors.length?'blocked':rows.length?'available':'empty'},fields:rows.length?Object.keys(rows[0]):COVID_FIELDS,linkage:{kind:'citywide_weekly_aggregate',temporal_rule:'Complete monitoring week within inclusive selected dates; exclusion periods remove intersecting weeks.',clinical_target:'Proportion of PHLSB respiratory specimens positive for SARS-CoV-2',clinical_unit:'proportion (1 = 100%)',wastewater_unit:'copy/L',imputation:'none',original_values_preserved:true}};
}
function arrayRecords(value){return Array.isArray(value)?value:value?.records||[];}
function chosen(value,selection){return selection===undefined||selection===null||selection===''||selection==='all'||(Array.isArray(selection)?selection.includes(value):value===selection);}
function clinicalResolution(days){return days<=7?'weekly':days<=31?'monthly':days<=92?'quarterly':days<=366?'annual':'multiannual';}
function buildEcologicalLinkage(options={}){
 const wastewater=arrayRecords(options.wastewater),clinical=arrayRecords(options.clinical),mapping=arrayRecords(options.mapping),f=options.filters||{},range=rangeOptions(f),rows=[],excluded=[],issues=[...range.errors];
 const resolution=f.resolution||'weekly',purpose=f.purpose||(f.analysisMode==='weekly_prediction'?'prediction':'association'),limits={weekly:7,monthly:31,annual:366};
 const linkage={kind:'ecological_temporal_geographic_linkage',same_sample_pairing:false,geography:'Explicit uploaded area mapping only',temporal_rule:'Wastewater collection date falls inside the complete clinical reporting period',aggregation:'Unweighted arithmetic mean of eligible wastewater samples',clinical_aggregation:'Clinical counts are retained per original reporting record; repeated linked rows must not be pooled as independent denominators.',prediction_feasibility:'not_evaluated',prediction_requirements:'Future clinical targets, actual publication availability and independent temporal validation are not established by concurrent ecological linkage.',unit_policy:'Different units, methods or normalizations block aggregation within an indicator and clinical reporting period.',resolution,purpose};
 const finish=()=>({rows,excluded,issues,blockers:issues.filter(i=>i.severity==='error').map(i=>i.message),summary:{inputWastewater:wastewater.length,inputClinical:clinical.length,inputMappings:mapping.length,eligible:rows.length,linkageRows:rows.length,excluded:excluded.length,reasonCounts:reasonCounts(excluded),blockers:issues.filter(x=>x.severity==='error').length,status:issues.some(x=>x.severity==='error')&&!rows.length?'blocked':rows.length?'available':'empty'},fields:LINK_FIELDS,linkage});
 if(!own(limits,resolution)){issues.push(issue('error','invalid_resolution','Resolution must be weekly, monthly or annual.'));return finish();}
 if(!['prediction','association','background'].includes(purpose)){issues.push(issue('error','invalid_purpose','Purpose must be prediction, association or background.'));return finish();}
 if(range.errors.length)return finish();
 if(!wastewater.length||!clinical.length||!mapping.length){issues.push(issue('error','missing_imports','Import validated wastewater measurements, clinical counts and explicit area mappings to construct an AMR research table.',{missing:[!wastewater.length?'wastewater':null,!clinical.length?'clinical':null,!mapping.length?'mapping':null].filter(Boolean)}));return finish();}
 const mappedByWW=new Map(),mappedByClinical=new Map();
 for(const m of mapping){if(!m.wastewater_area_id||!m.clinical_area_id||!m.basis){issues.push(issue('error','invalid_mapping','Each mapping requires both area IDs and a basis.'));continue;}if(!mappedByWW.has(m.wastewater_area_id))mappedByWW.set(m.wastewater_area_id,[]);mappedByWW.get(m.wastewater_area_id).push(m);if(!mappedByClinical.has(m.clinical_area_id))mappedByClinical.set(m.clinical_area_id,[]);mappedByClinical.get(m.clinical_area_id).push(m);}
 const eligibleWW=[];
 for(const w of wastewater){let reason=rangeReason(w.collection_date,w.collection_date,range);if(dateValue(w.collection_date)===null||numeric(w.value)===null||Number(w.value)<0)reason=['invalid_wastewater_record','Wastewater records must pass import validation.'];else if(!reason&&!chosen(w.indicator,f.indicator))reason=['indicator_filter','Wastewater indicator is outside the selected research object.'];else if(!reason&&!mappedByWW.has(w.area_id))reason=['unmapped_wastewater_area','No explicit clinical-area mapping exists for this wastewater area.'];if(reason)excluded.push(exclusion('wastewater',w.source_row,reason[0],reason[1],w));else eligibleWW.push(w);}
 const consumed=new Set();
 for(const c of clinical){
  let reason=rangeReason(c.period_start,c.period_end,range);const a=dateValue(c.period_start),b=dateValue(c.period_end),n=numeric(c.n_tested),positive=numeric(c.n_positive);
  if(a===null||b===null||a>b||n===null||positive===null||!Number.isSafeInteger(n)||!Number.isSafeInteger(positive)||n<0||positive<0||positive>n||!['resistant','non_susceptible'].includes(c.endpoint)||c.count_quality!=='exact'||c.evidence_type!=='experimental_ast')reason=['invalid_clinical_record','Clinical records must pass import validation.'];
  else if(!reason&&(!chosen(c.organism,f.organism)||!chosen(c.antibiotic,f.antibiotic)||!chosen(c.endpoint,f.endpoint)))reason=['clinical_object_filter','Clinical record is outside the selected organism, antibiotic or endpoint.'];
  else if(!reason&&!chosen(c.area_id,f.area_id||f.clinical_area_id))reason=['clinical_area_filter','Clinical record is outside the selected area.'];
  else if(!reason&&!mappedByClinical.has(c.area_id))reason=['unmapped_clinical_area','No explicit wastewater-area mapping exists for this clinical area.'];
  else if(!reason&&n===0)reason=['zero_denominator','Clinical n_tested is zero; a resistance proportion cannot be calculated.'];
  const days=a===null||b===null?null:(b-a)/86400000+1,actual=days?clinicalResolution(days):'unknown',coarse=days>limits[resolution];
  if(!reason&&coarse&&purpose!=='background'){reason=['resolution_mismatch',`Clinical reporting period is ${days} days (${actual}); it cannot support the requested ${resolution} ${purpose}. Use a coarser analysis or background context.`];issues.push(issue('error',reason[0],reason[1],{source:'clinical',row:c.source_row}));}
  if(reason){excluded.push(exclusion('clinical',c.source_row,reason[0],reason[1],c));continue;}
  const maps=mappedByClinical.get(c.area_id),areaSet=new Set(maps.map(m=>m.wastewater_area_id)),matched=eligibleWW.filter(w=>areaSet.has(w.area_id)&&w.collection_date>=c.period_start&&w.collection_date<=c.period_end);
  if(!matched.length){excluded.push(exclusion('clinical',c.source_row,'no_environment_samples','No eligible wastewater collection falls inside this clinical period and its mapped areas.',c));continue;}
  const indicators=[...new Set(matched.map(w=>w.indicator))];
  for(const indicator of indicators){
   const samples=matched.filter(w=>w.indicator===indicator),signatures=new Set(samples.map(w=>JSON.stringify([w.unit,w.method,w.normalization])));
   if(signatures.size!==1||samples.some(w=>!w.unit||!w.method||!w.normalization)){
    const message='Different or missing unit, method or normalization values prevent aggregation for this indicator and clinical period.';
    issues.push(issue('error','incompatible_measurements',message,{source:'linkage',clinical_row:c.source_row,indicator,signatures:[...signatures].map(s=>JSON.parse(s))}));
    excluded.push(exclusion('linkage',c.source_row,'incompatible_measurements',message,{clinical:c,wastewater:samples}));continue;
   }
   samples.forEach(w=>consumed.add(w));const base=samples[0],usedAreas=[...new Set(samples.map(w=>w.area_id))].sort(),usedMaps=maps.filter(m=>usedAreas.includes(m.wastewater_area_id));
   const mean=samples.reduce((sum,w)=>sum+Number(w.value)/samples.length,0);
   rows.push({period_start:c.period_start,period_end:c.period_end,clinical_area_id:c.area_id,organism:c.organism,antibiotic:c.antibiotic,endpoint:c.endpoint,n_tested:n,n_positive:positive,rate:positive/n,standard:c.standard,dedup_rule:c.dedup_rule,count_quality:c.count_quality,evidence_type:c.evidence_type,source_reference:c.source_reference||'',indicator,environment_mean:mean,unit:base.unit,method:base.method,normalization:base.normalization,n_samples:samples.length,source_sample_ids:samples.map(w=>w.sample_id),wastewater_area_ids:usedAreas,mapping_basis:[...new Set(usedMaps.map(m=>m.basis))],aggregation:'unweighted arithmetic mean',clinical_resolution:actual,clinical_period_days:days,requested_resolution:resolution,purpose,resolution_compatible:!coarse,weekly_resolution_compatible:days<=7,prediction_feasibility:'not_evaluated',clinical_source_row:c.source_row??null,wastewater_source_rows:samples.map(w=>w.source_row??null)});
   if(coarse)issues.push(issue('warning','background_only','Coarser clinical records are retained as background only, without claiming the requested finer temporal resolution.',{source:'clinical',row:c.source_row}));
  }
 }
 for(const w of eligibleWW)if(!consumed.has(w))excluded.push(exclusion('wastewater',w.source_row,'not_linked','Sample contributed to no accepted clinical-period aggregate; see clinical and linkage exclusions.',w));
 rows.sort((a,b)=>a.period_start.localeCompare(b.period_start)||a.clinical_area_id.localeCompare(b.clinical_area_id)||a.indicator.localeCompare(b.indicator));
 if(!rows.length&&!issues.some(i=>i.severity==='error'))issues.push(issue('warning','no_linkage_rows','No eligible ecological linkage rows satisfy the selected research conditions.'));
 return finish();
}
function toCSV(rows,fields){const keys=fields||[...new Set(rows.flatMap(Object.keys))],cell=v=>{if(v===null||v===undefined)return'';let s=typeof v==='object'?JSON.stringify(v):String(v);if(typeof v==='string'&&numeric(v)===null&&(/^[\t\r]/.test(v)||/^\s*[=+@-]/.test(v)))s="'"+s;return /[",\r\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s;};return '\uFEFF'+[keys.map(cell).join(','),...rows.map(r=>keys.map(k=>cell(r[k])).join(','))].join('\r\n')+'\r\n';}
return{SCHEMAS:clone(SCHEMAS),parseCSV,validateImport,buildCovidTable,buildEcologicalLinkage,toCSV,dateValue};
});

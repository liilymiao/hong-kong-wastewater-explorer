/* Versioned, deterministic analysis URLs. No saved observations are changed. */
(function(root,factory){const api=factory(root);if(typeof module==='object'&&module.exports)module.exports=api;else root.AnalysisState=api})(typeof window!=='undefined'?window:globalThis,function(root){'use strict';
const VERSION='1';
const FIELDS={page:'page',language:'lang',overviewYears:'years',overviewScale:'scale',replaySplit:'replay-period',replayHorizon:'replay-h',replayAnchor:'week',replayDelay:'delay',replayScore:'replay-score',compareSplit:'compare-period',compareHorizon:'h',compareScore:'score',compareModels:'models',patternYears:'query-years',patternSort:'order',patternWeek:'query-week',patternTab:'tab',neighborsK:'neighbors',research:'research'};
const ARRAYS=['overviewYears','compareModels','patternYears'];
const META={software:'app',analysis:'analysis',snapshot:'snapshot',source:'source',generated:'results'};
const RESEARCH_DEFAULT={question:'',topic:'covid',region:'Hong Kong',purpose:'prediction',organism:'Escherichia coli',antibiotic:'ciprofloxacin',endpoint:'non_susceptible',start:'2023-01-29',end:'2026-10-17',resolution:'weekly',selected:['covid-weekly'],notes:'',exclusions:[],importDigests:{},datasetFilters:{years:[]},datasetVersions:{}};
const SOURCE_IDS=['covid-weekly','hk-amr-annual','bv-brc','ena','clinical-partner','phlsb-outpatient','europe-arg','hk-community','ha-amr','antimicrobial-supply','bvbrc-ast','hko-rainfall','flu-express','global-sewage'];
const DATASET_IDS=['phlsb-outpatient','europe-arg','hk-community','ha-amr','antimicrobial-supply','bvbrc-ast','hko-rainfall','flu-express','global-sewage'];
const DATASET_FILTERS=['specimen','organism','analyte','measure','city','plant','arg','sampleSearch','season','platform','antimicrobial','onset_setting','sector','antimicrobial_group','resistant_phenotype','laboratory_typing_method','measurement_unit','isolation_country','host_name','isolation_source','station','country','gene','field','mic','sequence','yearMode','collection_year','method','cohort_eligible','measurement_type','evidence','mic_eligible','conflict_label','sequence_available','quality_status','value_status','year','date','group','sample_id','clinical_area_id','cohortTask','measurement_sign','compareFrom','compareTo','qcSection','qcMetric','qcMin','qcMax','qcSort','qcGroup'];
const plain=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const clone=x=>JSON.parse(JSON.stringify(x));
const week=r=>`${r.anchor_year}W${String(r.anchor_week).padStart(2,'0')}`;
const unique=x=>[...new Set(x)];
const numeric=x=>typeof x==='number'&&Number.isFinite(x)||typeof x==='string'&&/^\d+$/.test(x)?Number(x):NaN;
function researchDefaults(){return clone(RESEARCH_DEFAULT)}
function isoDate(value){if(typeof value!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(value))return false;const date=new Date(value+'T00:00:00Z');return Number.isFinite(date.getTime())&&date.toISOString().slice(0,10)===value}
function normalizeResearch(input,defaults=RESEARCH_DEFAULT){
  const value=plain(input)?input:{},out=clone(RESEARCH_DEFAULT),base=plain(defaults)?defaults:RESEARCH_DEFAULT;
  for(const [key,max] of Object.entries({question:1500,region:100,organism:100,antibiotic:100,notes:3000}))out[key]=String(typeof value[key]==='string'?value[key]:base[key]??RESEARCH_DEFAULT[key]).replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/g,'').slice(0,max);
  const enums={topic:['covid','amr','phlsb','arg','hk','ha','supply','bvbrc','rainfall','flu','global'],purpose:['prediction','association','background','table','query'],endpoint:['','R','marker_positive','resistant','resistant_R','non_susceptible','clinical_positivity','official_non_susceptibility','wholesale_supply','experimental_AST','MIC','raw_counts'],resolution:['source','sample','daily','weekly','monthly','annual']};
  for(const [key,allowed] of Object.entries(enums))out[key]=allowed.includes(value[key])?value[key]:allowed.includes(base[key])?base[key]:RESEARCH_DEFAULT[key];
  for(const key of ['start','end'])out[key]=isoDate(value[key])?value[key]:isoDate(base[key])?base[key]:RESEARCH_DEFAULT[key];
  out.selected=Array.isArray(value.selected)?SOURCE_IDS.filter(x=>value.selected.includes(x)):SOURCE_IDS.filter(x=>(base.selected||RESEARCH_DEFAULT.selected).includes(x));
  out.exclusions=(Array.isArray(value.exclusions)?value.exclusions:base.exclusions||[]).filter(x=>plain(x)&&isoDate(x.start)&&isoDate(x.end)&&x.start<=x.end).slice(0,20).map(x=>({start:x.start,end:x.end,reason:typeof x.reason==='string'?x.reason.replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/g,'').slice(0,300):''}));
  const digests=plain(value.importDigests)?value.importDigests:plain(base.importDigests)?base.importDigests:{};out.importDigests={};for(const role of ['wastewater','clinical','mapping'])if(typeof digests[role]==='string'&&/^[a-fA-F0-9]{64}$/.test(digests[role]))out.importDigests[role]=digests[role].toLowerCase();
  const filters=plain(value.datasetFilters)?value.datasetFilters:plain(base.datasetFilters)?base.datasetFilters:{};out.datasetFilters={};
  for(const key of DATASET_FILTERS)if(typeof filters[key]==='string'||(['compareFrom','compareTo'].includes(key)&&Number.isFinite(filters[key]))){
    const text=String(filters[key]).replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/g,'').slice(0,160);
    if(key!=='measure'||['','drug_resistance','marker_positivity'].includes(text))out.datasetFilters[key]=text;
  }
  for(const key of ['analytes','genes'])if(Array.isArray(filters[key]))out.datasetFilters[key]=unique(filters[key].filter(x=>typeof x==='string').map(x=>x.replace(/[\u0000-\u001f\u007f]/g,'').slice(0,160))).slice(0,600);
  const selectedYears=Array.isArray(filters.years)?filters.years:[];
  out.datasetFilters.years=unique(selectedYears.filter(x=>typeof x==='number'&&Number.isInteger(x)&&x>=1900&&x<=2100)).sort((a,b)=>a-b).slice(0,150);
  // An incoming research object must carry its own dataset identity. Missing or
  // explicitly empty identities must never inherit the currently loaded files.
  const datasetVersions=plain(input)?(plain(value.datasetVersions)?value.datasetVersions:{}):(plain(base.datasetVersions)?base.datasetVersions:{});
  out.datasetVersions={};for(const id of DATASET_IDS)if(typeof datasetVersions[id]==='string'&&/^[a-fA-F0-9]{64}$/.test(datasetVersions[id]))out.datasetVersions[id]=datasetVersions[id].toLowerCase();
  const module=['phlsb','arg','hk'].includes(out.topic)?root.DatasetQuery:['ha','supply','bvbrc','rainfall','flu','global'].includes(out.topic)?root.ExtensionQuery:root.ResearchQuery;
  return module?.normalizeResearch?module.normalizeResearch(out):out;
}
function identity(data,software){return{software:String(software),analysis:String(data.source_meta.project_version),snapshot:data.source_meta.snapshot_date,source:data.config.data.sha256,generated:data.source_meta.generated_at_utc}}
function normalize(input,defaults,data){
  const source=plain(input)?input:{},state=clone(defaults);
  const enums={page:['overview','replay','comparison','patterns','research'],language:['en','zh'],overviewScale:['raw','log'],replaySplit:['test','validation','future'],replayScore:['clipped','raw'],compareSplit:['test','validation'],compareScore:['clipped','raw'],patternSort:['lof','recent'],patternTab:['centers','neighbors','sensitivity','source']};
  for(const [key,allowed] of Object.entries(enums))if(allowed.includes(source[key]))state[key]=source[key];
  for(const key of ['replayHorizon','compareHorizon'])if([1,2].includes(numeric(source[key])))state[key]=numeric(source[key]);
  const yearSets={overviewYears:unique(data.clean.map(r=>Number(r.Year))),patternYears:unique(data.patterns.map(r=>Number(r.week_key.slice(0,4))))};
  for(const [key,allowed] of Object.entries(yearSets))if(Array.isArray(source[key]))state[key]=unique(source[key].map(Number).filter(x=>allowed.includes(x))).sort((a,b)=>a-b);
  if(Array.isArray(source.compareModels))state.compareModels=['persistence','clinical_ridge','combined_ridge'].filter(x=>source.compareModels.includes(x));
  const anchors=unique(data.predictions.filter(r=>r.split===state.replaySplit&&r.horizon===state.replayHorizon).map(week)).sort();
  state.replayAnchor=anchors.includes(source.replayAnchor)?source.replayAnchor:anchors.includes(state.replayAnchor)?state.replayAnchor:anchors.at(-1)||defaults.replayAnchor;
  const delays=state.replaySplit==='future'?[0,5,6,7,8]:[5,6,7,8];
  state.replayDelay=delays.includes(numeric(source.replayDelay))&&source.replayDelay!==null&&source.replayDelay!==''?numeric(source.replayDelay):state.replaySplit==='future'?0:5;
  const dates=Object.fromEntries(data.clean.map(r=>[r.week_key,r.From]));
  const byDate=(a,b)=>String(dates[b.week_key]||'').localeCompare(String(dates[a.week_key]||''));
  const records=data.patterns.filter(r=>state.patternYears.includes(Number(r.week_key.slice(0,4)))).sort((a,b)=>state.patternSort==='recent'?byDate(a,b):(Number.isFinite(b.lof_score)?b.lof_score:-Infinity)-(Number.isFinite(a.lof_score)?a.lof_score:-Infinity)||byDate(a,b));
  const queryWeeks=records.map(r=>r.week_key);
  state.patternWeek=queryWeeks.includes(source.patternWeek)?source.patternWeek:queryWeeks.includes(state.patternWeek)?state.patternWeek:queryWeeks[0]||defaults.patternWeek;
  const ks=unique(data.pattern_neighbors.filter(r=>r.query_week_key===state.patternWeek).map(r=>Number(r.lof_k))).sort((a,b)=>a-b);
  state.neighborsK=ks.includes(numeric(source.neighborsK))?numeric(source.neighborsK):ks.includes(defaults.neighborsK)?defaults.neighborsK:ks[0]||defaults.neighborsK;
  if(plain(defaults.research))state.research=normalizeResearch(source.research,defaults.research);
  return state;
}
function read(href,saved,defaults,data,software){
  const url=new URL(href),q=url.searchParams,fragment=new URLSearchParams(url.hash.slice(1)),versioned=q.has('view'),known=[...Object.values(FIELDS),...Object.values(META)],hasParameters=versioned||known.some(k=>q.has(k))||fragment.has('research');
  let input=hasParameters?{}:plain(saved)?{...saved,language:'en'}:{},researchInvalid=false;
  if(hasParameters)for(const [key,param] of Object.entries(FIELDS)){if(key==='research'){const raw=fragment.has('research')?fragment.get('research'):q.get('research');if(raw!==null){if(raw.length>64000)researchInvalid=true;else try{input.research=JSON.parse(raw);if(!plain(input.research))researchInvalid=true}catch(_){researchInvalid=true}}}else if(q.has(param))input[key]=ARRAYS.includes(key)?q.get(param)===''?[]:q.get(param).split(','):q.get(param)}
  const actual=identity(data,software),requested={},issues=researchInvalid?['research']:[];
  if(versioned){
    if(q.get('view')!==VERSION)issues.push('format');
    for(const [key,param] of Object.entries(META)){requested[key]=q.get(param);if(key!=='software'&&requested[key]!==actual[key])issues.push(key)}
    if(!requested.software||!/^[A-Za-z0-9._+-]{1,64}$/.test(requested.software))issues.push('software-format');
  }else if(Object.values(META).some(k=>q.has(k)))issues.push('format');
  return{state:normalize(input,defaults,data),issues,blocked:issues.length>0,softwareChanged:versioned&&Boolean(requested.software)&&requested.software!==actual.software,requested,actual,hasParameters};
}
function encode(href,state,defaults,data,software){
  const url=new URL(href);url.username='';url.password='';url.search='';url.hash='';const q=url.searchParams,normalized=normalize(state,defaults,data);
  q.set('view',VERSION);for(const [key,param] of Object.entries(FIELDS))if(key!=='research')q.set(param,ARRAYS.includes(key)?normalized[key].join(','):String(normalized[key]));
  if(plain(normalized.research)){const fragment=new URLSearchParams();fragment.set('research',JSON.stringify(normalized.research));url.hash=fragment.toString()}
  const meta=identity(data,software);for(const [key,param] of Object.entries(META))q.set(param,meta[key]);
  return url.toString();
}
return{VERSION,FIELDS,META,RESEARCH_DEFAULT,SOURCE_IDS,DATASET_IDS,DATASET_FILTERS,researchDefaults,normalizeResearch,normalize,identity,read,encode};
});

'use strict';
// Deliberate build-time seal of the reviewed frozen data and saved statistics.
// Runtime never regenerates this manifest to accept changed inputs.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),proof=require(path.join(root,'comparison-fingerprint.js'));
const c={window:{ComparisonFingerprint:proof}};vm.createContext(c);
const dataText=fs.readFileSync(path.join(root,'data.js'),'utf8');
const expectedDataSHA256='f64af06f30fab8f370e52faf40ff4067e8c4a1230c5a3efcbe6938f46aaad342';
const actualDataSHA256=crypto.createHash('sha256').update(dataText).digest('hex');
if(actualDataSHA256!==expectedDataSHA256)throw new Error('Unreviewed data.js content; existing comparison manifest was not changed');
vm.runInContext(dataText,c);
const app=fs.readFileSync(path.join(root,'app.js'),'utf8'),line=prefix=>{const value=app.split('\n').find(x=>x.startsWith(prefix));if(!value)throw new Error(prefix);return value;};
const code=['const D=window.WASTEWATER_DATA;',line('const MODEL_KEYS='),line('function numeric('),line('const finiteNumber='),line('const day='),line('const week='),line('const byDate='),line('const PREDICTION_NUMBERS='),line('function predictionRows('),app.slice(app.indexOf('function reviewDiagnostics('),app.indexOf('function periodSummary(')),'globalThis.read={predictionRows,reviewDiagnostics};'].join('\n');
vm.runInContext(code,c);
const manifest={contract:proof.VERSION,source_data_js_sha256:crypto.createHash('sha256').update(dataText).digest('hex'),scopes:{}};
for(const split of ['test','validation'])for(const h of [1,2]){
 const diagnostic=c.read.reviewDiagnostics(split,h),input=c.read.predictionRows(split,h);
 for(const score of ['clipped','raw'])manifest.scopes[proof.key(split,h,score)]=proof.seal(c.window.WASTEWATER_DATA,input,diagnostic.predictions,split,h,score);
}
const text='/* Deterministic seal of the reviewed frozen comparison payloads. */\nwindow.COMPARISON_MANIFEST='+JSON.stringify(manifest,null,2)+';\n';
fs.writeFileSync(path.join(root,'comparison-manifest.js'),text);
console.log(JSON.stringify({scopes:Object.keys(manifest.scopes).length,source_data_js_sha256:manifest.source_data_js_sha256}));

/* Shared source links, readable description and optional technical detail. Callers escape HTML. */
(function(root){'use strict';
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const content=value=>Array.isArray(value)?[...new Set(value.filter(Boolean))].map(item=>`<div class="coverage-item">${item}</div>`).join(''):(value||'');
function render(input={},language){
 const lang=language||input.language||root.WastewaterExplorer?.state?.language||'en',zh=lang==='zh';
 const sources=content(input.source),retrieved=input.retrieved?`<p class="note">${zh?'获取日期：':'Retrieved: '}${esc(input.retrieved)}</p>`:'';
 const description=input.description!==undefined?content(input.description):['coverage','measurements','notes','processing'].map(key=>content(input[key])).filter(Boolean).join('');
 const meta=input.metadata?`<pre>${esc(typeof input.metadata==='string'?input.metadata:JSON.stringify(input.metadata,null,2))}</pre>`:'';
 const technical=content(input.technical)+content(input.version)+meta;
 return `<details class="coverage-sources" data-coverage-sources data-detail-key="data-coverage-sources"><summary>${zh?'数据覆盖与来源':'Data coverage & sources'}</summary><div class="coverage-sections">${sources||retrieved?`<div class="coverage-links">${sources}${retrieved}</div>`:''}${description?`<div class="coverage-description">${description}</div>`:''}${technical?`<details class="coverage-metadata" data-detail-key="coverage-metadata"><summary>${zh?'技术信息':'Technical details'}</summary>${technical}</details>`:''}</div></details>`;
}
root.CoverageSources={render};if(typeof module==='object'&&module.exports)module.exports=root.CoverageSources;
})(typeof window!=='undefined'?window:globalThis);

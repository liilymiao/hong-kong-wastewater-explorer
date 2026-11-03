/* Shared, collapsed provenance panel. Section content is escaped by its caller. */
(function(root){'use strict';
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function render(input={},language){
 const lang=language||input.language||root.WastewaterExplorer?.state?.language||'en',zh=lang==='zh';
 const sections=[['source','Source','来源'],['coverage','Coverage','覆盖范围'],['measurements','Measurements','指标'],['notes','Coverage notes','覆盖说明'],['processing','Processing','处理方法'],['version','Version','版本']];
 const body=sections.map(([key,en,cn])=>{let value=input[key];if(!value||(Array.isArray(value)&&!value.length))return '';if(Array.isArray(value))value=value.map(item=>`<div class="coverage-item">${item}</div>`).join('');return `<section class="coverage-section"><h3>${zh?cn:en}</h3>${value}</section>`}).join('');
 const meta=input.metadata?`<details class="coverage-metadata" data-detail-key="coverage-metadata"><summary>${zh?'完整元数据与校验值':'Full metadata & checksums'}</summary><pre>${esc(typeof input.metadata==='string'?input.metadata:JSON.stringify(input.metadata,null,2))}</pre></details>`:'';
 return `<details class="coverage-sources" data-coverage-sources data-detail-key="data-coverage-sources"><summary>${zh?'数据覆盖与来源':'Data coverage & sources'}</summary><div class="coverage-sections">${body}${meta}</div></details>`;
}
root.CoverageSources={render};if(typeof module==='object'&&module.exports)module.exports=root.CoverageSources;
})(typeof window!=='undefined'?window:globalThis);

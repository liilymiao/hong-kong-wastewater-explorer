/* Small deterministic ZIP STORE writer. UTF-8 filenames; no compression or ZIP64. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.ZipStore=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){'use strict';
const table=new Uint32Array(256);for(let n=0;n<256;n++){let c=n;for(let k=0;k<8;k++)c=c&1?0xedb88320^(c>>>1):c>>>1;table[n]=c>>>0;}
function crc32(bytes){let c=0xffffffff;for(const b of bytes)c=table[(c^b)&255]^(c>>>8);return(c^0xffffffff)>>>0;}
function zipStore(files){
 const encoder=new TextEncoder(),list=Array.isArray(files)?files:Object.entries(files).map(([name,data])=>({name,data})),names=new Set(),entries=[];
 if(list.length>65535)throw new RangeError('ZIP STORE supports at most 65535 entries.');
 let offset=0,centralSize=0;
 for(const entry of list){const name=entry.name,data=entry.data;
  if(typeof name!=='string'||!name||name.includes('\\')||name.includes('\0')||name.startsWith('/')||/^[A-Za-z]:/.test(name)||name.split('/').some(p=>!p||p==='.'||p==='..'))throw new Error('Unsafe ZIP filename.');
  if(names.has(name))throw new Error('Duplicate ZIP filename.');names.add(name);
  const encoded=encoder.encode(name);if(encoded.length>65535)throw new RangeError('ZIP filename is too long.');
  const bytes=typeof data==='string'?encoder.encode(data):data instanceof Uint8Array?new Uint8Array(data):data instanceof ArrayBuffer?new Uint8Array(data):null;
  if(!bytes)throw new TypeError('ZIP content must be text, Uint8Array or ArrayBuffer.');
  if(bytes.length>0xffffffff)throw new RangeError('ZIP64 is not supported.');
  entries.push({name:encoded,bytes,crc:crc32(bytes),offset});offset+=30+encoded.length+bytes.length;centralSize+=46+encoded.length;
  if(offset+centralSize+22>0xffffffff)throw new RangeError('ZIP64 is not supported.');
 }
 const output=new Uint8Array(offset+centralSize+22),view=new DataView(output.buffer);let p=0;
 const u16=(at,n)=>view.setUint16(at,n,true),u32=(at,n)=>view.setUint32(at,n,true);
 for(const e of entries){u32(p,0x04034b50);u16(p+4,20);u16(p+6,0x800);u16(p+8,0);u16(p+10,0);u16(p+12,33);u32(p+14,e.crc);u32(p+18,e.bytes.length);u32(p+22,e.bytes.length);u16(p+26,e.name.length);u16(p+28,0);output.set(e.name,p+30);output.set(e.bytes,p+30+e.name.length);p+=30+e.name.length+e.bytes.length;}
 const centralOffset=p;
 for(const e of entries){u32(p,0x02014b50);u16(p+4,20);u16(p+6,20);u16(p+8,0x800);u16(p+10,0);u16(p+12,0);u16(p+14,33);u32(p+16,e.crc);u32(p+20,e.bytes.length);u32(p+24,e.bytes.length);u16(p+28,e.name.length);u16(p+30,0);u16(p+32,0);u16(p+34,0);u16(p+36,0);u32(p+38,0);u32(p+42,e.offset);output.set(e.name,p+46);p+=46+e.name.length;}
 u32(p,0x06054b50);u16(p+4,0);u16(p+6,0);u16(p+8,entries.length);u16(p+10,entries.length);u32(p+12,p-centralOffset);u32(p+16,centralOffset);u16(p+20,0);return output;
}
return{zipStore,crc32};
});

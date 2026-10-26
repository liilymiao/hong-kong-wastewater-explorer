/* Native text tracks preserve the video timeline when the subtitle changes. */
(()=>{'use strict';
  const video=document.getElementById('proposal-player');
  const control=document.getElementById('subtitle-language');
  const languages=new Set(['en','zh-CN','zh-TW','yue','ja','ko','es','fr','off']);
  let selected='en';
  let applying=false;
  let started=false;
  function setLanguage(code){
    if(!languages.has(code))return false;
    selected=code;
    control.value=code;
    applying=true;
    for(const track of video.textTracks){
      const mode=code!=='off'&&track.language===code?'showing':'disabled';
      if(track.mode!==mode)track.mode=mode;
    }
    applying=false;
    return true;
  }
  control.addEventListener('change',()=>setLanguage(control.value));
  video.addEventListener('loadedmetadata',()=>setLanguage(selected));
  video.addEventListener('loadeddata',()=>{if(!started)setLanguage(selected)});
  video.addEventListener('play',()=>{if(!started)setLanguage(selected);started=true},{once:true});
  video.textTracks.addEventListener('addtrack',()=>setLanguage(selected));
  video.textTracks.addEventListener('change',()=>{
    if(applying)return;
    if(!started){setLanguage(selected);return;}
    const active=[...video.textTracks].find(track=>track.mode==='showing');
    selected=active?.language||'off';
    control.value=selected;
  });
  window.ProposalPlayer={
    setLanguage,
    getState:()=>({language:selected,currentTime:video.currentTime,paused:video.paused,tracks:[...video.textTracks].map(({language,mode})=>({language,mode}))})
  };
  setLanguage('en');
})();

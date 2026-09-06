/* Resolvance - SIH26142 - Fixed UI */
const $=id=>document.getElementById(id);
let statusEl, slider, valEl, progressEl, progressBar, progressText, themeToggle;
let maps={}, mapLayers={}, currentImages={}, currentMeta=null;
let syncEnabled=true;

function initDOM(){
  statusEl=$('status'); slider=$('slider'); valEl=$('slider-val');
  progressEl=$('progress'); progressBar=document.querySelector('.bar'); progressText=document.querySelector('.progress-text');
  themeToggle=$('theme-toggle');
  if(themeToggle) themeToggle.addEventListener('click',()=>applyTheme(document.documentElement.getAttribute('data-theme')==='dark'?'light':'dark'));
  const drop=$('drop');
  if(drop){
    ['dragenter','dragover'].forEach(e=>drop.addEventListener(e,ev=>{ev.preventDefault();drop.classList.add('drag-active');}));
    ['dragleave','drop'].forEach(e=>drop.addEventListener(e,ev=>{ev.preventDefault();drop.classList.remove('drag-active');}));
    drop.addEventListener('drop',ev=>{
      if(ev.dataTransfer.files.length){$('file').files=ev.dataTransfer.files; upload();}
    });
    drop.addEventListener('click',ev=>{
      if(ev.target.closest('#file')||ev.target.closest('button')) return;
      $('file').click();
    });
    drop.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();$('file').click();}});
  }
  const fileInput=$('file');
  if(fileInput) fileInput.addEventListener('change',upload);
  if(slider){
    slider.addEventListener('input',e=>onSlider(e.target.value));
    slider.addEventListener('keydown',e=>{
      let v=parseInt(slider.value); if(e.key==='ArrowLeft')v=Math.max(0,v-5); else if(e.key==='ArrowRight')v=Math.min(100,v+5); else if(e.key==='Home')v=0; else if(e.key==='End')v=100; else return;
      slider.value=v; onSlider(v);
    });
  }
  const handle=$('handle');
  if(handle) handle.addEventListener('keydown',e=>{
    let v=parseInt(slider.value); if(e.key==='ArrowLeft')v=Math.max(0,v-5); else if(e.key==='ArrowRight')v=Math.min(100,v+5); else return;
    slider.value=v; onSlider(v);
  });
  const browse=$('browse-btn');
  if(browse) browse.addEventListener('click',e=>{e.stopPropagation();$('file').click();});
  const full=$('fullscreen-btn');
  if(full) full.addEventListener('click',()=>{
    if(!document.fullscreenElement) document.documentElement.requestFullscreen().catch(()=>{}); else document.exitFullscreen();
  });
  ['layer-input','layer-sr'].forEach(id=>{
    const el=$(id); if(el) el.addEventListener('change',()=>switchMapLayer(id.replace('layer-',''), el.value));
  });
}

const THEME_KEY='resolvance-theme';
function applyTheme(t){
  document.documentElement.setAttribute('data-theme',t);
  try{localStorage.setItem(THEME_KEY,t);}catch(e){}
}
function initTheme(){
  let saved=null; try{saved=localStorage.getItem(THEME_KEY);}catch(e){}
  const dark=window.matchMedia('(prefers-color-scheme: dark)').matches;
  applyTheme(saved || (dark?'dark':'light'));
}
function setStatus(msg,err=false){
  if(!statusEl) return;
  statusEl.textContent=msg;
  statusEl.style.color=err?'#A32B20':'#15803D';
}
function showProgress(show,pct=0){
  if(!progressEl) return;
  progressEl.hidden=!show;
  if(show && progressBar){ progressBar.style.width=pct+'%'; if(progressText) progressText.textContent=Math.round(pct)+'%';}
}
function escapeHTML(s){
  if(typeof s!=='string') return s;
  return s.replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
}
function initMaps(){
  if(!window.L){return;}
  if(maps.input) return;
  const opts={center:[19.1,72.8],zoom:11,zoomControl:true,attributionControl:false,preferCanvas:true};
  const sat=L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:19});
  ['input','sr','heat','diff'].forEach(id=>{
    const m=L.map('map-'+id,{...opts,layers:[sat]});
    maps[id]=m; mapLayers[id]={};
    m.on('move',e=>{
      if(!syncEnabled) return;
      const c=e.target.getCenter(), z=e.target.getZoom();
      Object.keys(maps).forEach(o=>{ if(o!==id) maps[o].setView(c,z,{animate:false,noMoveStart:true});});
    });
  });
}
function getBounds(){
  let aspect=1;
  if(currentMeta && currentMeta.input_size){
    const raw=currentMeta.input_size.replace(/×/g,'x').split('x');
    const w=parseInt(raw[0]), h=parseInt(raw[1]);
    if(h>0) aspect=w/h;
  }
  const dLat=0.4, dLon=dLat*aspect/0.945;
  return [[18.9,72.5],[18.9+dLat,72.5+dLon]];
}
function switchMapLayer(mapId, type){
  if(!maps[mapId] || !currentImages[mapId]) return;
  const m=maps[mapId], layers=mapLayers[mapId];
  Object.values(layers).forEach(l=>{ if(l) try{m.removeLayer(l);}catch(e){}});
  const b=getBounds();
  const img=currentImages[mapId];
  if(!img) return;
  if(type==='rgb') layers.rgb=L.imageOverlay(img,b,{opacity:0.9}).addTo(m);
  else if(type==='nir' && currentImages.heatmap) layers.nir=L.imageOverlay(currentImages.heatmap,b,{opacity:0.7}).addTo(m);
  else if(type==='ndvi' && currentImages.heatmap) layers.ndvi=L.imageOverlay(currentImages.heatmap,b,{opacity:0.7}).addTo(m);
}
function addImageOverlays(imgs){
  currentImages=imgs;
  // Defer Leaflet init until results is visible — otherwise maps have 0 size
  const resSec=$('results');
  const visible = resSec && !resSec.hidden;
  if(!visible){
    // Delay Leaflet until after visible
    setTimeout(()=>addImageOverlays(imgs), 200);
    return;
  }
  if(!maps.input) initMaps();
  const b=getBounds();
  ['input','sr','heat','diff'].forEach(id=>{
    if(!maps[id]) return;
    Object.values(mapLayers[id]).forEach(l=>{ if(l) try{maps[id].removeLayer(l);}catch(e){}});
  });
  try{
    if(imgs.input && maps.input) mapLayers.input.rgb=L.imageOverlay(imgs.input,b,{opacity:0.95}).addTo(maps.input);
    if(imgs.sr && maps.sr) mapLayers.sr.rgb=L.imageOverlay(imgs.sr,b,{opacity:0.95}).addTo(maps.sr);
    if(imgs.heatmap && maps.heat) mapLayers.heat.rgb=L.imageOverlay(imgs.heatmap,b,{opacity:0.95}).addTo(maps.heat);
    if(imgs.sr && maps.diff) mapLayers.diff.rgb=L.imageOverlay(imgs.sr,b,{opacity:0.85}).addTo(maps.diff);
    maps.input.fitBounds(L.latLngBounds(b));
  }catch(e){ console.warn('Leaflet overlay failed', e); }
  setTimeout(()=>Object.values(maps).forEach(m=>{ try{m.invalidateSize();}catch(e){}}),200);
  // Also ensure static previews are set
  ['img-input','img-sr','img-heat'].forEach(id=>{
    const el=$(id);
    if(el && imgs[id.replace('img-','')]) el.src=imgs[id.replace('img-','')];
  });
}

let currentCompare='input-sr';
function updateCompareMode(){
  const el=$('compare-mode');
  if(el) currentCompare=el.value;
  onSlider(slider?slider.value:50);
}
function onSlider(v){
  const p=Number(v);
  if(valEl) valEl.textContent=p+'%';
  const handle=$('handle');
  if(handle){ handle.style.left=p+'%'; handle.setAttribute('aria-valuenow',p); }
  const leftEl=$('c-left'), rightEl=$('c-right');
  if(!leftEl || !rightEl) return;
  // Map compare modes to images
  let leftKey='input', rightKey='sr';
  if(currentCompare==='input-heat'){ leftKey='input'; rightKey='heatmap';}
  else if(currentCompare==='sr-diff'){ leftKey='sr'; rightKey='heatmap';}
  const lImg=currentImages[leftKey], rImg=currentImages[rightKey];
  if(lImg) leftEl.src=lImg;
  if(rImg) rightEl.src=rImg;
  leftEl.style.clipPath=`inset(0 ${100-p}% 0 0)`;
  rightEl.style.clipPath=`inset(0 0 0 ${p}% 0)`;
}

function renderProof(j){
  const m=j.metrics||{}, meta=j.meta||{};
  const crsCard=$('crs-card'), dl=$('downloads'), proof=$('proof');
  const crsOk=meta.crs && meta.crs!=='Unknown' && String(meta.crs).includes('EPSG');
  if(crsCard) crsCard.innerHTML=`<div class="proof ${crsOk?'pass':'fail'}"><b>${escapeHTML(meta.crs)||'Unknown'}</b>CRS ${crsOk?'✓ preserved':'✗ Unknown (PNG)'}<br><small>${escapeHTML(meta.input_size)} → ${escapeHTML(meta.output_size)}</small></div>`;
  if(dl) dl.innerHTML=`<a href="${escapeHTML(j.download)}" download>⬇ PNG</a><a class="secondary" href="${escapeHTML(j.download_tif)||'#'}" download>⬇ COG GeoTIFF</a><a class="secondary" href="${escapeHTML(j.download_heatmap)||'#'}" download>⬇ Heatmap TIF</a><br><small style="color:var(--muted);font-size:11px">Open COG in QGIS → overlay check</small>`;
  if(proof){
    const sam=m.sam_mean_deg, ndvi=m.ndvi_corr, rmse=m.rmse_px;
    const sPass=sam!=null && sam<3, nPass=ndvi!=null && ndvi>0.90, rPass=rmse!=null && rmse<0.3;
    proof.innerHTML=`
      <div class="proof ${sam==null?'':sPass?'pass':'fail'}"><b>${sam!=null?escapeHTML(String(sam)):'-'}°</b>SAM &lt;3° ${sam==null?'':sPass?'✓':'✗'}<br><small>spectral</small></div>
      <div class="proof ${ndvi==null?'':nPass?'pass':'fail'}"><b>${ndvi!=null?escapeHTML(String(ndvi)):'-'}</b>NDVI r &gt;0.90 ${ndvi==null?'':nPass?'✓':'✗'}<br><small>vegetation</small></div>
      <div class="proof ${rmse==null?'':rPass?'pass':'fail'}"><b>${rmse!=null?escapeHTML(String(rmse)):'-'} px</b>RMSE &lt;0.3px ${rmse==null?'':rPass?'✓':'✗'}<br><small>geospatial</small></div>`;
  }
  const leg=$('legend-mini');
  if(leg) leg.innerHTML=`<span style="display:flex;align-items:center;gap:6px"><span style="width:70px;height:6px;background:linear-gradient(90deg,#440154,#3b528b,#21918c,#5ec962,#fde725);border-radius:2px"></span><span style="font-size:10px">Low</span><span style="font-size:10px">High</span></span>`;
}

async function upload(){
  const f=$('file')?$('file').files[0]:null;
  if(!f){ setStatus('Pick a file first',true); return;}
  if(f.size>50*1024*1024){ setStatus('Max 50MB',true); return;}
  const fd=new FormData(); fd.append('file',f);
  setStatus('Uploading & processing - this takes a minute on CPU...');
  showProgress(true,10);
  let pct=10; const iv=setInterval(()=>{ pct+= (90-pct)*0.05; showProgress(true,pct);},1000);
  try{
    const r=await fetch('/api/infer',{method:'POST',body:fd});
    clearInterval(iv); showProgress(true,95);
    const j=await r.json();
    showProgress(false);
    if(!j.success){ setStatus(j.error,true); return;}
    setStatus('Done ✓ — scroll down to see results');
    const resSec=$('results');
    if(resSec){ resSec.hidden=false; resSec.style.display='block'; resSec.removeAttribute('hidden');}
    currentImages=j.images; currentMeta=j.meta;
    // Static previews — guaranteed visible
    const els={ 'img-input':j.images.input, 'img-sr':j.images.sr, 'img-heat':j.images.heatmap };
    Object.entries(els).forEach(([id,src])=>{ const el=$(id); if(el){ el.src=src; el.style.display='block'; }});
    // Leaflet overlays after visible
    setTimeout(()=>addImageOverlays(j.images), 100);
    const metaEl=$('meta'), metricsEl=$('metrics');
    if(metaEl) metaEl.textContent=JSON.stringify(j.meta,null,2);
    if(metricsEl) metricsEl.textContent=JSON.stringify(j.metrics,null,2);
    renderProof(j);
    onSlider(slider?slider.value:50);
    if(resSec) window.scrollTo({top:resSec.offsetTop-80,behavior:'smooth'});
  }catch(e){
    clearInterval(iv); showProgress(false); setStatus('Failed: '+e.message,true);
  }
}

// Init
document.addEventListener('DOMContentLoaded',()=>{
  initDOM();
  initTheme();
  // Defer map init until results shown — avoids 0-size init when hidden
  // initMaps(); // lazy
  onSlider(50);
  // particles
  const canvas=$('particles');
  if(canvas){
    const ctx=canvas.getContext('2d');
    function resize(){ canvas.width=canvas.clientWidth; canvas.height=canvas.clientHeight; }
    window.addEventListener('resize',resize); resize();
    const pts=Array.from({length:50},()=>({x:Math.random()*canvas.width,y:Math.random()*canvas.height,vx:(Math.random()-.5)*.35,vy:(Math.random()-.5)*.35}));
    (function frame(){
      const w=canvas.width, h=canvas.height;
      ctx.clearRect(0,0,w,h);
      pts.forEach(p=>{ p.x+=p.vx; p.y+=p.vy; if(p.x<0||p.x>w) p.vx*=-1; if(p.y<0||p.y>h) p.vy*=-1;});
      ctx.strokeStyle='rgba(0,255,136,.22)';
      pts.forEach((a,i)=> pts.slice(i+1).forEach(b=>{
        const d=Math.hypot(a.x-b.x,a.y-b.y);
        if(d<120){ ctx.globalAlpha=1-d/120; ctx.beginPath(); ctx.moveTo(a.x,a.y); ctx.lineTo(b.x,b.y); ctx.stroke();}
      }));
      pts.forEach(p=>{ ctx.globalAlpha=1; ctx.fillStyle='#00ff88'; ctx.beginPath(); ctx.arc(p.x,p.y,1.4,0,Math.PI*2); ctx.fill();});
      requestAnimationFrame(frame);
    })();
  }
  // expose for inline onchange
  window.updateCompareMode=updateCompareMode;
  window.upload=upload;
});

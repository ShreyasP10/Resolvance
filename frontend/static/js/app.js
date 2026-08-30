const $=id=>document.getElementById(id);
const statusEl=$('status'), slider=$('slider'), valEl=$('slider-val');

const escapeHTML = (str) => {
  if (typeof str !== 'string') return str;
  return str.replace(/[&<>'"]/g, 
    tag => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    }[tag])
  );
};

function setStatus(msg, err=false){
  statusEl.textContent=msg;
  statusEl.style.color=err?'#A32B20':'#15803D';
}

function renderProof(j){
  const m=j.metrics||{}, meta=j.meta||{};
  // CRS card
  const crsOk = meta.crs && meta.crs!=='Unknown' && meta.crs.includes('EPSG');
  $('crs-card').innerHTML = `<div class="proof ${crsOk?'pass':'fail'}"><b>${escapeHTML(meta.crs)||'Unknown'}</b>CRS ${crsOk?'✓ preserved':'✗ Unknown (PNG)'}<br><small>${escapeHTML(meta.input_size)} → ${escapeHTML(meta.output_size)}</small></div>`;
  // Downloads
  $('downloads').innerHTML = `<a href="${escapeHTML(j.download)}">⬇ PNG</a> <a href="${escapeHTML(j.download_tif)||'#'}">⬇ COG GeoTIFF</a> <a href="${escapeHTML(j.download_heatmap)||'#'}">⬇ Heatmap TIF</a><br><small>Open COG in QGIS → overlay check</small>`;
  // Metrics proof grid
  const sam = m.sam_mean_deg, ndvi = m.ndvi_corr, rmse = m.rmse_px;
  const samPass = sam!=null && sam < 3;
  const ndviPass = ndvi!=null && ndvi > 0.98;
  const rmsePass = rmse!=null && rmse < 0.3;
  $('proof').innerHTML = `
    <div class="proof ${sam==null?'':samPass?'pass':'fail'}"><b>${escapeHTML(sam)??'—'}°</b>SAM &lt;3° ${sam==null?'':samPass?'✓':'✗'}<br><small>spectral</small></div>
    <div class="proof ${ndvi==null?'':ndviPass?'pass':'fail'}"><b>${escapeHTML(ndvi)??'—'}</b>NDVI r &gt;0.98 ${ndvi==null?'':ndviPass?'✓':'✗'}<br><small>vegetation</small></div>
    <div class="proof ${rmse==null?'':rmsePass?'pass':'fail'}"><b>${escapeHTML(rmse)??'—'} px</b>RMSE &lt;0.3px ${rmse==null?'':rmsePass?'✓':'✗'}<br><small>geospatial</small></div>
  `;
}

let currentImages = {};

function updateLayers() {
  if (!currentImages.sr) return;
  const rightSel = $('right-layer').value;
  $('c-right').src = rightSel === 'heat' ? currentImages.heatmap : currentImages.sr;
}

async function upload(){
  const f=$('file').files[0];
  if(!f){ setStatus('Pick a file first',true); return; }
  if(f.size>50*1024*1024){ setStatus('Max 50MB',true); return; }
  const fd=new FormData(); fd.append('file',f);
  setStatus('Processing…');
  try{
    const r=await fetch('/api/infer',{method:'POST',body:fd});
    let j;
    try {
      j = await r.json();
    } catch (e) {
      setStatus(`Server error: ${r.status} ${r.statusText}`, true);
      return;
    }
    if(!j.success){ setStatus(j.error,true); return; }
    setStatus('Done');
    $('results').style.display='block';
    
    currentImages = j.images;
    $('img-input').src=j.images.input; $('c-input').src=j.images.input;
    $('img-sr').src=j.images.sr; 
    $('img-heat').src=j.images.heatmap;
    updateLayers();
    
    $('meta').textContent=JSON.stringify(j.meta,null,2);
    $('metrics').textContent=JSON.stringify(j.metrics,null,2);
    renderProof(j);
    onSlider(slider.value);
    window.scrollTo({top: $('results').offsetTop, behavior:'smooth'});
  }catch(e){ setStatus('Failed: '+e,true); }
}

function onSlider(v){
  const p=Number(v);
  valEl.textContent=p+'%';
  $('c-input').style.clipPath=`inset(0 ${100-p}% 0 0)`;
  $('handle').style.left=p+'%';
}
slider.addEventListener('input', e=> onSlider(e.target.value));

const drop=$('drop');
drop.addEventListener('dragover', e=>{e.preventDefault(); drop.style.background='#eef4ff'});
drop.addEventListener('dragleave', ()=> drop.style.background='');
drop.addEventListener('drop', e=>{
  e.preventDefault(); drop.style.background='';
  if(e.dataTransfer.files.length){ $('file').files=e.dataTransfer.files; upload(); }
});

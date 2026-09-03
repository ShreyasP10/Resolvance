/* Resolvance Frontend - SIH26142 Sentinel-SRM */
const $ = id => document.getElementById(id);
const statusEl = $('status'), slider = $('slider'), valEl = $('slider-val');
const progressEl = $('progress'), progressBar = document.querySelector('.bar'), progressText = document.querySelector('.progress-text');
const themeToggle = $('#theme-toggle');
const fullscreenBtn = $('#fullscreen-btn');

// --- Theme ---
const THEME_KEY = 'resolvance-theme';
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem(THEME_KEY, theme);
  themeToggle.textContent = theme === 'dark' ? '☀️' : '🌙';
}
function initTheme() {
  const saved = localStorage.getItem(THEME_KEY);
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  applyTheme(saved || (prefersDark ? 'dark' : 'light'));
}
themeToggle?.addEventListener('click', () => applyTheme(document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark'));

// --- Status ---
function setStatus(msg, err = false) {
  statusEl.textContent = msg;
  statusEl.style.color = err ? '#A32B20' : '#15803D';
  statusEl.className = 'status ' + (err ? 'error' : 'success');
}
function showProgress(show, percent = 0) {
  progressEl.hidden = !show;
  if (show) {
    progressBar.style.width = percent + '%';
    document.querySelector('.progress-text').textContent = Math.round(percent) + '%';
  }
}

// --- XSS Protection ---
function escapeHTML(str) {
  if (typeof str !== 'string') return str;
  return str.replace(/[&<>'"]/g, tag => ({
    '&': '&', '<': '<', '>': '>', "'": ''', '"': '"'
  }[tag]));
}

// --- Leaflet Maps ---
let maps = { input: null, sr: null, heat: null, diff: null };
let mapLayers = { input: {}, sr: {}, heat: {} };
let currentImages = {};
let syncEnabled = true;

function initMaps() {
  if (!window.L) { console.warn('Leaflet not loaded'); return; }
  const mapOptions = {
    center: [19.1, 72.8], // Mumbai
    zoom: 12,
    zoomControl: true,
    attributionControl: false,
    preferCanvas: true
  };

  // Base layers
  const osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '' });
  const satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19, attribution: '' });

  // Create maps
  const mapIds = ['input', 'sr', 'heat', 'diff'];
  mapIds.forEach(id => {
    const map = L.map(`map-${id}`, { ...mapOptions, layers: [satellite], zoomControl: true });
    maps[id] = map;
    mapLayers[id] = { rgb: null, nir: null, ndvi: null };
  });

  // Sync pan/zoom
  mapIds.forEach(id => {
    maps[id].on('move', e => {
      if (!syncEnabled) return;
      const center = e.target.getCenter();
      const zoom = e.target.getZoom();
      mapIds.forEach(otherId => {
        if (otherId !== id) {
          maps[otherId].setView(center, zoom, { animate: false, noMoveStart: true });
        }
      });
    });
  });

  // Layer selectors
  ['input', 'sr'].forEach(id => {
    const sel = $(`layer-${id}`);
    sel?.addEventListener('change', () => switchMapLayer(id, sel.value));
  });
}

function switchMapLayer(mapId, layerType) {
  if (!maps[mapId] || !currentImages[mapId]) return;
  const map = maps[mapId];
  const layers = mapLayers[mapId];
  
  // Remove existing layer
  if (layers.rgb) map.removeLayer(layers.rgb);
  if (layers.nir) map.removeLayer(layers.nir);
  if (layers.ndvi) map.removeLayer(layers.ndvi);

  // Add new layer from current image data
  // For now, use the current image as overlay
  const img = currentImages[mapId];
  if (!img) return;

  const bounds = getImageBounds();
  if (layerType === 'rgb') {
    layers.rgb = L.imageOverlay(img, bounds, { opacity: 0.9 }).addTo(map);
  } else if (layerType === 'nir' && currentImages.heat) {
    layers.nir = L.imageOverlay(currentImages.heat, bounds, { opacity: 0.7 }).addTo(map);
  } else if (layerType === 'ndvi') {
    layers.ndvi = L.imageOverlay(currentImages.heat, bounds, { opacity: 0.7 }).addTo(map);
  }
}

function getImageBounds() {
  // Mumbai area approximate bounds
  return [[18.9, 72.5], [19.3, 73.1]];
}

function addImageOverlays(images) {
  if (!maps.input) initMaps();
  currentImages = images;

  // Clear existing overlays
  ['input', 'sr', 'heat', 'diff'].forEach(id => {
    if (maps[id]) {
      ['rgb', 'nir', 'ndvi'].forEach(l => {
        if (mapLayers[id][l]) maps[id].removeLayer(mapLayers[id][l]);
      });
    });

  // Add new overlays
  if (images.input) {
    mapLayers.input.rgb = L.imageOverlay(images.input, getImageBounds(), { opacity: 0.9 }).addTo(maps.input);
    mapLayers.input.nir = L.imageOverlay(images.heat, getImageBounds(), { opacity: 0.7 }).addTo(maps.input);
  }
  if (images.sr) {
    mapLayers.sr.rgb = L.imageOverlay(images.sr, getImageBounds(), { opacity: 0.9 }).addTo(maps.sr);
    mapLayers.sr.nir = L.imageOverlay(images.heat, getImageBounds(), { opacity: 0.7 }).addTo(maps.sr);
  }
  if (images.heat) {
    mapLayers.heat.rgb = L.imageOverlay(images.heat, getImageBounds(), { opacity: 0.9 }).addTo(maps.heat);
  }

  // Fit bounds
  maps.input.fitBounds(L.latLngBounds(getImageBounds()));
  setTimeout(() => mapIds.forEach(id => maps[id]?.invalidateSize()), 100);
}

// --- Comparison Slider ---
let currentCompareMode = 'input-sr';
let sliderDragging = false;

function updateCompareMode() {
  currentCompareMode = $('compare-mode').value;
  onSlider(slider.value);
}

function onSlider(v) {
  const p = Number(v);
  valEl.textContent = p + '%';
  
  const left = currentCompareMode.startsWith('input') ? 'input' : 
               currentCompareMode.startsWith('sr') ? 'sr' : 'heat';
  const right = currentCompareMode.includes('sr') ? 'sr' : 
                currentCompareMode.includes('heat') ? 'heat' : 'diff';
  
  const leftImg = currentImages[left];
  const rightImg = currentImages[right] || currentImages.sr;
  
  if (leftImg) {
    $('c-left').src = leftImg;
    $('c-left').style.clipPath = `inset(0 ${100-p}% 0 0)`;
  }
  if (rightImg) {
    $('c-right').src = rightImg;
    $('c-right').style.clipPath = `inset(0 0 0 ${p}% 0)`;
  }
  $('handle').style.left = p + '%';
  $('c-left').style.clipPath = `inset(0 ${100-p}% 0 0)`;
  $('c-right').style.clipPath = `inset(0 0 0 ${p}% 0)`;
  $('handle').style.left = p + '%';
}

slider.addEventListener('input', e => onSlider(e.target.value));
slider.addEventListener('mousedown', () => sliderDragging = true);
slider.addEventListener('mouseup', () => sliderDragging = false);
document.addEventListener('mouseup', () => sliderDragging = false);

// Keyboard support for slider
slider.addEventListener('keydown', e => {
  let val = parseInt(slider.value);
  if (e.key === 'ArrowLeft') val = Math.max(0, val - 5);
  else if (e.key === 'ArrowRight') val = Math.min(100, val + 5);
  else if (e.key === 'Home') val = 0;
  else if (e.key === 'End') val = 100;
  else return;
  slider.value = val;
  onSlider(val);
});

// Handle focus for accessibility
document.getElementById('handle').addEventListener('keydown', e => {
  const slider = document.getElementById('slider');
  let val = parseInt(slider.value);
  if (e.key === 'ArrowLeft') val = Math.max(0, val - 5);
  else if (e.key === 'ArrowRight') val = Math.min(100, val + 5);
  else return;
  slider.value = val;
  onSlider(val);
});

// --- Render Proof ---
function renderProof(j) {
  const m = j.metrics || {}, meta = j.meta || {};
  
  // CRS Card
  const crsOk = meta.crs && meta.crs !== 'Unknown' && meta.crs.includes('EPSG');
  $('crs-card').innerHTML = `<div class="proof ${crsOk ? 'pass' : 'fail'}"><b>${escapeHTML(meta.crs) || 'Unknown'}</b>CRS ${crsOk ? '✓ preserved' : '✗ Unknown (PNG)'}<br><small>${escapeHTML(meta.input_size)} → ${escapeHTML(meta.output_size)}</small></div>`;
  
  // Downloads
  $('downloads').innerHTML = `
    <a href="${escapeHTML(j.download)}">⬇ PNG</a>
    <a class="secondary" href="${escapeHTML(j.download_tif) || '#'}">⬇ COG GeoTIFF</a>
    <a class="secondary" href="${escapeHTML(j.download_heatmap) || '#'}">⬇ Heatmap TIF</a>
    <br><small>Open COG in QGIS → overlay check</small>
  `;
  
  // Proof Grid
  const sam = m.sam_mean_deg, ndvi = m.ndvi_corr, rmse = m.rmse_px;
  const samPass = sam != null && sam < 3;
  const ndviPass = ndvi != null && ndvi > 0.98;
  const rmsePass = rmse != null && rmse < 0.3;
  $('proof').innerHTML = `
    <div class="proof ${sam == null ? '' : samPass ? 'pass' : 'fail'}"><b>${escapeHTML(sam) ?? '—'}°</b>SAM <3° ${sam == null ? '' : samPass ? '✓' : '✗'}<br><small>spectral</small></div>
    <div class="proof ${ndvi == null ? '' : ndviPass ? 'pass' : 'fail'}"><b>${escapeHTML(ndvi) ?? '—'}</b>NDVI r >0.98 ${ndvi == null ? '' : ndviPass ? '✓' : '✗'}<br><small>vegetation</small></div>
    <div class="proof ${rmse == null ? '' : rmsePass ? 'pass' : 'fail'}"><b>${escapeHTML(rmse) ?? '—'} px</b>RMSE <0.3px ${rmse == null ? '' : rmsePass ? '✓' : '✗'}<br><small>geospatial</small></div>
  `;
  
  // Legend
  const legend = $('legend-mini');
  if (legend) {
    legend.innerHTML = `
      <span style="display:flex;align-items:center;gap:6px;">
        <span style="width:80px;height:8px;background:linear-gradient(90deg,#440154,#3b528b,#21918c,#5ec962,#fde725);border-radius:2px;"></span>
        <span style="font-size:10px;color:#fff;">Low</span>
        <span style="font-size:10px;color:#fff;">High</span>
      </span>
    `;
  }
}

// --- Upload ---
async function upload() {
  const f = $('file').files[0];
  if (!f) { setStatus('Pick a file first', true); return; }
  if (f.size > 50 * 1024 * 1024) { setStatus('Max 50MB', true); return; }
  
  const fd = new FormData();
  fd.append('file', f);
  setStatus('Uploading & Processing AI (This takes a minute on CPU)...');
  showProgress(true, 10);
  
  // Fake progress ticking for CPU processing so user knows it hasn't hung
  let aiPct = 10;
  const aiInterval = setInterval(() => {
    aiPct += (90 - aiPct) * 0.05;
    showProgress(true, aiPct);
  }, 1000);

  try {
    const response = await fetch('/api/infer', { method: 'POST', body: fd });
    clearInterval(aiInterval);
    showProgress(true, 95);
    const j = await response.json();
    showProgress(false);
    
    if (!j.success) { setStatus(j.error, true); return; }
    
    setStatus('Done');
    $('results').hidden = false;
    currentImages = j.images;
    
    // Update static images
    $('img-input').src = j.images.input;
    $('img-sr').src = j.images.sr;
    $('img-heat').src = j.images.heatmap;
    
    // Initialize maps and add overlays
    addImageOverlays(j.images);
    
    // Update compare images
    updateLayers();
    
    // Meta & metrics
    $('meta').textContent = JSON.stringify(j.meta, null, 2);
    $('metrics').textContent = JSON.stringify(j.metrics, null, 2);
    renderProof(j);
    onSlider(slider.value);
    
    window.scrollTo({ top: $('results').offsetTop - 80, behavior: 'smooth' });
  } catch (e) {
    showProgress(false);
    setStatus('Failed: ' + e.message, true);
  }
}

function updateLayers() {
  if (!currentImages.sr) return;
  const rightSel = $('right-layer').value;
  $('c-right').src = rightSel === 'heat' ? currentImages.heatmap : currentImages.sr;
}

// --- Drag & Drop ---
const drop = $('drop');
['dragenter', 'dragover'].forEach(evt => drop.addEventListener(evt, e => { e.preventDefault(); drop.classList.add('drag-active'); }));
['dragleave', 'drop'].forEach(evt => drop.addEventListener(evt, e => { e.preventDefault(); drop.classList.remove('drag-active'); }));
drop.addEventListener('drop', e => {
  if (e.dataTransfer.files.length) { $('file').files = e.dataTransfer.files; upload(); }
});

drop.addEventListener('click', e => { if (e.target === drop || e.target.classList.contains('drop-content') || e.target.classList.contains('drop-icon') || e.target.classList.contains('drop-text')) $('file').click(); });

// Trigger the upload when the user selects a file from the file picker
$('file').addEventListener('change', upload);

// Fullscreen
fullscreenBtn?.addEventListener('click', () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen().catch(() => {});
    fullscreenBtn.textContent = '⛶';
  } else {
    document.exitFullscreen();
    fullscreenBtn.textContent = '⛶';
  }
});

// Particles
(function() {
  const canvas = document.getElementById('particles');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  function resize() { canvas.width = canvas.clientWidth; canvas.height = canvas.clientHeight; }
  window.addEventListener('resize', resize); resize();
  const pts = Array.from({ length: 60 }, () => ({ x: Math.random() * canvas.width, y: Math.random() * canvas.height, vx: (Math.random() - .5) * .4, vy: (Math.random() - .5) * .4 }));
  function frame() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    pts.forEach(p => { p.x += p.vx; p.y += p.vy; if (p.x < 0 || p.x > canvas.width) p.vx *= -1; if (p.y < 0 || p.y > canvas.height) p.vy *= -1; });
    ctx.strokeStyle = 'rgba(0,255,136,.25)'; 
    pts.forEach((a, i) => pts.slice(i + 1).forEach(b => {
      const d = Math.hypot(a.x - b.x, a.y - b.y);
      if (d < 120) { ctx.globalAlpha = 1 - d / 120; ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke(); }
    }));
    pts.forEach(p => { ctx.globalAlpha = 1; ctx.fillStyle = '#00ff88'; ctx.beginPath(); ctx.arc(p.x, p.y, 1.5, 0, Math.PI * 2); ctx.fill(); });
    requestAnimationFrame(frame);
  } frame();
})();

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initMaps();
  updateLayers();
  
  // Auto-focus file input on page load
  setTimeout(() => $('file')?.focus(), 500);
});
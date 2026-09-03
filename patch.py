import re

with open('frontend/static/js/app.js', 'r', encoding='utf-8') as f:
    code = f.read()

target_listener = "$('file').addEventListener('change', upload);"
if target_listener not in code:
    code = code.replace("drop.addEventListener('click', e => { if (e.target === drop || e.target.classList.contains('drop-content') || e.target.classList.contains('drop-icon') || e.target.classList.contains('drop-text')) $('file').click(); });", "drop.addEventListener('click', e => { if (e.target === drop || e.target.classList.contains('drop-content') || e.target.classList.contains('drop-icon') || e.target.classList.contains('drop-text')) $('file').click(); });\n  " + target_listener)

code = re.sub(r"const fd = new FormData\(\);.*?const j = await response.json\(\);\s*showProgress\(false\);", 
    """const fd = new FormData();
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
    showProgress(false);""", code, flags=re.DOTALL)

with open('frontend/static/js/app.js', 'w', encoding='utf-8') as f:
    f.write(code)

print('Patched successfully!')

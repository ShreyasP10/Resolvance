import re

with open('frontend/static/css/style.css', 'r', encoding='utf-8') as f:
    css = f.read()

# Fix #particles
css = re.sub(r'#particles\s*\{[^}]*\}', '#particles{position:fixed;inset:0;opacity:.32;z-index:-2;pointer-events:none}', css)

# Fix .hero-gradient
css = re.sub(r'\.hero-gradient\s*\{[^}]*\}', '.hero-gradient{position:fixed;inset:0;z-index:-1;pointer-events:none;background:radial-gradient(800px 400px at 30% 10%,rgba(14,165,104,.15),transparent 60%),radial-gradient(600px 300px at 85% 20%,rgba(96,165,255,.12),transparent 60%)}', css)

# Fix .hero background and text color to adapt to theme
css = re.sub(r'\.hero\s*\{([^}]*)\}', lambda m: '.hero{' + m.group(1).replace('background:linear-gradient(135deg,#0b1220 0%,#0f2040 40%,#14365f 100%);', 'background:var(--card-hero);').replace('color:#fff;', 'color:var(--ink);') + '}', css)

# Add --card-hero variable
if '--card-hero:' not in css:
    css = css.replace(':root{', ':root{--card-hero:linear-gradient(135deg,rgba(255,255,255,0.7) 0%,rgba(240,245,255,0.5) 100%);', 1)
    css = css.replace('[data-theme="dark"] {', '[data-theme="dark"] {\n  --card-hero: linear-gradient(135deg, rgba(11,18,32,0.8) 0%, rgba(15,32,64,0.6) 100%);')

# Also .hero-badge and .kpi-card text color should adapt
css = css.replace('border:1px solid rgba(255,255,255,.18);', 'border:1px solid var(--line);')
css = css.replace('background:rgba(255,255,255,.1);', 'background:var(--cream2);')
css = css.replace('.kpi-card{min-width:108px;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.12);', '.kpi-card{min-width:108px;background:var(--card);border:1px solid var(--line);')

with open('frontend/static/css/style.css', 'w', encoding='utf-8') as f:
    f.write(css)

print('Updated CSS for hero integration!')

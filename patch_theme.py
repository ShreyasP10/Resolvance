import re

with open('frontend/static/css/style.css', 'r', encoding='utf-8') as f:
    css = f.read()

dark_css = """
/* Dark Theme Additions */
[data-theme="dark"] {
  --hdr: #e2e8f0;
  --hdr2: #00ff88;
  --green: #00ff88;
  --green2: #0fd276;
  --red: #f43f5e;
  --cream: #1e293b;
  --cream2: #0f172a;
  --grey: #1e293b;
  --ink: #e2e8f0;
  --muted: #94a3b8;
  --line: #334155;
  --card: #1e293b;
  --shadow: 0 10px 30px rgba(0,0,0,0.4);
  --shadow-lg: 0 20px 50px rgba(0,0,0,0.6);
}
[data-theme="dark"] body {
  background: radial-gradient(1200px 600px at 20% -10%, #0b1220 0%, transparent 60%),
              radial-gradient(900px 500px at 90% 0%, #0f2040 0%, transparent 55%),
              #020617;
}
[data-theme="dark"] .hdr { background: rgba(15, 23, 42, 0.85); border-color: rgba(255,255,255,0.06); }
[data-theme="dark"] .card { background: rgba(30, 41, 59, 0.8); border-color: rgba(255,255,255,0.08); }
[data-theme="dark"] .card.glass { background: linear-gradient(180deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.9)); }
[data-theme="dark"] .node { background: #0f172a; border-color: #334155; }
[data-theme="dark"] .node.accent { background: linear-gradient(180deg, #0f172a, #134e4a); border-color: #0f766e; }
[data-theme="dark"] .drop { background: linear-gradient(180deg, #0f172a, #1e293b); border-color: #334155; }
[data-theme="dark"] .drop:hover { border-color: var(--green); background: linear-gradient(180deg, #134e4a, #0f172a); }
[data-theme="dark"] .drop-icon-wrap { background: #1e293b; border-color: #334155; }
[data-theme="dark"] #theme-toggle { background: #1e293b; border-color: #334155; color: #fff; }
[data-theme="dark"] .btn.primary { background: var(--green); color: #000; box-shadow: 0 0 12px rgba(0,255,136,0.3); }
[data-theme="dark"] .btn.primary:hover { filter: brightness(1.1); }
[data-theme="dark"] .hdr-gh { background: #1e293b; color: #fff; border-color: #334155; }
[data-theme="dark"] .hdr nav a { color: #e2e8f0; }
[data-theme="dark"] select, [data-theme="dark"] input { background: #0f172a; color: #e2e8f0; border-color: #334155; }
"""

if '/* Dark Theme Additions */' not in css:
    css += '\n' + dark_css
    with open('frontend/static/css/style.css', 'w', encoding='utf-8') as f:
        f.write(css)

with open('frontend/static/js/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

# The JS file has an incorrect textContent setter that replaces the inner <span>s
# Let's completely remove it. It's usually like: themeToggle.textContent = theme === 'dark' ? '...' : '...';
js = re.sub(r"themeToggle\.textContent\s*=.*?;", "", js)

with open('frontend/static/js/app.js', 'w', encoding='utf-8') as f:
    f.write(js)

print('Updated Dark Theme CSS and fixed JS toggle!')

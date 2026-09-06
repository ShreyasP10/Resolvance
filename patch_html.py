import re

with open('frontend/templates/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace exactly
html = html.replace('<canvas id="particles" aria-hidden="true"></canvas>', '')
html = html.replace('<div class="hero-gradient"></div>', '')

body_idx = html.find('<body>')
if body_idx != -1:
    insert_pos = body_idx + len('<body>')
    html = html[:insert_pos] + '\n<canvas id="particles" aria-hidden="true"></canvas>\n<div class="hero-gradient"></div>' + html[insert_pos:]

with open('frontend/templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Moved particles and gradient to body!')

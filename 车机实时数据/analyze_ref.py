# -*- coding: utf-8 -*-
"""把参考件开幕那一段彻底拆开：粒子、抖动、时值。"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

REF = os.path.join(os.environ['TEMP'], 'cx-boot', 'ref2')
css = io.open(os.path.join(REF, 'lib', 'splash.css'), encoding='utf-8', errors='replace').read()
js = io.open(os.path.join(REF, 'lib', 'splash.js'), encoding='utf-8', errors='replace').read()

print(u'=== 1. 开幕选择器的完整规则 ===')
seen = set()
for m in re.finditer(r'([^{}]{0,120})\{([^{}]*)\}', css):
    sel = ' '.join(m.group(1).split())
    body = ' '.join(m.group(2).split())
    if re.search(r'(black|whale|noise|grain|dust|star|mote|ember|speck|bokeh|jitter|shake|trem|vibra|glitch|flash|wash|sweep)', sel, re.I):
        k = (sel, body)
        if k in seen:
            continue
        seen.add(k)
        print(u'  %-44s { %s }' % (sel[-44:], body[:150]))
print(u'  共 %d 条' % len(seen))

print(u'\n=== 2. 所有 @keyframes 的完整内容（找抖动/粒子） ===')
for m in re.finditer(r'@keyframes\s+([\w-]+)\s*\{(.*?)\n\}', css, re.S):
    name = m.group(1)
    body = ' '.join(m.group(2).split())
    print(u'  @%s  %s' % (name, body[:230]))

print(u'\n=== 3. 粒子常见做法：多偏移 box-shadow / 重复 radial-gradient ===')
for m in re.finditer(r'([^{}]{0,80})\{([^{}]*box-shadow\s*:[^{};]{60,})\}', css):
    sel = ' '.join(m.group(1).split())
    print(u'  box-shadow 多偏移 %-30s %s…' % (sel[-30:], ' '.join(m.group(2).split())[:120]))
n_rg = len(re.findall(r'radial-gradient', css))
print(u'  radial-gradient 出现 %d 次' % n_rg)
for m in re.finditer(r'([^{}]{0,80})\{([^{}]*radial-gradient[^{};]*)\}', css):
    sel = ' '.join(m.group(1).split())
    print(u'    %-38s %s' % (sel[-38:], ' '.join(m.group(2).split())[:110]))

print(u'\n=== 4. JS 里开幕相关的关键词计数 ===')
for k in ('black', 'whale', 'noise', 'dust', 'star', 'particle', 'shak', 'jitter',
          'trembl', 'requestAnimationFrame', 'setInterval', 'setTimeout', 'createElement',
          'innerHTML', 'boxShadow', 'style.'):
    n = len(re.findall(k, js, re.I))
    if n:
        print(u'  %-22s %d' % (k, n))

print(u'\n=== 5. JS 里的时值常量 ===')
vals = {}
for m in re.finditer(r'([A-Za-z_$][\w$]*)\s*[:=]\s*(\d{2,5})\b', js):
    v = int(m.group(2))
    if 60 <= v <= 8000:
        vals.setdefault(m.group(1), set()).add(v)
for k in sorted(vals):
    print(u'  %-26s %s' % (k, sorted(vals[k])[:8]))

print(u'\n=== 6. JS 里出现的「幕」名（找编排顺序） ===')
for m in sorted(set(re.findall(r"['\"]([a-z][a-z0-9-]{2,20})['\"]", js))):
    if re.search(r'(black|wash|paper|boot|auth|ident|read|verify|welcome|reveal|final|scene|stage|phase|act)', m):
        print(u'  %s' % m)

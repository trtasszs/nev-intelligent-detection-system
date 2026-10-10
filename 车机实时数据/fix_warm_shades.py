# -*- coding: utf-8 -*-
"""把 yellow/amber/orange 的暗档（200/800/900，当底纹用的）改为中性墨色，
   300-700 保留语义橙（警告文字/图表/进度条仍需要它）。"""
import io
import re
import shutil
import time

P = r'E:\！！！高职比赛\新能源汽车智能检测系统-1.0版.html'
shutil.copy2(P, P + '.bak-warm-' + time.strftime('%Y%m%d-%H%M%S'))
t = io.open(P, encoding='utf-8').read()
n0 = len(t)

NEUTRAL = [('200', '#16161A'), ('800', '#1A1A1E'), ('900', '#121215')]
done = 0
for fam in ('yellow', 'amber', 'orange'):
    m = re.search(fam + r':\s*\{[^}]*\}', t)
    if not m:
        print(u'  未找到 %s 色族' % fam)
        continue
    line = m.group()
    new = line
    for lvl, val in NEUTRAL:
        new = re.sub(r"(\b" + lvl + r":\s*')[^']*(')", lambda mm, v=val: mm.group(1) + v + mm.group(2), new)
    if new != line:
        t = t[:m.start()] + new + t[m.end():]
        done += 1
        print(u'  %-8s -> %s' % (fam, new[:130]))

print(u'\n改动色族: %d 个' % done)
d = n0 - len(t)
print(u'字符变化: %d' % d)
if abs(d) < n0 * 0.02 and 'cx-can-js' in t and '</html>' in t and 'page-content' in t:
    io.open(P, 'w', encoding='utf-8').write(t)
    print(u'已写盘（%d 字符）' % len(t))
else:
    print(u'未写盘（校验未通过）')

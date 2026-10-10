# -*- coding: utf-8 -*-
"""
调色板 v7 —— 金色退出「结构层」，只保留在「点缀层」
------------------------------------------------------------------
问题：金色被当成结构色用（发丝线 / 侧栏选中 / 卡片左边框），铺满即是廉价。
原则：结构用中性（石墨灰），金色只出现在真正需要"贵"的地方：
      主按钮、进度条、关键数字、图表主线。
      结构一旦中性，剩下那点金才显贵。

    python palette_nogold.py
"""
import io
import os
import re

SITE = r'E:\！！！高职比赛'
HERE = os.path.dirname(os.path.abspath(__file__))
_CAND = [u'新能源汽车智能检测系统-1.0版.html',
         u'新能源汽车智能检测系统-美化，实测改进版.html',
         u'新能源汽车智能检测系统.html']

# 中性石墨（结构色）
SLATE = u'158, 168, 182'

FILES = [os.path.join(SITE, u'检测系统-美化', 'theme.css'),
         os.path.join(HERE, 'live.css'),
         os.path.join(HERE, 'can_live.js'),
         os.path.join(HERE, 'boot550.js')]


def find_html():
    for c in _CAND:
        p = os.path.join(SITE, c)
        if os.path.isfile(p):
            return p
    import glob
    hits = [p for p in glob.glob(os.path.join(SITE, '*.html'))
            if u'智能检测系统' in os.path.basename(p) and u'原版' not in os.path.basename(p)]
    return max(hits, key=os.path.getmtime) if hits else os.path.join(SITE, _CAND[0])


P = find_html()
FILES.append(P)
print(u'目标: %s\n' % P)

# ---- 1. 侧栏选中：金色 → 中性白
SIDE = [
    (u'@apply bg-dark-200 border-l-2 border-primary;',
     u'@apply bg-dark-200 border-l-2 border-white/80;'),
    (u'.sidebar-active {',
     u'.sidebar-active span, .sidebar-active i { color: #E8E8EC !important; }\n'
     u'.sidebar-active {'),
]

# ---- 2. 卡片左边框：金 → 石墨
CARD = [
    (u'border-left: 2px solid #D4AF37;', u'border-left: 2px solid rgba(158, 168, 182, .5);'),
    (u'border-left-color: #D4AF37;', u'border-left-color: rgba(158, 168, 182, .5);'),
    (u'linear-gradient(to right, #D4AF37, #C2453F', u'linear-gradient(to right, rgba(158,168,182,.55), rgba(194,69,63,.55)'),
]

# ---- 3. 发丝线 / 边框 / 辉光：金 → 石墨（这是"去金"的大头）
HAIR = [
    (u'rgba(212, 175, 55,', u'rgba(158, 168, 182,'),
    (u'rgba(212,175,55,', u'rgba(158,168,182,'),
    (u'rgba(255, 176, 32,', u'rgba(158, 168, 182,'),
    (u'rgba(255,176,32,', u'rgba(158,168,182,'),
]

# ---- 4. 变量归位
VAR = [
    (u'--cx-gr: #D4AF37;', u'--cx-gr: #2EE59D;'),
    (u'--cx-cy-l: #2EE59D;', u'--cx-cy-l: #E8E8EC;'),
    (u'--cx-cy-d: #6E5A20;', u'--cx-cy-d: #565E6A;'),
]

for p in FILES:
    if not os.path.isfile(p):
        continue
    t = io.open(p, encoding='utf-8').read()
    orig = t
    counts = []
    for table in (SIDE, CARD, HAIR, VAR):
        n = 0
        for a, b in table:
            c = t.count(a)
            if c:
                t = t.replace(a, b)
                n += c
        counts.append(n)
    if t != orig:
        io.open(p, 'w', encoding='utf-8').write(t)
    print(u'  %-26s 侧栏 %d · 卡片边 %d · 发丝线 %d · 变量 %d'
          % (os.path.basename(p), counts[0], counts[1], counts[2], counts[3]))

# ---- 5. 页面里直接写在标签上的金色边框（Tailwind 类）
t = io.open(P, encoding='utf-8').read()
n = 0
for a, b in ((u'bg-primary text-white border border-primary rounded',
              u'bg-primary text-white border border-transparent rounded'),):
    c = t.count(a)
    if c:
        t = t.replace(a, b)
        n += c
io.open(P, 'w', encoding='utf-8').write(t)
print(u'\n  按钮上的金色描边去除: %d 处' % n)
print(u'  金 #D4AF37 剩余: %d 处（只应在按钮/进度条/图表/关键数字）'
      % len(re.findall(r'#D4AF37', t)))

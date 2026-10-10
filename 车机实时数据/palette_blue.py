# -*- coding: utf-8 -*-
"""
调色板 v9 —— 金色退场，科技蓝上位
------------------------------------------------------------------
用户三点：
  ① 实体填充色块（导出报告等）→ 蓝色，增科技感
  ② 曲线折线不要屎黄
  ③ 底色屎黄很丑
做法：把金色系整体替换为科技蓝；暖色提示框 / 暗金底调一并中性化；
      黄/琥珀色族单独重置为暖橙（保留"警告"语义），避免被一起刷成蓝。

  科技蓝  主 #3D9BFF  亮 #8CC6FF  暗 #2E7BC4  深底 #1E5C99 / #14304A

    python palette_blue.py
"""
import io
import os
import re
import shutil
import time

SITE = r'E:\！！！高职比赛'
HERE = os.path.dirname(os.path.abspath(__file__))
_CAND = [u'新能源汽车智能检测系统-1.0版.html',
         u'新能源汽车智能检测系统-美化，实测改进版.html',
         u'新能源汽车智能检测系统.html']


def find_html():
    for c in _CAND:
        p = os.path.join(SITE, c)
        if os.path.isfile(p):
            return p
    import glob
    hits = [p for p in glob.glob(os.path.join(SITE, '*.html'))
            if u'智能检测系统' in os.path.basename(p) and u'原版' not in os.path.basename(p)]
    return max(hits, key=os.path.getmtime) if hits else os.path.join(SITE, _CAND[0])


# 金 → 蓝（先长后短，避免子串误伤）
TABLE = [
    # 金族 → 科技蓝
    (u'#D4AF37', u'#3D9BFF'), (u'#d4af37', u'#3D9BFF'),
    (u'#E8D08A', u'#8CC6FF'),                       # 若仍是浅金
    (u'#A8862E', u'#2E7BC4'), (u'#B08D2E', u'#2E7BC4'),
    (u'#8A7028', u'#25618F'), (u'#8A6A24', u'#25618F'),
    (u'#6E5A20', u'#1C4666'), (u'#7A6424', u'#1C4666'),
    (u'#5C4A18', u'#183A54'), (u'#4A3C14', u'#14304A'),
    (u'#2A2410', u'#11243A'), (u'#24200E', u'#0E1E30'),
    # 暖色提示框 / 暖灰 → 中性
    (u'#F0EBE2', u'#E8E8EC'), (u'#695E47', u'#26262C'),
    (u'rgb(122,106,92)', u'rgb(140,145,155)'),
    (u'rgb(122, 106, 92)', u'rgb(140, 145, 155)'),
    (u'rgb(54,43,20)', u'rgb(18,36,58)'), (u'rgb(54, 43, 20)', u'rgb(18, 36, 58)'),
    # 万一还有金色发丝线
    (u'rgba(212, 175, 55,', u'rgba(61, 155, 255,'), (u'rgba(212,175,55,', u'rgba(61,155,255,'),
    # 变量
    (u'--cx-cy: #3D9BFF;', u'--cx-cy: #3D9BFF;'),
    (u'--cx-cy-d: #565E6A;', u'--cx-cy-d: #1E5C99;'),
]

# 黄 / 琥珀 / 橙 色族 → 暖橙（保住"警告"语义，不被刷成蓝）
WARM = {
    u'yellow': u"yellow: { 200:'#3A2A14', 300:'#B87A28', 400:'#E09030', 500:'#C87A20', 600:'#A86218', 700:'#8A4E12', 800:'#6E3E10', 900:'#2E2010' },",
    u'amber': u"amber: { 200:'#3A2A14', 400:'#E09030', 500:'#C87A20', 600:'#A86218', 800:'#6E3E10', 900:'#2E2010' },",
    u'orange': u"orange: { 200:'#3A2418', 400:'#D4762A', 500:'#B86020', 600:'#9A4E1A', 800:'#6E3612', 900:'#2E1A10' },",
}


def find_html_safe():
    return find_html()


P = find_html_safe()
bak = P + '.bak-blue-' + time.strftime('%Y%m%d-%H%M%S')
shutil.copy2(P, bak)
print(u'已备份 -> %s\n' % os.path.basename(bak))

FILES = [(os.path.join(SITE, u'检测系统-美化', 'theme.css'), u'theme.css'),
         (os.path.join(HERE, 'live.css'), u'live.css'),
         (os.path.join(HERE, 'can_live.js'), u'can_live.js'),
         (os.path.join(HERE, 'boot550.js'), u'boot550.js'),
         (P, u'页面')]

for path, label in FILES:
    if not os.path.isfile(path):
        continue
    t = io.open(path, encoding='utf-8').read()
    orig = t
    n = 0
    for a, b in TABLE:
        if a == b:
            continue
        c = t.count(a)
        if c:
            t = t.replace(a, b)
            n += c
    if t != orig:
        io.open(path, 'w', encoding='utf-8').write(t)
    print(u'  %-14s 金→蓝 %d 处' % (label, n))

# boot550.js 的常量
b = os.path.join(HERE, 'boot550.js')
if os.path.isfile(b):
    t = io.open(b, encoding='utf-8').read()
    t = t.replace(u"var AM = '#D4AF37', OR = '#A8862E'", u"var AM = '#3D9BFF', OR = '#2E7BC4'")
    io.open(b, 'w', encoding='utf-8').write(t)
    print(u'  boot550.js     常量 → 科技蓝')

# 尾表：暖色族重置
t = io.open(P, encoding='utf-8').read()
for fam, line in WARM.items():
    pat = re.compile(r'\n\s*' + fam + r':\s*\{[^}]*\},')
    if pat.search(t):
        t = pat.sub(u'\n                        ' + line, t, count=1)
print(u'  暖色族（yellow/amber/orange）→ 暖橙，保住警告语义')
io.open(P, 'w', encoding='utf-8').write(t)

t = io.open(P, encoding='utf-8').read()
print(u'\n页面剩余金 #D4AF37: %d 处' % t.count(u'#D4AF37'))
print(u'页面科技蓝 #3D9BFF: %d 处' % t.count(u'#3D9BFF'))

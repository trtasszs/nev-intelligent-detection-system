# -*- coding: utf-8 -*-
"""
v10 —— ① 开机动画还原（不改动画）
       ② 趋势图曲线下方填充：屎黄 → 蓝 / 红
       ③ 清掉剩余暗暖色
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


P = find_html()
bak = P + '.bak-v10-' + time.strftime('%Y%m%d-%H%M%S')
shutil.copy2(P, bak)
print(u'已备份 -> %s\n' % os.path.basename(bak))

# ============ ① 开机动画还原 ============
B = os.path.join(HERE, 'boot550.js')
t = io.open(B, encoding='utf-8').read()
n1 = t.count(u'#3D9BFF') + t.count(u'#2E7BC4')
t = t.replace(u'#3D9BFF', u'#D4AF37').replace(u'#2E7BC4', u'#A8862E')
io.open(B, 'w', encoding='utf-8').write(t)
m = re.search(r"var AM[^\n]*", t)
print(u'① 开机动画还原：%d 处金→蓝回退' % n1)
print(u'   当前常量: %s' % (m.group() if m else u'?'))
print(u'   仍有 #3D9BFF: %d 处（应为 0）\n' % t.count(u'#3D9BFF'))

# ============ ② 趋势图填充 + ③ 暗暖色 ============
TABLE = [
    # 曲线下方填充：屎黄 → 对应线条色
    (u"rgb(246, 184, 59, 0.1)", u"rgb(61, 155, 255, 0.13)"),
    (u"rgb(246,184,59,0.1)", u"rgb(61,155,255,0.13)"),
    (u"rgb(246, 195, 92, 0.1)", u"rgb(194, 69, 63, 0.11)"),
    (u"rgb(246,195,92,0.1)", u"rgb(194,69,63,0.11)"),
    (u"rgb(246, 184, 59,", u"rgb(61, 155, 255,"),
    (u"rgb(246,184,59,", u"rgb(61,155,255,"),
    (u"rgb(246, 195, 92,", u"rgb(194, 69, 63,"),
    (u"rgb(246,195,92,", u"rgb(194,69,63,"),
    # 剩余暗暖色 → 墨 / 冷色
    (u'#3B311E', u'#1A2430'),
    (u'#2A210F', u'#14243A'),
    (u'#3A2A14', u'#2A2014'),
    (u'#2E2010', u'#20160E'),
    (u'#3A2418', u'#2A1A14'),
]

for path, label in ((os.path.join(SITE, u'检测系统-美化', 'theme.css'), u'theme.css'),
                    (os.path.join(HERE, 'live.css'), u'live.css'),
                    (os.path.join(HERE, 'can_live.js'), u'can_live.js'),
                    (P, u'页面')):
    if not os.path.isfile(path):
        continue
    s = io.open(path, encoding='utf-8').read()
    o = s
    n = 0
    for a, b in TABLE:
        c = s.count(a)
        if c:
            s = s.replace(a, b)
            n += c
    if s != o:
        io.open(path, 'w', encoding='utf-8').write(s)
    print(u'  %-14s 填充/暖色修正 %d 处' % (label, n))

s = io.open(P, encoding='utf-8').read()
print(u'\n页面剩余 屎黄填充 rgb(246,: %d 处' % s.count(u'rgb(246,'))
print(u'页面剩余 #3D9BFF: %d 处' % s.count(u'#3D9BFF'))
print(u'页面剩余 #D4AF37: %d 处' % s.count(u'#D4AF37'))
print(u'\n完成（开机动画已还原，未改动其设计）')

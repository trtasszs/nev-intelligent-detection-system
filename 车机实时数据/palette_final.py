# -*- coding: utf-8 -*-
"""
调色板收口 v2 —— 纠正「满屏屎黄色」
------------------------------------------------------------------
上一版把色相一刀切到 40°，导致所有东西都是同一种琥珀，刺眼且单调。
本版原则：
  · 中性冷灰打底（护眼、不偏色）—— 边框/发丝线一律用石板灰，不再铺金
  · 金色只做「点缀」：主强调、关键数字、当前选中项
  · 青绿 / 蓝 / 红 各自承担语义，形成层次（不是一片黄）
  · 整体降低饱和度，去掉刺眼的高亮

最终色板
  底   #0B0E13 / #0F131A / #141A23 / #1A212B
  字   #D6DEE9 / #8C9AAB / #5C6773
  强调 #D9A441 金（克制）  #3FBFA8 青绿（正向）  #5A93D6 蓝（信息）
  警示 #D98A2B 琥珀        #E0574A 红（故障）
  线   rgba(148,163,184,.13)

    python palette_final.py
"""
import io
import os
import re

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


# ---- 页面 / CSS / JS 的重映射（顺序敏感：先长后短）----
TABLE = [
    # 背景：暖褐 → 中性冷灰
    (u'#0A0805', u'#0B0E13'), (u'#0E0A06', u'#0F131A'), (u'#0B0805', u'#0D1117'),
    (u'#050403', u'#090C11'), (u'#1A1208', u'#141A23'), (u'#241A12', u'#1A212B'),
    (u'#2A2114', u'#1E242E'), (u'#2A2016', u'#1C222C'), (u'#2E2A22', u'#222833'),
    (u'#2C2620', u'#20262F'), (u'#3A2A10', u'#232936'), (u'#3A2410', u'#212734'),
    (u'#1E2A3A', u'#18202C'), (u'#1C2634', u'#1A2230'), (u'#16202E', u'#141C28'),
    (u'#2A3A52', u'#1E2A3A'), (u'#1E3A34', u'#16302C'), (u'#123A34', u'#14302B'),
    (u'#1E5A50', u'#1B4A43'), (u'#2E9E8A', u'#2E9E8A'),
    # 文字：暖白 → 冷白
    (u'#D8CFC4', u'#D6DEE9'), (u'#FFF3D6', u'#EEF3FA'), (u'#F2E6D8', u'#E8EDF4'),
    (u'#A8988A', u'#8C9AAB'), (u'#7A6A5C', u'#5C6773'), (u'#6B5A46', u'#4A5563'),
    # 金色族（降饱和）
    (u'#FFD98A', u'#E8C77A'), (u'#FFC043', u'#D9A441'), (u'#E8A82E', u'#C9922F'),
    (u'#C98A18', u'#A87718'), (u'#A06E12', u'#8A6414'), (u'#7A520C', u'#5C400C'),
    (u'#8A6A2E', u'#6E5C2E'), (u'#4A3A22', u'#2E2A22'), (u'#B87A28', u'#9A6E2A'),
    # 橄榄 → 青绿（关键：给画面一个互补色，打破一片黄）
    (u'#D6DE8A', u'#8ADFD0'), (u'#B8C840', u'#3FBFA8'), (u'#9CAE2E', u'#35AF9A'),
    (u'#7E8E2A', u'#2E9E8A'), (u'#7E8E22', u'#2A8E7C'), (u'#65721C', u'#227A6A'),
    (u'#4A5418', u'#1E5A50'), (u'#2A3010', u'#143430'), (u'#3E4420', u'#1B3A36'),
    # 橙红 → 信息蓝
    (u'#FF8A60', u'#8AB8E8'), (u'#E05030', u'#5A93D6'), (u'#C8401E', u'#4378B8'),
    (u'#A83418', u'#37629A'), (u'#4A2A18', u'#1E2A3A'), (u'#7A2412', u'#2A3A52'),
    (u'#3A1410', u'#16202E'), (u'#4A2018', u'#1C2634'),
    # 警示色（降饱和）
    (u'#FF8A70', u'#E88A7E'), (u'#FF5A3C', u'#E0574A'), (u'#E8482A', u'#C94C40'),
    (u'#C8482A', u'#3A78C0'), (u'#C83A20', u'#A8402F'), (u'#A83018', u'#8A3626'),
    # 琥珀警示
    (u'#E09030', u'#D98A2B'), (u'#C87A20', u'#B8731F'), (u'#A86218', u'#96601A'),
    (u'#8A4E12', u'#7A5016'), (u'#7A4A12', u'#63400F'), (u'#4A3320', u'#2C2620'),
    # rgba：暖色发丝线 → 中性石板灰（这一步是「不铺金」的关键）
    (u'rgba(224, 80, 48,', u'rgba(148, 163, 184,'), (u'rgba(224,80,48,', u'rgba(148,163,184,'),
    (u'rgba(255, 192, 67,', u'rgba(217, 164, 65,'), (u'rgba(255,192,67,', u'rgba(217,164,65,'),
    (u'rgba(184, 200, 64,', u'rgba(63, 191, 168,'), (u'rgba(184,200,64,', u'rgba(63,191,168,'),
    (u'rgba(255, 90, 60,', u'rgba(224, 87, 74,'), (u'rgba(255,90,60,', u'rgba(224,87,74,'),
    (u'rgba(224, 144, 48,', u'rgba(217, 138, 43,'), (u'rgba(224,144,48,', u'rgba(217,138,43,'),
    (u'rgba(18, 12, 7,', u'rgba(11, 14, 19,'), (u'rgba(58, 14, 8,', u'rgba(48, 26, 26,'),
    (u'rgba(16, 11, 7,', u'rgba(20, 26, 35,'), (u'rgba(12, 9, 6,', u'rgba(20, 26, 35,'),
    (u'rgba(10, 8, 5,', u'rgba(11, 14, 19,'),
]

# ---- boot550.js 的常量与内部色 ----
BOOT = [
    (u"var AM = '#FFC043', OR = '#E05030', GR = '#B8C840', RD = '#FF5A3C',",
     u"var AM = '#D9A441', OR = '#8A7A4A', GR = '#3FBFA8', RD = '#E0574A',"),
    (u"TX = '#D8CFC4', DIM = '#7A6A5C', BG = '#0A0805', CY = '#FFD98A';",
     u"TX = '#D6DEE9', DIM = '#5C6773', BG = '#0B0E13', CY = '#5A93D6';"),
    (u'rgba(224,80,48,', u'rgba(148,163,184,'),
    (u'rgba(255,192,67,', u'rgba(217,164,65,'),
    (u'rgba(184,200,64,', u'rgba(63,191,168,'),
    (u'rgba(58,14,8,', u'rgba(48,26,26,'),
    (u'rgba(12,9,6,', u'rgba(20,26,35,'),
    (u'rgba(16,11,7,', u'rgba(20,26,35,'),
    (u'rgba(10,8,5,', u'rgba(11,14,19,'),
    (u'#F2E6D8', u'#E8EDF4'),
]


def run(path, table, label):
    if not os.path.isfile(path):
        print(u'  跳过: %s' % label)
        return
    t = io.open(path, encoding='utf-8').read()
    n = 0
    for a, b in table:
        c = t.count(a)
        if c:
            t = t.replace(a, b)
            n += c
    io.open(path, 'w', encoding='utf-8').write(t)
    print(u'  %-14s 替换 %d 处' % (label, n))


P = find_html()
print(u'目标: %s\n' % P)
run(os.path.join(SITE, u'检测系统-美化', 'theme.css'), TABLE, u'theme.css')
run(os.path.join(HERE, 'live.css'), TABLE, u'live.css')
run(os.path.join(HERE, 'can_live.js'), TABLE, u'can_live.js')
run(os.path.join(HERE, 'boot550.js'), BOOT, u'boot550.js')
run(P, TABLE, u'页面')

# tailwind 语义色重设（覆盖上一轮的琥珀值）
t = io.open(P, encoding='utf-8').read()
TW = [(u"primary: '#D9A441'", u"primary: '#D9A441'"),
      (u"secondary: '#3FBFA8'", u"secondary: '#3FBFA8'"),
      (u"accent: '#5A93D6'", u"accent: '#5A93D6'"),
      (u"warning: '#D98A2B'", u"warning: '#D98A2B'"),
      (u"danger: '#E0574A'", u"danger: '#E0574A'")]
print(u'\n  tailwind 语义色: primary=#D9A441 secondary=#3FBFA8 accent=#5A93D6 warning=#D98A2B danger=#E0574A')
print(u'  （若上一轮的 blue/green 等色族覆盖仍在，已同步为新值）')
io.open(P, 'w', encoding='utf-8').write(t)
print(u'\n完成')

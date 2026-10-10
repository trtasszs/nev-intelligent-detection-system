# -*- coding: utf-8 -*-
"""
调色板 v4 —— 黑金红为主
------------------------------------------------------------------
  黑  #0A0A0C / #0E0E11 / #131317 / #18181D   中性纯黑，绝不偏暖（避免再变"屎黄"）
  金  #D4AF37（主）  #E8D08A（浅·正向）  #A8862E（暗）  #6E5A20 / #4A3C14（金底）
  红  #D93A3A（主·故障）  #E87A6A（浅）  #C2453F（深·次要强调）  #3A1414（红底）
  琥珀 #D4762A  仅用于"警告"这一档，与金、红区分
  字  #E8E8EC / #9A9AA5 / #5A5A66
  线  金 rgba(212,175,55,.xx) —— 黑金 HUD 的招牌，但只在 1px 线上，不做面

    python palette_bgr.py
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


TABLE = [
    # ---------- 底：冷灰 → 中性纯黑 ----------
    (u'#0B0E13', u'#0A0A0C'), (u'#0F131A', u'#0E0E11'), (u'#141A23', u'#131317'),
    (u'#1A212B', u'#18181D'), (u'#090C11', u'#08080A'), (u'#0D1117', u'#0C0C0F'),
    (u'#1E242E', u'#1C1C22'), (u'#1C222C', u'#1A1A20'), (u'#222833', u'#1E1E24'),
    (u'#20262F', u'#1D1D23'), (u'#232936', u'#1F1F26'), (u'#212734', u'#1E1E25'),
    (u'#18202C', u'#16161B'), (u'#1A2230', u'#18181E'), (u'#141C28', u'#131318'),
    (u'#1B1B21', u'#1B1B21'), (u'#2E2A22', u'#24242C'), (u'#2C2620', u'#2A2018'),
    # ---------- 字：冷白 → 中性白 ----------
    (u'#D6DEE9', u'#E8E8EC'), (u'#EEF3FA', u'#F2F2F5'), (u'#EDEDF0', u'#EDEDF0'),
    (u'#E8EDF4', u'#EDEDF0'), (u'#8C9AAB', u'#9A9AA5'), (u'#5C6773', u'#5A5A66'),
    (u'#4A5563', u'#45454F'),
    # ---------- 金 ----------
    (u'#E8D08A', u'#E8D08A'), (u'#E8C77A', u'#E8D08A'), (u'#D9A441', u'#D4AF37'),
    (u'#C9922F', u'#B08D2E'), (u'#A87718', u'#8A7028'), (u'#8A6414', u'#6E5A20'),
    (u'#5C400C', u'#4A3C14'), (u'#6E5C2E', u'#5C4A18'), (u'#9A6E2A', u'#8A6A24'),
    (u'#A8862E', u'#A8862E'),
    # ---------- 青绿 → 金（黑金红里"正向"由金承担）----------
    (u'#8ADFD0', u'#E8D08A'), (u'#3FBFA8', u'#D4AF37'), (u'#35AF9A', u'#B08D2E'),
    (u'#2E9E8A', u'#8A7028'), (u'#2A8E7C', u'#7A6424'), (u'#227A6A', u'#6E5A20'),
    (u'#1E5A50', u'#6E5A20'), (u'#143430', u'#24200E'), (u'#1B3A36', u'#2A2410'),
    # ---------- 蓝 → 深红（次强调）----------
    (u'#8AB8E8', u'#E87A6A'), (u'#5A93D6', u'#C2453F'), (u'#4378B8', u'#A82A2A'),
    (u'#37629A', u'#8A2424'), (u'#3A78C0', u'#C2453F'), (u'#2A3A52', u'#2A1A1A'),
    (u'#1E2A3A', u'#1E1414'), (u'#1C2634', u'#1C1414'), (u'#16202E', u'#140F0F'),
    # ---------- 红 ----------
    (u'#E88A7E', u'#E87A6A'), (u'#E0574A', u'#D93A3A'), (u'#C94C40', u'#B83030'),
    (u'#A8402F', u'#962A2A'), (u'#8A3626', u'#7A2424'),
    # ---------- 琥珀（仅"警告"档）----------
    (u'#D98A2B', u'#D4762A'), (u'#B8731F', u'#A86024'), (u'#96601A', u'#8A5A20'),
    (u'#7A5016', u'#6E4A1A'), (u'#63400F', u'#5A3C16'), (u'#2C2620', u'#2A2018'),
    # ---------- rgba：金发丝线 + 红/琥珀 ----------
    (u'rgba(148, 163, 184,', u'rgba(212, 175, 55,'), (u'rgba(148,163,184,', u'rgba(212,175,55,'),
    (u'rgba(217, 164, 65,', u'rgba(212, 175, 55,'), (u'rgba(217,164,65,', u'rgba(212,175,55,'),
    (u'rgba(63, 191, 168,', u'rgba(232, 208, 138,'), (u'rgba(63,191,168,', u'rgba(232,208,138,'),
    (u'rgba(224, 87, 74,', u'rgba(217, 58, 58,'), (u'rgba(224,87,74,', u'rgba(217,58,58,'),
    (u'rgba(217, 138, 43,', u'rgba(212, 118, 42,'), (u'rgba(217,138,43,', u'rgba(212,118,42,'),
    (u'rgba(11, 14, 19,', u'rgba(10, 10, 12,'), (u'rgba(48, 26, 26,', u'rgba(58, 20, 20,'),
    (u'rgba(20, 26, 35,', u'rgba(19, 19, 23,'),
    # 兜底：万一还残留暖褐
    (u'#0A0805', u'#0A0A0C'), (u'#1A1208', u'#131317'),
]

BOOT = [
    (u"var AM = '#D9A441', OR = '#8A7A4A', GR = '#3FBFA8', RD = '#E0574A',",
     u"var AM = '#D4AF37', OR = '#A8862E', GR = '#E8D08A', RD = '#D93A3A',"),
    (u"TX = '#D6DEE9', DIM = '#5C6773', BG = '#0B0E13', CY = '#5A93D6';",
     u"TX = '#E8E8EC', DIM = '#5A5A66', BG = '#0A0A0C', CY = '#E87A6A';"),
    (u'rgba(148,163,184,', u'rgba(212,175,55,'),
    (u'rgba(217,164,65,', u'rgba(212,175,55,'),
    (u'rgba(63,191,168,', u'rgba(232,208,138,'),
    (u'rgba(224,87,74,', u'rgba(217,58,58,'),
    (u'rgba(58,26,26,', u'rgba(58,20,20,'),
    (u'rgba(48,26,26,', u'rgba(58,20,20,'),
    (u'rgba(20,26,35,', u'rgba(19,19,23,'),
    (u'rgba(11,14,19,', u'rgba(10,10,12,'),
]


def run(path, table, label):
    if not os.path.isfile(path):
        print(u'  跳过: %s' % label)
        return
    t = io.open(path, encoding='utf-8').read()
    n = 0
    for a, b in table:
        c = t.count(a)
        if c and a != b:
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

# Tailwind 语义色
t = io.open(P, encoding='utf-8').read()
tw = [(u"primary: '#D9A441'", u"primary: '#D4AF37'"),
      (u"secondary: '#3FBFA8'", u"secondary: '#E8D08A'"),
      (u"accent: '#5A93D6'", u"accent: '#C2453F'"),
      (u"warning: '#D98A2B'", u"warning: '#D4762A'"),
      (u"danger: '#E0574A'", u"danger: '#D93A3A'")]
n = 0
for a, b in tw:
    if t.count(a):
        t = t.replace(a, b)
        n += 1
io.open(P, 'w', encoding='utf-8').write(t)
print(u'\n  tailwind 语义色更新 %d 项 → primary 金 / secondary 浅金 / accent 深红 / warning 琥珀 / danger 红' % n)
print(u'完成')

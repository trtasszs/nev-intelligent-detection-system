# -*- coding: utf-8 -*-
"""
调色板 v6 —— 底调改为「墨色」
------------------------------------------------------------------
把中性灰黑整体压深、去掉冷灰感，做成墨色底（近中性、微冷、有纵深），
让金 / 安全绿 / 警示红 浮在墨底上，对比更干净。

  墨   #050506 → #070709 → #09090B → #0A0A0C → #0F0F12 → #141418 → #18181C …

    python palette_ink.py
"""
import io
import os

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


# 顺序敏感：从最深开始，避免链式替换
TABLE = [
    (u'#08080A', u'#050506'),
    (u'#0A0A0C', u'#070709'),
    (u'#0C0C0F', u'#09090B'),
    (u'#0D0D10', u'#0A0A0C'),
    (u'#0E0E11', u'#0A0A0C'),
    (u'#0F0F12', u'#0B0B0E'),
    (u'#101013', u'#0C0C0F'),
    (u'#111115', u'#0D0D10'),
    (u'#131316', u'#0F0F12'),
    (u'#131317', u'#0F0F12'),
    (u'#141418', u'#101013'),
    (u'#15151A', u'#111114'),
    (u'#16161A', u'#121215'),
    (u'#18181C', u'#131316'),
    (u'#18181D', u'#131316'),
    (u'#18181E', u'#131317'),
    (u'#1A1A1E', u'#141417'),
    (u'#1A1A1F', u'#141418'),
    (u'#1A1A20', u'#151518'),
    (u'#1B1B20', u'#16161A'),
    (u'#1B1B21', u'#16161A'),
    (u'#1C1C22', u'#17171B'),
    (u'#1D1D23', u'#18181C'),
    (u'#1E1E24', u'#19191D'),
    (u'#1E1E25', u'#19191E'),
    (u'#1F1F24', u'#1A1A1E'),
    (u'#1F1F26', u'#1A1A1F'),
    (u'#24242C', u'#1D1D22'),
    # rgba 底纹同步压深
    (u'rgba(10, 10, 12,', u'rgba(7, 7, 9,'),
    (u'rgba(19, 19, 23,', u'rgba(16, 16, 19,'),
]

BOOT = [(u"BG = '#0A0A0C'", u"BG = '#070709'")]


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
run(os.path.join(HERE, 'boot550.js'), TABLE + BOOT, u'boot550.js')
run(P, TABLE, u'页面')

# tailwind dark 色阶（若仍是旧值则同步）
t = io.open(P, encoding='utf-8').read()
for a, b in ((u"100: '#", u"100: '#"),):
    pass
print(u'\n完成（墨色底：最深 #050506 · 主底 #070709 · 面板 #0F0F12 · 浮起 #131316）')

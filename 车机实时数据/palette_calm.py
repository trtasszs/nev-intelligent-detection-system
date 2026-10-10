# -*- coding: utf-8 -*-
"""
调色板收口 v3 —— 去暖底调 + 收敛辉光（「醒目不张扬，看的舒服」）
------------------------------------------------------------------
问题：金色以极低透明度大面积铺在卡片/面板上，虽然每个都不是"黄色"，
      叠加起来仍让整页泛暖黄底调。
做法：① 低透明度(<0.10)的金色底纹 → 中性石板灰（保留金的只有边框与高光）
      ② 收敛过强的 box-shadow 辉光
      ③ 清掉零散的漏网暖色

    python palette_calm.py
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


# 漏网暖色
STRAY = [
    (u'rgb(255, 176, 32)', u'rgb(217, 138, 43)'), (u'rgb(255,176,32)', u'rgb(217,138,43)'),
    (u'rgb(246, 184, 59)', u'rgb(217, 164, 65)'), (u'rgb(246,184,59)', u'rgb(217,164,65)'),
    (u'rgb(255, 226, 168)', u'rgb(232, 199, 122)'), (u'rgb(255,226,168)', u'rgb(232,199,122)'),
    (u'#FF9A80', u'#E88A7E'), (u'#D89A1D', u'#D9A441'),
    (u'#96690E', u'#8A6414'), (u'#8A6218', u'#8A6414'),
    (u'#FFC043', u'#D9A441'),
]

# 低透明度金色底纹 → 中性石板灰（这是"去暖底调"的关键）
def calm_gold(text):
    n = 0

    def rep(m):
        nonlocal n
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        a = float(m.group(4))
        # 金色系（R>G>B 且偏黄）且透明度低 → 换成中性灰
        if r > 180 and g > 130 and b < 110 and a <= 0.10:
            n += 1
            return 'rgba(148, 163, 184, %.3f)' % a
        return m.group(0)

    return re.sub(r'rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([0-9.]+)\s*\)', rep, text), n


# 辉光收敛：把过大的扩散半径与过高的辉光透明度压下来
def calm_glow(text):
    n = 0
    before = text
    # box-shadow 里 alpha >= .55 的辉光降到 .34
    def rep(m):
        nonlocal n
        a = float(m.group(2))
        if a > 0.55:
            n += 1
            return '%s, %.2f)' % (m.group(1), 0.34)
        return m.group(0)
    text = re.sub(r'(rgba\([^)]*?),\s*(0\.[5-9][0-9]?|1)\)', rep, text)
    return text, (n if text != before else 0)


def run(path, label):
    if not os.path.isfile(path):
        print(u'  跳过: %s' % label)
        return
    t = io.open(path, encoding='utf-8').read()
    orig = t
    n1 = 0
    for a, b in STRAY:
        c = t.count(a)
        if c:
            t = t.replace(a, b)
            n1 += c
    t, n2 = calm_gold(t)
    t, n3 = calm_glow(t)
    if t != orig:
        io.open(path, 'w', encoding='utf-8').write(t)
    print(u'  %-14s 漏网色 %d · 暖底纹→中性 %d · 辉光收敛 %d' % (label, n1, n2, n3))


P = find_html()
print(u'目标: %s\n' % P)
run(os.path.join(SITE, u'检测系统-美化', 'theme.css'), u'theme.css')
run(os.path.join(HERE, 'live.css'), u'live.css')
run(os.path.join(HERE, 'can_live.js'), u'can_live.js')
run(os.path.join(HERE, 'boot550.js'), u'boot550.js')
run(P, u'页面')
print(u'\n完成')

# -*- coding: utf-8 -*-
"""
调色板统一 第三轮（收口）：按色相把残留的蓝/青/紫色系统性地转到琥珀系。
蓝/青(色相 170~260) → 40°（琥珀）
紫/品红(色相 260~330) → 18°（橙红）
保持饱和度与明度不变，只转色相 —— 不会误伤已经调好的琥珀色（40°）与灰阶（S≈0）。

    python palette3.py
"""
import colorsys
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


HEXRE = re.compile(r'#([0-9A-Fa-f]{6})\b')
RGBARE = re.compile(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(,\s*[0-9.]+\s*)?\)')


def rot(r, g, b):
    """把蓝/青/紫的色相转到琥珀/橙红；其它不动。返回 (r,g,b) 或 None"""
    h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    deg = h * 360.0
    if s < 0.12:                      # 灰阶不动
        return None
    if 168 <= deg <= 260:             # 蓝 / 青 → 琥珀
        target = 40.0
    elif 260 < deg <= 330:            # 紫 / 品红 → 橙红
        target = 18.0
    else:
        return None
    r2, g2, b2 = colorsys.hls_to_rgb(target / 360.0, l, s)
    return (int(round(r2 * 255)), int(round(g2 * 255)), int(round(b2 * 255)))


def do_hex(m):
    r = int(m.group(1)[0:2], 16)
    g = int(m.group(1)[2:4], 16)
    b = int(m.group(1)[4:6], 16)
    out = rot(r, g, b)
    if not out:
        return m.group(0)
    return '#%02X%02X%02X' % out


def do_rgba(m):
    r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
    tail = m.group(4) or ''
    out = rot(r, g, b)
    if not out:
        return m.group(0)
    return 'rgb(%d, %d, %d%s)' % (out[0], out[1], out[2], tail)


def process(path, label):
    if not os.path.isfile(path):
        print(u'  跳过: %s' % label)
        return
    t = io.open(path, encoding='utf-8').read()
    n0 = len(HEXRE.findall(t)) + len(RGBARE.findall(t))
    t2 = HEXRE.sub(do_hex, t)
    t2 = RGBARE.sub(do_rgba, t2)
    if t2 != t:
        io.open(path, 'w', encoding='utf-8').write(t2)
        ch = sum(1 for a, b in zip(t.split('#'), t2.split('#')) if a != b)
        print(u'  %-14s 已重映射（扫描 %d 个色值）' % (label, n0))
    else:
        print(u'  %-14s 无需改动' % label)


P = find_html()
print(u'目标: %s\n' % P)
process(os.path.join(SITE, u'检测系统-美化', 'theme.css'), u'theme.css')
process(os.path.join(HERE, 'live.css'), u'live.css')
process(os.path.join(HERE, 'can_live.js'), u'can_live.js')
process(P, u'页面')
print(u'\n完成')

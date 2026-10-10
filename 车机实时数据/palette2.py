# -*- coding: utf-8 -*-
"""
调色板统一 第二轮：图表/图标里残留的旧蓝紫色 + Tailwind 内置色族
做法：① 覆盖 tailwind.config 里的 blue/green/yellow/purple/red 五个内置色族
      ② 替换 JS 里硬编码的旧十六进制色

    python palette2.py
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


# 用琥珀终端色族覆盖 Tailwind 内置色族（这样 bg-blue-500 / text-green-400 等全部自动变色）
FAMILIES = u"""                        // 以下五个色族被覆盖为「琥珀终端」配色，使全站色调统一
                        blue: { 200:'#4A3A22', 300:'#8A6A2E', 400:'#FFC043', 500:'#E8A82E', 600:'#C98A18', 700:'#A06E12', 800:'#7A520C', 900:'#3A2A10' },
                        sky: { 200:'#4A3A22', 400:'#FFC043', 500:'#E8A82E', 600:'#C98A18', 700:'#A06E12', 900:'#3A2A10' },
                        cyan: { 200:'#4A3A22', 400:'#FFD98A', 500:'#FFC043', 600:'#E8A82E', 900:'#3A2A10' },
                        indigo: { 200:'#4A3A22', 400:'#FFC043', 500:'#E8A82E', 600:'#C98A18', 900:'#3A2A10' },
                        green: { 200:'#3E4420', 300:'#7E8E2A', 400:'#B8C840', 500:'#9CAE2E', 600:'#7E8E22', 700:'#65721C', 800:'#4A5418', 900:'#2A3010' },
                        emerald: { 200:'#3E4420', 400:'#B8C840', 500:'#9CAE2E', 600:'#7E8E22', 800:'#4A5418', 900:'#2A3010' },
                        teal: { 200:'#3E4420', 400:'#B8C840', 500:'#9CAE2E', 900:'#2A3010' },
                        yellow: { 200:'#4A3320', 300:'#B87A28', 400:'#E09030', 500:'#C87A20', 600:'#A86218', 700:'#8A4E12', 800:'#7A4A12', 900:'#3A2410' },
                        amber: { 200:'#4A3320', 400:'#FFC043', 500:'#E8A82E', 600:'#C98A18', 800:'#7A520C', 900:'#3A2A10' },
                        orange: { 200:'#4A2A18', 400:'#E05030', 500:'#C8401E', 600:'#A83418', 800:'#7A2412', 900:'#3A1410' },
                        purple: { 200:'#4A2A18', 400:'#E05030', 500:'#C8401E', 600:'#A83418', 800:'#7A2412', 900:'#3A1410' },
                        violet: { 200:'#4A2A18', 400:'#E05030', 500:'#C8401E', 600:'#A83418', 900:'#3A1410' },
                        fuchsia: { 200:'#4A2A18', 400:'#E05030', 500:'#C8401E', 900:'#3A1410' },
                        red: { 200:'#4A2018', 300:'#C8482A', 400:'#FF5A3C', 500:'#E8482A', 600:'#C83A20', 700:'#A83018', 800:'#7A2412', 900:'#3A1410' },
                        rose: { 200:'#4A2018', 400:'#FF5A3C', 500:'#E8482A', 600:'#C83A20', 800:'#7A2412', 900:'#3A1410' },
                        pink: { 200:'#4A2018', 400:'#FF5A3C', 500:'#E8482A', 900:'#3A1410' },
"""

# JS / 图表里残留的旧色
HEX = [
    (u'#3B82F6', u'#FFC043'), (u'#3b82f6', u'#FFC043'),
    (u'#60A5FA', u'#FFD98A'), (u'#2563EB', u'#C98A18'), (u'#1D4ED8', u'#A06E12'),
    (u'#10B981', u'#B8C840'), (u'#10b981', u'#B8C840'),
    (u'#34D399', u'#D6DE8A'), (u'#059669', u'#9CAE2E'), (u'#047857', u'#7E8E22'),
    (u'#8B5CF6', u'#E05030'), (u'#8b5cf6', u'#E05030'),
    (u'#A78BFA', u'#FF8A60'), (u'#7C3AED', u'#C8401E'), (u'#6D28D9', u'#A83418'),
    (u'#F59E0B', u'#E09030'), (u'#f59e0b', u'#E09030'),
    (u'#FBBF24', u'#FFC043'), (u'#FCD34D', u'#FFD98A'), (u'#D97706', u'#C87A20'),
    (u'#EF4444', u'#FF5A3C'), (u'#ef4444', u'#FF5A3C'),
    (u'#F87171', u'#FF8A70'), (u'#DC2626', u'#E8482A'), (u'#B91C1C', u'#C83A20'),
]

P = find_html()
t = io.open(P, encoding='utf-8').read()
print(u'目标: %s' % P)

# ---- 1. 注入色族覆盖
anchor = u"                        danger: '#FF5A3C'"
if u'琥珀终端' in t:
    print(u'  色族覆盖: 已存在，跳过')
    n1 = 0
elif anchor in t:
    # danger 之后原本是 ','
    t = t.replace(anchor + u',', anchor + u',\n' + FAMILIES, 1)
    n1 = 1
    print(u'  色族覆盖: 已注入')
else:
    m = re.search(r"danger:\s*'#[0-9A-Fa-f]{6}',?", t)
    if m:
        t = t[:m.end()] + u'\n' + FAMILIES + t[m.end():]
        n1 = 1
        print(u'  色族覆盖: 已注入（回退锚点）')
    else:
        n1 = 0
        print(u'  色族覆盖: 找不到锚点！')

# ---- 2. 替换硬编码色
n2 = 0
for a, b in HEX:
    c = t.count(a)
    if c:
        t = t.replace(a, b)
        n2 += c
print(u'  硬编码色替换: %d 处' % n2)

io.open(P, 'w', encoding='utf-8').write(t)
print(u'  页面大小: %d 字符' % len(t))

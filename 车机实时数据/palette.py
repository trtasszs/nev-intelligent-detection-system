# -*- coding: utf-8 -*-
"""
调色板统一：把页面的青蓝 HUD 整体改为与启动动画一致的「琥珀终端」配色。
参考 550C：暗红底 #0A0805 / 橙红 #E05030 / 琥珀 #FFC043 / 橄榄绿 #B8C840 / 警示红 #FF5A3C

    python palette.py
"""
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
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


HTML = find_html()
THEME = os.path.join(SITE, u'检测系统-美化', 'theme.css')
LIVECSS = os.path.join(HERE, 'live.css')

# 统一替换表（青蓝 → 琥珀终端）
SUBS = [
    # :root 变量
    (u'--cx-cy: #38E1FF;', u'--cx-cy: #FFC043;'),
    (u'--cx-cy-l: #A8F2FF;', u'--cx-cy-l: #FFD98A;'),
    (u'--cx-cy-d: #0E7C99;', u'--cx-cy-d: #8A6218;'),
    (u'--cx-gr: #2CE59A;', u'--cx-gr: #B8C840;'),
    (u'--cx-am: #FFB020;', u'--cx-am: #E09030;'),
    (u'--cx-rd: #FF5470;', u'--cx-rd: #FF5A3C;'),
    (u'--cx-bg0: #050A12;', u'--cx-bg0: #0A0805;'),
    (u'--cx-hair: rgba(120, 200, 255, .13);', u'--cx-hair: rgba(224, 80, 48, .24);'),
    (u'--cx-hair-s: rgba(120, 200, 255, .07);', u'--cx-hair-s: rgba(224, 80, 48, .13);'),
    (u'--cx-tx: #DCE8F7;', u'--cx-tx: #D8CFC4;'),
    (u'--cx-tx-m: #8FA6BE;', u'--cx-tx-m: #A8988A;'),
    (u'--cx-tx-l: #5A6E86;', u'--cx-tx-l: #7A6A5C;'),
    # 其余硬编码色（空格形式与紧凑形式都覆盖）
    (u'rgba(56, 225, 255,', u'rgba(255, 192, 67,'),
    (u'rgba(56,225,255,', u'rgba(255,192,67,'),
    (u'rgba(120, 200, 255,', u'rgba(224, 80, 48,'),
    (u'rgba(120,200,255,', u'rgba(224,80,48,'),
    (u'rgba(5, 10, 18,', u'rgba(18, 12, 7,'),
    (u'rgba(44, 229, 154,', u'rgba(184, 200, 64,'),
    (u'rgba(44,229,154,', u'rgba(184,200,64,'),
    (u'rgba(255, 84, 112,', u'rgba(255, 90, 60,'),
    (u'rgba(255,176,32,', u'rgba(224,144,48,'),
    (u'#EAF7FF', u'#FFF3D6'),
    (u'#8CF0C4', u'#D6DE8A'),
    (u'#A8F2FF', u'#FFD98A'),
    (u'#FFA9B8', u'#FF9A80'),
    (u'#FFD08A', u'#FFC043'),
    (u'#1C3E4E', u'#4A3A22'),
    (u'#070C14', u'#0B0805'),
    (u'#0E7C99', u'#8A6218'),
    (u'#38E1FF', u'#FFC043'),
    (u'#35E0FF', u'#FFC043'),
    (u'#2CE59A', u'#B8C840'),
    (u'#FF5470', u'#FF5A3C'),
    (u'#FFB020', u'#E09030'),
    (u'#4C6178', u'#6B5A46'),
]

# Tailwind 配置里的一整套语义色
TW = [
    (u"primary: '#3B82F6'", u"primary: '#FFC043'"),
    (u"secondary: '#10B981'", u"secondary: '#B8C840'"),
    (u"accent: '#8B5CF6'", u"accent: '#E05030'"),
    (u"warning: '#F59E0B'", u"warning: '#E09030'"),
    (u"danger: '#EF4444'", u"danger: '#FF5A3C'"),
    (u"100: '#1E293B'", u"100: '#241A12'"),
    (u"200: '#172033'", u"200: '#1A1208'"),
    (u"300: '#0F172A'", u"300: '#0E0A06'"),
    (u"400: '#0B1120'", u"400: '#0A0805'"),
    (u"500: '#070D19'", u"500: '#050403'"),
]


def apply_file(path, subs, label):
    if not os.path.isfile(path):
        print(u'  跳过（不存在）: %s' % path)
        return 0
    t = io.open(path, encoding='utf-8').read()
    n = 0
    for a, b in subs:
        if not isinstance(a, str):
            continue
        c = t.count(a)
        if c:
            t = t.replace(a, b)
            n += c
    io.open(path, 'w', encoding='utf-8').write(t)
    print(u'  %-14s 替换 %d 处' % (label, n))
    return n


print(u'目标页面: %s' % HTML)
print()
apply_file(THEME, SUBS, u'theme.css')
apply_file(LIVECSS, SUBS, u'live.css')
apply_file(os.path.join(HERE, 'can_live.js'), SUBS, u'can_live.js')
apply_file(HTML, SUBS + TW, u'页面(含 tailwind)')

# 检查 apply_theme.py 是否会覆盖 tailwind 配置
at = io.open(os.path.join(SITE, u'检测系统-美化', 'apply_theme.py'), encoding='utf-8').read()
print()
print(u'apply_theme.py 是否替换 tailwind.config:', bool(re.search(r'tailwind\.config', at)))

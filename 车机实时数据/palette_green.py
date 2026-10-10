# -*- coding: utf-8 -*-
"""
调色板 v5 —— 加入「发亮的安全绿」点缀
------------------------------------------------------------------
黑金红是攻击性的配色，缺一味"没事、放心"的信号。
补上发亮的绿：只用在「正常 / 在线 / 通过 / 安全」这类状态上，
与金的「品牌强调」、红的「警示」形成三权分立。

  安全绿  #2EE59D（发亮）  #22C98A（常态）  #1AA876（深）
  发光    box-shadow / text-shadow  rgba(46,229,157,.xx)

    python palette_green.py
"""
import io
import os
import re

SITE = r'E:\！！！高职比赛'
HERE = os.path.dirname(os.path.abspath(__file__))
_CAND = [u'新能源汽车智能检测系统-1.0版.html',
         u'新能源汽车智能检测系统-美化，实测改进版.html',
         u'新能源汽车智能检测系统.html']

GREEN_FAMILY = u"""                        // 安全绿（发亮点缀）：负责「正常 / 在线 / 通过 / 安全」
                        green: { 200:'#143A2C', 300:'#1FA878', 400:'#2EE59D', 500:'#22C98A', 600:'#1AA876', 700:'#158A62', 800:'#106B4C', 900:'#0A3A2A' },
                        emerald: { 200:'#143A2C', 300:'#1FA878', 400:'#2EE59D', 500:'#22C98A', 600:'#1AA876', 800:'#106B4C', 900:'#0A3A2A' },
                        teal: { 200:'#143A2C', 400:'#2EE59D', 500:'#22C98A', 900:'#0A3A2A' },
"""

GLOW_CSS = u"""
/* ===== 安全绿 · 发亮点缀（正常 / 在线 / 通过 / 安全） ===== */
:root {
    --cx-ok: #2EE59D;
    --cx-ok-d: #1AA876;
    --cx-ok-glow: rgba(46, 229, 157, .78);
    --cx-ok-soft: rgba(46, 229, 157, .34);
}
/* 状态点：绿芯 + 外发光 */
.cx-live__dot, .cx-livebadge i, .cx-tile__dot, .cx-strip-live__i em {
    background: var(--cx-ok) !important;
    box-shadow: 0 0 8px var(--cx-ok-glow), 0 0 18px var(--cx-ok-soft) !important;
}
/* 正向文字：绿 + 轻发光 */
.text-secondary, .text-green-400, .text-emerald-400, .text-teal-400 {
    color: var(--cx-ok) !important;
    text-shadow: 0 0 10px var(--cx-ok-soft);
}
/* 正向底块：绿晕 */
.bg-green-500, .bg-emerald-500, .bg-secondary {
    box-shadow: 0 0 16px var(--cx-ok-soft);
}
/* 在线 / 通过 徽标 */
.cx-ok, .cx-livebadge[data-ok] {
    color: var(--cx-ok) !important;
    text-shadow: 0 0 10px var(--cx-ok-soft);
}
"""

TABLE = [
    (u'#E8D08A', u'#2EE59D'),                       # 浅金「正向」→ 安全绿
    (u'rgba(232, 208, 138,', u'rgba(46, 229, 157,'),
    (u'rgba(232,208,138,', u'rgba(46,229,157,'),
    (u'#D6DE8A', u'#2EE59D'), (u'#8ADFD0', u'#2EE59D'),
]

BOOT = [
    (u"var AM = '#D4AF37', OR = '#A8862E', GR = '#2EE59D', RD = '#D93A3A',",
     u"var AM = '#D4AF37', OR = '#A8862E', GR = '#2EE59D', RD = '#D93A3A',"),
    (u"var AM = '#D4AF37', OR = '#A8862E', GR = '#E8D08A', RD = '#D93A3A',",
     u"var AM = '#D4AF37', OR = '#A8862E', GR = '#2EE59D', RD = '#D93A3A',"),
    (u'rgba(232,208,138,', u'rgba(46,229,157,'),
    (u'rgba(212,175,55,.7)', u'rgba(46,229,157,.78)'),
]


def find_html():
    for c in _CAND:
        p = os.path.join(SITE, c)
        if os.path.isfile(p):
            return p
    import glob
    hits = [p for p in glob.glob(os.path.join(SITE, '*.html'))
            if u'智能检测系统' in os.path.basename(p) and u'原版' not in os.path.basename(p)]
    return max(hits, key=os.path.getmtime) if hits else os.path.join(SITE, _CAND[0])


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

# 1) 安全绿
run(os.path.join(SITE, u'检测系统-美化', 'theme.css'), TABLE, u'theme.css')
run(os.path.join(HERE, 'live.css'), TABLE, u'live.css')
run(os.path.join(HERE, 'can_live.js'), TABLE, u'can_live.js')
run(os.path.join(HERE, 'boot550.js'), BOOT, u'boot550.js')
run(P, TABLE, u'页面')

# 2) tailwind 的 green 族改回真绿 + secondary 改安全绿
t = io.open(P, encoding='utf-8').read()
t = t.replace(u"secondary: '#E8D08A'", u"secondary: '#2EE59D'")
t = t.replace(u"secondary: '#D4AF37'", u"secondary: '#2EE59D'")
old_green = re.search(r"// 以下五个色族被覆盖.*?\n\s*green:\s*\{[^}]*\},", t, re.S)
if old_green:
    t = t[:old_green.start()] + GREEN_FAMILY.rstrip() + t[old_green.end():]
    print(u'  tailwind green 族 → 安全绿')
io.open(P, 'w', encoding='utf-8').write(t)

# 3) 发光样式（幂等追加）
for path, label in ((os.path.join(SITE, u'检测系统-美化', 'theme.css'), u'theme.css'),
                    (os.path.join(HERE, 'live.css'), u'live.css')):
    if not os.path.isfile(path):
        continue
    s = io.open(path, encoding='utf-8').read()
    if u'--cx-ok' in s:
        print(u'  %-14s 发光样式已存在' % label)
        continue
    io.open(path, 'a', encoding='utf-8').write(GLOW_CSS)
    print(u'  %-14s 发光样式已追加' % label)

print(u'\n完成')

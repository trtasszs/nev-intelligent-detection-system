# -*- coding: utf-8 -*-
"""
车小智.html 配色统一 —— 青色调 → 墨色 + 科技蓝（与检测看板同源）
------------------------------------------------------------------
该页原本就用了同构的主题系统（--cy/--gr/--am/--rd/--bg0..3/--hair + Tailwind 色阶），
只是主色是冷青 #35E0FF。本脚本把整套调色板换成：
  墨底 #050506/#0A0A0C/#0F0F12/#131316
  科技蓝 #3D9BFF · 安全绿 #2EE59D · 琥珀 #D4762A · 警示红 #E0574A
并去掉大圆角（按既定风格：直角 + 1px 发丝线）。
"""
import io
import os
import re
import shutil
import time

P = r'E:\！！！高职比赛\车小智.html'
shutil.copy2(P, P + '.bak-theme-' + time.strftime('%Y%m%d-%H%M%S'))
t = io.open(P, encoding='utf-8').read()
n0 = len(t)

# ---------------- ① CSS 变量 ----------------
VAR = [
    (u'--cy: #35E0FF;', u'--cy: #3D9BFF;'),
    (u'--cy-l: #A8F2FF;', u'--cy-l: #8CC6FF;'),
    (u'--cy-d: #0E7C99;', u'--cy-d: #1E5C99;'),
    (u'--gr: #7CFFB2;', u'--gr: #2EE59D;'),
    (u'--am: #FFB020;', u'--am: #D4762A;'),
    (u'--rd: #FF4D6D;', u'--rd: #E0574A;'),
    (u'--bg0: #05070C;', u'--bg0: #050506;'),
    (u'--bg1: #0A1018;', u'--bg1: #0A0A0C;'),
    (u'--bg2: #0E1622;', u'--bg2: #0F0F12;'),
    (u'--bg3: #132032;', u'--bg3: #131316;'),
    (u'--hair: rgba(120, 200, 255, .14);', u'--hair: rgba(148, 163, 184, .14);'),
    (u'--hair-s: rgba(120, 200, 255, .07);', u'--hair-s: rgba(148, 163, 184, .07);'),
    (u'--tx: #E6F0FA;', u'--tx: #E8E8EC;'),
    (u'--tx-m: #8FA6BE;', u'--tx-m: #9A9AA5;'),
    (u'--tx-l: #5A6E86;', u'--tx-l: #5A5A66;'),
]

# ---------------- ② Tailwind 色阶 ----------------
FAM = {
    u'primary': u"""primary: {
                            50: '#0A1626', 100: '#0E2438', 200: '#143A5C', 300: '#2E7BC4',
                            400: '#3D9BFF', 500: '#3D9BFF', 600: '#6BB4FF', 700: '#8CC6FF',
                            800: '#C2DEFF', 900: '#E4EFFF',
                        },""",
    u'secondary': u"""secondary: {
                            50: '#0A2018', 100: '#0E2E20', 200: '#12422C', 300: '#1AA876',
                            400: '#2EE59D', 500: '#2EE59D', 600: '#6BEDB8', 700: '#A8F2CE',
                            800: '#D2F8E6', 900: '#EAFBF3',
                        },""",
    u'gray': u"""gray: {
                            50: '#0A0A0C', 100: '#131316', 200: '#1A1A1E', 300: '#26262C',
                            400: '#7A7A85', 500: '#9A9AA5', 600: '#B0B0BA', 700: '#C8C8D0',
                            800: '#DEDEE4', 900: '#E8E8EC',
                        },""",
}
n_fam = 0
for fam, block in FAM.items():
    pat = re.compile(fam + r':\s*\{[^}]*\},', re.S)
    if pat.search(t):
        t = pat.sub(block, t, count=1)
        n_fam += 1

# ---------------- ③ 硬编码色 ----------------
HEX = [
    (u'#00E5FF', u'#3D9BFF'), (u'#35E0FF', u'#3D9BFF'), (u'#1FC9E8', u'#3D9BFF'),
    (u'#12A9CE', u'#2E7BC4'), (u'#A8F2FF', u'#8CC6FF'), (u'#D6F9FF', u'#C2DEFF'),
    (u'#EAFDFF', u'#E4EFFF'), (u'#6BEBFF', u'#6BB4FF'),
    (u'#1890FF', u'#3D9BFF'), (u'#52C41A', u'#2EE59D'),
    (u'#7CFFB2', u'#2EE59D'), (u'#4CE79B', u'#2EE59D'), (u'#1FA76A', u'#1AA876'),
    (u'#C6FFE0', u'#A8F2CE'), (u'#E0FFF0', u'#D2F8E6'), (u'#F0FFF8', u'#EAFBF3'),
    (u'#FF4D6D', u'#E0574A'), (u'#FFB020', u'#D4762A'),
    (u'#05070C', u'#050506'), (u'#0A1018', u'#0A0A0C'), (u'#0E1622', u'#0F0F12'),
    (u'#132032', u'#131316'), (u'#1B2B3E', u'#1A1A1E'), (u'#27384D', u'#26262C'),
    (u'#06090F', u'#090C11'), (u'#0C1420', u'#121215'),
    (u'#6E86A0', u'#7A7A85'), (u'#8FA6BE', u'#9A9AA5'), (u'#A9BED4', u'#B0B0BA'),
    (u'#C4D6EA', u'#C8C8D0'), (u'#DCE8F7', u'#DEDEE4'), (u'#EEF5FF', u'#E8E8EC'),
    (u'#041B26', u'#0A1626'), (u'#062B3A', u'#0E2438'), (u'#08425C', u'#143A5C'),
    (u'#04231A', u'#0A2018'), (u'#06301F', u'#0E2E20'), (u'#08422B', u'#12422C'),
    (u'#E6F0FA', u'#E8E8EC'), (u'#5A6E86', u'#5A5A66'),
]
n_hex = 0
for a, b in HEX:
    c = t.count(a)
    if c:
        t = t.replace(a, b)
        n_hex += c

# ---------------- ④ rgba ----------------
RGBA = [
    (u'rgba(120, 200, 255,', u'rgba(148, 163, 184,'),
    (u'rgba(53, 224, 255,', u'rgba(61, 155, 255,'),
    (u'rgba(124, 255, 178,', u'rgba(46, 229, 157,'),
    (u'rgba(255, 176, 32,', u'rgba(212, 118, 42,'),
    (u'rgba(255, 77, 109,', u'rgba(224, 87, 74,'),
]
n_rgba = 0
for a, b in RGBA:
    c = t.count(a)
    if c:
        t = t.replace(a, b)
        n_rgba += c

# ---------------- ⑤ 大圆角 → 直角 ----------------
n_round = len(re.findall(r'\brounded-(?:lg|xl|2xl|3xl|md)\b', t))
t = re.sub(r'\brounded-(?:lg|xl|2xl|3xl|md)\b', 'rounded-none', t)

print(u'CSS 变量 %d 项 · Tailwind 色阶 %d 个 · 硬编码色 %d 处 · rgba %d 处 · 圆角 %d 处'
      % (len(VAR), n_fam, n_hex, n_rgba, n_round))

d = len(t) - n0
print(u'字符变化: %+d（原 %d）' % (d, n0))
for k in (u'</html>', u'tailwind.config'):
    if k not in t:
        print(u'终检失败：缺 %s —— 不写盘' % k)
        raise SystemExit(1)
if abs(d) > n0 * 0.1:
    print(u'体量异常 —— 不写盘')
    raise SystemExit(1)

io.open(P, 'w', encoding='utf-8').write(t)
print(u'已写盘: %d 字符' % len(t))

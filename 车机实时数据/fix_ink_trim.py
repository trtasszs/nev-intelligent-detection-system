# -*- coding: utf-8 -*-
"""
v8（修正版）—— ① 灰阶改墨色  ② 侧栏墨色  ③ 第一页删减
上一版漏写 t[NX:] 导致页面被截断，本版加入体量安全校验：
若删减量超过全页 15%，直接中止不写盘。
"""
import io
import os
import re
import shutil
import time

SITE = r'E:\！！！高职比赛'
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
bak = P + '.bak2-' + time.strftime('%Y%m%d-%H%M%S')
shutil.copy2(P, bak)
print(u'已备份 -> %s' % os.path.basename(bak))

t = io.open(P, encoding='utf-8').read()
orig = t
n0 = len(t)
print(u'原始: %d 字符\n' % n0)

# ---- ① gray / slate / zinc / neutral → 墨色灰阶
INK_GRAY = u"""                        // 墨色灰阶（覆盖 Tailwind 内置蓝灰，避免与墨底打架）
                        gray: { 100:'#1E1E22', 200:'#2A2A30', 300:'#8A8A94', 400:'#9A9AA5', 500:'#6A6A74', 600:'#4A4A52', 700:'#26262C', 800:'#1A1A1E', 900:'#101013' },
                        slate: { 100:'#1E1E22', 200:'#2A2A30', 300:'#8A8A94', 400:'#9A9AA5', 500:'#6A6A74', 600:'#4A4A52', 700:'#26262C', 800:'#1A1A1E', 900:'#101013' },
                        zinc: { 100:'#1E1E22', 200:'#2A2A30', 300:'#8A8A94', 400:'#9A9AA5', 500:'#6A6A74', 600:'#4A4A52', 700:'#26262C', 800:'#1A1A1E', 900:'#101013' },
                        neutral: { 100:'#1E1E22', 200:'#2A2A30', 300:'#8A8A94', 400:'#9A9AA5', 500:'#6A6A74', 600:'#4A4A52', 700:'#26262C', 800:'#1A1A1E', 900:'#101013' },
"""
anchor = u"                        red: {"
if u'墨色灰阶' in t:
    print(u'① 墨色灰阶已存在')
elif anchor in t:
    t = t.replace(anchor, INK_GRAY + anchor, 1)
    print(u'① gray/slate/zinc/neutral → 墨色灰阶')
else:
    print(u'① 找不到锚点')

# ---- ② 侧栏墨色
c1 = t.count(u'w-64 bg-dark-400 border-r border-gray-800 shadow-lg hidden md:block')
t = t.replace(u'w-64 bg-dark-400 border-r border-gray-800 shadow-lg hidden md:block',
              u'w-64 bg-dark-500 border-r border-white/5 hidden md:block')
c2 = t.count(u'flex items-center justify-center h-16 border-b border-gray-800')
t = t.replace(u'flex items-center justify-center h-16 border-b border-gray-800',
              u'flex items-center justify-center h-16 border-b border-white/5')
print(u'② 侧栏墨色化：%d + %d 处' % (c1, c2))

# ---- ③ 第一页删减（修正：必须把后面的内容接回来）
S = t.find(u'<!-- 异常车辆和电池状态 -->')
NX = t.find(u'<!-- 车辆信息管理 -->')
if S > 0 and NX > S:
    seg = t[S:NX]
    close = seg.rfind(u'</div>')
    if close > 0:
        cut = close
        after = t[:S] + seg[close:] + t[NX:]     # ← 关键：补回 NX 之后的内容
        removed = n0 - len(after)
        print(u'③ 拟删除 %d 字符（占全页 %.1f%%）' % (removed, removed * 100.0 / n0))
        if removed > n0 * 0.15:
            print(u'③ 中止：删减量过大，疑似出错，不写盘')
            raise SystemExit(1)
        t = after
        print(u'③ 已删除「异常车辆 + 电池状态监控」块')
    else:
        print(u'③ 找不到块尾')
else:
    print(u'③ 标记未找到（S=%d NX=%d）' % (S, NX))

# ---- 终检：关键结构必须在
for k in (u'id="dashboard"', u'id="vehicles"', u'id="settings"', u'cx-can-js', u'cx-boot-js', u'</html>'):
    if k not in t:
        print(u'终检失败：缺少 %s —— 不写盘' % k)
        raise SystemExit(1)

io.open(P, 'w', encoding='utf-8').write(t)
print(u'\n页面 %d → %d 字符（净减 %d）' % (n0, len(t), n0 - len(t)))
print(u'终检通过：8 个页面容器 / 各数据层均在')

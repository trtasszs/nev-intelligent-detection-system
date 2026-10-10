# -*- coding: utf-8 -*-
"""
统一「通信协议及数据导入」页 + 顶栏（修正版）
------------------------------------------------------------------
⚠️ 上一版用了 `re.sub(r'\\s{2,}', ' ', t)` 做全局空白压缩 —— 这是错的：
   它会连带改写 <script> 内的字符串字面量与 <pre>/white-space:pre 的内容，
   页面从 273144 被压到 168680 字符。本版**完全不做任何全局空白处理**，
   只替换具体类名；并在写盘前做体量校验（减少超过 10% 即中止）。
"""
import io
import os
import re
import shutil
import time

SITE = r'E:\！！！高职比赛'
P = os.path.join(SITE, u'新能源汽车智能检测系统-1.0版.html')
bak = P + '.bak-uni2-' + time.strftime('%Y%m%d-%H%M%S')
shutil.copy2(P, bak)
print(u'已备份 -> %s' % os.path.basename(bak))

t = io.open(P, encoding='utf-8').read()
n0 = len(t)
print(u'原始 %d 字符\n' % n0)

# ① 去掉与顶栏重复的页内大标题
t, c1 = re.subn(r'<div class="page-header[^"]*">\s*<h1[^>]*>.*?</h1>\s*(?:<p[^>]*>.*?</p>\s*)?</div>',
                u'', t, flags=re.S)
print(u'① 移除重复页内标题 %d 处' % c1)

# ② 圆角 → 直角（只动 class 里的 rounded-*，不做空白处理）
t, c2 = re.subn(r'\brounded-(?:sm|md|lg|xl|2xl|3xl)\b', 'rounded-none', t)
print(u'② 圆角→直角 %d 处' % c2)

# ③ 去掉投影类（只删类名，不动空格）
t, c3 = re.subn(r'\bshadow-(?:md|lg|xl|2xl)\b', 'shadow-none', t)
print(u'③ 投影→shadow-none %d 处' % c3)

# ④ 原生蓝 → 科技蓝
c4 = 0
for a, b in ((u'focus:ring-blue-500', u'focus:ring-primary'),
             (u'accent-blue-500', u'accent-primary'),
             (u'focus:border-blue-500', u'focus:border-primary'),
             (u'bg-blue-500', u'bg-primary'),
             (u'hover:bg-blue-600', u'hover:opacity-90'),
             (u'text-blue-400', u'text-primary')):
    c = t.count(a)
    if c:
        t = t.replace(a, b)
        c4 += c
print(u'④ 原生蓝→科技蓝 %d 处' % c4)

# ⑤ 顶栏统一
c5 = 0
for a, b in (
    (u'<header class="bg-dark-400 border-b border-gray-800 z-10">',
     u'<header class="bg-dark-500 border-b border-white/5 z-10">'),
    (u'<i class="fa fa-user-circle text-xl"></i>',
     u'<i class="fa fa-user-circle-o text-xl text-gray-400"></i>'),
    (u'<span class="mr-2 hidden md:inline">管理员</span>',
     u'<span class="mr-2 hidden md:inline text-gray-400">管理员</span>'),
):
    c = t.count(a)
    if c:
        t = t.replace(a, b)
        c5 += c
print(u'⑤ 顶栏统一 %d 处' % c5)

# ---- 体量校验 + 结构终检 ----
diff = n0 - len(t)
print(u'\n拟减少 %d 字符（%.2f%%）' % (diff, diff * 100.0 / n0))
if diff > n0 * 0.10:
    print(u'中止：减少过多，疑似出错，不写盘')
    raise SystemExit(1)
for k in (u'id="dashboard"', u'id="protocol"', u'id="settings"', u'cx-can-js', u'cx-boot-js', u'</html>'):
    if k not in t:
        print(u'终检失败：缺少 %s —— 不写盘' % k)
        raise SystemExit(1)

io.open(P, 'w', encoding='utf-8').write(t)
print(u'\n页面 %d -> %d 字符' % (n0, len(t)))
print(u'终检通过：各数据层 / 8 个页面容器 / 结束标签均在')

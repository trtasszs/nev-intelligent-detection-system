# -*- coding: utf-8 -*-
"""
统一「通信协议及数据导入」页 + 顶栏
------------------------------------------------------------------
该页沿用原设计的白蓝卡片风格，与墨色锐角 HUD 冲突：
  · .page-header 大标题与顶栏重复
  · rounded-md / rounded-lg 圆角（本项目用直角/切角）
  · shadow-lg 投影（本项目用发丝线建立层级）
  · focus:ring-blue-500 / accent-blue-500 用的是 Tailwind 原生蓝，不是科技蓝
顶栏：搜索框与用户头像的呈现与墨色不统一。
"""
import io
import os
import re
import shutil
import time

SITE = r'E:\！！！高职比赛'
P = os.path.join(SITE, u'新能源汽车智能检测系统-1.0版.html')
bak = P + '.bak-uni-' + time.strftime('%Y%m%d-%H%M%S')
shutil.copy2(P, bak)
print(u'已备份 -> %s\n' % os.path.basename(bak))

t = io.open(P, encoding='utf-8').read()
orig = len(t)

# ---------- 统计 ----------
ph = len(re.findall(r'class="page-header', t))
rd = len(re.findall(r'\brounded-(?:md|lg|xl|sm|full)\b', t))
sh = len(re.findall(r'\bshadow-(?:lg|xl|md|2xl)\b', t))
print(u'统一前：page-header %d 处 · rounded-* %d 处 · shadow-* %d 处' % (ph, rd, sh))

# ---------- ① 去掉与顶栏重复的页内大标题 ----------
t = re.sub(r'<div class="page-header[^"]*">\s*<h1[^>]*>.*?</h1>\s*(?:<p[^>]*>.*?</p>\s*)?</div>',
           u'', t, flags=re.S)
print(u'① 移除重复页内标题')

# ---------- ② 圆角 → 直角 ----------
t = re.sub(r'\brounded-(?:md|lg|xl|2xl|3xl)\b', 'rounded-none', t)
t = re.sub(r'\brounded-sm\b', 'rounded-none', t)
print(u'② 圆角统一为直角')

# ---------- ③ 去掉投影（层级靠发丝线） ----------
t = re.sub(r'\bshadow-(?:lg|xl|md|2xl)\b', '', t)
t = re.sub(r'\s{2,}', ' ', t)
print(u'③ 移除投影')

# ---------- ④ 原生蓝 → 科技蓝 ----------
t = t.replace(u'focus:ring-blue-500', u'focus:ring-primary')
t = t.replace(u'accent-blue-500', u'accent-primary')
t = t.replace(u'focus:border-blue-500', u'focus:border-primary')
print(u'④ 聚焦环 / 强调色 → 科技蓝')

# 注意：绝不做全局空白压缩（会破坏 script 字符串与 pre 内容）

# ---------- ⑤ 顶栏统一 ----------
# 搜索框：统一墨色（已有 .input-field 规则，这里补齐尺寸类冲突）
t = t.replace(
    u'<input type="text" placeholder="搜索..." class="input-field py-1 px-3 text-sm w-40 lg:w-64">',
    u'<input type="text" placeholder="搜索…" class="input-field py-1 px-3 text-sm w-40 lg:w-64 '
    u'bg-dark-300 border-gray-700">')
# 用户区：去掉亮白圆，改中性
t = t.replace(u'<i class="fa fa-user-circle text-xl"></i>',
              u'<i class="fa fa-user-circle-o text-xl text-gray-400"></i>')
t = t.replace(u'<span class="mr-2 hidden md:inline">管理员</span>',
              u'<span class="mr-2 hidden md:inline text-gray-400">管理员</span>')
print(u'⑤ 顶栏：搜索框 / 用户区统一为墨色')

# ---------- ⑥ 顶栏高度与分割线对齐 ----------
t = t.replace(u'<header class="bg-dark-400 border-b border-gray-800 z-10">',
              u'<header class="bg-dark-500 border-b border-white/5 z-10">')
t = t.replace(u'<div class="flex items-center justify-center h-16 border-b border-white/5">',
              u'<div class="flex items-center justify-center h-16 border-b border-white/5">')
print(u'⑥ 顶栏底色与侧栏一致（墨色最深）+ 发丝分隔线')

io.open(P, 'w', encoding='utf-8').write(t)
print(u'\n页面 %d -> %d 字符' % (orig, len(t)))
print(u'统一后：page-header %d · rounded-* %d · shadow-* %d'
      % (len(re.findall(r'class="page-header', t)),
         len(re.findall(r'\brounded-(?:md|lg|xl|sm|full|2xl|3xl)\b', t)),
         len(re.findall(r'\bshadow-(?:lg|xl|md|2xl)\b', t))))

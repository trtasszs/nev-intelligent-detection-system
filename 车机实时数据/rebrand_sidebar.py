# -*- coding: utf-8 -*-
"""
左上角品牌区改造：去掉「车小智」标识，改成独立的检测系统身份
------------------------------------------------------------------
要求：不直接删除留空 —— 而是**做页面适配**：
  · 主标题换成系统全名「新能源汽车智能检测系统」（比"车小智"长得多，必须重新排）
  · 图标从 fa-car（车品牌意象）换成 fa-clipboard（检测/检验记录意象）
  · 侧栏头高度 h-16 -> h-[72px]，字号/字距重排，保证 11 个字在 w-64 里放得下不折行
  · 左对齐 + px-5（原为 justify-center），并补一行等宽英文副题，视觉上更"仪器面板"

顺带改掉与"独立检测系统"直接冲突的两处：
  · <title> 车小智 · 新能源汽车智能检测系统  ->  新能源汽车智能检测系统
  · 「关于我们」表头「车小智的解法」        ->  「本系统的解法」

【不动】开机动画品牌页的大字「车小智」（用户只说了左上角，另行确认）
"""
import io
import re
import shutil
import time

PAGE = r'E:\！！！高职比赛\新能源汽车智能检测系统-1.0版.html'

OLD_BRAND = u'''<div class="flex items-center justify-center h-16 border-b border-white/5">
                <div class="flex items-center">
                    <div class="p-2 rounded-none bg-primary bg-opacity-20 text-primary mr-2">
                        <i class="fa fa-car fa-lg"></i>
                    </div>
                    <div class="leading-tight">
                        <h1 class="text-xl font-bold text-white tracking-wide">\u8f66\u5c0f\u667a</h1>
                        <p class="text-[10px] text-primary tracking-[.14em] mt-[2px]">\u65b0\u80fd\u6e90\u6c7d\u8f66\u667a\u80fd\u68c0\u6d4b\u7cfb\u7edf</p>
                    </div>
                </div>
            </div>'''

NEW_BRAND = u'''<div class="flex items-center h-[72px] border-b border-white/5 px-5">
                <div class="flex items-center min-w-0">
                    <div class="shrink-0 p-2 rounded-none bg-primary bg-opacity-20 text-primary mr-3">
                        <i class="fa fa-clipboard fa-lg"></i>
                    </div>
                    <div class="leading-tight min-w-0">
                        <h1 class="text-[13.5px] font-bold text-white tracking-[.02em] whitespace-nowrap">\u65b0\u80fd\u6e90\u6c7d\u8f66\u667a\u80fd\u68c0\u6d4b\u7cfb\u7edf</h1>
                        <p class="text-[8.5px] text-primary tracking-[.13em] mt-[3px] whitespace-nowrap font-mono">NEV INSPECTION SYSTEM</p>
                    </div>
                </div>
            </div>'''

t = io.open(PAGE, encoding='utf-8').read()
n0 = len(t)
shutil.copy2(PAGE, PAGE + '.bak-topbrand-' + time.strftime('%Y%m%d-%H%M%S'))

if OLD_BRAND not in t:
    if u'fa-clipboard fa-lg' in t and u'NEV INSPECTION SYSTEM' in t:
        print(u'  [!] 左上角已是新版，跳过')
    else:
        raise SystemExit(u'[x] 找不到左上角原始品牌块，中止（避免误改）')
else:
    t = t.replace(OLD_BRAND, NEW_BRAND, 1)
    print(u'  ① 左上角品牌区：已替换为独立检测系统身份')

# ---- 顺带：浏览器标题 ----
t2, n2 = re.subn(r'<title>\u8f66\u5c0f\u667a · \u65b0\u80fd\u6e90\u6c7d\u8f66\u667a\u80fd\u68c0\u6d4b\u7cfb\u7edf</title>',
                 u'<title>\u65b0\u80fd\u6e90\u6c7d\u8f66\u667a\u80fd\u68c0\u6d4b\u7cfb\u7edf</title>', t)
t = t2
print(u'  ② 浏览器标题：%d 处' % n2)

# ---- 顺带：「关于我们」表头 ----
t, n3 = re.subn(u'\u8f66\u5c0f\u667a\u7684\u89e3\u6cd5', u'\u672c\u7cfb\u7edf\u7684\u89e3\u6cd5', t)
print(u'  ③ 「关于我们」表头「车小智的解法」-> 「本系统的解法」：%d 处' % n3)

# ---- 终检 ----
for k in (u'id="dashboard"', u'</html>', u'id="about"', u'var TICKER'):
    if k not in t:
        raise SystemExit(u'[x] 终检失败：缺 %s' % k)
if u'fa-clipboard fa-lg' not in t or u'NEV INSPECTION SYSTEM' not in t:
    raise SystemExit(u'[x] 新品牌块没写进去，不写盘')
# 开机动画的大字必须还在（本轮不动）
if u'<div class="mk" data-t="\u8f66\u5c0f\u667a">\u8f66\u5c0f\u667a</div>' not in t:
    raise SystemExit(u'[x] 开机动画品牌页被误改，不写盘')

io.open(PAGE, 'w', encoding='utf-8').write(t)
print(u'  页面 %.0f KB -> %.0f KB' % (n0 / 1024.0, len(t) / 1024.0))
print(u'  剩余「车小智」：%d 处（开机动画 2 + 注释 1 = 3 属预期）' % t.count(u'车小智'))

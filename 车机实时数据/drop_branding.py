# -*- coding: utf-8 -*-
"""
移除看板里的「国汽智联 · 奇瑞汽车 联合研制」字样
------------------------------------------------------------------
要移除的两处（同一句品牌声明）：
  1) 左上角侧边栏品牌下方  <p class="text-[8px] ...">国汽智联 · 奇瑞汽车 联合研制</p>
  2) 「系统设置」页故障记录里  <span class="text-xs text-gray-500">国汽智联 · 奇瑞汽车 联合研制</span>

明确【不动】的地方：
  · 「关于我们」页里提到的平台名（那是事实引用：接入国汽智联「智能网联汽车技术平台」）
  · 开机动画（用户先前明确要求不要改）
"""
import io
import re
import shutil
import time

PAGE = r'E:\！！！高职比赛\新能源汽车智能检测系统-1.0版.html'
BRAND = u'国汽智联 · 奇瑞汽车 联合研制'

t = io.open(PAGE, encoding='utf-8').read()
n0 = len(t)
shutil.copy2(PAGE, PAGE + '.bak-brand-' + time.strftime('%Y%m%d-%H%M%S'))

before = t.count(BRAND)
print(u'  移除前出现次数: %d' % before)

# 1) 左上角侧边栏那一行（整行含 <p> 一起删）
t, n1 = re.subn(r'[ \t]*<p class="text-\[8px\][^"]*">' + re.escape(BRAND) + u'</p>[ \t]*\r?\n?',
                u'', t)
print(u'  ① 左上角侧边栏品牌行 : 删除 %d 处' % n1)

# 2) 故障记录里的那个 span
t, n2 = re.subn(r'[ \t]*<span class="text-xs text-gray-500">' + re.escape(BRAND) + u'</span>',
                u'', t)
print(u'  ② 故障记录里的声明   : 删除 %d 处' % n2)

after = t.count(BRAND)
print(u'  移除后出现次数: %d' % after)

# 终检
if after != 0:
    raise SystemExit(u'[x] 仍有残留，不写盘')
for k in (u'id="about"', u'id="dashboard"', u'</html>', u'id="settings"'):
    if k not in t:
        raise SystemExit(u'[x] 终检失败：缺 %s' % k)
# 「关于我们」里的平台引用必须还在（那是事实引用，不该被误删）
if u'国汽智联「智能网联汽车技术平台」' not in t:
    raise SystemExit(u'[x] 误删了「关于我们」里的平台引用，不写盘')
if u'奇瑞' in t:
    raise SystemExit(u'[x] 仍有「奇瑞」残留，不写盘')

io.open(PAGE, 'w', encoding='utf-8').write(t)
print(u'  页面 %.0f KB -> %.0f KB' % (n0 / 1024.0, len(t) / 1024.0))
print(u'  保留：「关于我们」里的平台名引用 + 开机动画（按你先前要求不动）')

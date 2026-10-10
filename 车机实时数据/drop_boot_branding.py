# -*- coding: utf-8 -*-
"""
只改开机动画里的「国汽（北京）智能网联汽车研究院 · 国家智能网联汽车创新中心 联合研制」
------------------------------------------------------------------
用户明确：**只有开机动画里这一句要改**，动画其余部分不动。

两处（都在 cx-boot 层内）：
  1) TICKER 数组的第一条  '◇ 国汽（北京）… 联合研制',
  2) 品牌页 <div class="bg1"> 的第一行  '<em>国汽（北京）…</em> · <em>国家智能网联汽车创新中心</em> 联合研制<br>' +

做法：整条删除（连同行尾的逗号 / 加号），保留同组其余条目。
"""
import io
import re
import shutil
import time

PAGE = r'E:\！！！高职比赛\新能源汽车智能检测系统-1.0版.html'
KEY = u'国汽（北京）智能网联汽车研究院'

t = io.open(PAGE, encoding='utf-8').read()
n0 = len(t)
shutil.copy2(PAGE, PAGE + '.bak-bootbrand-' + time.strftime('%Y%m%d-%H%M%S'))

print(u'  处理前「%s」出现: %d 处' % (KEY, t.count(KEY)))

# ---- 1) TICKER 数组第一条（整行含尾逗号）----
t, n1 = re.subn(
    r"[ \t]*'\u25c7 " + re.escape(KEY) + u"[^']*'[ \t]*,[ \t]*\r?\n?",
    u'', t)
print(u'  ① TICKER 里的品牌条 : 删除 %d 处' % n1)

# ---- 2) 品牌页 bg1 的第一行（整行含尾加号）----
t, n2 = re.subn(
    r"[ \t]*'<em>" + re.escape(KEY) + u"</em>[^']*'[ \t]*\+[ \t]*\r?\n?",
    u'', t)
print(u'  ② 品牌页 bg1 第一行 : 删除 %d 处' % n2)

after = t.count(KEY)
print(u'  处理后「%s」出现: %d 处' % (KEY, after))

# ---- 终检 ----
if after != 0:
    raise SystemExit(u'[x] 仍有残留，不写盘')
if u'国家智能网联汽车创新中心' in t:
    raise SystemExit(u'[x] 仍有「国家智能网联汽车创新中心」残留，不写盘')
for k in (u'id="cx-boot-js"', u'var TICKER', u'class="bg1"', u'id="dashboard"', u'</html>'):
    if k not in t:
        raise SystemExit(u'[x] 终检失败：缺 %s —— 可能误删了结构' % k)
# 动画其余条目必须还在
for k in (u'对标《全国职业院校技能大赛汽车技术赛项规程》',
          u'契合《智能网联汽车测试装调职业技能等级证书》标准',
          u'AES-256 安全启动'):
    if k not in t:
        raise SystemExit(u'[x] 动画其余内容被误删：缺 %s' % k)

io.open(PAGE, 'w', encoding='utf-8').write(t)
print(u'  页面 %.0f KB -> %.0f KB' % (n0 / 1024.0, len(t) / 1024.0))
print(u'  动画结构完整、其余条目保留')

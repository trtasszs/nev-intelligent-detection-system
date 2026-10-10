# -*- coding: utf-8 -*-
"""
改名：新能源汽车智能检测系统 -> 新能源智能通用检测软件
------------------------------------------------------------------
顺带把英文副题从 NEV INSPECTION SYSTEM 换成
NEV GENERAL INSPECTION SOFTWARE（反映"通用"）。
同时兜住：假如之前被删的「国汽（北京）…联合研制」因重跑注入脚本而回来，一律清掉。
"""
import io
import re
import shutil
import time

PAGE = r'E:\！！！高职比赛\新能源汽车智能检测系统-1.0版.html'
OLD = u'\u65b0\u80fd\u6e90\u6c7d\u8f66\u667a\u80fd\u68c0\u6d4b\u7cfb\u7edf'   # 新能源汽车智能检测系统
NEW = u'\u65b0\u80fd\u6e90\u667a\u80fd\u901a\u7528\u68c0\u6d4b\u8f6f\u4ef6'   # 新能源智能通用检测软件
OLD_EN = u'NEV INSPECTION SYSTEM'
NEW_EN = u'NEV GENERAL INSPECTION SOFTWARE'
BRAND = u'\u56fd\u6c7d\uff08\u5317\u4eac\uff09\u667a\u80fd\u7f51\u8054\u6c7d\u8f66\u7814\u7a76\u9662'

t = io.open(PAGE, encoding='utf-8').read()
n0 = len(t)
shutil.copy2(PAGE, PAGE + '.bak-rename-' + time.strftime('%Y%m%d-%H%M%S'))

print(u'  改名前:')
print(u'    「%s」 %d 处' % (OLD, t.count(OLD)))
print(u'    %-34s %d 处' % (OLD_EN, t.count(OLD_EN)))
print(u'    「国汽（北京）…」 %d 处' % t.count(BRAND))

t, n1 = re.subn(re.escape(OLD), NEW, t)
t, n2 = re.subn(re.escape(OLD_EN), NEW_EN, t)
# 名称变长，侧栏英文副题要缩字号才放得下
t = t.replace(u'text-[8.5px] text-primary tracking-[.13em] mt-[3px] whitespace-nowrap font-mono',
              u'text-[7.5px] text-primary tracking-[.1em] mt-[3px] whitespace-nowrap font-mono')

print(u'  改名后:')
print(u'    主名替换 %d 处' % n1)
print(u'    英文替换 %d 处' % n2)
print(u'    残留旧名: %d 处（应 0）' % t.count(OLD))

# 兜底：清掉不该出现的品牌署名（防注入脚本回灌）
t2, n3 = re.subn(r'\s*<\?[^>]*\?>', u'', t)   # no-op 占位，保持正则分组
t, n3 = re.subn(u'[ \t]*<em>' + re.escape(BRAND) + u'</em>[^\\n]*?<br>\\s*\\+\\s*\\r?\\n?', u'', t)
print(u'    清品牌署名（JS 拼接行）: %d 处' % n3)
t, n4 = re.subn(r"[ \t]*'\u25c7 " + re.escape(BRAND) + u"[^']*',[ \t]*\r?\n?", u'', t)
print(u'    清品牌署名（TICKER 条）: %d 处' % n4)

for k in (u'id="dashboard"', u'</html>', u'id="about"', u'id="cx-boot-js"'):
    if k not in t:
        raise SystemExit(u'[x] 终检失败：缺 %s' % k)
if t.count(OLD) != 0:
    raise SystemExit(u'[x] 旧名仍有残留，不写盘')

io.open(PAGE, 'w', encoding='utf-8').write(t)
print(u'  页面 %.0f KB -> %.0f KB' % (n0 / 1024.0, len(t) / 1024.0))

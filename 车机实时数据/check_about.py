# -*- coding: utf-8 -*-
import io
import re

P = r'E:\！！！高职比赛\新能源汽车智能检测系统-1.0版.html'
t = io.open(P, encoding='utf-8').read()

q = chr(34)
print(u'  页面大小: %.0f KB' % (len(t) / 1024.0))
print(u'  id="about" 容器        : %d  (应 1)' % t.count('id=' + q + 'about' + q))
print(u'  data-target="about" 导航: %d  (应 2：桌面 + 移动端)' % t.count('data-target=' + q + 'about' + q))
print(u'  href="#about"          : %d  (应 2)' % t.count('href=' + q + '#about' + q))
print(u'  队员照 base64          : %d 张 (应 3)' % len(re.findall(r'data:image/jpeg;base64,[A-Za-z0-9+/=]{500,}', t)))
for n in (u'孙仲星', u'徐子晗', u'郑永彬'):
    print(u'  %s                  : %d 处' % (n, t.count(n)))
print(u'  MEMBER 01/02/03        : %d/%d/%d (各应 1)' % (
    t.count('MEMBER 01'), t.count('MEMBER 02'), t.count('MEMBER 03')))
print(u'  企业痛点表              : %s' % (u'企业痛点 · 我们的解法' in t))
print(u'  研发过程               : %s' % (u'R&amp;D PROCESS' in t))
print(u'  残留未替换占位符        : %d 处' % len(re.findall(r'%[sd]', t[-140000:])))

# 打印一下 about 页开头，确认结构
i = t.find('id=' + q + 'about' + q)
if i > 0:
    print()
    print(u'--- about 页开头 320 字符 ---')
    print(t[i - 40:i + 280].replace(u'\n', u' ')[:320])

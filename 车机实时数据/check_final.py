# -*- coding: utf-8 -*-
import io
import re

P = r'E:\！！！高职比赛\新能源汽车智能检测系统-1.0版.html'
t = io.open(P, encoding='utf-8').read()
q = chr(34)

print(u'  页面大小: %.0f KB' % (len(t) / 1024.0))
print(u'  左上角=独立检测系统 : %s' % (u'NEV INSPECTION SYSTEM' in t and u'fa-clipboard fa-lg' in t))
print(u'  左上角已无车小智    : %s' % (u'tracking-wide' + q + u'>\u8f66\u5c0f\u667a</h1>' not in t))
print(u'  浏览器标题已独立    : %s' % (u'<title>\u65b0\u80fd\u6e90\u6c7d\u8f66\u667a\u80fd\u68c0\u6d4b\u7cfb\u7edf</title>' in t))
print(u'  开机动画大字仍在    : %s  (本轮只改左上角，动画未动)' % (u'data-t=' + q + u'\u8f66\u5c0f\u667a' + q + u'>\u8f66\u5c0f\u667a' in t))
print(u'  ros.js 链路判据注入 : %s' % (u'\u8f66\u673a\u672a\u8fde\u63a5' in t and u'vehicleLive' in t))
print(u'  retry.js 软离线注入 : %s' % (u'r.soft' in t and u'\u6b64\u65f6\u9875\u9762\u4e0a\u7684\u6570\u503c\u662f\u4e0a\u4e00\u6b21\u7684\u7f13\u5b58' in t))
print(u'  离线版外部引用残留  : %d 处' % len(re.findall(r'(?:src|href)=' + q + r'https?://', t)))
print(u'  页面容器            : %d 个' % len(re.findall(r'class=' + q + 'page-content', t)))
print(u'  剩余「车小智」      : %d 处' % t.count(u'\u8f66\u5c0f\u667a'))
for m in re.finditer(u'\u8f66\u5c0f\u667a', t):
    s = max(0, m.start() - 60)
    print(u'      ...%s...' % t[s:m.start() + 40].replace(u'\n', u' '))

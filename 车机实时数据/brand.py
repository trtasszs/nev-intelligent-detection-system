# -*- coding: utf-8 -*-
"""品牌区改为「车小智 + 副标题」，并补一行资质小字、改浏览器标题"""
import io
import os
import re

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
t = io.open(P, encoding='utf-8').read()
n = 0

# ---- 1. 品牌区
NEW_BRAND = (
    u'<div class="flex items-center">\n'
    u'                    <div class="p-2 rounded-sm bg-primary bg-opacity-20 text-primary mr-2">\n'
    u'                        <i class="fa fa-car fa-lg"></i>\n'
    u'                    </div>\n'
    u'                    <div class="leading-tight">\n'
    u'                        <h1 class="text-xl font-bold text-white tracking-wide">'
    u'\u8f66\u5c0f\u667a</h1>\n'
    u'                        <p class="text-[10px] text-primary tracking-[.14em] mt-[2px]">'
    u'\u65b0\u80fd\u6e90\u6c7d\u8f66\u667a\u80fd\u68c0\u6d4b\u7cfb\u7edf</p>\n'
    u'                        <p class="text-[8px] text-gray-500 tracking-[.12em] mt-[1px]">'
    u'\u56fd\u6c7d\u667a\u8054 \u00b7 \u5947\u745e\u6c7d\u8f66 \u8054\u5408\u7814\u5236</p>\n'
    u'                    </div>\n'
    u'                </div>'
)
pat = re.compile(
    r'<div class="flex items-center">\s*'
    r'<div class="p-2 rounded-sm bg-primary bg-opacity-20 text-primary mr-2">\s*'
    r'<i class="fa fa-car fa-lg"></i>\s*</div>\s*'
    r'<h1 class="text-xl font-bold text-white">[^<]*</h1>\s*</div>', re.S)
t, k = pat.subn(NEW_BRAND, t, count=1)
n += k
print(u'品牌区替换: %d' % k)

# ---- 2. 浏览器标题
t2, k2 = re.subn(r'<title>[^<]*</title>',
                 u'<title>\u8f66\u5c0f\u667a \u00b7 \u65b0\u80fd\u6e90\u6c7d\u8f66\u667a\u80fd\u68c0\u6d4b\u7cfb\u7edf</title>',
                 t, count=1)
t = t2
n += k2
print(u'标题替换: %d' % k2)

# ---- 3. 顶栏副标题（页面右侧那条状态带里的小字）
t3, k3 = re.subn(r'(<span class="text-xs text-gray-500">)[^<]*(</span>)',
                 lambda m: m.group(1) + u'\u56fd\u6c7d\u667a\u8054 \u00b7 \u5947\u745e\u6c7d\u8f66 \u8054\u5408\u7814\u5236' + m.group(2),
                 t, count=1)
if k3:
    t = t3
    n += k3
    print(u'顶栏小字: %d' % k3)

io.open(P, 'w', encoding='utf-8').write(t)
print(u'共替换 %d 处 -> %s' % (n, P))

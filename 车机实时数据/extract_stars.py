# -*- coding: utf-8 -*-
"""挖参考件的三样：标识逐块拼装 assembleLogo / 档案方块群 watermark / 光标 caret。"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

REF = os.path.join(os.environ['TEMP'], 'cx-boot', 'ref2')
css = io.open(os.path.join(REF, 'lib', 'splash.css'), encoding='utf-8', errors='replace').read()
js = io.open(os.path.join(REF, 'lib', 'splash.js'), encoding='utf-8', errors='replace').read()

print(u'=== 1. CSS：watermark / logo 分块 / caret ===')
for m in re.finditer(r'([^{}]{0,180})\{([^{}]*)\}', css):
    sel = ' '.join(m.group(1).split())
    if re.search(r'(watermark|dsu-logo|dsu-wm|dsu-caret|dsu-blink|dsu-piece)', sel, re.I):
        print(u'  %s' % sel[-130:])
        print(u'      { %s }\n' % ' '.join(m.group(2).split())[:400])

print(u'=== 2. JS：assembleLogo 的完整实现 ===')
for m in list(re.finditer(r'assembleLogo', js))[:4]:
    a = max(0, m.start() - 500)
    b = min(len(js), m.end() + 1400)
    print(u'--- 第 %d 处 ---' % (list(re.finditer(r'assembleLogo', js)).index(m) + 1))
    print(js[a:b])
    print()

print(u'=== 3. JS：watermark 的构建 ===')
for m in list(re.finditer(r'watermark|dsu-wm', js))[:3]:
    a = max(0, m.start() - 500)
    b = min(len(js), m.end() + 1200)
    print(u'--- 第 %d 处 ---' % (list(re.finditer(r'watermark|dsu-wm', js)).index(m) + 1))
    print(js[a:b])
    print()

print(u'=== 4. JS：caret / blink 的用法 ===')
for m in list(re.finditer(r'caret|blink', js, re.I))[:6]:
    a = max(0, m.start() - 240)
    b = min(len(js), m.end() + 240)
    print(u'  …%s…' % ' '.join(js[a:b].split())[:400])

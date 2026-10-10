# -*- coding: utf-8 -*-
"""看对话区图片是怎么上传/发送的，以及诊断演示区的结构。"""
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

P = r'E:\！！！高职比赛\车小智.html'
t = io.open(P, encoding='utf-8').read()
L = t.split('\n')

print(u'===== 1. 图片读取/压缩（readImages 之类） =====')
for m in list(re.finditer(r'function\s+(\w*[Ii]mg\w*|\w*[Ii]mage\w*)\s*\(', t))[:8]:
    ln = t[:m.start()].count('\n')
    print(u'--- %s  (L%d) ---' % (m.group(1), ln + 1))
    for i in range(ln, min(len(L), ln + 22)):
        print(u'  %s' % L[i][:150])
    print()

print(u'===== 2. 送图到后端的地方（images 字段 / FormData） =====')
for kw in ('images', 'FormData', 'body:', 'fetch('):
    ms = list(re.finditer(re.escape(kw), t))
    print(u'  %-10s %d 次' % (kw, len(ms)))

print(u'\n===== 3. #demo 区完整结构（L2570~L2615） =====')
for i in range(2568, min(len(L), 2616)):
    print(u'  %4d | %s' % (i + 1, L[i][:150]))

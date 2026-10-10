# -*- coding: utf-8 -*-
"""把 cx-retry 那层（自动诊断面板）的 JS 完整挖出来。"""
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

P = r'E:\！！！高职比赛\新能源汽车智能检测系统-1.0版.html'
t = io.open(P, encoding='utf-8').read()

for key in ('cx-retry-panel', 'function schedule(', 'function run(', '开启自动', '自动诊断'):
    idx = t.find(key)
    print(u'=== %s  出现位置 %s ===' % (key, idx))

# 找 retry 那一段 script
i = t.find('cx-retry-panel')
# 往前找最近的 <script
s = t.rfind('<script', 0, i)
e = t.find('</script>', i)
print(u'\n  script 段：%d ~ %d  （%d 字符）' % (s, e, e - s))
if s > 0 and e > s:
    blk = t[s:e]
    io.open(r'C:\Users\ASUS\AppData\Local\Temp\retry.js', 'w', encoding='utf-8').write(blk)
    print(u'  已导出到 %%TEMP%%\\retry.js')
    # 只打印关键片段
    for kw in ('function schedule', 'function run', 'panel.classList', 'autoOpen', 'open(', 'close('):
        for m in list(re.finditer(re.escape(kw), blk))[:3]:
            a = max(0, m.start() - 200)
            b = min(len(blk), m.end() + 400)
            print(u'\n  --- 含 %s ---' % kw)
            print(u'  %s' % ' '.join(blk[a:b].split())[:560])

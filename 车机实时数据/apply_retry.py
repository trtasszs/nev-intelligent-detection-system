# -*- coding: utf-8 -*-
"""注入「重连诊断」按钮层（retry.js）"""
import io
import os
import re
import shutil
import time

SITE = r'E:\！！！高职比赛'
HERE = os.path.dirname(os.path.abspath(__file__))
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
JS = os.path.join(HERE, 'retry.js')
shutil.copy2(P, P + '.bak-retry-' + time.strftime('%Y%m%d-%H%M%S'))

t = io.open(P, encoding='utf-8').read()
n0 = len(t)
js = io.open(JS, encoding='utf-8').read().rstrip()

t, _ = re.subn(r'\s*<script id="cx-retry-js">.*?</script>', '', t, flags=re.S)
t, n1 = re.subn(r'(\s*</body>)',
                lambda m: ('\n    <!-- 页内重连诊断（调试用） -->\n'
                           '    <script id="cx-retry-js">\n' + js + '\n    </script>\n</body>'),
                t, count=1)
print(u'注入 retry.js: %d 处' % n1)

for k in (u'id="dashboard"', u'cx-can-js', u'cx-ros-js', u'cx-boot-js', u'</html>'):
    if k not in t:
        print(u'终检失败：缺少 %s —— 不写盘' % k)
        raise SystemExit(1)
if abs(len(t) - n0) > n0 * 0.12:
    print(u'体量异常 —— 不写盘')
    raise SystemExit(1)

io.open(P, 'w', encoding='utf-8').write(t)
print(u'页面 %d -> %d 字符' % (n0, len(t)))
print(u'层：' + u' '.join([x for x in (
    u'CAN' if u'cx-can-js' in t else u'',
    u'ROS' if u'cx-ros-js' in t else u'',
    u'RETRY' if u'cx-retry-js' in t else u'',
    u'FLOW' if u'cx-flow-js' in t else u'',
    u'MODE' if u'cx-mode-js' in t else u'',
    u'BOOT' if u'cx-boot-js' in t else u'') if x]))

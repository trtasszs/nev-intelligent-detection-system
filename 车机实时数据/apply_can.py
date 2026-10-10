# -*- coding: utf-8 -*-
"""
把 CAN 实时数据层注入看板。
- 复用 live.css 的样式类
- 移除旧的 ROS 数据层脚本（cx-live-js）
- 注入 can_live.js（cx-can-js）

    python apply_can.py
"""

import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)

_CAND = [
    u'新能源汽车智能检测系统-1.0版.html',
    u'新能源汽车智能检测系统-美化，实测改进版.html',
    u'新能源汽车智能检测系统.html',
]


def find_html():
    for c in _CAND:
        p = os.path.join(SITE, c)
        if os.path.isfile(p):
            return p
    import glob
    hits = [p for p in glob.glob(os.path.join(SITE, '*.html'))
            if u'智能检测系统' in os.path.basename(p) and u'原版' not in os.path.basename(p)]
    return max(hits, key=os.path.getmtime) if hits else os.path.join(SITE, _CAND[0])


HTML = find_html()
CSS = os.path.join(HERE, 'live.css')
JS = os.path.join(HERE, 'can_live.js')


def main():
    for p in (HTML, CSS, JS):
        if not os.path.isfile(p):
            print(u'  缺少文件：%s' % p)
            sys.exit(1)

    t = io.open(HTML, encoding='utf-8').read()
    css = io.open(CSS, encoding='utf-8').read().rstrip()
    js = io.open(JS, encoding='utf-8').read().rstrip()
    rep = []

    # 1. 样式层（幂等替换）
    if '<style id="cx-live-css">' in t:
        t, n = re.subn(r'<style id="cx-live-css">.*?</style>',
                       lambda m: '<style id="cx-live-css">\n' + css + '\n    </style>',
                       t, count=1, flags=re.S)
    else:
        t, n = re.subn(r'(\n</head>)',
                       lambda m: '\n    <style id="cx-live-css">\n' + css + '\n    </style>\n</head>',
                       t, count=1)
    rep.append(u'样式层: %d' % n)

    # 2. 移除旧的 ROS 数据层
    t, n1 = re.subn(r'\s*<script id="cx-live-js">.*?</script>', '', t, flags=re.S)
    rep.append(u'移除 ROS 数据层: %d' % n1)

    # 3. 注入 CAN 数据层
    t, n2 = re.subn(r'\s*<script id="cx-can-js">.*?</script>', '', t, flags=re.S)
    t, n3 = re.subn(r'(\s*</body>)',
                    lambda m: ('\n    <!-- CAN 实时数据层（创芯 CANalyst-II 直读整车CAN） -->\n'
                               '    <script id="cx-can-js">\n' + js + '\n    </script>\n</body>'),
                    t, count=1)
    rep.append(u'注入 CAN 数据层: %d' % n3)

    io.open(HTML, 'w', encoding='utf-8').write(t)
    print(u'  注入完成 -> %s' % HTML)
    for r in rep:
        print(u'   ·', r)
    print(u'   · 文件大小: %d 字节' % len(t.encode('utf-8')))


if __name__ == '__main__':
    main()

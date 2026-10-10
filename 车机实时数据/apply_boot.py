# -*- coding: utf-8 -*-
"""
把赛博朋克启动动画注入看板。
注入点在 <body> 之后 —— 这样页面一打开就立刻出现，不必等整页解析完。

    python apply_boot.py
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
JS = os.path.join(HERE, 'boot550.js')


def main():
    for p in (HTML, JS):
        if not os.path.isfile(p):
            print(u'  缺少文件：%s' % p)
            sys.exit(1)

    t = io.open(HTML, encoding='utf-8').read()
    js = io.open(JS, encoding='utf-8').read().rstrip()

    # 先移除旧的
    t, n0 = re.subn(r'\s*<script id="cx-boot-js">.*?</script>', '', t, flags=re.S)

    block = ('\n    <!-- 启动加载动画（赛博朋克风）· ?noboot=1 跳过 · ?boot=hold 定格 -->\n'
             '    <script id="cx-boot-js">\n' + js + '\n    </script>')

    # 注入点：<body ...> 之后
    t, n1 = re.subn(r'(<body[^>]*>)', lambda m: m.group(1) + block, t, count=1)
    if n1 == 0:
        print(u'  找不到 <body>，改为插在 </body> 前')
        t, n1 = re.subn(r'(\s*</body>)', lambda m: block + m.group(1), t, count=1)

    io.open(HTML, 'w', encoding='utf-8').write(t)
    print(u'  注入完成 -> %s' % HTML)
    print(u'   · 清理旧块: %d' % n0)
    print(u'   · 注入: %d' % n1)
    print(u'   · 文件大小: %d 字节' % len(t.encode('utf-8')))


if __name__ == '__main__':
    main()

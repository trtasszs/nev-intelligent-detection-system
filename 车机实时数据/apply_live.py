# -*- coding: utf-8 -*-
"""
把「车机实时数据」面板注入看板的【车辆信息管理】页。
幂等：可反复执行，每次用最新版本的 css/js 覆盖。

    python apply_live.py
"""

import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)

# 目标页面：用户可能会改名，按优先级自动识别
CANDIDATES = [
    u'新能源汽车智能检测系统-1.0版.html',
    u'新能源汽车智能检测系统-美化，实测改进版.html',
    u'新能源汽车智能检测系统.html',
]


def find_html():
    for c in CANDIDATES:
        p = os.path.join(SITE, c)
        if os.path.isfile(p):
            return p
    import glob
    hits = [p for p in glob.glob(os.path.join(SITE, "*.html"))
            if u"智能检测系统" in os.path.basename(p) and u"原版" not in os.path.basename(p)]
    if hits:
        return max(hits, key=os.path.getmtime)
    return os.path.join(SITE, CANDIDATES[0])


HTML = find_html()
CSS = os.path.join(HERE, "live.css")
JS = os.path.join(HERE, "live.js")

# 插入点：车辆信息管理页里"整车核心状态"之前
ANCHOR = '                    <!-- 整车核心状态 -->'
PANEL = ('                    <!-- 真实车机实时数据（由 ros_bridge.py 提供） -->\n'
         '                    <div id="cx-live" class="card cx-live mb-6"></div>\n\n')


def main():
    for p in (HTML, CSS, JS):
        if not os.path.isfile(p):
            print("  缺少文件：%s" % p)
            sys.exit(1)

    t = io.open(HTML, encoding="utf-8").read()
    css = io.open(CSS, encoding="utf-8").read().rstrip()
    js = io.open(JS, encoding="utf-8").read().rstrip()
    rep = []

    # ---- 1. 样式（整体替换，幂等） ----
    if '<style id="cx-live-css">' in t:
        t, n = re.subn(r'<style id="cx-live-css">.*?</style>',
                       lambda m: '<style id="cx-live-css">\n' + css + '\n    </style>',
                       t, count=1, flags=re.S)
    else:
        t, n = re.subn(r'(\n</head>)',
                       lambda m: '\n    <style id="cx-live-css">\n' + css + '\n    </style>\n</head>',
                       t, count=1)
    rep.append("样式层: %d" % n)

    # ---- 2. 面板容器（幂等） ----
    if 'id="cx-live"' not in t:
        if ANCHOR not in t:
            print("  找不到插入锚点（整车核心状态），中止")
            sys.exit(2)
        t = t.replace(ANCHOR, PANEL + ANCHOR, 1)
        rep.append("面板容器: 1")
    else:
        rep.append("面板容器: 已存在")

    # ---- 3. 脚本（先删旧再插，幂等） ----
    t = re.sub(r'\s*<script id="cx-live-js">.*?</script>', "", t, flags=re.S)
    t, n = re.subn(r'(\s*</body>)',
                   lambda m: '\n    <script id="cx-live-js">\n' + js + '\n    </script>\n</body>',
                   t, count=1)
    rep.append("脚本层: %d" % n)

    io.open(HTML, "w", encoding="utf-8").write(t)
    print("  注入完成 -> %s" % HTML)
    for r in rep:
        print("   ·", r)
    print("   · 文件大小: %d 字节" % len(t.encode("utf-8")))


if __name__ == "__main__":
    main()

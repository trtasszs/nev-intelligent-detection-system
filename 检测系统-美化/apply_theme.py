# -*- coding: utf-8 -*-
"""
把 theme.css / fx.js 注入「新能源汽车智能检测系统.html」。
可重复执行（幂等）：每次运行都会用最新版本覆盖注入内容。

    python apply_theme.py
"""

import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)                      # ！！！高职比赛

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
CSS = os.path.join(HERE, "theme.css")
JS = os.path.join(HERE, "fx.js")


def main():
    for p in (HTML, CSS, JS):
        if not os.path.isfile(p):
            print("  缺少文件：%s" % p)
            sys.exit(1)

    t = io.open(HTML, encoding="utf-8").read()
    css = io.open(CSS, encoding="utf-8").read().rstrip()
    js = io.open(JS, encoding="utf-8").read().rstrip()
    report = []

    # ---- 1. 主题样式层（整体替换，幂等） ----
    if '<style id="cx-theme">' in t:
        t, n = re.subn(r'<style id="cx-theme">.*?</style>',
                       lambda m: '<style id="cx-theme">\n' + css + '\n    </style>',
                       t, count=1, flags=re.S)
    else:
        t, n = re.subn(r'(\n</head>)',
                       lambda m: '\n    <!-- 仪器化看板主题层（由 检测系统-美化/apply_theme.py 注入） -->\n'
                                 '    <style id="cx-theme">\n' + css + '\n    </style>\n</head>',
                       t, count=1)
    report.append("主题样式层: %d" % n)

    # ---- 2. 动效层（先删旧的再插入，幂等） ----
    t = re.sub(r'\s*<script id="cx-fx">.*?</script>', "", t, flags=re.S)
    t, n = re.subn(r'(\s*</body>)',
                   lambda m: '\n    <!-- 看板动效层（零依赖） -->\n'
                             '    <script id="cx-fx">\n' + js + '\n    </script>\n</body>',
                   t, count=1)
    report.append("动效层: %d" % n)

    io.open(HTML, "w", encoding="utf-8").write(t)

    print("  注入完成 -> %s" % HTML)
    for r in report:
        print("   ·", r)
    print("   · 文件大小: %d 字节" % len(t.encode("utf-8")))


if __name__ == "__main__":
    main()

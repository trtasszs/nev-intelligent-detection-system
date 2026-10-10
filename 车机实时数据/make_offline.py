# -*- coding: utf-8 -*-
"""
把 3 个 CDN 依赖内嵌进看板，做成**完全离线可用**的单文件
------------------------------------------------------------------
现状：页面依赖 3 个 CDN（Tailwind / Chart.js / Font Awesome）。
      没有外网时页面会掉光样式（实测有内容像素 19.2% -> 4.6%）。
做法：把三份资源原样内嵌（JS/CSS 直接内联为文本，字体转 base64 写进 @font-face），
      体积从 342KB 增至约 1.1MB —— 本地文件完全可接受，换来零风险离线可用。
"""
import base64
import io
import os
import re
import shutil
import time

PAGE = r'E:\！！！高职比赛\新能源汽车智能检测系统-1.0版.html'
LIB = os.path.join(os.environ['TEMP'], 'cx-boot', 'lib')

CDN = {
    'tailwind': 'https://cdn.tailwindcss.com',
    'chart': 'https://cdn.jsdelivr.net/npm/chart.js@4.4.8/dist/chart.umd.min.js',
    'fa_css': 'https://cdn.jsdelivr.net/npm/font-awesome@4.7.0/css/font-awesome.min.css',
}


def read(p):
    return io.open(p, encoding='utf-8', errors='replace').read()


def fa_inline_css():
    """FA 的 CSS + 只保留 woff2 的 base64 内嵌字体

    ★坑：FA 4.7 的 @font-face 里有【两条 src:】——
      第一条是 eot（单独一行），第二条才是 woff2/woff/ttf/svg 的合并列表。
      如果只替换第一条，第二条会把内嵌的 woff2 覆盖掉，导致字体加载失败、
      所有图标变成空方框。正解是**整块 @font-face 重建**，只留 woff2。
    """
    css = read(os.path.join(LIB, 'fa.css'))
    woff2 = open(os.path.join(LIB, 'fa.woff2'), 'rb').read()
    b64 = base64.b64encode(woff2).decode('ascii')

    new_face = (u"@font-face{font-family:'FontAwesome';"
                u"src:url(data:font/woff2;base64,%s) format('woff2');"
                u"font-weight:normal;font-style:normal}" % b64)

    css2, n = re.subn(r'@font-face\s*\{[^}]*\}', new_face, css, count=1)
    if n == 0:
        raise SystemExit(u'[x] 没能定位 @font-face，放弃内嵌字体')
    # 复核：不能残留任何相对字体路径
    left = re.findall(r'url\([^)]*fonts/[^)]*\)', css2)
    if left:
        raise SystemExit(u'[x] 仍残留相对字体引用: %s' % left[:2])
    return css2, len(woff2)


def main():
    t = io.open(PAGE, encoding='utf-8').read()
    n0 = len(t)
    shutil.copy2(PAGE, PAGE + '.bak-offline-' + time.strftime('%Y%m%d-%H%M%S'))

    tw = read(os.path.join(LIB, 'tailwind.js'))
    chart = read(os.path.join(LIB, 'chart.umd.min.js'))
    fa, fsz = fa_inline_css()

    for name, blob in (('tailwind.js', tw), ('chart.umd.min.js', chart), ('fa.css', fa)):
        for tok in ('</script', '</style'):
            if tok in blob.lower():
                raise SystemExit(u'[x] %s 含 %s，不能内嵌' % (name, tok))

    # ---- 1. Tailwind ----
    t, n1 = re.subn(r'<script[^>]*src="[^"]*cdn\.tailwindcss\.com"[^>]*>\s*</script>',
                    lambda m: u'<script>/* Tailwind CSS (内嵌，离线可用) */\n' + tw + u'\n</script>',
                    t, count=1)
    # ---- 2. Chart.js ----
    t, n2 = re.subn(r'<script[^>]*src="[^"]*chart\.umd\.min\.js"[^>]*>\s*</script>',
                    lambda m: u'<script>/* Chart.js 4.4.8 (内嵌，离线可用) */\n' + chart + u'\n</script>',
                    t, count=1)
    # ---- 3. Font Awesome ----
    t, n3 = re.subn(r'<link[^>]*href="[^"]*font-awesome[^"]*"[^>]*>',
                    lambda m: u'<style>/* Font Awesome 4.7 (内嵌 + woff2 base64，离线可用) */\n' + fa + u'\n</style>',
                    t, count=1)

    print(u'  替换: Tailwind=%d  Chart.js=%d  FontAwesome=%d' % (n1, n2, n3))
    if not (n1 and n2 and n3):
        raise SystemExit(u'[x] 有资源没替换成功，不写盘')

    # 终检：不能残留 CDN 引用
    left = re.findall(r'(?:src|href)="(https?://[^"]*(?:tailwind|chart\.js|font-awesome)[^"]*)"', t)
    if left:
        raise SystemExit(u'[x] 仍残留 CDN 引用: %s' % left)

    for k in (u'id="dashboard"', u'</html>', u'cx-mode-js', u'cx-ros-js'):
        if k not in t:
            raise SystemExit(u'[x] 终检失败：缺 %s' % k)

    io.open(PAGE, 'w', encoding='utf-8').write(t)
    print(u'  FA 字体 woff2: %.0f KB -> base64 %.0f KB' % (fsz / 1024.0, fsz * 4 / 3 / 1024.0))
    print(u'  页面 %.0f KB -> %.0f KB' % (n0 / 1024.0, len(t) / 1024.0))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

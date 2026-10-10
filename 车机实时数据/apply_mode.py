# -*- coding: utf-8 -*-
"""
① 让 flow.js 的 canvas 跟随日/夜模式换色（Chart.js 之外的 canvas 同样管不到）
② 把 mode.js 注入页面

    python apply_mode.py
"""
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
F = os.path.join(HERE, 'flow.js')
M = os.path.join(HERE, 'mode.js')
shutil.copy2(P, P + '.bak-mode-' + time.strftime('%Y%m%d-%H%M%S'))

# ================= ① flow.js 跟随模式 =================
f = io.open(F, encoding='utf-8').read()
OLD_COLORS = u"var BLUE = '#3D9BFF', GREEN = '#2EE59D', AMBER = '#D4762A', RED = '#E0574A';"
NEW_COLORS = (
    u"// 日/夜模式取色（canvas 的颜色 CSS 管不到，只能在这里按模式取）\n"
    u"    function C() {\n"
    u"        var day = document.documentElement.dataset.cxMode === 'day';\n"
    u"        return day\n"
    u"            ? { BLUE: '#1E6FD9', GREEN: '#0E9F6E', AMBER: '#B8600F', RED: '#C93A2E',\n"
    u"                LINE: 'rgba(15,23,42,.18)', TXT: 'rgba(85,96,111,.9)', NODE: 'rgba(15,23,42,.35)' }\n"
    u"            : { BLUE: '#3D9BFF', GREEN: '#2EE59D', AMBER: '#D4762A', RED: '#E0574A',\n"
    u"                LINE: 'rgba(158,168,182,.16)', TXT: 'rgba(158,168,182,.75)', NODE: 'rgba(158,168,182,.5)' };\n"
    u"    }\n"
    u"    var BLUE = '#3D9BFF', GREEN = '#2EE59D', AMBER = '#D4762A', RED = '#E0574A';")
if u'function C()' not in f:
    if OLD_COLORS in f:
        f = f.replace(OLD_COLORS, NEW_COLORS)
        print(u'① flow.js 已加入模式取色函数')
    else:
        print(u'① 未找到 flow.js 颜色定义，跳过')
else:
    print(u'① flow.js 已支持模式（跳过）')

# 在绘制帧里按模式取值
if u'var M = C();' not in f:
    f = f.replace(u"        var N = nodes();\n        var midY = H * 0.42;",
                  u"        var M = C();\n        var N = nodes();\n        var midY = H * 0.42;")
    f = f.replace(u"var color = !S.ok ? RED : (S.fps > 300 ? BLUE : AMBER);",
                  u"var color = !S.ok ? M.RED : (S.fps > 300 ? M.BLUE : M.AMBER);")
    f = f.replace(u"ctx.strokeStyle = 'rgba(158,168,182,.16)';", u"ctx.strokeStyle = M.LINE;")
    f = f.replace(u"ctx.fillStyle = S.ok ? (i === 2 ? GREEN : BLUE) : 'rgba(158,168,182,.5)';",
                  u"ctx.fillStyle = S.ok ? (i === 2 ? M.GREEN : M.BLUE) : M.NODE;")
    f = f.replace(u"ctx.strokeStyle = (i === 2 ? 'rgba(46,229,157,.35)' : 'rgba(61,155,255,.3)');",
                  u"ctx.strokeStyle = (i === 2 ? 'rgba(14,159,110,.4)' : 'rgba(30,111,217,.35)');")
    f = f.replace(u"ctx.fillStyle = 'rgba(158,168,182,.75)';", u"ctx.fillStyle = M.TXT;")
    f = f.replace(u"ctx.fillStyle = S.ok ? (S.fps > 300 ? BLUE : AMBER) : RED;",
                  u"ctx.fillStyle = S.ok ? (S.fps > 300 ? M.BLUE : M.AMBER) : M.RED;")
    f = f.replace(u"ctx.strokeStyle = GREEN; ctx.lineWidth = 1.5; ctx.stroke();",
                  u"ctx.strokeStyle = M.GREEN; ctx.lineWidth = 1.5; ctx.stroke();")
    io.open(F, 'w', encoding='utf-8').write(f)
    print(u'① flow.js 绘制逻辑已接入模式取色')
else:
    print(u'① flow.js 绘制逻辑已接入（跳过）')
io.open(F, 'w', encoding='utf-8').write(f)

# ================= ② 注入 mode.js =================
t = io.open(P, encoding='utf-8').read()
n0 = len(t)
js = io.open(M, encoding='utf-8').read().rstrip()

t, _ = re.subn(r'\s*<script id="cx-mode-js">.*?</script>', '', t, flags=re.S)
# 放在 <head> 之后尽早执行，避免首帧闪白/闪黑；但需要 body 存在才挂按钮（脚本内已处理）
t, n1 = re.subn(r'(<head[^>]*>)',
                lambda m: m.group(1) + '\n    <!-- 日间/夜间模式 -->\n'
                          '    <script id="cx-mode-js">\n' + js + '\n    </script>',
                t, count=1)
print(u'② 注入 mode.js: %d 处' % n1)

for k in (u'id="dashboard"', u'cx-can-js', u'cx-boot-js', u'cx-flow-js', u'</html>'):
    if k not in t:
        print(u'终检失败：缺少 %s —— 不写盘' % k)
        raise SystemExit(1)
if abs(len(t) - n0) > n0 * 0.1:
    print(u'体量异常 —— 不写盘')
    raise SystemExit(1)

io.open(P, 'w', encoding='utf-8').write(t)
print(u'\n页面 %d -> %d 字符' % (n0, len(t)))

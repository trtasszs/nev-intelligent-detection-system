# -*- coding: utf-8 -*-
"""
修复日/夜模式的四个问题：
 1. 切换按钮空白 —— boot() 里 apply() 先于 mountBtn() 执行，按钮创建后没被赋值
 2. .btn-secondary 用的是 @apply，Tailwind 会把它编译成独立规则（不是 .bg-dark-200），
    所以 .bg-dark-* 的覆盖够不到它 → 日间下仍是黑底
 3. .cx-live__title 硬编码 color:#F2F2F5 → 日间白底上几乎看不见
 4. 数据管线画布容器是**内联** background:rgba(7,7,9,.55) → 日间呈灰条
"""
import io
import os

M = r'E:\！！！高职比赛\车机实时数据\mode.js'
t = io.open(M, encoding='utf-8').read()
n = 0

# ---------- 1. 按钮赋值顺序 ----------
OLD_BOOT = (u"    function boot() {\n"
            u"        apply(document.documentElement.dataset.cxMode);\n"
            u"        if (!mountBtn()) {")
NEW_BOOT = (u"    function boot() {\n"
            u"        // 先挂按钮再赋值，否则按钮建出来是空的\n"
            u"        if (!mountBtn()) {")
if OLD_BOOT in t:
    t = t.replace(OLD_BOOT, NEW_BOOT)
    n += 1

OLD_TAIL = (u"            var t = window.setInterval(function () {\n"
            u"                if (mountBtn() || ++tries > 20) window.clearInterval(t);\n"
            u"                else apply(document.documentElement.dataset.cxMode);\n"
            u"            }, 250);")
NEW_TAIL = (u"            var t = window.setInterval(function () {\n"
            u"                if (mountBtn() || ++tries > 20) window.clearInterval(t);\n"
            u"                apply(document.documentElement.dataset.cxMode);\n"
            u"            }, 250);")
if OLD_TAIL in t:
    t = t.replace(OLD_TAIL, NEW_TAIL)
    n += 1
# 挂完按钮后必须再 apply 一次
if u"        if (!mountBtn()) {\n            var tries" in t or u"        if (!mountBtn()) {" in t:
    # 在 boot 内、interval 块之后补一次 apply
    marker = u"        // 图表是异步初始化的，稍后再着一次色"
    if u"        apply(document.documentElement.dataset.cxMode);\n        // 图表是异步初始化的" not in t:
        t = t.replace(marker,
                      u"        apply(document.documentElement.dataset.cxMode);\n" + marker, 1)
        n += 1

# ---------- 2~4. 追加日间覆盖规则 ----------
EXTRA = u"""
        /* ---- @apply 编译出的独立规则（.bg-dark-* 覆盖够不到） ---- */
        'html[data-cx-mode="day"] .btn-secondary { background-color: #FFFFFF !important; color: #3A4552 !important; border-color: rgba(15,23,42,.14) !important; }',
        'html[data-cx-mode="day"] .btn-secondary:hover { background-color: #F1F4F8 !important; border-color: rgba(30,111,217,.4) !important; color: #1E6FD9 !important; }',
        /* ---- 硬编码的近白色，日间会看不见 ---- */
        'html[data-cx-mode="day"] .cx-live__title { color: #1A2230 !important; }',
        'html[data-cx-mode="day"] .cx-row__v { color: #1A2230 !important; }',
        'html[data-cx-mode="day"] .cx-big__n { color: #1A2230 !important; }',
        'html[data-cx-mode="day"] .cx-live__meta { color: #7C8798 !important; }',
        'html[data-cx-mode="day"] .cx-live__meta b { color: #1E6FD9 !important; }',
        /* ---- 数据管线画布容器：内联背景只能靠结构选择器压过去 ---- */
        'html[data-cx-mode="day"] #cx-flow-card > div[style] { background: #FFFFFF !important; border-color: rgba(15,23,42,.12) !important; }',
        'html[data-cx-mode="day"] #cx-flow-card canvas { background: #FFFFFF; }',
        /* ---- 其它面板容器 ---- */
        'html[data-cx-mode="day"] .cx-live { background-color: #FFFFFF !important; }',
        'html[data-cx-mode="day"] .cx-live__boxhd { border-bottom-color: rgba(15,23,42,.10) !important; }',
        'html[data-cx-mode="day"] .cx-live__head { border-bottom-color: rgba(15,23,42,.10) !important; }',
        'html[data-cx-mode="day"] .cx-livebadge { color: #1E6FD9 !important; background: rgba(30,111,217,.07) !important; border-color: rgba(30,111,217,.28) !important; }',
        'html[data-cx-mode="day"] .cx-livebadge i { background: #0E9F6E !important; }',
        'html[data-cx-mode="day"] .cx-filters button { color: #55606F !important; border-color: rgba(15,23,42,.14) !important; }',
        'html[data-cx-mode="day"] .cx-filters button.on { background: rgba(30,111,217,.10) !important; border-color: rgba(30,111,217,.45) !important; color: #1E6FD9 !important; }',
        'html[data-cx-mode="day"] .cx-cfg__k { color: #7C8798 !important; }',
        'html[data-cx-mode="day"] .cx-cfg__v { color: #1A2230 !important; }',
        'html[data-cx-mode="day"] .cx-chartbox__h { color: #55606F !important; }',
"""
anchor = u"        /* ---------------- 切换按钮 ---------------- */"
if u'@apply 编译出的独立规则' not in t and anchor in t:
    t = t.replace(anchor, EXTRA + anchor, 1)
    n += 1

io.open(M, 'w', encoding='utf-8').write(t)
print(u'mode.js 修补 %d 处' % n)
for k in (u'先挂按钮再赋值', u'@apply 编译出的独立规则', u'#cx-flow-card > div'):
    print(u'  %-28s %s' % (k, k in t))

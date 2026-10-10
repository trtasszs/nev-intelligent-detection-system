# -*- coding: utf-8 -*-
"""
告警框改红 —— 「CAN 采集未启动」这类警告应为红色（原来跟正文一样是蓝的，读不出警示）
同时给「说明性」提示留一个中性 is-info 变体，避免把"解码依据"这种说明也标成错误。
"""
import io
import os
import re

L = r'E:\！！！高职比赛\车机实时数据\live.css'
J = r'E:\！！！高职比赛\车机实时数据\can_live.js'

RED = u'#E0574A'
RED_BG = u'rgba(224, 87, 74, .09)'
RED_BD = u'rgba(224, 87, 74, .38)'

# ---------- live.css ----------
t = io.open(L, encoding='utf-8').read()
n = 0


def repl(m):
    global n
    n += 1
    return (u'.cx-live__warn {\n'
            u'    display: flex; align-items: center; gap: 8px;\n'
            u'    margin-top: 10px; padding: 7px 10px;\n'
            u'    background: ' + RED_BG + u'; border: 1px solid ' + RED_BD + u';\n'
            u'    font-size: 11px; color: ' + RED + u';\n'
            u'    border-left: none;\n'
            u'}')


t2 = re.sub(r'\.cx-live__warn\s*\{[^}]*\}', repl, t, count=1)
t = t2

ADD = u"""
/* ---- 告警 / 说明 两级提示 ---- */
/* 默认（告警）：红 */
.cx-live__warn i { color: """ + RED + u"""; }
/* 说明性提示：中性灰，别把"解码依据"这类也标成错误 */
.cx-live__warn.is-info {
    background: rgba(158, 168, 182, .07);
    border-color: rgba(158, 168, 182, .28);
    color: #9A9AA5;
}
.cx-live__warn.is-info i { color: #9A9AA5; }
/* 状态文字：链路异常时也变红 */
.cx-live.is-bad .cx-live__state { color: """ + RED + u"""; }
.cx-live.is-ok  .cx-live__state { color: var(--cx-gr); }
"""
if u'告警 / 说明 两级提示' not in t:
    t = t + ADD
io.open(L, 'w', encoding='utf-8').write(t)
print(u'live.css: 告警框改红 %d 处，已补 is-info / 状态文字变红' % n)

# ---------- can_live.js：把"解码依据"标为说明性 ----------
j = io.open(J, encoding='utf-8').read()
o = j
j = j.replace(u"el('div', 'cx-live__warn', '<i class=\"fa fa-info-circle\"></i>' +",
              u"el('div', 'cx-live__warn is-info', '<i class=\"fa fa-info-circle\"></i>' +")
j = j.replace(u"'<div class=\"cx-live__warn\" style=\"background:rgba(255,176,32,.07)\">'",
              u"'<div class=\"cx-live__warn is-info\">'")
io.open(J, 'w', encoding='utf-8').write(j)
print(u'can_live.js: 说明性提示标记 %s' % (u'已改' if j != o else u'未命中'))

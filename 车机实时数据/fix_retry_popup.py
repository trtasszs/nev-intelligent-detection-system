# -*- coding: utf-8 -*-
"""
修「重连诊断」面板自己弹出来遮挡视线的问题。
==================================================================
现象：检测系统右上角（right:22px / top:70px）的面板每 5 秒自己弹开一次，挡视线。

根因：render() 里无条件执行 `p.classList.add('on')`，而 render() 由**每一次 run()**
      调用 —— 包括 schedule() 每 5 秒跑的那个**静默自动刷新** run(true)。
      ⇒ 自动刷新本来只想更新按钮颜色，却顺手把面板拉开了。

修法：把"要不要打开面板"作为参数传下去 ——
      run(false)（点按钮 / 点刷新）→ 打开；
      run(true)（自动刷新、开页首次）→ 只更新按钮颜色，不打开。
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

P = r'E:\！！！高职比赛\车机实时数据\retry.js'
t = io.open(P, encoding='utf-8').read()
orig = t
n = 0

# 1) render 增加 openIt 形参
t2, c = re.subn(r'function render\(results\)\s*\{', 'function render(results, openIt) {', t, count=1)
if c:
    t = t2
    n += 1
    print(u'  [1] render(results) -> render(results, openIt)')

# 2) 无条件打开改成条件打开
t2, c = re.subn(r'(\n\s*)p\.classList\.add\(\'on\'\);',
                r"\1// 只有手动触发才拉开面板；自动刷新只更新按钮颜色，绝不弹窗遮挡\n\1if (openIt) p.classList.add('on');",
                t, count=1)
if c:
    t = t2
    n += 1
    print(u'  [2] p.classList.add(\'on\') -> if (openIt) ...')

# 3) 调用处把 silent 取反传进去
t2, c = re.subn(r'(\n\s*)render\(rs\);', r'\1render(rs, !silent);', t, count=1)
if c:
    t = t2
    n += 1
    print(u'  [3] render(rs) -> render(rs, !silent)')

# 4) 更新那段容易误读的注释
t = t.replace(u'// 打开页面先自动诊断一次，随后由 schedule() 自维持循环（开面板 2s / 关面板 5s）',
              u'// 打开页面先自动诊断一次（**静默**，只更新按钮颜色，不弹面板）\n'
              u'        // 随后由 schedule() 自维持：面板开着 2s 一次、关着 5s 一次，全程不打扰')
t = t.replace(u'// 面板开着就高频，关着就低频 —— 始终挂着，不用手动点',
              u'// 面板开着就高频，关着就低频 —— 始终挂着，不用手动点；自动刷新不会把面板弹出来')

io.open(P, 'w', encoding='utf-8').write(t)
print(u'  共改 %d 处，文件 %d -> %d 字符' % (n, len(orig), len(t)))

# 校验
t3 = io.open(P, encoding='utf-8').read()
checks = [
    (u'render 带 openIt 形参', 'function render(results, openIt)'),
    (u'条件打开面板', "if (openIt) p.classList.add('on');"),
    (u'调用处传 !silent', 'render(rs, !silent);'),
    (u'没有无条件 add(on)', "p.classList.add('on');" not in t3.replace("if (openIt) p.classList.add('on');", '')),
]
print(u'\n  校验:')
for name, ok in checks:
    print(u'    %-22s %s' % (name, u'✓' if ok else u'✗'))

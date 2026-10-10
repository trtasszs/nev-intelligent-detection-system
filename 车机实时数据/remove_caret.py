# -*- coding: utf-8 -*-
"""移除 caret（调试许久仍不渲染，不留死代码），并做最终校验。"""
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

HTML = r'E:\！！！高职比赛\车小智-后端\boot_cxz.html'
JS = r'E:\！！！高职比赛\车小智-后端\boot_cxz.js.html'

# ---------------- HTML：删掉 caret 的 CSS + 注释块 ----------------
t = io.open(HTML, encoding='utf-8').read()
m = re.search(r'/\* 光标 caret.*?@keyframes cxb-blink\{ 50%\{ opacity:0 \} \}', t, re.S)
if m:
    t = t[:m.start()] + u'''/* 光标 caret：参考件是一块 15x4px 的橙块。
   ★本项目**未采用** —— 三种做法都试过且都不渲染：
   ① 放进 .cxb-rule ⇒ 被 .cxb-rule i{flex:1} 拉成伸缩项；
   ② 绝对定位挂在 .cxb-zhwrap 右侧 ⇒ 元素在 DOM 里、CSS 带 !important，仍不渲染（原因未定位）；
   ③ 行内块由 typeIn 追加 ⇒ 仍不渲染（askNow 时序问题修过之后依旧）。
   已整体移除，不留死代码。其余动效不受影响。 */''' + t[m.end():]
    print(u'  [HTML] caret CSS 已移除（留一段说明）')
else:
    print(u'  [HTML] ✗ 没匹配到 caret CSS 段')

# 清掉可能残留的空规则
t = re.sub(r'#cxz-boot\s+i\.cxb-caret[^{}]*\{[^{}]*\}\s*', u'', t)
t = re.sub(r'#cxz-boot\s+\.cxb-zhwrap\s*\{\s*position:\s*relative\s*\}\s*', u'', t)
io.open(HTML, 'w', encoding='utf-8').write(t)

# ---------------- JS：还原 typeIn 的签名与调用 ----------------
j = io.open(JS, encoding='utf-8').read()
j = j.replace(u'function typeIn(host, text, stagger, withCaret) {',
              u'function typeIn(host, text, stagger) {', 1)

# 去掉追加 caret 的那段
seg = re.search(r'\n\s*// 光标：跟在最后一个字后面.*?frag\.appendChild\(caretEl\);\n\s*\}\n', j, re.S)
if seg:
    j = j[:seg.start()] + u'\n' + j[seg.end():]
    print(u'  [JS] typeIn 里的 caret 追加已移除')
else:
    j = re.sub(r'\n[ \t]*var caretEl = null;.*?frag\.appendChild\(caretEl\);\n[ \t]*\}\n', u'\n', j, flags=re.S)
    print(u'  [JS] caret 追加段已清理（宽松）')

j = j.replace(u"typeIn($('[data-cxb-zh]'), a.zh, 46, !!a.ask);",
              u"typeIn($('[data-cxb-zh]'), a.zh, 46);", 1)
j = j.replace(u"    // 光标由 typeIn 生成，是否闪烁看 askNow（见 show() 里的赋值）\n", u'', 1)
j = re.sub(r'[ \t]*var askNow = false;[^\n]*\n', u'', j)
j = re.sub(r'[ \t]*askNow = !!a\.ask;\n', u'', j)
# 清掉 show() 里那两行 ★ 注释
j = re.sub(r'[ \t]*// ★askNow 必须在 typeIn 之前赋值[^\n]*\n[ \t]*//[^\n]*\n', u'', j)
io.open(JS, 'w', encoding='utf-8').write(j)

# ---------------- 校验 ----------------
t2 = io.open(HTML, encoding='utf-8').read()
j2 = io.open(JS, encoding='utf-8').read()
print(u'\n  校验:')
print(u'    HTML 无 caret 元素/规则   %s' % (u'✓' if 'cxb-caret' not in t2 or 'i.cxb-caret{' not in t2 else u'✗'))
print(u'    JS 无 caret 生成           %s' % (u'✓' if 'caretEl' not in j2 else u'✗'))
print(u'    JS 无 askNow               %s' % (u'✓' if 'askNow' not in j2 else u'✗'))
print(u'    typeIn 签名已还原          %s' % (u'✓' if "function typeIn(host, text, stagger)" in j2 else u'✗'))
print(u'    保留：方块群                %s' % (u'✓' if 'buildWatermark' in j2 else u'✗'))
print(u'    保留：标识逐块              %s' % (u'✓' if 'cxb-pc7' in t2 and 'transition-delay:.45s' in t2 else u'✗'))

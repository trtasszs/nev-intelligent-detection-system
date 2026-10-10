# -*- coding: utf-8 -*-
"""
caret 最终方案：改成**普通行内块**，由 typeIn 在铺完字之后追加。
==================================================================
前面试过"绝对定位挂在标题右侧"，元素在 DOM 里、CSS 也在，但就是不渲染（原因未定位，
可能是 .cxb-center 的 transform 造成的包含块怪异）。不再往那个方向挖。

改成最朴素的做法：caret 是标题行里的一个 inline-block，紧跟在最后一个字后面
（这也正是参考件的做法 —— 它的 caret 就在 .dsu-status 那行里）。
代价：标题行会宽 15+8px，居中标题整体左移约 11px。这是一次性位移，不是逐字抖动，可接受。
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

HTML = r'E:\！！！高职比赛\车小智-后端\boot_cxz.html'
JS = r'E:\！！！高职比赛\车小智-后端\boot_cxz.js.html'

# ---------------- HTML：把 caret 从 zhwrap 里拿出来（由 JS 追加）----------------
t = io.open(HTML, encoding='utf-8').read()
m = re.search(r'<i class="cxb-caret" data-cxb-caret></i>', t)
if m:
    t = t[:m.start()] + t[m.end():]
    print(u'  [HTML] 已从 zhwrap 移除 caret（改由 JS 追加）')

NEW_CSS = u'''/* 光标 caret：参考件是一块 15x4px 的橙块，挂在**大字那一行**里（.dsu-status）。
   ★这个部件折腾了很久，记录试错：
   ① 放进 .cxb-rule 会被 .cxb-rule i{flex:1} 拉成伸缩项，width 失效；
   ② 改成绝对定位挂在 .cxb-zhwrap 右侧 —— 元素在 DOM 里、CSS 也带 !important，
      但**就是不渲染**（原因未定位，怀疑与 .cxb-center 的 transform 有关）；
   ③ 最终用最朴素的办法：**行内块，由 typeIn 在铺完字之后追加到标题行末尾** ——
      必定紧跟在最后一个字右边，也必定参与正常渲染。
   代价：标题行宽 15+8px，居中标题整体左移约 11px；一次性位移，不是逐字抖动。
   另外：只在**交互幕**亮（参考件 caret.toggle('dsu-on', action !== 'auto')）。 */
#cxz-boot i.cxb-caret{
  display:inline-block; width:15px; height:4px; background:var(--cxb-accent);
  margin-left:9px; vertical-align:middle; font-style:normal;
  opacity:0; transition:opacity .25s ease;
}
#cxz-boot i.cxb-caret.cxb-on{ opacity:1; animation:cxb-blink 1s steps(1,end) infinite }
@keyframes cxb-blink{ 50%{ opacity:0 } }'''

old = re.search(r'/\* 光标 caret.*?#cxz-boot i\.cxb-caret\.cxb-on\{[^}]*\}', t, re.S)
if old:
    t = t[:old.start()] + NEW_CSS + t[old.end():]
    print(u'  [HTML] caret CSS 已改为行内块版本')
io.open(HTML, 'w', encoding='utf-8').write(t)

# ---------------- JS：typeIn 在末尾追加 caret ----------------
j = io.open(JS, encoding='utf-8').read()

old_js = u"""  function typeIn(host, text, stagger) {
    if (!host) return;
    host.textContent = '';"""
new_js = u"""  function typeIn(host, text, stagger, withCaret) {
    if (!host) return;
    host.textContent = '';"""
if old_js in j:
    j = j.replace(old_js, new_js, 1)
    print(u'  [JS] typeIn 增加 withCaret 参数')
else:
    print(u'  [JS] ✗ typeIn 签名没匹配到')

old_tail = u"""    host.appendChild(frag);
    var t = setTimeout(function () {"""
new_tail = u"""    // 光标：跟在最后一个字后面（行内块，参与正常排版，必定渲染）
    var caretEl = null;
    if (withCaret) {
      caretEl = document.createElement('i');
      caretEl.className = 'cxb-caret';
      if (askNow) caretEl.classList.add('cxb-on');
      frag.appendChild(caretEl);
    }
    host.appendChild(frag);
    var t = setTimeout(function () {"""
if old_tail in j:
    j = j.replace(old_tail, new_tail, 1)
    print(u'  [JS] typeIn 末尾追加 caret')
else:
    print(u'  [JS] ✗ typeIn 尾部没匹配到')

# 调用处：中文标题带 caret（仅交互幕）
old_call = u"    typeIn($('[data-cxb-zh]'), a.zh, 46);"
new_call = u"    typeIn($('[data-cxb-zh]'), a.zh, 46, !!a.ask);"
if old_call in j:
    j = j.replace(old_call, new_call, 1)
    print(u'  [JS] 中文标题调用已带上 caret')

# typeIn 里引用的 askNow：用 show() 里的当前幕作判据
old_var = u"  var idx = -1, timer = null, waiting = false, finished = false;"
new_var = u"  var idx = -1, timer = null, waiting = false, finished = false;\n  var askNow = false;   // 当前幕是否交互幕（caret 据此决定闪不闪）"
if old_var in j and 'var askNow' not in j:
    j = j.replace(old_var, new_var, 1)
    print(u'  [JS] 增加 askNow 状态位')

old_set = u"    if (a.logo) root.classList.add('cxb-logoon');"
new_set = u"    if (a.logo) root.classList.add('cxb-logoon');\n    askNow = !!a.ask;"
if old_set in j and 'askNow = !!a.ask;' not in j:
    j = j.replace(old_set, new_set, 1)
    print(u'  [JS] show() 里更新 askNow')

# 去掉旧的 DOM 查询式 caret 逻辑（元素已不在 DOM 里）
old_q = u"""    // 光标只在**交互幕**闪（参考件 caret.toggle('dsu-on', action !== 'auto')）
    var cr = $('[data-cxb-caret]');
    if (cr) cr.classList.toggle('cxb-on', !!a.ask);
"""
if old_q in j:
    j = j.replace(old_q, u"    // 光标由 typeIn 生成，是否闪烁看 askNow（见 show() 里的赋值）\n", 1)
    print(u'  [JS] 已移除旧的 DOM 查询式 caret 逻辑')
elif "var cr = $('[data-cxb-caret]')" in j:
    j = re.sub(r"[ \t]*var cr = \$]\('\[data-cxb-caret\]'\);?\n", u"", j)
    print(u'  [JS] 旧 caret 查询已清理（宽松）')

io.open(JS, 'w', encoding='utf-8').write(j)

# ---------------- 校验 ----------------
t2 = io.open(HTML, encoding='utf-8').read()
j2 = io.open(JS, encoding='utf-8').read()
print(u'\n  校验:')
print(u'    HTML 里不再有 caret 元素   %s' % (u'✓' if '<i class="cxb-caret"' not in t2 else u'✗'))
print(u'    CSS 为行内块               %s' % (u'✓' if 'display:inline-block; width:15px; height:4px' in t2 else u'✗'))
print(u'    typeIn 带 withCaret        %s' % (u'✓' if 'function typeIn(host, text, stagger, withCaret)' in j2 else u'✗'))
print(u'    typeIn 追加 caret          %s' % (u'✓' if "caretEl.className = 'cxb-caret'" in j2 else u'✗'))
print(u'    中文标题带 caret           %s' % (u'✓' if "typeIn($('[data-cxb-zh]'), a.zh, 46, !!a.ask)" in j2 else u'✗'))
print(u'    askNow 状态位              %s' % (u'✓' if 'var askNow' in j2 else u'✗'))

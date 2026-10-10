# -*- coding: utf-8 -*-
"""
给车小智开机序列补三样动效（照参考件的做法）
==================================================================
1. 光标 caret —— 参考件 .dsu-caret 是 **15×4px 的橙色块**（不是细线），
   `steps(1,end)` 闪；而且**只在交互幕闪**（参考的 caret.toggle('dsu-on', action !== 'auto')）。
2. 右侧档案方块群 —— 参考件 .dsu-watermark 容器 + 若干 .dsu-wm 绝对定位矩形，
   样式是「白色渐变 + 发丝边框」，极淡，右侧若隐若现。
3. 中央标识**逐块拼装** —— 把车标拆成 7 个可独立动画的部件，
   按 地面线 → 车顶弧 → 左轮 → 右轮 → 三条信号弧 依次出现。

幂等：靠 BEGIN/END 标记包住补丁段落，重复执行不会叠加。

    python apply_fx2_cxz.py
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

HTML = r'E:\！！！高职比赛\车小智-后端\boot_cxz.html'
JS = r'E:\！！！高职比赛\车小智-后端\boot_cxz.js.html'

B_HTML = '<!-- ==== CXZ-FX2 BEGIN ==== -->'
E_HTML = '<!-- ==== CXZ-FX2 END ==== -->'
B_CSS = '/* ==== CXZ-FX2-CSS BEGIN ==== */'
E_CSS = '/* ==== CXZ-FX2-CSS END ==== */'

# ---------------------------------------------------------------- 1. 标识拆成 7 块
OLD_LOGO = u'''      <div class="cxb-logo" data-cxb-logo>
        <svg viewBox="0 0 64 40" aria-hidden="true">
          <path d="M8 30h48" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="square"/>
          <path d="M13 30c0-8 6-14 14-14h10c8 0 14 6 14 14" fill="none" stroke="currentColor" stroke-width="2.4"/>
          <circle cx="22" cy="30" r="4" fill="none" stroke="currentColor" stroke-width="2.4"/>
          <circle cx="42" cy="30" r="4" fill="none" stroke="currentColor" stroke-width="2.4"/>
          <path d="M32 3v7M22 6l3 6M42 6l-3 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="square"/>
        </svg>
        <span class="cxb-logolabel">CHE XIAO ZHI</span>
      </div>'''

NEW_LOGO = u'''      <div class="cxb-logo" data-cxb-logo>
        <svg viewBox="0 0 64 40" aria-hidden="true">
          <path class="cxb-pc cxb-pc1" d="M8 30h48" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="square"/>
          <path class="cxb-pc cxb-pc2" d="M13 30c0-8 6-14 14-14h10c8 0 14 6 14 14" fill="none" stroke="currentColor" stroke-width="2.4"/>
          <circle class="cxb-pc cxb-pc3" cx="22" cy="30" r="4" fill="none" stroke="currentColor" stroke-width="2.4"/>
          <circle class="cxb-pc cxb-pc4" cx="42" cy="30" r="4" fill="none" stroke="currentColor" stroke-width="2.4"/>
          <path class="cxb-pc cxb-pc5" d="M32 3v7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="square"/>
          <path class="cxb-pc cxb-pc6" d="M22 6l3 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="square"/>
          <path class="cxb-pc cxb-pc7" d="M42 6l-3 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="square"/>
        </svg>
        <span class="cxb-logolabel">CHE XIAO ZHI</span>
      </div>'''


def patch_html():
    t = io.open(HTML, encoding='utf-8').read()
    before = len(t)

    # (a) 标识拆块
    if OLD_LOGO in t:
        t = t.replace(OLD_LOGO, NEW_LOGO, 1)
    elif 'cxb-pc1' not in t:
        print(u'  ✗ 找不到标识 SVG，跳过拆块')

    # (b) 光标 caret：插在英文副标题后面（同一行内）
    if 'data-cxb-caret' not in t:
        m = re.search(r'(<span data-cxb-en></span>)', t)
        if m:
            t = t[:m.end()] + u'\n        <i class="cxb-caret" data-cxb-caret></i>' + t[m.end():]
        else:
            print(u'  ✗ 找不到英文副标题锚点，caret 未插入')

    # (c) 档案方块群容器：放在底部三栏之前
    if 'data-cxb-wm' not in t:
        anchor = u'    <!-- 底部三栏 -->'
        if anchor in t:
            t = t.replace(anchor,
                          B_HTML + u'\n    <div class="cxb-watermark" data-cxb-wm></div>\n    ' + E_HTML + u'\n'
                          + anchor, 1)
    t = t.replace(B_HTML + u'\n' + B_HTML, B_HTML)  # 防重
    io.open(HTML, 'w', encoding='utf-8').write(t)
    print(u'  HTML: %.0f -> %.0f 字符' % (before / 1024.0 * 1024 / 1024 * 1024 * 0 + len(t) / 1024.0 * 0 + before, len(t)))
    return t


def patch_css(t):
    css = u"""
""" + B_CSS + u"""
/* ---------- 光标 caret（参考件 .dsu-caret）
   注意它是一块 **15×4px 的橙色方块**，不是常见的那种 1px 细线；
   而且**只在交互幕闪**（参考件是 caret.toggle('dsu-on', action !== 'auto')）。 */
#cxz-boot .cxb-caret{
  display:inline-block; width:15px; height:4px; background:var(--cxb-accent);
  transform:translateY(-3px); margin-left:8px; opacity:0; vertical-align:middle;
}
#cxz-boot .cxb-caret.cxb-on{ opacity:1; animation:cxb-blink 1s steps(1,end) infinite }
@keyframes cxb-blink{ 50%{ opacity:0 } }

/* ---------- 右侧档案方块群（参考件 .dsu-watermark + .dsu-wm）
   极淡的白色渐变 + 发丝边框，像背景里若隐若现的档案面板。 */
#cxz-boot .cxb-watermark{ position:absolute; inset:0; opacity:0; pointer-events:none; z-index:2;
  transition:opacity 900ms ease }
#cxz-boot.cxb-paperon .cxb-watermark{ opacity:1 }
#cxz-boot .cxb-wm{
  position:absolute; background:linear-gradient(180deg, rgba(255,255,255,.55), rgba(255,255,255,0));
  border:1px solid rgba(10,10,10,.07); opacity:0; transform:translateY(8px);
  transition:opacity 700ms ease, transform 700ms cubic-bezier(.16,.84,.24,1);
}
#cxz-boot .cxb-wm.cxb-wmon{ opacity:1; transform:none }

/* ---------- 标识逐块拼装：7 个部件依次出现 ---------- */
#cxz-boot .cxb-pc{ opacity:0; transform:scale(.86); transform-origin:32px 24px;
  transition:opacity 320ms ease, transform 380ms cubic-bezier(.2,.85,.3,1) }
#cxz-boot.cxb-logoon .cxb-pc{ opacity:1; transform:none }
#cxz-boot.cxb-logoon .cxb-pc1{ transition-delay:.00s }
#cxz-boot.cxb-logoon .cxb-pc2{ transition-delay:.09s }
#cxz-boot.cxb-logoon .cxb-pc3{ transition-delay:.18s }
#cxz-boot.cxb-logoon .cxb-pc4{ transition-delay:.24s }
#cxz-boot.cxb-logoon .cxb-pc5{ transition-delay:.33s }
#cxz-boot.cxb-logoon .cxb-pc6{ transition-delay:.39s }
#cxz-boot.cxb-logoon .cxb-pc7{ transition-delay:.45s }
""" + E_CSS + u'\n'

    # ★ 关键修复（2026-10-09）：补丁 CSS 必须落在 <style>…</style> **之内**。
    #   旧版是 t.rstrip() + css，即把 CSS 追加到文件末尾 —— 正好落在 </style> 之后。
    #   被 apply_boot_cxz.py 整块注入页面后，这段 CSS 不在任何 <style> 里，
    #   浏览器就把整段源码当**正文文本**渲染出来（页面顶部糊一大段 CSS 源码），
    #   而且方块群 / 标识逐块拼装 / @keyframes cxb-blink 全部不生效。
    #   现改成：先无条件摘掉旧块，再插到最后一个 </style> 之前（幂等 + 能自愈已坏的文件）。
    if B_CSS in t:
        t = re.sub(re.escape(B_CSS) + r'.*?' + re.escape(E_CSS) + r'\n?', u'', t, count=1, flags=re.S)

    i = t.rfind(u'</style>')
    if i < 0:
        raise SystemExit(u'  ✗ boot_cxz.html 里找不到 </style>，补丁 CSS 无处安放')
    t = t[:i].rstrip() + u'\n' + css.strip(u'\n') + u'\n' + t[i:]

    io.open(HTML, 'w', encoding='utf-8').write(t)
    return t


def patch_js():
    t = io.open(JS, encoding='utf-8').read()
    before = len(t)

    # (a) 光标只在交互幕亮
    if 'cxb-caret' not in t:
        old = u"""    // 中央标识装配（参考件的 assembleLogo）：某一幕把标识"装"到中央，之后一直留着
    if (a.logo) root.classList.add('cxb-logoon');"""
        new = u"""    // 中央标识装配（参考件的 assembleLogo）：某一幕把标识"装"到中央，之后一直留着
    // 部件是逐块出现的，靠 CSS 的 transition-delay 错开（地面线→车顶弧→双轮→信号弧）
    if (a.logo) root.classList.add('cxb-logoon');
    // 光标只在**交互幕**闪（参考件 caret.toggle('dsu-on', action !== 'auto')）
    var cr = $('[data-cxb-caret]');
    if (cr) cr.classList.toggle('cxb-on', !!a.ask);"""
        if old in t:
            t = t.replace(old, new, 1)
        else:
            print(u'  ✗ JS 锚点没找到，caret 逻辑未接')

    # (b) 生成档案方块群
    if 'buildWatermark' not in t:
        old2 = u"""  /* ---------- 浮尘粒子 ----------"""
        gen = u"""  /* ---------- 右侧档案方块群 ----------
     参考件 .dsu-watermark：右侧若干极淡的"档案面板"方块，白色渐变 + 发丝边框。
     尺寸与位置取一组固定值（不用随机，避免每次开机位置都变），按 100ms 错开淡入。 */
  (function buildWatermark() {
    var host = $('[data-cxb-wm]');
    if (!host) return;
    var boxes = [
      { l: 55, t: 10, w: 15, h: 26 },
      { l: 73, t:  6, w: 19, h: 15 },
      { l: 62, t: 40, w: 26, h: 12 },
      { l: 84, t: 26, w: 12, h: 34 },
      { l: 57, t: 60, w: 18, h: 20 },
      { l: 78, t: 66, w: 16, h: 24 },
      { l: 68, t: 86, w: 24, h:  9 }
    ];
    for (var i = 0; i < boxes.length; i++) {
      var b = boxes[i];
      var d = document.createElement('div');
      d.className = 'cxb-wm';
      d.style.left = b.l + '%';
      d.style.top = b.t + '%';
      d.style.width = b.w + '%';
      d.style.height = b.h + '%';
      d.setAttribute('data-wm', String(i));
      host.appendChild(d);
    }
    // 逐块淡入
    setTimeout(function () {
      var all = $$('[data-wm]');
      all.forEach(function (el, i) {
        setTimeout(function () { if (el.parentNode) el.classList.add('cxb-wmon'); }, i * 100);
      });
    }, 400);
  })();

  /* ---------- 浮尘粒子 ----------"""
        if old2 in t:
            t = t.replace(old2, gen, 1)
        else:
            print(u'  ✗ JS 锚点 2 没找到，方块群未生成')

    t = t.replace(before and '' or '', '')
    io.open(JS, 'w', encoding='utf-8').write(t)
    print(u'  JS: %d -> %d 字符' % (before, len(t)))
    return t


def main():
    t = patch_html()
    t = patch_css(t)
    patch_js()
    t2 = io.open(HTML, encoding='utf-8').read()
    j2 = io.open(JS, encoding='utf-8').read()
    print(u'  标记块: HTML %d（应为 1）  CSS %d（应为 1）' % (t2.count(B_HTML), t2.count(B_CSS)))
    # ★ 自检：补丁 CSS 必须落在 <style> 之内，否则浏览器会把整段源码当正文渲染出来
    bi = t2.find(B_CSS)
    inside = bi >= 0 and t2.rfind(u'<style', 0, bi) > t2.rfind(u'</style>', 0, bi)
    print(u'    %-18s %s' % (u'CSS 在 style 内', u'✓' if inside else u'✗ 会被渲染成可见文本！'))
    for k, v, src in ((u'光标 caret', 'data-cxb-caret', t2),
                      (u'caret 样式', '.cxb-caret', t2),
                      (u'方块群容器', 'data-cxb-wm', t2),
                      (u'方块样式', '.cxb-wm', t2),
                      (u'标识拆 7 块', 'cxb-pc7', t2),
                      (u'逐块错开', 'transition-delay:.45s', t2),
                      (u'caret 只在交互幕', "toggle('cxb-on', !!a.ask)", j2),
                      (u'方块生成器', 'buildWatermark', j2)):
        print(u'    %-18s %s' % (k, u'✓' if v in src else u'✗'))


if __name__ == '__main__':
    main()

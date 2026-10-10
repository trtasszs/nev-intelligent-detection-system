# -*- coding: utf-8 -*-
"""
注入数据管线粒子层（flow.js），并移除「事先背板」式装饰：
  · #particleBackground（原页面的装饰性粒子画布，与数据无关）
  · 卡片顶边的扫描流光（预先编排的装饰动画）
保留真正由数据驱动的：数值跳动高亮、在线状态点呼吸、数据管线粒子。

    python apply_flow.py
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
L = os.path.join(HERE, 'live.css')
JS = os.path.join(HERE, 'flow.js')
shutil.copy2(P, P + '.bak-flow-' + time.strftime('%Y%m%d-%H%M%S'))

t = io.open(P, encoding='utf-8').read()
js = io.open(JS, encoding='utf-8').read().rstrip()
n0 = len(t)

# ---- 1. 注入脚本
t, _ = re.subn(r'\s*<script id="cx-flow-js">.*?</script>', '', t, flags=re.S)
t, n1 = re.subn(r'(\s*</body>)',
                lambda m: ('\n    <!-- 数据管线粒子层（真实数据驱动） -->\n'
                           '    <script id="cx-flow-js">\n' + js + '\n    </script>\n</body>'),
                t, count=1)
print(u'注入 flow.js: %d 处' % n1)

# ---- 2. 移除装饰性粒子背板
n2 = t.count(u'id="particleBackground"')
t = re.sub(r'<div id="particleBackground"[^>]*></div>', u'', t)
print(u'移除装饰性粒子背板: %d 处' % n2)

# ---- 3. 移除卡片扫描流光（预先编排的装饰动画）
t, n3 = re.subn(r'/\* 1\) 卡片顶边 1px 数据流光.*?\.page-content \.card:nth-of-type\(5n\)::after\s*\{[^}]*\}\n',
                u'', t, flags=re.S)
t, n3b = re.subn(r'@keyframes cx-flow\s*\{.*?\n\}\n', u'', t, flags=re.S)
print(u'移除卡片扫描流光: %d + %d 处' % (n3, n3b))

# ---- 校验
for k in (u'id="dashboard"', u'cx-can-js', u'cx-boot-js', u'</html>'):
    if k not in t:
        print(u'终检失败：缺少 %s —— 不写盘' % k)
        raise SystemExit(1)
if abs(len(t) - n0) > n0 * 0.1:
    print(u'体量异常 —— 不写盘')
    raise SystemExit(1)

io.open(P, 'w', encoding='utf-8').write(t)
print(u'\n页面 %d -> %d 字符' % (n0, len(t)))

# ---- 4. live.css 侧：删掉卡片流的样式（若在 css 里）
if os.path.isfile(L):
    c = io.open(L, encoding='utf-8').read()
    c2 = re.sub(r'/\* 1\) 卡片顶边 1px 数据流光.*?\.page-content \.card:nth-of-type\(5n\)::after\s*\{[^}]*\}\n', u'', c, flags=re.S)
    c2 = re.sub(r'@keyframes cx-flow\s*\{.*?\n\}\n', u'', c2, flags=re.S)
    if c2 != c:
        io.open(L, 'w', encoding='utf-8').write(c2)
        print(u'live.css 已清理卡片流光样式')
    else:
        print(u'live.css 无卡片流光样式')
print(u'完成')

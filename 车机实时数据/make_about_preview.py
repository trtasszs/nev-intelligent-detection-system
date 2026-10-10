# -*- coding: utf-8 -*-
"""生成 about 页的预览副本：加载后自动点开「关于我们」"""
import io
import os

P = r'E:\！！！高职比赛\新能源汽车智能检测系统-1.0版.html'
OUT = os.path.join(os.environ['TEMP'], 'cx-boot', 'about_page.html')

t = io.open(P, encoding='utf-8').read()

# 用 join 拼，避免任何引号转义问题
sel = 'a[data-target=' + chr(34) + 'about' + chr(34) + ']'
inj = (
    '\n<script>\n'
    'window.addEventListener("load", function () {\n'
    '  setTimeout(function () {\n'
    '    var a = document.querySelector(' + repr(sel) + ');\n'
    '    if (a) { a.click(); }\n'
    '  }, 800);\n'
    '});\n'
    '</script>\n</body>'
)

t2 = t.replace('</body>', inj, 1)
io.open(OUT, 'w', encoding='utf-8').write(t2)
print(u'  预览页: %s' % OUT)
print(u'  注入的 JS 选择器: %s' % sel)

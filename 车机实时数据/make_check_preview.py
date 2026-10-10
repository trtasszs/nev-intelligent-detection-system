# -*- coding: utf-8 -*-
"""生成预览副本：加载后自动点开「重连诊断」面板，便于检查链路状态显示"""
import io
import os

P = r'E:\！！！高职比赛\新能源汽车智能检测系统-1.0版.html'
OUT = os.path.join(os.environ['TEMP'], 'cx-boot', 'check_page.html')

t = io.open(P, encoding='utf-8').read()
inj = (
    '\n<script>\n'
    'window.addEventListener("load", function () {\n'
    '  setTimeout(function () {\n'
    '    var b = document.getElementById("cx-retry-btn");\n'
    '    if (b) b.click();\n'
    '  }, 2600);\n'
    '});\n'
    '</script>\n</body>'
)
io.open(OUT, 'w', encoding='utf-8').write(t.replace('</body>', inj, 1))
print(u'  预览页: %s' % OUT)

# -*- coding: utf-8 -*-
"""提取 HTML 里的内联 <script> 块，交给 node --check 逐个验语法。
★为什么要这么验：页面是 1MB+ 单文件、库都内联在里面，
  改完 JS 光看是看不出来的，必须真让 JS 引擎解析一遍。
"""
import io
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

PAGE = r'E:\！！！高职比赛\车小智.html'
TMP = os.path.join(os.environ['TEMP'], 'cxz_js_check')
os.makedirs(TMP, exist_ok=True)


def find_node():
    for p in (r'E:\ds\node.exe', r'C:\Program Files\nodejs\node.exe'):
        if os.path.exists(p):
            return p
    return None


page = io.open(PAGE, encoding='utf-8', errors='replace').read()
blocks = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', page, re.S | re.I)
print(u'页面 %d KB，内联 script 块 %d 个' % (len(page) / 1024, len(blocks)))

node = find_node()
if not node:
    print(u'找不到 node.exe，跳过语法检查')
    sys.exit(0)
print(u'node: %s' % node)

bad = 0
for i, code in enumerate(blocks):
    if len(code.strip()) < 40:
        continue
    f = os.path.join(TMP, 'block%02d.js' % i)
    io.open(f, 'w', encoding='utf-8').write(code)
    r = subprocess.run([node, '--check', f], capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    tag = u'OK  ' if r.returncode == 0 else u'✗ 语法错'
    if r.returncode != 0:
        bad += 1
    print(u'  块 %02d (%6d 字节): %s' % (i, len(code), tag))
    if r.returncode != 0:
        for line in (r.stderr or '').splitlines()[:6]:
            print(u'        ' + line)

print(u'\n结论：%d 个块有语法错误' % bad)

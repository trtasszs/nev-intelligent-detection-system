# -*- coding: utf-8 -*-
"""
把「车小智 · 开机序列」注入 车小智.html
==================================================================
设计成幂等：已注入过就先摘掉旧的再插新的，重复跑不会叠加。
注入点：<body ...> 之后紧接着，保证它是页面第一个可见层。

    python apply_boot_cxz.py

来源文件（改这两个，别直接改页面 —— 下次跑本脚本会被覆盖回去）
    boot_cxz.html      结构 + 样式
    boot_cxz.js.html   序列引擎
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE = r'E:\！！！高职比赛'
PAGE = os.path.join(BASE, '车小智.html')
SRC_HTML = os.path.join(BASE, '车小智-后端', 'boot_cxz.html')
SRC_JS = os.path.join(BASE, '车小智-后端', 'boot_cxz.js.html')

BEGIN = '<!-- ==== CXZ-BOOT BEGIN（由 apply_boot_cxz.py 注入，勿手改）==== -->'
END = '<!-- ==== CXZ-BOOT END ==== -->'


def main():
    page = io.open(PAGE, encoding='utf-8').read()
    frag = io.open(SRC_HTML, encoding='utf-8').read()
    js = io.open(SRC_JS, encoding='utf-8').read()

    # 1) 摘掉旧块
    removed = 0
    if BEGIN in page:
        pat = re.compile(re.escape(BEGIN) + r'.*?' + re.escape(END), re.S)
        page, n = pat.subn('', page)
        removed = n
    # 兼容早期没有标记的残留
    if '<div id="cxz-boot"' in page:
        pat2 = re.compile(r'<div id="cxz-boot".*?</script>\s*', re.S)
        page, n2 = pat2.subn('', page, count=1)
        removed += n2

    if removed:
        print(u'  已摘除旧的开机序列块 %d 处' % removed)

    block = '\n'.join([BEGIN, frag, js, END, ''])

    # 2) 插到 <body> 之后
    m = re.search(r'<body[^>]*>', page, re.I)
    if not m:
        print(u'  ✗ 页面里找不到 <body>')
        return 2
    at = m.end()
    page = page[:at] + '\n' + block + page[at:]

    io.open(PAGE, 'w', encoding='utf-8', newline='').write(page)

    size = os.path.getsize(PAGE)
    print(u'  ✓ 已注入 %s' % PAGE)
    print(u'     页面大小 %.0f KB' % (size / 1024.0))
    print(u'     结构 %d 字节 · 引擎 %d 字节' % (len(frag), len(js)))

    # 3) 自检
    chk = io.open(PAGE, encoding='utf-8').read()
    for name, needle in ((u'开机层容器', 'id="cxz-boot"'),
                         (u'样式块', '.cxb-reticle'),
                         (u'引擎', 'CXZ-BOOT'),
                         (u'第1幕文案', u'需要访问许可'),
                         (u'末幕文案', u'核验通过')):
        print(u'     %-10s %s' % (name, u'✓' if needle in chk else u'✗'))
    print(u'     注入块数量 = %d（应为 1）' % chk.count(BEGIN))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

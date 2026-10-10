# -*- coding: utf-8 -*-
"""重打车小智.zip 并核验。"""
import hashlib
import io
import os
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8')

B = r'E:\！！！高职比赛'
D = r'E:\AI输出\桌面版程序\车小智'
PK = r'E:\AI输出\桌面版程序-发布包'


def is_log(n):
    return (u'日志' in n) or n.endswith('.log')


zp = os.path.join(PK, u'车小智.zip')
if os.path.exists(zp):
    os.remove(zp)
n = 0
with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for root, dirs, files in os.walk(D):
        for f in files:
            if is_log(f):
                continue
            fp = os.path.join(root, f)
            z.write(fp, os.path.relpath(fp, D))
            n += 1
print(u'  车小智.zip  %.1f MB  %d 个文件' % (os.path.getsize(zp) / 1048576.0, n))

src = os.path.join(B, u'车小智.html')
h0 = hashlib.sha256(io.open(src, 'rb').read()).hexdigest()[:16]
with zipfile.ZipFile(zp) as z:
    inner = [x for x in z.namelist() if x.endswith(u'车小智.html')][0]
    page = z.read(inner).decode('utf-8', 'replace')
    hp = hashlib.sha256(z.read(inner)).hexdigest()[:16]
    print(u'  页面 sha256  源=%s 包内=%s -> %s' % (h0, hp, u'一致 ✓' if h0 == hp else u'不一致 ✗'))
    checks = [
        (u'演示区上传按钮', 'data-demo-img-btn'),
        (u'演示区缩略图条', 'data-demo-img-strip'),
        (u'演示区粘贴支持', 'data-demo-img-input'),
        (u'diagnose 带 images', 'images: (window.__demoImages'),
        (u'结果卡展示', 'window.renderDemoResultImages'),
        (u'跨块调用带判断', 'if (window.renderDemoResultImages)'),
        (u'开机层仍在', 'id="cxz-boot"'),
    ]
    for k, v in checks:
        print(u'     %-18s %s' % (k, u'✓' if v in page else u'✗'))
    print(u'     使用说明 %s   包内日志 %s' % (
        u'✓' if any(x.endswith(u'使用说明.txt') for x in z.namelist()) else u'✗',
        [x for x in z.namelist() if is_log(os.path.basename(x))] or u'无 ✓'))
    print(u'     顶层: %s' % u', '.join(sorted(set(x.split('/')[0] for x in z.namelist()))[:6]))

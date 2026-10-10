# -*- coding: utf-8 -*-
"""全屏扫橙色像素，定位 caret 到底在哪（或根本不存在）。"""
import glob
import os
import sys

from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

D = os.path.join(os.environ['TEMP'], 'cx-boot', 'v13')
for f in sorted(glob.glob(os.path.join(D, 'c*.png'))):
    im = Image.open(f).convert('RGB')
    W, H = im.size
    px = im.load()
    pts = [(x, y, px[x, y]) for y in range(0, H, 2) for x in range(0, W, 2)
           if px[x, y][0] > 180 and 60 < px[x, y][1] < 190 and px[x, y][2] < 110]
    print(u'  %-14s 全屏橙色像素 %3d' % (os.path.basename(f), len(pts)))
    if pts:
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        print(u'       分布 x %d~%d  y %d~%d' % (min(xs), max(xs), min(ys), max(ys)))
        # 取最集中的一簇
        from collections import Counter
        c = Counter((p[0] // 40, p[1] // 40) for p in pts)
        (bx, by), n = c.most_common(1)[0]
        print(u'       最密一簇在 x~%d y~%d（%d 个点）' % (bx * 40, by * 40, n))
        box = (max(0, bx * 40 - 120), max(0, by * 40 - 60), min(W, bx * 40 + 160), min(H, by * 40 + 80))
        im.crop(box).resize(((box[2] - box[0]) * 3, (box[3] - box[1]) * 3), Image.LANCZOS).save(
            os.path.join(D, 'caret-zoom.png'))
        print(u'       已存 caret-zoom.png  (裁剪区 %s)' % (box,))
        break
else:
    print(u'\n  六帧全屏都没有橙色 ✗ —— caret 根本没渲染')
    # 顺便看看橙色的调色板到底有没有（比如被压成了灰色）
    im = Image.open(sorted(glob.glob(os.path.join(D, 'c*.png')))[0]).convert('RGB')
    W, H = im.size
    a = im.crop((int(W * 0.30), int(H * 0.40), int(W * 0.95), int(H * 0.56)))
    a.resize((a.width * 2, a.height * 2), Image.LANCZOS).save(os.path.join(D, 'wide-zoom.png'))
    print(u'  已存 wide-zoom.png（标题右侧到屏幕右缘）')

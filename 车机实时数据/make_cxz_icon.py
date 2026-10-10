# -*- coding: utf-8 -*-
"""生成「车小智」图标（多尺寸 .ico），存放于 E 盘，供桌面快捷方式引用。"""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = r'E:\！！！高职比赛\车小智-后端\车小智.ico'
INK = (10, 10, 12, 255)          # 墨底
CY = (61, 155, 255, 255)         # 科技蓝
CY_D = (30, 92, 153, 255)
GR = (46, 229, 157, 255)         # 安全绿
TX = (232, 232, 236, 255)

FONTS = [r'C:\Windows\Fonts\msyhbd.ttc', r'C:\Windows\Fonts\msyh.ttc',
         r'C:\Windows\Fonts\simhei.ttf', r'C:\Windows\Fonts\arialbd.ttf']


def font(size):
    for f in FONTS:
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, size)
            except Exception:
                continue
    return ImageFont.load_default()


def draw(size):
    S = size * 8                       # 超采样后缩放，边缘更干净
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    # 墨色底 + 直角（整体方角，符合既有风格）
    pad = int(S * 0.045)
    d.rectangle([pad, pad, S - pad, S - pad], fill=INK)

    # 科技蓝内描边
    b = max(2, int(S * 0.018))
    d.rectangle([pad, pad, S - pad, S - pad], outline=CY, width=b)
    # 四角加粗（HUD 括号感）
    c = int(S * 0.20)
    t = max(3, int(S * 0.035))
    for (x0, y0, x1, y1) in ((pad, pad, pad + c, pad + t), (pad, pad, pad + t, pad + c),
                             (S - pad - c, pad, S - pad, pad + t), (S - pad - t, pad, S - pad, pad + c),
                             (pad, S - pad - t, pad + c, S - pad), (pad, S - pad - c, pad + t, S - pad),
                             (S - pad - c, S - pad - t, S - pad, S - pad), (S - pad - t, S - pad - c, S - pad, S - pad)):
        d.rectangle([x0, y0, x1, y1], fill=CY)

    # 中央「智」字
    f = font(int(S * 0.60))
    txt = u'智'
    bb = d.textbbox((0, 0), txt, font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.text(((S - tw) / 2 - bb[0], (S - th) / 2 - bb[1] - int(S * 0.02)), txt, font=f, fill=TX)

    # 右上角安全绿状态点
    r = int(S * 0.075)
    cx, cy = int(S * 0.795), int(S * 0.205)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GR)

    return im.resize((size, size), Image.LANCZOS)


sizes = [256, 128, 64, 48, 32, 24, 16]
imgs = [draw(s) for s in sizes]
imgs[0].save(OUT, format='ICO', sizes=[(s, s) for s in sizes], append_images=imgs[1:])
print(u'图标已生成: %s  (%d 字节, 尺寸 %s)' % (OUT, os.path.getsize(OUT), sizes))

# 顺带存一张 png 预览，方便看
prev = os.path.join(os.path.dirname(OUT), 'preview', u'车小智图标预览.png')
os.makedirs(os.path.dirname(prev), exist_ok=True)
sheet = Image.new('RGBA', (256 + 128 + 64 + 48 + 32 + 24 + 16 + 7 * 12, 256), (18, 18, 22, 255))
x = 0
for s in sizes:
    im = draw(s)
    sheet.paste(im, (x, 256 - s), im)
    x += s + 12
sheet.save(prev)
print(u'预览已存: %s' % prev)

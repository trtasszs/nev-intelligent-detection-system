# -*- coding: utf-8 -*-
"""
生成车小智 / 检测软件的图标（一套，风格统一）
==================================================================
之前两个图标不一致：一个蓝框内缩成环、一个贴边；绿点位置和字号比例也不同。
这里用同一套几何重画：
  · 切角方形底（直角/切角，符合既有视觉规则）
  · 同厚度的科技蓝描边
  · 同光学比例的中文字
  · 同一位置的绿色状态点
  · 底部一条蓝色基线，做出"仪表"感
输出多尺寸 .ico（16/24/32/48/64/128/256）。

    python make_icons.py
"""
import io
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding='utf-8')

INK = (7, 7, 9, 255)            # --cx-ink 家族
BLUE = (61, 155, 255, 255)      # 科技蓝
GREEN = (46, 229, 157, 255)     # 安全绿
TILE = 1024                     # 先在 1024 上画，再缩小


def find_font():
    for p in (r'C:\Windows\Fonts\msyhbd.ttc', r'C:\Windows\Fonts\msyh.ttc',
              r'C:\Windows\Fonts\simhei.ttf', r'C:\Windows\Fonts\msyhbd.ttf'):
        if os.path.exists(p):
            return p
    raise SystemExit('找不到中文字体')


def cut_rect(size, inset, cut):
    """切角方形（四角各切掉 cut 像素）"""
    a, b = inset, size - inset
    return [(a + cut, a), (b - cut, a), (b, a + cut), (b, b - cut),
            (b - cut, b), (a + cut, b), (a, b - cut), (a, a + cut)]


def build(ch):
    im = Image.new('RGBA', (TILE, TILE), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pad = int(TILE * 0.055)          # 外留白，避免贴边被裁
    cut = int(TILE * 0.085)          # 切角尺寸 —— 原来 0.16 太大，看着像八边形，不是"切角方形"
    bw = int(TILE * 0.040)           # 蓝框厚度

    # 蓝色外板（描边作用）
    d.polygon(cut_rect(TILE, pad, cut), fill=BLUE)
    # 墨色内板，内缩一个框厚
    d.polygon(cut_rect(TILE, pad + bw, cut), fill=INK)

    # 底部基线（仪表感）
    ly = int(TILE * 0.795)
    lx0, lx1 = int(TILE * 0.245), int(TILE * 0.755)
    d.rectangle([lx0, ly, lx1, ly + int(TILE * 0.020)], fill=BLUE)

    # 中文字，按光学比例居中（中文字面略低于几何中心，往上提一点）
    fpath = find_font()
    fs = int(TILE * 0.520)
    font = ImageFont.truetype(fpath, fs)
    box = d.textbbox((0, 0), ch, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    tx = (TILE - tw) / 2 - box[0]
    ty = (TILE * 0.445) - th / 2 - box[1]
    d.text((tx, ty), ch, font=font, fill=(242, 242, 245, 255))

    # 右上状态点
    r = int(TILE * 0.062)
    cx, cy = int(TILE * 0.780), int(TILE * 0.222)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GREEN)
    return im


def main():
    base = r'E:\！！！高职比赛'
    outs = [
        (u'智', os.path.join(base, u'车小智-后端', u'车小智.ico')),
        (u'检', os.path.join(base, u'检测系统.ico')),
    ]
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    for ch, path in outs:
        im = build(ch)
        im.save(path, format='ICO', sizes=sizes)
        # 同步一份 256 png 方便肉眼检查
        png = os.path.splitext(path)[0] + u'-预览.png'
        im.resize((256, 256), Image.LANCZOS).save(png)
        print(u'  ✓ %s   %d B   尺寸档 %s' % (path, os.path.getsize(path), sizes))
        print(u'     预览 %s' % png)


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""
三张队员照统一化处理（让它像一套，而不是贴上去的）
------------------------------------------------------------------
1. 用「黄色安全帽」自动定位头部 -> 裁出统一头肩比例（帽顶留白一致、人脸居中）
2. 白底 -> 换成与页面同源的墨色渐变（白底在深色页上会发亮、显脏）
3. 统一色调与暗角，三张读起来是一套
"""
import io
import os
import base64
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

NEW = os.path.join(r'C:\Users\ASUS\.dsh\attachments\v1\objects',
                   '')  # 基目录
IDS = [r'82\8264c55b16b68892de381dd3ab5a32b760e2337bdd816aacfc40b771d48459cc',
       r'86\86cf95e9ef3236e3446a5c5c755ed03e06c939c986b1d9067470a5e99efe2982',
       r'b2\b204e43788ef6fdb0008709d3de5910609391919e87f5a9b62be896b3d024939']

OUT_W, OUT_H = 560, 700          # 4:5
HAT_W_FRAC = 0.455               # 安全帽宽度占画幅宽的比例（三张统一）
HAT_TOP_FRAC = 0.075             # 帽顶距画幅顶部的比例
INK_TOP = (17, 20, 26)           # 墨色渐变（上）
INK_BOT = (9, 10, 13)            # 墨色渐变（下）


def _is_yellow(r, g, b):
    """安全帽那种高饱和镭射黄；收紧判据，避免把皮肤/白底暖色算进来"""
    return r > 185 and g > 140 and b < 115 and (r - b) > 110 and (g - b) > 55


def helmet_bbox(im):
    """只取「从顶部往下连续的那一段黄色」作为安全帽。
    直接对全图取黄色包围盒会把脸/脖子也算进去（实测误差 3 倍）。"""
    small = im.resize((max(1, im.width // 4), max(1, im.height // 4)))
    px = small.load()
    rows = {}
    for y in range(small.height):
        xs = [x for x in range(small.width) if _is_yellow(*px[x, y][:3])]
        if len(xs) >= 2:
            rows[y] = (min(xs), max(xs), len(xs))
    if not rows:
        return None
    ys = sorted(rows)
    band = [ys[0]]
    for y in ys[1:]:
        if y - band[-1] <= 3:          # 允许小空档
            band.append(y)
        else:
            break
    if len(band) < 3:                  # 太薄，不可信
        return None
    x0 = min(rows[y][0] for y in band)
    x1 = max(rows[y][1] for y in band)
    return (x0 * 4, band[0] * 4, (x1 + 1) * 4, (band[-1] + 1) * 4)


def safe_crop_box(im, bb):
    """按**安全帽宽度**算裁剪框。
    为什么不用帽高：三张照片机位远近不同，且帽子佩戴姿态不同（中间那张帽子架得高），
    帽高与脸的比例在每张里并不一致 —— 用帽高归一化后中间那张脸仍明显偏大。
    帽宽≈头宽，且帽子是硬物，跨照片更稳。"""
    hx0, hy0, hx1, hy1 = bb
    hw = max(1, hx1 - hx0)                 # 帽宽 = 尺度基准
    hcx = (hx0 + hx1) / 2.0
    cw = int(hw / HAT_W_FRAC)              # 帽宽占画幅宽的比例
    ch = int(cw * OUT_H / float(OUT_W))
    top = int(hy0 - ch * HAT_TOP_FRAC)      # 帽顶上方留白（按画幅高）
    left = int(hcx - cw / 2.0)
    cw = min(cw, im.width);  ch = min(ch, im.height)
    cw = max(cw, 1);         ch = max(ch, 1)
    left = max(0, min(left, im.width - cw))
    top = max(0, min(top, im.height - ch))
    return (left, top, left + cw, top + ch)


def grade(im):
    """统一色调：略降饱和 + 轻微提对比，三张观感一致"""
    im = ImageEnhance.Color(im).enhance(0.92)
    im = ImageEnhance.Contrast(im).enhance(1.04)
    return im


def tone_unify(im):
    """统一色调（**全局**处理，不做抠图）。
    棚拍白底本身是干净的证件照质感，硬抠会留下锯齿边，比白底更难看。
    这里只做两件事：① 把刺眼的纯白往冷调柔白压一档，减弱在深色页面上的割裂感；
    ② 轻微统一肤色与对比。全程整体混色，不产生边缘artifact。"""
    # ① 整体向冷灰混 9%，纯白 255 -> 约 232 的冷白
    cool = Image.new('RGB', im.size, (196, 206, 221))
    im = Image.blend(im, cool, 0.11)
    # ② 略微收一点高光，避免白底发亮
    im = ImageEnhance.Brightness(im).enhance(0.975)
    im = ImageEnhance.Color(im).enhance(1.02)
    im = ImageEnhance.Contrast(im).enhance(1.03)
    return im


def vignette(im, strength=0.34):
    """暗角：中心保留原图，四周轻压暗。
    注意 composite(im, dark, mask) 里 mask=255 取 im、mask=0 取 dark，
    所以 mask 必须「中心 255、边缘 255*(1-strength)」——反过来会把中心压黑。"""
    w, h = im.size
    v = Image.new('L', (w, h), 0)
    ImageDraw.Draw(v).ellipse([-w * 0.24, -h * 0.20, w * 1.24, h * 1.20], fill=255)
    v = v.filter(ImageFilter.GaussianBlur(int(min(w, h) * 0.18)))
    a = v.point(lambda p: 255 - int((255 - p) * strength))
    return Image.composite(im, Image.new('RGB', (w, h), (0, 0, 0)), a)


def build(src, idx):
    im = Image.open(src).convert('RGB')
    bb = helmet_bbox(im)
    if not bb:
        print('   [x] 第 %d 张没找到安全帽，改用居中方框' % idx)
        cw = int(im.width * 0.7); ch = int(cw * OUT_H / float(OUT_W))
        left = (im.width - cw) // 2; top = int(im.height * 0.04)
        box = (left, top, left + cw, top + ch)
    else:
        box = safe_crop_box(im, bb)
    im = im.crop(box).resize((OUT_W, OUT_H), Image.LANCZOS)
    im = tone_unify(im)
    im = vignette(im, strength=0.16)      # 很轻，只是收边
    return im


def b64(im):
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=86, optimize=True, progressive=True)
    return base64.b64encode(buf.getvalue()).decode('ascii'), len(buf.getvalue())


if __name__ == '__main__':
    os.makedirs(os.environ['TEMP'] + r'\cx-boot\team', exist_ok=True)
    store = {}
    for i, rel in enumerate(IDS, 1):
        im = build(os.path.join(NEW, rel), i)
        b, sz = b64(im)
        store[i] = b
        p = os.environ['TEMP'] + r'\cx-boot\team\t%d.jpg' % i
        im.save(p, quality=92)
        print('  MEMBER 0%d -> %d KB  %s' % (i, sz // 1024, p))
    # 三联预览
    trio = Image.new('RGB', (OUT_W * 3 + 40, OUT_H + 20), (10, 10, 12))
    for i in range(1, 4):
        trio.paste(Image.open(os.environ['TEMP'] + r'\cx-boot\team\t%d.jpg' % i),
                   ((i - 1) * (OUT_W + 10) + 10, 10))
    trio.save(os.environ['TEMP'] + r'\cx-boot\team_trio.png')
    print('  三联预览:', os.environ['TEMP'] + r'\cx-boot\team_trio.png')
    # 存 base64 供下一步替换
    with io.open(os.environ['TEMP'] + r'\cx-boot\team_b64.txt', 'w', encoding='utf-8') as f:
        for i in range(1, 4):
            f.write(store[i] + '\n')
    print('  base64 已存')

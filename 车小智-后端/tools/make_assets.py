# -*- coding: utf-8 -*-
"""
车小智 · 赛博视觉素材生成器 v2
================================================
纯标准库，运行后在 assets/cyber/ 下生成全部 SVG 素材：

    python tools/make_assets.py                  # 默认输出到 ..\\assets\\cyber
    python tools/make_assets.py D:\\out\\cyber     # 指定输出目录

设计语言（v2）：
    · 直角切角面板 + 1px 发丝线，取代圆角卡片 + 泛光描边
    · 真实 HUD 构件：四角括号、边缘刻度尺、等宽字模块编号、序列号
    · 辉光只留给"热"元素（状态点、数据包），其余靠线条精度取胜
    · 全部带 SMIL 动画，作为 <img> 嵌入时也会动

素材清单：
    hero-hud.svg         首屏主视觉：整车诊断控制台（车辆线稿 + 引线标注 + 扫描 + 数据包）
    hero-bg.svg          首屏背景：透视网格 + 地平线光带 + 电路走线
    can-topology.svg     CAN 网络拓扑图（可下载、可打印）
    circuit-divider.svg  章节分隔：带刻度的技术尺
    noise.svg            胶片颗粒（叠加用，去塑料感）
    favicon.svg          站点图标
"""

import math
import os
import sys

# ---------------------------------------------------------------- 主题色
CY = "#35E0FF"        # 主强调：冷青
CY_D = "#0E7C99"      # 青·暗
CY_L = "#A8F2FF"      # 青·亮
GR = "#7CFFB2"        # 次强调：薄荷绿（成功态）
AM = "#FFB020"        # 警示
RD = "#FF4D6D"        # 危险
BG0 = "#05070C"
BG1 = "#0A1018"
BG2 = "#0E1622"
HAIR = "rgba(120,200,255,.14)"
TXT = "#E6F0FA"
TXT_M = "#8FA6BE"
TXT_L = "#5A6E86"
MONO = "JetBrains Mono, Consolas, Menlo, monospace"
CJK = "Microsoft YaHei, PingFang SC, Noto Sans CJK SC, sans-serif"


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# ---------------------------------------------------------------- 几何工具
def ch(x, y, w, h, c=16, corners="tl,tr,br,bl"):
    """切角矩形路径（cut-corner panel）。corners 取 tl/tr/br/bl 的逗号组合。"""
    cs = set(corners.split(","))
    tl = c if "tl" in cs else 0
    tr = c if "tr" in cs else 0
    br = c if "br" in cs else 0
    bl = c if "bl" in cs else 0
    f = lambda v: ("%g" % v)
    d = ["M%s %s" % (f(x + tl), f(y))]
    d.append("H%s" % f(x + w - tr))
    d.append("L%s %s" % (f(x + w), f(y + tr)))
    d.append("V%s" % f(y + h - br))
    d.append("L%s %s" % (f(x + w - br), f(y + h)))
    d.append("H%s" % f(x + bl))
    d.append("L%s %s" % (f(x), f(y + h - bl)))
    d.append("V%s" % f(y + tl))
    d.append("L%s %s" % (f(x + tl), f(y)))
    d.append("Z")
    return "".join(d)


def glow(fid, dev=6, extra=1):
    merge = "".join("<feMergeNode in='b'/>" for _ in range(extra))
    return (f"<filter id='{fid}' x='-70%' y='-70%' width='240%' height='240%'>"
            f"<feGaussianBlur stdDeviation='{dev}' result='b'/>"
            f"<feMerge>{merge}<feMergeNode in='SourceGraphic'/></feMerge></filter>")


def ticks(x1, x2, y, n, major=14, minor=6, color=CY, op=".35", step=1):
    out = []
    span = x2 - x1
    for i in range(n + 1):
        x = x1 + span * i / n
        big = (i % step == 0)
        out.append("<path d='M%g %gV%g' stroke='%s' stroke-opacity='%s' stroke-width='1'/>"
                   % (x, y, y - (major if big else minor), color, op))
    return "".join(out)


def segmented(x, y, w, h, total, filled, color, gap=3):
    """分段电平条。"""
    out = []
    seg = (w - gap * (total - 1)) / total
    for i in range(total):
        xx = x + i * (seg + gap)
        on = i < filled
        out.append("<rect x='%.1f' y='%g' width='%.1f' height='%g' fill='%s' fill-opacity='%s'/>"
                   % (xx, y, seg, h, color if on else CY, ".85" if on else ".10"))
    return "".join(out)


# ================================================================ 1. 首屏主视觉
def hero_hud():
    W, H = 1280, 760
    s = ["<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1280 760' width='1280' height='760' "
         "font-family='%s' role='img' aria-label='整车诊断控制台'>" % MONO]
    s.append("<defs>"
             + glow("g-cy", 5, 1) + glow("g-gr", 4, 1)
             + f"<linearGradient id='lg-scan' x1='0' y1='0' x2='0' y2='1'>"
               f"<stop offset='0' stop-color='{CY}' stop-opacity='0'/>"
               f"<stop offset='.5' stop-color='{CY}' stop-opacity='.55'/>"
               f"<stop offset='1' stop-color='{CY}' stop-opacity='0'/></linearGradient>"
             + f"<linearGradient id='lg-fill' x1='0' y1='0' x2='0' y2='1'>"
               f"<stop offset='0' stop-color='#132032' stop-opacity='.95'/>"
               f"<stop offset='1' stop-color='{BG1}' stop-opacity='.97'/></linearGradient>"
             + f"<pattern id='pt-fine' width='24' height='24' patternUnits='userSpaceOnUse'>"
               f"<path d='M24 0H0V24' fill='none' stroke='{CY}' stroke-opacity='.055' stroke-width='1'/>"
               f"</pattern>"
             + "</defs>")
    s.append("<style>"
             ".k{fill:" + TXT_L + ";font-size:10px;letter-spacing:.22em}"
             ".v{fill:" + CY_L + ";font-size:13px;letter-spacing:.08em}"
             ".n{fill:" + TXT + ";font-size:26px;letter-spacing:.06em}"
             ".t{fill:" + TXT_M + ";font-size:11px;letter-spacing:.16em}"
             ".c{fill:" + TXT_M + ";font-size:10px;letter-spacing:.1em}"
             "@keyframes sw{0%{transform:translateY(0)}100%{transform:translateY(560px)}}"
             ".sw{animation:sw 5.2s linear infinite}"
             "</style>")

    # ---- 外框（切角 + 发丝 + 颗粒网格）----
    s.append("<path d='%s' fill='url(#lg-fill)'/>" % ch(6, 6, W - 12, H - 12, 22, "tl,br"))
    s.append("<path d='%s' fill='url(#pt-fine)'/>" % ch(6, 6, W - 12, H - 12, 22, "tl,br"))
    s.append("<path d='%s' fill='none' stroke='%s' stroke-width='1.4'/>" % (ch(6, 6, W - 12, H - 12, 22, "tl,br"), CY))
    s.append("<path d='%s' fill='none' stroke='%s' stroke-opacity='.35'/>" % (ch(12, 12, W - 24, H - 24, 17, "tl,br"), CY))

    # 四角括号
    for (x, y, dx, dy) in ((30, 30, 1, 1), (W - 30, 30, -1, 1), (30, H - 30, 1, -1), (W - 30, H - 30, -1, -1)):
        s.append("<path d='M%g %gH%gM%g %gV%g' stroke='%s' stroke-width='2' stroke-opacity='.85'/>"
                 % (x + dx * 26, y, x, x, y, y + dy * 26, CY))

    # ---- 顶栏 ----
    s.append("<path d='M6 62H1274' stroke='%s'/>" % HAIR)
    s.append("<circle cx='40' cy='34' r='4.5' fill='%s' filter='url(#g-gr)'>"
             "<animate attributeName='opacity' values='1;.25;1' dur='2.4s' repeatCount='indefinite'/></circle>" % GR)
    s.append("<text x='56' y='31' class='t'>VEHICLE DIAGNOSTIC CONSOLE</text>")
    s.append("<text x='56' y='47' class='k'>整车诊断控制台 · CHXZ-OS v1.0</text>")
    s.append("<text x='1224' y='31' class='k' text-anchor='end'>SYS 09:41:23</text>")
    s.append("<text x='1224' y='47' class='k' text-anchor='end' fill='%s'>LINK OK</text>" % GR)

    # ---- 左栏：系统扫描 ----
    LX, LW = 34, 196
    s.append("<text x='%g' y='90' class='k'>SYSTEM SCAN</text>" % LX)
    s.append("<path d='M%g 100H%g' stroke='%s'/>" % (LX, LX + LW, HAIR))
    rows = [("BMS", "电池管理", 86, CY), ("MCU", "电机控制", 72, CY), ("OBC", "车载充电", 64, GR),
            ("VCU", "整车控制", 93, CY), ("EPS", "电动转向", 48, AM)]
    for i, (code, cn, val, col) in enumerate(rows):
        y = 126 + i * 52
        s.append("<text x='%g' y='%g' class='v'>%s</text>" % (LX, y, code))
        s.append("<text x='%g' y='%g' class='k'>%s</text>" % (LX + 46, y, cn))
        s.append("<text x='%g' y='%g' class='k' text-anchor='end'>%d%%</text>" % (LX + LW, y, val))
        s.append(segmented(LX, y + 10, LW, 6, 16, round(val / 100 * 16), col))
    s.append("<path d='M%g 400H%g' stroke='%s'/>" % (LX, LX + LW, HAIR))
    s.append("<text x='%g' y='420' class='k'>BUS LOAD</text>" % LX)
    s.append("<rect x='%g' y='430' width='%g' height='8' fill='%s' fill-opacity='.12'/>" % (LX, LW, CY))
    s.append("<rect x='%g' y='430' width='%g' height='8' fill='%s' fill-opacity='.75'>"
             "<animate attributeName='width' values='%g;%g;%g' dur='6s' repeatCount='indefinite'/></rect>"
             % (LX, LW * 0.42, CY, LW * 0.42, LW * 0.86, LW * 0.42))
    for i in range(5):
        s.append("<text x='%g' y='%g' class='k'>0x%02X</text>" % (LX, 466 + i * 20, 0xA0 + i * 0x17))
    s.append("<text x='%g' y='%g' class='k' text-anchor='end'>DTC FRAME</text>" % (LX + LW, 466))

    # ---- 右栏：总线与读数 ----
    RX, RW = 1050, 196
    s.append("<text x='%g' y='90' class='k'>CAN BUS WAVEFORM</text>" % RX)
    s.append("<path d='M%g 100H%g' stroke='%s'/>" % (RX, RX + RW, HAIR))
    s.append("<rect x='%g' y='110' width='%g' height='96' fill='%s' fill-opacity='.55' stroke='%s'/>"
             % (RX, RW, BG0, HAIR))
    pts = []
    for i in range(0, 97):
        x = RX + 6 + i * (RW - 12) / 96.0
        base = 158 + (10 if (i // 4) % 2 else -10)
        pts.append("%.1f,%d" % (x, base))
    s.append("<polyline points='%s' fill='none' stroke='%s' stroke-width='1.6' filter='url(#g-gr)'/>"
             % (" ".join(pts), GR))
    s.append("<path d='M%g 158H%g' stroke='%s' stroke-opacity='.25' stroke-dasharray='3 5'/>" % (RX + 6, RX + RW - 6, CY))
    s.append("<text x='%g' y='226' class='k'>CAN_H 3.48V · CAN_L 1.52V</text>" % RX)
    s.append("<path d='M%g 240H%g' stroke='%s'/>" % (RX, RX + RW, HAIR))
    readouts = [("终端电阻", "60.2", "Ω", GR), ("绝缘阻值", "OK", "", GR), ("单体压差", "12", "mV", CY)]
    for i, (k, v, u, col) in enumerate(readouts):
        y = 268 + i * 46
        s.append("<text x='%g' y='%g' class='k'>%s</text>" % (RX, y, k))
        s.append("<text x='%g' y='%g' class='v' text-anchor='end' fill='%s'>%s</text>" % (RX + RW - 26, y, col, v))
        s.append("<text x='%g' y='%g' class='k' text-anchor='end'>%s</text>" % (RX + RW, y, u))
    s.append("<path d='M%g 400H%g' stroke='%s'/>" % (RX, RX + RW, HAIR))
    s.append("<text x='%g' y='420' class='k'>SENSOR FUSION</text>" % RX)
    # 小雷达
    cxx, cyy = RX + 34, 470
    for r in (16, 30, 44):
        s.append("<path d='M%g %gA%g %g 0 0 1 %g %g' fill='none' stroke='%s' stroke-opacity='.3'/>"
                 % (cxx - r, cyy, r, r, cxx + r, cyy, CY))
    for a in (0, 45, 90, 135, 180):
        xx = cxx + 44 * math.cos(math.radians(a))
        yy = cyy - 44 * math.sin(math.radians(a))
        s.append("<path d='M%g %gL%.1f %.1f' stroke='%s' stroke-opacity='.16'/>" % (cxx, cyy, xx, yy, CY))
    s.append("<path d='M%g %gL%.1f %.1fA44 44 0 0 1 %g %gZ' fill='%s' fill-opacity='.18'>"
             "<animateTransform attributeName='transform' type='rotate' values='0 %g %g;360 %g %g' dur='7s' repeatCount='indefinite'/>"
             "</path>" % (cxx, cyy, cxx + 40, cyy - 18, cxx + 44, cyy, GR, cxx, cyy, cxx, cyy))
    s.append("<circle cx='%g' cy='%g' r='3.6' fill='%s' filter='url(#g-cy)'/>" % (cxx, cyy, CY))
    s.append("<text x='%g' y='%g' class='k'>ADAS 4D RADAR</text>" % (RX + 92, 474))

    # ---- 中央：整车线稿 ----
    s.append("<text x='252' y='90' class='k'>VEHICLE HARNESS · 整车线束与部件</text>")
    s.append("<path d='M252 100H1044' stroke='%s'/>" % HAIR)

    car = ("M270 470C264 442 272 426 292 420C330 408 380 400 436 394"
           "C474 390 500 384 520 372C552 352 580 300 612 276C634 260 660 254 694 254"
           "L826 254C866 256 900 268 928 288C956 308 980 330 1000 348"
           "C1016 362 1022 384 1020 404C1018 428 1014 450 1012 470"
           "L932 470A66 66 0 0 0 800 470L496 470A66 66 0 0 0 364 470Z")
    s.append("<path d='%s' fill='%s' fill-opacity='.42' stroke='%s' stroke-width='1.8'/>" % (car, "#0F1A2A", CY))
    glass = ("M470 392C500 374 534 322 566 296C590 278 620 268 656 266L826 266"
             "C866 268 902 282 930 302L950 318Z")
    s.append("<path d='%s' fill='%s' fill-opacity='.10' stroke='%s' stroke-opacity='.55' stroke-width='1.1'/>"
             % (glass, CY, CY_L))
    s.append("<path d='M470 392L950 318' fill='none' stroke='%s' stroke-opacity='.45' stroke-width='1'/>" % CY_L)
    s.append("<path d='M742 262V356' fill='none' stroke='%s' stroke-opacity='.35' stroke-width='1'/>" % CY_L)
    # 车门缝
    s.append("<path d='M600 400L604 470' fill='none' stroke='%s' stroke-opacity='.22' stroke-width='1'/>" % CY)
    s.append("<path d='M760 386L762 470' fill='none' stroke='%s' stroke-opacity='.22' stroke-width='1'/>" % CY)
    # 注意：SVG 里开放路径默认会被填充为黑色，凡是只描边的路径必须显式 fill='none'
    s.append("<path d='M292 420C340 452 470 462 640 462' fill='none' stroke='%s' stroke-opacity='.28' "
             "stroke-width='1' stroke-dasharray='6 5'/>" % CY)
    s.append("<path d='M1010 430L1032 430' fill='none' stroke='%s' stroke-width='3' stroke-linecap='round'/>" % RD)

    for cx in (430, 866):
        s.append("<circle cx='%d' cy='480' r='66' fill='%s' stroke='%s' stroke-width='1.8'/>" % (cx, BG0, CY))
        s.append("<circle cx='%d' cy='480' r='42' fill='none' stroke='%s' stroke-opacity='.5' stroke-width='1.2'/>" % (cx, CY))
        for a in range(0, 360, 72):
            x1 = cx + 15 * math.cos(math.radians(a)); y1 = 480 + 15 * math.sin(math.radians(a))
            x2 = cx + 40 * math.cos(math.radians(a)); y2 = 480 + 40 * math.sin(math.radians(a))
            s.append("<path d='M%.1f %.1fL%.1f %.1f' stroke='%s' stroke-opacity='.4' stroke-width='1.4'/>" % (x1, y1, x2, y2, CY))
        s.append("<circle cx='%d' cy='480' r='10' fill='none' stroke='%s' stroke-opacity='.8' stroke-width='1.4'/>" % (cx, CY))

    # 高压线束（总线）+ 数据包（走在车轮下方，避免压到轮子）
    s.append("<path d='M300 566H1000' fill='none' stroke='%s' stroke-opacity='.30' stroke-width='1.4'/>" % CY)
    s.append("<path d='M300 566H1000' fill='none' stroke='%s' stroke-opacity='.10' stroke-width='6'/>" % CY)
    for x0, dur, col in ((320, 3.4, CY), (620, 4.2, GR), (860, 3.9, CY)):
        s.append("<rect x='0' y='562' width='26' height='8' fill='%s' filter='url(#g-cy)'>"
                 "<animate attributeName='x' values='%d;%d' dur='%ss' repeatCount='indefinite'/></rect>"
                 % (col, x0, x0 + 620, dur))
    for i, (mx, my, num) in enumerate(((640, 452, "01"), (866, 480, "02"), (306, 436, "03"), (566, 424, "04"))):
        s.append("<circle cx='%g' cy='%g' r='13' fill='%s' fill-opacity='.85' stroke='%s' stroke-width='1.2'/>"
                 % (mx, my, BG0, CY))
        s.append("<text x='%g' y='%g' class='c' text-anchor='middle' dominant-baseline='central' fill='%s'>%s</text>"
                 % (mx, my + 0.5, CY_L, num))
        s.append("<circle cx='%g' cy='%g' r='13' fill='none' stroke='%s' stroke-width='1'>"
                 "<animate attributeName='r' values='13;22;13' dur='3s' repeatCount='indefinite' begin='%gs'/>"
                 "<animate attributeName='stroke-opacity' values='.7;0;.7' dur='3s' repeatCount='indefinite' begin='%gs'/>"
                 "</circle>" % (mx, my, CY, i * 0.5, i * 0.5))

    s.append("<text x='252' y='600' class='k'>01 动力电池包 BATTERY PACK</text>")
    s.append("<text x='500' y='600' class='k'>02 驱动电机 DRIVE MOTOR</text>")
    s.append("<text x='748' y='600' class='k'>03 车载充电机 OBC</text>")
    s.append("<text x='960' y='600' class='k'>04 整车控制器 VCU</text>")

    # 扫描光带（裁剪在中央区）
    s.append("<clipPath id='cp-center'><rect x='240' y='104' width='800' height='470'/></clipPath>")
    s.append("<g clip-path='url(#cp-center)'><g class='sw'>"
             "<rect x='240' y='104' width='800' height='3' fill='url(#lg-scan)'/>"
             "<rect x='240' y='98' width='800' height='16' fill='%s' fill-opacity='.07'/></g></g>" % CY)

    # ---- 底栏读数 ----
    s.append("<path d='M6 636H1274' stroke='%s'/>" % HAIR)
    cells = [("DTC 数量", "0", GR), ("SOC", "72", CY), ("SOH", "98", GR), ("SCAN", "100", CY)]
    for i, (k, v, col) in enumerate(cells):
        x = 34 + i * 236
        s.append("<text x='%g' y='672' class='k'>%s</text>" % (x, k))
        s.append("<text x='%g' y='712' class='n' fill='%s'>%s</text>" % (x, col, v))
        s.append("<path d='M%g 726H%g' stroke='%s'/>" % (x, x + 200, HAIR))
        s.append(ticks(x, x + 200, 726, 20, 0, 5, CY, ".35", 5))
    s.append("<text x='1224' y='712' class='k' text-anchor='end'>CHXZ-DIAG / 2026</text>")
    s.append("</svg>")
    return "".join(s)


# ================================================================ 2. 首屏背景
def hero_bg():
    W, H = 1600, 900
    vx, hy = 800, 430
    s = ["<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1600 900' width='1600' height='900'>"]
    s.append("<defs>"
             + f"<radialGradient id='b1'><stop offset='0' stop-color='{CY}' stop-opacity='.30'/>"
               f"<stop offset='1' stop-color='{CY}' stop-opacity='0'/></radialGradient>"
             + f"<radialGradient id='b2'><stop offset='0' stop-color='{GR}' stop-opacity='.16'/>"
               f"<stop offset='1' stop-color='{GR}' stop-opacity='0'/></radialGradient>"
             + f"<linearGradient id='fade' x1='0' y1='0' x2='1' y2='0'>"
               f"<stop offset='0' stop-color='{CY}' stop-opacity='0'/>"
               f"<stop offset='.5' stop-color='{CY}' stop-opacity='.5'/>"
               f"<stop offset='1' stop-color='{CY}' stop-opacity='0'/></linearGradient>"
             + "</defs>")
    s.append("<circle cx='1180' cy='470' r='430' fill='url(#b1)'/>")
    s.append("<circle cx='300' cy='200' r='320' fill='url(#b2)'/>")
    y, step = hy, 4.0
    while y < H:
        op = min(.22, .04 + (y - hy) / H * .24)
        s.append("<path d='M0 %.0fH%d' stroke='%s' stroke-opacity='%.2f' stroke-width='1'/>" % (y, W, CY, op))
        y += step
        step *= 1.30
    for xb in range(-1600, 3400, 100):
        s.append("<path d='M%d %dL%d %d' stroke='%s' stroke-opacity='.055' stroke-width='1'/>" % (vx, hy, xb, H, CY))
    s.append("<path d='M0 %dH%d' stroke='%s' stroke-opacity='.30' stroke-width='1'/>" % (hy, W, CY))
    s.append("<rect x='0' y='%d' width='%d' height='2' fill='url(#fade)'/>" % (hy - 1, W))
    # 上半区电路走线
    for x1, y1, x2, y2 in ((90, 130, 430, 130), (430, 130, 430, 240), (90, 130, 90, 300),
                           (1250, 100, 1520, 100), (1250, 100, 1250, 250), (1090, 300, 1250, 250),
                           (560, 64, 560, 150), (560, 150, 700, 150)):
        s.append("<path d='M%d %dL%d %d' stroke='%s' stroke-opacity='.18' stroke-width='1.2'/>" % (x1, y1, x2, y2, CY))
        for cx, cy in ((x1, y1), (x2, y2)):
            s.append("<rect x='%d' y='%d' width='5' height='5' fill='%s' fill-opacity='.35'/>" % (cx - 2, cy - 2, CY))
    # 刻度尺点缀
    s.append(ticks(0, W, hy - 18, 64, 10, 4, CY, ".18", 4))
    s.append("</svg>")
    return "".join(s)


# ================================================================ 3. CAN 拓扑
def can_topology():
    W, H = 1480, 920
    s = ["<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 %d %d' width='%d' height='%d' "
         "font-family='%s' role='img' aria-label='整车 CAN 网络拓扑图'>" % (W, H, W, H, CJK)]
    s.append("<defs>" + glow("g-cy", 4, 1) + "</defs>")
    s.append("<rect width='%d' height='%d' fill='%s'/>" % (W, H, BG0))
    s.append("<style>"
             ".h1{fill:" + TXT + ";font-size:30px;font-weight:700;letter-spacing:.06em}"
             ".sub{fill:" + TXT_L + ";font-size:13px;letter-spacing:.2em;font-family:" + MONO + "}"
             ".bus{fill:" + CY_L + ";font-size:16px;font-weight:700;letter-spacing:.05em}"
             ".rate{fill:" + TXT_L + ";font-size:11px;letter-spacing:.1em;font-family:" + MONO + "}"
             ".nd{fill:" + TXT + ";font-size:14px}"
             ".nd2{fill:" + TXT_M + ";font-size:11px;letter-spacing:.06em}"
             ".lg{fill:" + TXT_M + ";font-size:12px}"
             "</style>")
    s.append("<text x='48' y='64' class='h1'>整车 CAN 网络拓扑图</text>")
    s.append("<text x='48' y='92' class='sub'>VEHICLE CAN NETWORK TOPOLOGY / CHXZ-DIAG</text>")
    s.append("<path d='M48 110H1432' stroke='%s'/>" % HAIR)
    s.append(ticks(48, 1432, 110, 48, 0, 6, CY, ".3", 6))

    buses = [
        ("动力 CAN", "500 kbps", CY, [("VCU", "整车控制器"), ("BMS", "电池管理系统"),
                                    ("MCU", "电机控制器"), ("OBC", "车载充电机"), ("DC/DC", "直流变换器")]),
        ("底盘 CAN", "500 kbps", GR, [("ABS", "防抱死制动"), ("ESP", "车身稳定系统"),
                                    ("EPS", "电动助力转向"), ("SRS", "安全气囊")]),
        ("车身 CAN", "125 kbps", AM, [("BCM", "车身控制模块"), ("DOOR", "车门模块"),
                                     ("HVAC", "空调系统"), ("LIGHT", "灯光模块")]),
        ("信息娱乐 CAN", "125 kbps", "#B98CFF", [("HU", "车机主机"), ("IPC", "仪表"),
                                              ("T-BOX", "远程终端"), ("AVM", "360 环视"), ("RADAR", "毫米波雷达")]),
    ]
    top, gap = 168, 184
    for bi, (name, rate, col, nodes) in enumerate(buses):
        y = top + bi * gap
        s.append("<path d='M250 %dH1432' stroke='%s' stroke-opacity='.85' stroke-width='2.4'/>" % (y, col))
        s.append("<path d='M250 %dH1432' stroke='%s' stroke-opacity='.07' stroke-width='9'/>" % (y, col))
        for x in (250, 1400):
            s.append("<rect x='%d' y='%d' width='14' height='24' rx='2' fill='%s' stroke='%s' stroke-width='1.4'/>"
                     % (x - 7, y - 12, BG1, col))
        s.append("<text x='250' y='%d' class='rate' text-anchor='middle'>120Ω</text>" % (y - 24))
        s.append("<text x='1400' y='%d' class='rate' text-anchor='middle'>120Ω</text>" % (y - 24))
        s.append("<path d='%s' fill='%s' stroke='%s' stroke-width='1.4'/>" % (ch(48, y - 26, 176, 52, 10, "tl,br"), BG2, col))
        s.append("<path d='M48 %dH53V%d' stroke='%s' stroke-width='3'/>" % (y - 16, y + 16, col))
        s.append("<text x='70' y='%d' class='bus'>%s</text>" % (y - 2, name))
        s.append("<text x='70' y='%d' class='rate'>%s</text>" % (y + 19, rate))
        s.append("<path d='M224 %dH250' stroke='%s' stroke-width='1.6'/>" % (y, col))
        n = len(nodes)
        span_l, span_r, bw, bh = 330, 1330, 156, 72
        g = (span_r - span_l - n * bw) / max(n - 1, 1)
        for i, (code, cn) in enumerate(nodes):
            x = span_l + i * (bw + g)
            s.append("<path d='M%.0f %dV%d' stroke='%s' stroke-opacity='.55' stroke-width='1.4'/>"
                     % (x + bw / 2, y, y + 44, col))
            s.append("<rect x='%.0f' y='%d' width='6' height='6' fill='%s'/>" % (x + bw / 2 - 3, y - 3, col))
            s.append("<path d='%s' fill='%s' stroke='%s' stroke-opacity='.5' stroke-width='1.3'/>"
                     % (ch(x, y + 44, bw, bh, 9, "tl,br"), BG1, col))
            s.append("<text x='%.0f' y='%d' class='nd' text-anchor='middle'>%s</text>" % (x + bw / 2, y + 72, code))
            s.append("<text x='%.0f' y='%d' class='nd2' text-anchor='middle'>%s</text>" % (x + bw / 2, y + 95, cn))

    ly = H - 74
    s.append("<path d='M48 %dH1432' stroke='%s'/>" % (ly - 26, HAIR))
    s.append("<text x='48' y='%d' class='lg'>图例：</text>" % ly)
    xx = 100
    for col, txt in ((CY, "动力 CAN 500 kbps"), (GR, "底盘 CAN 500 kbps"),
                     (AM, "车身 CAN 125 kbps"), ("#B98CFF", "信息娱乐 CAN 125 kbps")):
        s.append("<path d='M%d %dH%d' stroke='%s' stroke-width='2.4'/>" % (xx, ly - 5, xx + 26, col))
        s.append("<text x='%d' y='%d' class='lg'>%s</text>" % (xx + 34, ly, txt))
        xx += 296
    s.append("<text x='1432' y='%d' class='lg' text-anchor='end'>终端电阻 120Ω ×2（并联约 60Ω 为正常）</text>" % ly)
    s.append("<text x='48' y='%d' class='lg'>提示：测量 CAN_H 与 CAN_L 之间电阻应为 60Ω 左右；"
             "若为 120Ω 说明一端终端缺失，接近 0Ω 说明短路。</text>" % (H - 26))
    s.append("</svg>")
    return "".join(s)


# ================================================================ 4. 分隔尺
def circuit_divider():
    W, H = 1200, 40
    s = ["<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 %d %d' width='%d' height='%d' "
         "preserveAspectRatio='none'>" % (W, H, W, H)]
    s.append("<defs>" + glow("g-cy", 4, 1) + "</defs>")
    s.append("<path d='M0 32H1200' stroke='%s' stroke-opacity='.55'/>" % CY)
    s.append(ticks(0, W, 32, 60, 0, 7, CY, ".30", 5))
    s.append("<path d='M480 32L500 8H700L720 32' fill='none' stroke='%s' stroke-opacity='.8' stroke-width='1.2'/>" % CY)
    s.append("<rect x='596' y='4' width='8' height='8' fill='%s' filter='url(#g-cy)'>"
             "<animate attributeName='opacity' values='1;.2;1' dur='2s' repeatCount='indefinite'/></rect>" % CY)
    s.append("<path d='M300 32V20H340' fill='none' stroke='%s' stroke-opacity='.4'/>" % CY)
    s.append("<path d='M900 32V20H860' fill='none' stroke='%s' stroke-opacity='.4'/>" % CY)
    s.append("</svg>")
    return "".join(s)


# ================================================================ 5. 颗粒
def noise():
    return ("<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180'>"
            "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='3' stitchTiles='stitch'/>"
            "<feColorMatrix type='saturate' values='0'/></filter>"
            "<rect width='180' height='180' filter='url(#n)' opacity='.42'/></svg>")


# ================================================================ 6. 图标
def favicon():
    return ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64' width='64' height='64'>"
            "<defs>" + glow("g", 4, 1) + "</defs>"
            f"<path d='{ch(2, 2, 60, 60, 14, 'tl,br')}' fill='{BG1}'/>"
            f"<path d='{ch(2, 2, 60, 60, 14, 'tl,br')}' fill='none' stroke='{CY}' stroke-width='2'/>"
            f"<path d='M14 42C13 34 16 30 22 29L28 21H40L46 29C52 30 52 35 52 42' fill='none' "
            f"stroke='{CY}' stroke-width='2.6' stroke-linecap='round'/>"
            f"<path d='M12 42H54' stroke='{CY}' stroke-width='2.6' stroke-linecap='round'/>"
            f"<circle cx='23' cy='45' r='5.4' fill='{BG1}' stroke='{CY}' stroke-width='2.2'/>"
            f"<circle cx='43' cy='45' r='5.4' fill='{BG1}' stroke='{CY}' stroke-width='2.2'/>"
            f"<path d='M22 33H44' stroke='{GR}' stroke-width='2' stroke-linecap='round'/>"
            "</svg>")


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "cyber")
    out = os.path.abspath(out)
    os.makedirs(out, exist_ok=True)
    files = {
        "hero-hud.svg": hero_hud(),
        "hero-bg.svg": hero_bg(),
        "can-topology.svg": can_topology(),
        "circuit-divider.svg": circuit_divider(),
        "noise.svg": noise(),
        "favicon.svg": favicon(),
    }
    for name, content in files.items():
        with open(os.path.join(out, name), "w", encoding="utf-8") as f:
            f.write(content)
        print("  %-22s %7d 字节" % (name, len(content.encode("utf-8"))))
    print("\n  输出目录：%s" % out)


if __name__ == "__main__":
    main()

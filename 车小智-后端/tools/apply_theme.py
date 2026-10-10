# -*- coding: utf-8 -*-
"""
把 theme-v2.css / cyber-fx.js 注入 车小智.html。
可重复执行（幂等）：每次运行都会用最新版本的 css/js 覆盖注入内容。

    python tools/apply_theme.py
"""

import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)                      # 车小智-后端
SITE = os.path.dirname(BACKEND)                      # ！！！高职比赛
HTML = os.path.join(SITE, "车小智.html")
CSS = os.path.join(HERE, "theme-v2.css")
JS = os.path.join(HERE, "cyber-fx.js")

NEW_CONFIG = """tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        // 冷青（主强调）
                        primary: {
                            50: '#041B26', 100: '#062B3A', 200: '#08425C', 300: '#12A9CE',
                            400: '#1FC9E8', 500: '#35E0FF', 600: '#6BEBFF', 700: '#A8F2FF',
                            800: '#D6F9FF', 900: '#EAFDFF',
                        },
                        // 薄荷绿（成功/次强调）
                        secondary: {
                            50: '#04231A', 100: '#06301F', 200: '#08422B', 300: '#1FA76A',
                            400: '#4CE79B', 500: '#7CFFB2', 600: '#A3FFCB', 700: '#C6FFE0',
                            800: '#E0FFF0', 900: '#F0FFF8',
                        },
                        // 灰阶整体反转为「深底浅字」
                        gray: {
                            50: '#0A1018', 100: '#132032', 200: '#1B2B3E', 300: '#27384D',
                            400: '#6E86A0', 500: '#8FA6BE', 600: '#A9BED4', 700: '#C4D6EA',
                            800: '#DCE8F7', 900: '#EEF5FF',
                        },
                        neutral: {
                            dark: '#C9D8E8',
                            light: '#05070C',
                        },
                        warning: '#FFB020',
                        error: '#FF4D6D',
                    },
                    fontFamily: {
                        sans: ['Inter', 'system-ui', 'sans-serif'],
                        mono: ['JetBrains Mono', 'monospace'],
                    },
                    animation: {
                        'float': 'float 6s ease-in-out infinite',
                        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                        'scan': 'scan 2s linear infinite',
                    },
                    keyframes: {
                        float: {
                            '0%, 100%': { transform: 'translateY(0)' },
                            '50%': { transform: 'translateY(-8px)' },
                        },
                        scan: {
                            '0%': { transform: 'translateY(-100%)' },
                            '100%': { transform: 'translateY(100%)' },
                        }
                    },
                }
            }
        }
"""


def main():
    for p in (HTML, CSS, JS):
        if not os.path.isfile(p):
            print("  缺少文件：%s" % p)
            sys.exit(1)

    t = io.open(HTML, encoding="utf-8").read()
    css = io.open(CSS, encoding="utf-8").read().rstrip()
    js = io.open(JS, encoding="utf-8").read().rstrip()
    report = []

    # ---- 1. tailwind 配色令牌 ----
    t, n = re.subn(r"tailwind\.config = \{.*?\n    </script>", NEW_CONFIG + "    </script>",
                   t, count=1, flags=re.S)
    report.append("tailwind 配色重映射: %d" % n)

    # ---- 2. 主题样式层（整体替换 cyber-theme 内容，幂等） ----
    t, n = re.subn(r'(<style id="cyber-theme">).*?(</style>)',
                   lambda m: m.group(1) + "\n" + css + "\n    " + m.group(2),
                   t, count=1, flags=re.S)
    report.append("主题样式层注入: %d" % n)

    # ---- 3. 移除 GSAP 依赖（入场动画改由 CYBER FX 负责） ----
    t, n = re.subn(r'\s*<script src="https://cdnjs\.cloudflare\.com/ajax/libs/gsap/[^"]*"></script>',
                   "", t)
    report.append("移除 GSAP 脚本: %d 处" % n)

    t, n = re.subn(r"// 页面加载动画\s*\n\s*window\.addEventListener\('load', function\(\) \{.*?\n        \}\);",
                   "// 入场动画由 CYBER FX 接管：滚动揭示 / 数字滚动 / 标题解码",
                   t, count=1, flags=re.S)
    report.append("移除 GSAP 入场调用: %d" % n)

    # ---- 4. 首屏：放大主视觉 + 挂上视差容器 ----
    t, n = re.subn(r'<div class="relative w-full max-w-md">',
                   '<div class="relative w-full max-w-2xl cy-visual">', t)
    report.append("首屏视觉容器标记: %d" % n)

    t, n = re.subn(r'<div class="absolute inset-0 z-0 opacity-40">',
                   '<div class="absolute inset-0 z-0 opacity-60">', t)
    report.append("首屏背景层透明度: %d" % n)

    # ---- 5. 注入动效脚本（先删旧的，保持幂等） ----
    t = re.sub(r'\s*<script id="cyber-fx">.*?</script>', "", t, flags=re.S)
    t, n = re.subn(r"(\s*)</body>",
                   lambda m: "\n    <script id=\"cyber-fx\">\n" + js + "\n    </script>\n</body>",
                   t, count=1)
    report.append("动效脚本注入: %d" % n)

    io.open(HTML, "w", encoding="utf-8").write(t)

    print("  注入完成 -> %s" % HTML)
    for r in report:
        print("   ·", r)
    print("   · 文件大小: %d 字节" % len(t.encode("utf-8")))


if __name__ == "__main__":
    main()

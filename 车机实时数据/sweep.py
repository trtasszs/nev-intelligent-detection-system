# -*- coding: utf-8 -*-
"""
全站暖底清除 + 逐页复验
------------------------------------------------------------------
上一轮只覆盖了 .bg-dark-400 / .bg-dark-300，漏了 dark-100/200/500，
而 .card 用的是 bg-dark-200、协议页表层用的是 bg-dark-200/300 —— 所以还有暖底。
本版：**五个色阶全部强制中性**，且不再限定 .page-content（侧栏/顶栏一并覆盖）。
然后自动渲染全部 8 个页面并逐页扫描暖偏像素，输出体检表。
"""
import io
import os
import re
import subprocess

SITE = r'E:\！！！高职比赛'
HERE = r'E:\！！！高职比赛\车机实时数据'
P = os.path.join(SITE, u'新能源汽车智能检测系统-1.0版.html')
L = os.path.join(HERE, 'live.css')
EXE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
TMP = os.path.join(os.environ['TEMP'], 'cx-sweep')
os.makedirs(TMP, exist_ok=True)

OVERRIDE = u'''
/* ===== CX-INK · 全站墨色强制覆盖（清除暖底总闸） ===== */
/* Tailwind Play CDN 未按 config 解析 dark-* 色阶，会渲染出暖褐底，
   这里对五个色阶全部强制中性值，不限定 .page-content，侧栏与顶栏一并覆盖。 */
.bg-dark-100 { background-color: #131316 !important; }
.bg-dark-200 { background-color: #0F0F12 !important; }
.bg-dark-300 { background-color: #0A0A0C !important; }
.bg-dark-400 { background-color: #070709 !important; }
.bg-dark-500 { background-color: #050506 !important; }
/* 半透明变体 */
.bg-dark-200\\/50, .bg-dark-300\\/50 { background-color: rgba(15,15,18,.5) !important; }
'''

t = io.open(L, encoding='utf-8').read()
if 'CX-INK' not in t:
    # 去掉上一轮那条窄覆盖
    t = re.sub(r'/\* ===== 强制中性（排查并修复暖底） ===== \*/.*?\.page-content \.bg-dark-300 \{[^}]*\}\n',
               u'', t, flags=re.S)
    t += OVERRIDE
    io.open(L, 'w', encoding='utf-8').write(t)
    print(u'已写入 CX-INK 全站墨色覆盖（五个色阶）')
else:
    print(u'CX-INK 已存在')

# 重新注入页面
r = subprocess.run(['python', os.path.join(HERE, 'apply_can.py')],
                   capture_output=True, text=True, encoding='utf-8')
print(r.stdout.strip().splitlines()[-1] if r.stdout else '')

PAGES = [('dashboard', u'系统概览', 1400), ('vehicles', u'车辆信息管理', 1300),
         ('detection', u'检测记录管理', 1200), ('battery', u'电池管理', 1300),
         ('statistics', u'数据分析', 1300), ('iot', u'智能网联管理', 1400),
         ('protocol', u'通信协议及数据导入', 1200), ('settings', u'系统设置', 1200)]

print(u'\n渲染并逐页扫描暖偏像素…')
for pid, name, h in PAGES:
    shot = os.path.join(TMP, pid + '.png')
    subprocess.run([EXE, '--headless=new', '--disable-gpu', '--hide-scrollbars',
                    '--force-device-scale-factor=1', '--virtual-time-budget=8000',
                    '--window-size=1600,%d' % h, '--screenshot=' + shot,
                    'file:///E:/！！！高职比赛/新能源汽车智能检测系统-1.0版.html?noboot=1#' + pid],
                   capture_output=True)
    print(u'  %s' % shot)

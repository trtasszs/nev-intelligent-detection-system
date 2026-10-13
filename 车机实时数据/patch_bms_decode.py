# -*- coding: utf-8 -*-
"""
① 往 can_bridge.py 的 decode() 里补上电池信号（实测确认的那几个）
② 更正 apply_bms_page.py 里被桥内信号表证伪的两处标签
"""
import io
import py_compile
import sys

sys.stdout.reconfigure(encoding='utf-8')

# ---------------- ① 桥的 decode() ----------------
P1 = r'E:\！！！高职比赛\车机实时数据\can_bridge.py'
t = io.open(P1, encoding='utf-8').read()

ANCHOR = "    b618 = READER.b('618')\n"
ADD = (
    "    b618 = READER.b('618')\n"
    "    b338 = READER.b('338')     # 电池：SOC\n"
    "    b636 = READER.b('636')     # 电池：总压\n"
    "    b45A = READER.b('45A')     # 电池：总压备份\n"
    "    b264 = READER.b('264')     # 电池：温度\n"
    "    b235 = READER.b('235')     # 电池：电流/辅助量\n"
)

if 'b338 = READER.b' in t:
    print(u'  桥：已是含电池版，跳过')
else:
    if t.count(ANCHOR) == 1:
        t = t.replace(ANCHOR, ADD, 1)
        print(u'  桥：已加 5 个电池帧引用')
    else:
        print(u'  桥：✗ 锚点不唯一（%d 处）' % t.count(ANCHOR))

RET_OLD = (
    "    # 刹车灯：Can_618\n"
    "    if b618:\n"
    "        r['brake_light_raw'] = b618[2]\n"
    "\n"
    "    return r"
)
RET_NEW = (
    "    # 刹车灯：Can_618\n"
    "    if b618:\n"
    "        r['brake_light_raw'] = b618[2]\n"
    "\n"
    "    # ---------------- 电池（BMS）----------------\n"
    "    # ★原 decode 表里没有电池，下面几条是 2026-10-11 用「激励—观测」实测确认的：\n"
    "    #   0x636 byte0-1 与 0x45A byte2-3 均为 0x0FA0=4000 ⇒ 400.0 V（双报文印证）\n"
    "    #   0x338 byte4 = 51，与仪表盘 SOC 51% 一致；15 分钟内 52→51 单调下降\n"
    "    #   0x264 byte2 = 15→17→19→20 ℃，随车动作单调上升\n"
    "    #   0x235 byte2 静止 0、给油 391/1428；byte5-6 含义未确认，不冒充电压\n"
    "    #   本平台无官方 DBC，换算系数按行业惯例，信号名未经厂商确认。\n"
    "    if b636:\n"
    "        r['pack_voltage'] = round(((b636[0] << 8) | b636[1]) * 0.1, 1)\n"
    "        r['pack_voltage_basis'] = 'Can_636 byte0-1 x0.1（与 Can_45A byte2-3 一致）'\n"
    "    if b45A:\n"
    "        r['pack_voltage_alt'] = round(((b45A[2] << 8) | b45A[3]) * 0.1, 1)\n"
    "    if b338:\n"
    "        r['soc_percent'] = b338[4]\n"
    "        r['soc_basis'] = 'Can_338 byte4 原值 %（与仪表盘 51% 实测一致）'\n"
    "    if b264:\n"
    "        r['battery_temp_c'] = b264[2]\n"
    "    if b235:\n"
    "        r['battery_current_raw'] = b235[2]\n"
    "        r['battery_aux_raw'] = (b235[5] << 8) | b235[6]\n"
    "\n"
    "    return r"
)
if 'pack_voltage' in t:
    print(u'  桥：电池解码已在')
else:
    if t.count(RET_OLD) == 1:
        t = t.replace(RET_OLD, RET_NEW, 1)
        print(u'  桥：电池解码已补入 decode()')
    else:
        print(u'  桥：✗ return 段锚点不唯一（%d 处）' % t.count(RET_OLD))

io.open(P1, 'w', encoding='utf-8').write(t)
t1 = io.open(P1, encoding='utf-8').read()
for k in ('b338 = READER.b', "r['pack_voltage']", "r['soc_percent']", "r['battery_temp_c']"):
    print(u'    %-28s %s' % (k, u'✓' if k in t1 else u'✗'))

# ---------------- ② 更正 BMS 页标签 ----------------
P2 = r'E:\！！！高职比赛\车机实时数据\apply_bms_page.py'
t2 = io.open(P2, encoding='utf-8').read()
fixes = [
    (u"name: '辅助量（含义未确认）', k: 1, unit: '', "
     u"conf: '低（曾读到 100，后又为 0，疑为状态位）', key: 'aux226'",
     u"name: '控制指令·油门', k: 1, unit: '', "
     u"conf: '高（桥内实测信号表：0x226 byte0=油门 byte1=反值 byte2=刹车；仅控制节点运行时出现）', key: 'acc_cmd'"),
    (u"name: '负载功率', k: 0.1, unit: 'kW', conf: '中（随踏板变化）', key: 'load'",
     u"name: '加速踏板位置', k: 1, unit: '', "
     u"conf: '高（桥内实测信号表：0x668 byte2 = 踏板）', key: 'pedal'"),
]
n = 0
for a, b in fixes:
    if a in t2:
        t2 = t2.replace(a, b, 1)
        n += 1
        print(u'  BMS 页标签已更正 -> %s' % b.split(u"name: '")[1].split(u"'")[0])
io.open(P2, 'w', encoding='utf-8').write(t2)
print(u'  标签更正 %d/2' % n)

for p in (P1, P2):
    try:
        py_compile.compile(p, doraise=True)
        print(u'  ✓ 语法 %s' % p.split('\\')[-1])
    except Exception as e:
        print(u'  ✗ %s: %s' % (p.split('\\')[-1], e))

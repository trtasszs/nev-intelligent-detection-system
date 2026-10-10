# -*- coding: utf-8 -*-
"""从 Qt 上位机 exe 里抽取字符串，找 CAN 信号定义"""
import re
import sys

P = r'E:\xun\CHE\22年国赛-智能网联\ChassisTest\Chassis_Debug_And_Test_1PlusX.exe'
data = open(P, 'rb').read()
print('文件大小', len(data))

# --- ASCII 串
asc = set(x.decode('ascii', 'ignore') for x in re.findall(rb'[\x20-\x7e]{4,}', data))
# --- UTF-16LE：ASCII 字符（低字节可打印、高字节 0）
u16a = set()
for m in re.finditer(rb'(?:[\x20-\x7e]\x00){4,}', data):
    u16a.add(m.group().decode('utf-16le', 'ignore'))
# --- UTF-16LE：中文（CJK 区 0x4E00-0x9FFF，低字节 0x00-0xFF，高字节 0x4E-0x9F）
u16c = set()
for m in re.finditer(rb'(?:[\x00-\xff][\x4e-\x9f]){2,}', data):
    try:
        s = m.group().decode('utf-16le', 'ignore')
    except Exception:
        continue
    if re.search(r'[\u4e00-\u9fff]', s):
        u16c.add(s)

print('ASCII %d / UTF16-ASCII %d / UTF16-中文 %d' % (len(asc), len(u16a), len(u16c)))
ALLU = u16a | u16c | asc

CN_KW = ['车速', '档位', '挡位', '电池', '电压', '电流', '荷电', '温度', '转向', '制动',
         '油门', '手刹', '巡航', '轮速', '绝缘', '充电', '单体', '里程', '踏板', '模式',
         '故障', '状态', '角度', '扭矩', '转速', '助力', '方向']
print('\n=== 含中文关键词的串 ===')
hit = set()
for s in ALLU:
    st = s.strip()
    if 2 <= len(st) <= 26 and any(k in st for k in CN_KW):
        hit.add(st)
for s in sorted(hit)[:120]:
    print('  ', s)

EN_KW = ['VehSpd', 'GearLev', 'EPB', 'YawRate', 'LongAcc', 'SOC', 'Cell', 'Pack',
         'Volt', 'Curr', 'Temp', 'StrAngle', 'AccPel', 'BrkPel', 'Cruise', 'ATO',
         'Wheel', 'BMS', 'VCU', 'ICPV', 'Spd']
print('\n=== 含英文信号名的串 ===')
hit2 = set()
for s in ALLU:
    st = s.strip()
    if 4 <= len(st) <= 44 and any(k.lower() in st.lower() for k in EN_KW):
        hit2.add(st)
for s in sorted(hit2)[:120]:
    print('  ', s)

print('\n=== 形如 0x1XX 的 CAN ID ===')
ids = set()
for s in ALLU:
    for m in re.finditer(r'\b0[xX]([0-9A-Fa-f]{2,3})\b', s):
        ids.add('0x' + m.group(1).upper())
print('  ', sorted(ids))

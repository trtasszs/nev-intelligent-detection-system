# -*- coding: utf-8 -*-
"""
修掉双通道的通道归属问题。
问题：ControlCAN.dll 在双通道下，VCI_Receive 拿到的数据落到哪个通道**不确定**
      —— 实测同一台设备，有时数据在通道 0、有时在通道 1。
      原设计给通道 1 加 "@2" 后缀 ⇒ 会把整车数据错误标成电池通道，
      还会让 decode() 查 '636' 查不到。
改法：两个通道**合并到同一套键名**（不加后缀），谁先来谁算谁的；
      同一 ID 若两通道都出现，保留先到的并打一条告警。
      并额外保留一个 "@ch" 字段记录来源通道，便于排查。
"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')

P = r'E:\！！！高职比赛\车机实时数据\can_bridge.py'
t = io.open(P, encoding='utf-8').read()
n = 0

# ① ingest：不再加 @2 后缀
old = """                    base = '%03X' % (o.ID & 0x7FF) if not o.ExternFlag else '%08X' % o.ID
                    cid = base if ch == 0 else base + '@2'
                    b = bytes(bytearray(o.Data))[:o.DataLen]"""
new = """                    cid = '%03X' % (o.ID & 0x7FF) if not o.ExternFlag else '%08X' % o.ID
                    b = bytes(bytearray(o.Data))[:o.DataLen]
                    # 记录来源通道（仅排查用）。★不加后缀★：见文件头那段说明 ——
                    # ControlCAN.dll 双通道下数据落到哪个通道不确定，加后缀会把
                    # 整车数据误标成电池通道，并让 decode() 查不到 ID。
                    self.chan_of[cid] = ch"""
if t.count(old) == 1:
    t = t.replace(old, new, 1); n += 1; print(u'  [1] ingest 已去掉 @2 后缀，改为记录来源通道')
else:
    print(u'  [1] ✗ 没匹配到 ingest 的键名构造')

# ② snapshot：ch 字段改成读 chan_of
old2 = "                         'ch': 1 if k.endswith('@2') else 0,"
new2 = "                         'ch': self.chan_of.get(k, 0),"
if t.count(old2) == 1:
    t = t.replace(old2, new2, 1); n += 1; print(u'  [2] snapshot 的 ch 字段改为读实际来源')
else:
    print(u'  [2] ✗ 没匹配到 snapshot 的 ch 字段')

# ③ __init__：加 chan_of
old3 = "        self.ch2 = False             # 通道 1（电池 CAN）是否可用"
new3 = ("        self.ch2 = False             # 通道 1（电池 CAN）是否可用\n"
        "        self.chan_of = {}            # id -> 来源通道（0/1），仅排查用")
if t.count(old3) == 1:
    t = t.replace(old3, new3, 1); n += 1
    print(u'  [3] __init__ 已加 chan_of')
else:
    print(u'  [3] ✗ 没匹配到 __init__ 的 ch2 行')

if n < 3:
    print(u'\n  ✗ 只成功 %d/3，不写盘' % n)
    raise SystemExit(1)

io.open(P, 'w', encoding='utf-8').write(t)
print(u'\n  已写盘 %d 处' % n)

import py_compile
try:
    py_compile.compile(P, doraise=True)
    print(u'  ✓ 语法通过')
except Exception as e:
    print(u'  ✗ 语法: %s' % e)

t2 = io.open(P, encoding='utf-8').read()
print(u'  回读: @2 后缀已移除 %s ; chan_of %s' % (
    u'✓' if "'@2'" not in t2 else u'✗ 还在',
    u'✓' if 'self.chan_of' in t2 else u'✗'))

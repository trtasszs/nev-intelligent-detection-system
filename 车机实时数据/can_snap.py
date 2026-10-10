# -*- coding: utf-8 -*-
"""抓一段 CAN，报告每个 ID 的字节变化情况（判断哪些信号是活的）"""
import collections
import sys
import time
from ctypes import byref

sys.path.insert(0, r'E:\！！！高职比赛\车机实时数据')
import can_read as C

DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 10.0

dll, path = C.load_dll()
if dll.VCI_OpenDevice(4, 0, 0) != 1:
    print('打开设备失败')
    sys.exit(1)
cfg = C.VCI_INIT_CONFIG()
cfg.AccCode = 0
cfg.AccMask = 0xFFFFFFFF
cfg.Filter = 1
cfg.Timing0, cfg.Timing1 = 0x00, 0x1C     # 500k
cfg.Mode = 0
if dll.VCI_InitCAN(4, 0, 0, byref(cfg)) != 1 or dll.VCI_StartCAN(4, 0, 0) != 1:
    print('初始化/启动失败')
    dll.VCI_CloseDevice(4, 0)
    sys.exit(1)
dll.VCI_ClearBuffer(4, 0, 0)

buf = (C.VCI_CAN_OBJ * 2000)()
seen = collections.Counter()
# 每个 ID 记录：每字节的最小/最大值 + 该 ID 的第 0 帧完整字节
bmin, bmax = {}, {}
first = {}
t0 = time.time()
while time.time() - t0 < DUR:
    n = dll.VCI_Receive(4, 0, 0, buf, 2000, 50)
    if n <= 0:
        time.sleep(0.003)
        continue
    for i in range(n):
        o = buf[i]
        cid = '%03X' % (o.ID & 0x7FF)
        b = list(bytes(bytearray(o.Data))[:o.DataLen])
        seen[cid] += 1
        if cid not in first:
            first[cid] = b
        lo = bmin.setdefault(cid, list(b))
        hi = bmax.setdefault(cid, list(b))
        for k in range(len(b)):
            if k < len(lo):
                lo[k] = min(lo[k], b[k])
                hi[k] = max(hi[k], b[k])
dll.VCI_CloseDevice(4, 0)

print('采集 %.0f 秒，收到 %d 个不同 CAN ID\n' % (DUR, len(seen)))
print('%-6s %8s  %-26s %s' % ('ID', '帧数', '首帧数据', '变化的字节(序号: 最小~最大)'))
print('-' * 92)
for cid, c in seen.most_common():
    f = first[cid]
    lo, hi = bmin[cid], bmax[cid]
    ch = ['%d:%02X~%02X' % (k, lo[k], hi[k]) for k in range(len(f)) if lo[k] != hi[k]]
    print('%-6s %8d  %-26s %s' % (cid, c, ' '.join('%02X' % x for x in f),
                                  ' '.join(ch) if ch else '（全字节恒定）'))

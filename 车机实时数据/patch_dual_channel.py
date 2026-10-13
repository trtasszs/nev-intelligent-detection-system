# -*- coding: utf-8 -*-
"""
把 can_bridge.py 改成**双通道**：
  CAN1（通道 0）→ 整车 CAN（OBD 6/14）—— 原有行为，键名与字段完全不变
  CAN2（通道 1）→ 电池 CAN（OBD 1/9）—— 新增；键名加 "@2" 后缀避免与通道 0 撞车
★ 通道 1 打不开（没接线 / 设备不支持）时**自动降级为单通道**，不影响原有功能。
每帧新增 "ch" 字段（0/1）。
"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')

P = r'E:\！！！高职比赛\车机实时数据\can_bridge.py'
t = io.open(P, encoding='utf-8').read()
orig = t
n = 0
MARK = '# ==== CX-DUALCH BEGIN ===='
if MARK in t:
    print(u'  已经是双通道版，跳过')
    raise SystemExit

# ---------- ① __init__ 增加 ch2 标志 ----------
old = "        self.opened = False          # 本次 _read 是否已经成功打开设备（看门狗用）"
new = ("        self.opened = False          # 本次 _read 是否已经成功打开设备（看门狗用）\n"
       "        self.ch2 = False             # 通道 1（电池 CAN）是否可用   " + MARK)
if t.count(old) == 1:
    t = t.replace(old, new, 1); n += 1; print(u'  [1] __init__ 已加 ch2 标志')

# ---------- ② snapshot 增加 ch 字段 ----------
old = """                'frames': OrderedDict(
                    (k, {'data': bytes(bytearray(v)).hex(' ').upper(),
                         'len': len(v),
                         'hz': round(self.stat[k]['hz'], 1),
                         'changed': self.stat[k]['changed'],
                         'age': round(now - self.stat[k]['last_t'], 2)})
                    for k, v in self.frames.items()),"""
new = """                'ch2': self.ch2,
                'frames': OrderedDict(
                    (k, {'data': bytes(bytearray(v)).hex(' ').upper(),
                         'len': len(v),
                         'hz': round(self.stat[k]['hz'], 1),
                         'changed': self.stat[k]['changed'],
                         'ch': 1 if k.endswith('@2') else 0,
                         'age': round(now - self.stat[k]['last_t'], 2)})
                    for k, v in self.frames.items()),"""
if t.count(old) == 1:
    t = t.replace(old, new, 1); n += 1; print(u'  [2] snapshot 已加 ch/ch2 字段')
else:
    print(u'  [2] ✗ 没匹配到 snapshot 的 frames 构造')

# ---------- ③ 启动通道 1 ----------
old = """        dll.VCI_ClearBuffer(DEVTYPE, DEVINDEX, 0)

        with self.lock:"""
new = """        dll.VCI_ClearBuffer(DEVTYPE, DEVINDEX, 0)

        # ---- 通道 1：电池 CAN（OBD 1/9）。打不开就降级为单通道，不影响通道 0。
        ch2 = False
        try:
            if dll.VCI_InitCAN(DEVTYPE, DEVINDEX, 1, byref(cfg)) == 1:
                if dll.VCI_StartCAN(DEVTYPE, DEVINDEX, 1) == 1:
                    dll.VCI_ClearBuffer(DEVTYPE, DEVINDEX, 1)
                    ch2 = True
        except Exception:
            ch2 = False
        self.ch2 = ch2
        print(u'  [CAN] 通道1(整车 CAN) 已启动; 通道2(电池 CAN) %s' % (
            u'已启动' if ch2 else u'不可用（未接线或设备不支持），降级为单通道'))

        with self.lock:"""
if t.count(old) == 1:
    t = t.replace(old, new, 1); n += 1; print(u'  [3] 通道 1 启动逻辑已插入')
else:
    print(u'  [3] ✗ 没匹配到 ClearBuffer(通道0) 的位置')

# ---------- ④ 接收循环：把入库逻辑抽成函数，两个通道都调 ----------
old = """        buf = (VCI_CAN_OBJ * 2000)()
        win_t, win_n = time.time(), 0
        while not self.stop_flag:
            n = dll.VCI_Receive(DEVTYPE, DEVINDEX, 0, buf, 2000, 50)
            now = time.time()
            if n > 0:
                with self.lock:
                    for i in range(n):
                        o = buf[i]
                        cid = '%03X' % (o.ID & 0x7FF) if not o.ExternFlag else '%08X' % o.ID
                        b = bytes(bytearray(o.Data))[:o.DataLen]
                        st = self.stat.get(cid)
                        if st is None:
                            self.stat[cid] = st = {'cnt': 0, 'hz': 0.0,
                                                   'last_t': now, 'changed': 0}
                        elif self.frames.get(cid) is not None:
                            old = self.frames[cid]
                            c = st['changed']
                            for k in range(min(len(old), len(b))):
                                if old[k] != b[k]:
                                    c += 1
                            st['changed'] = c
                        st['cnt'] += 1
                        st['last_t'] = now
                        self.frames[cid] = b
                        self.total += 1
                        win_n += 1
                    if now - win_t >= 2.0:
                        self.hz_total = win_n / (now - win_t)
                        for cid, st in self.stat.items():
                            st['hz'] = st['cnt'] / max(0.001, now - _BOOT)
                        win_t, win_n = now, 0"""
new = """        def ingest(ch, objs, cnt, now):
            \"\"\"把某一通道收到的一批帧记入统计表。ch=0 键名原样，ch=1 键名加 @2。\"\"\"
            got = 0
            with self.lock:
                for i in range(cnt):
                    o = objs[i]
                    base = '%03X' % (o.ID & 0x7FF) if not o.ExternFlag else '%08X' % o.ID
                    cid = base if ch == 0 else base + '@2'
                    b = bytes(bytearray(o.Data))[:o.DataLen]
                    st = self.stat.get(cid)
                    if st is None:
                        self.stat[cid] = st = {'cnt': 0, 'hz': 0.0,
                                               'last_t': now, 'changed': 0}
                    elif self.frames.get(cid) is not None:
                        old = self.frames[cid]
                        c = st['changed']
                        for k in range(min(len(old), len(b))):
                            if old[k] != b[k]:
                                c += 1
                        st['changed'] = c
                    st['cnt'] += 1
                    st['last_t'] = now
                    self.frames[cid] = b
                    self.total += 1
                    got += 1
            return got

        buf0 = (VCI_CAN_OBJ * 2000)()
        buf1 = (VCI_CAN_OBJ * 2000)()
        win_t, win_n = time.time(), 0
        while not self.stop_flag:
            # 两个通道各等 5ms（合计 10ms），既不互相饿死也不会把吞吐砍半
            n0 = dll.VCI_Receive(DEVTYPE, DEVINDEX, 0, buf0, 2000, 5)
            n1 = 0
            if ch2:
                n1 = dll.VCI_Receive(DEVTYPE, DEVINDEX, 1, buf1, 2000, 5)
            now = time.time()
            got = 0
            if n0 > 0:
                got += ingest(0, buf0, n0, now)
            if n1 > 0:
                got += ingest(1, buf1, n1, now)
            if got:
                win_n += got
                if now - win_t >= 2.0:
                    self.hz_total = win_n / (now - win_t)
                    for cid, st in self.stat.items():
                        st['hz'] = st['cnt'] / max(0.001, now - _BOOT)
                    win_t, win_n = now, 0"""
if t.count(old) == 1:
    t = t.replace(old, new, 1); n += 1; print(u'  [4] 接收循环已改为双通道')
else:
    print(u'  [4] ✗ 没匹配到接收循环原文（长度 %d）' % len(old))

if n < 4:
    print(u'\n  ✗ 只成功 %d/4 处，**不写盘**（避免半成品）' % n)
    raise SystemExit(1)

io.open(P, 'w', encoding='utf-8').write(t)
print(u'\n  已写盘 %d 处，%d -> %d 字符' % (n, len(orig), len(t)))

# 回读自检
t2 = io.open(P, encoding='utf-8').read()
print(u'  回读:')
for k in (MARK, 'self.ch2 = ch2', "'ch': 1 if k.endswith('@2') else 0",
          'def ingest(ch, objs, cnt, now)', 'VCI_Receive(DEVTYPE, DEVINDEX, 1, buf1, 2000, 5)',
          'buf1 = (VCI_CAN_OBJ * 2000)()'):
    print(u'    %-58s %s' % (k[:56], u'✓' if k in t2 else u'✗'))

# -*- coding: utf-8 -*-
"""
镭神 C32 激光雷达 · 直连本机 UDP 抓包 / 解码 / 点云出图
=================================================================
适用场景：雷达网线**直接插在本机网口**（不经过车机 ROS）。
此时没有 ROS，需要直接解析镭神雷达的 UDP 报文。

镭神 C32 默认网络参数（常见出厂值）：
    雷达 IP     192.168.1.222
    本机 IP     192.168.1.102 或同网段任意（本机现为 192.168.1.109）
    子网掩码    255.255.255.0
    MSOP 数据口 2368   ← 点云测距数据（UDP，单向推送到本机）
    DIFOP 信息口 7788  ← 设备信息/配置（可读雷达型号、转速、IP）

用法：
    python lidar_udp.py --probe                  # 抓包侦察：抓几包，打印结构与十六进制
    python lidar_udp.py --probe --secs 8         # 多抓一会
    python lidar_udp.py --view                   # 直接抓包并出点云三联图
    python lidar_udp.py --view --out E:\\AI输出\\激光雷达点云\\直连点云.png
"""
import io
import os
import sys
import time
import socket
import struct
import argparse
import collections

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

MSOP_PORT = 2368
DIFOP_PORT = 7788
LOCAL_IP = '0.0.0.0'

# 镭神 C32 的 32 线垂直角（度），从下到上
C32_ANGLES = [
    -16.042, -15.008, -13.973, -12.939, -11.905, -10.871, -9.837, -8.803,
    -7.769, -6.735, -5.701, -4.667, -3.633, -2.599, -1.565, -0.531,
    0.503, 1.537, 2.571, 3.605, 4.639, 5.673, 6.707, 7.741,
    8.775, 9.809, 10.843, 11.877, 12.911, 13.945, 14.979, 16.013,
]


def bind(port, secs=5.0, ip=LOCAL_IP):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8 * 1024 * 1024)
    except Exception:
        pass
    s.bind((ip, port))
    s.settimeout(secs)
    return s


# ----------------------------------------------------------------------------
# 侦察：把真实报文抓下来看结构，不预设格式
# ----------------------------------------------------------------------------
def probe(secs):
    print('=== 镭神 C32 直连抓包侦察 ===')
    print('  监听 UDP %d (MSOP 数据) 与 %d (DIFOP 信息)…' % (MSOP_PORT, DIFOP_PORT))
    print()
    got_any = False
    for port, label in ((MSOP_PORT, 'MSOP 点云'), (DIFOP_PORT, 'DIFOP 设备信息')):
        try:
            s = bind(port, secs)
        except Exception as e:
            print('  [x] 端口 %d 绑定失败: %s' % (port, e))
            continue
        sizes = collections.Counter()
        first = None
        src = None
        n = 0
        t0 = time.time()
        while time.time() - t0 < secs:
            try:
                data, addr = s.recvfrom(65535)
            except socket.timeout:
                break
            n += 1
            sizes[len(data)] += 1
            if first is None:
                first = data
                src = addr
        s.close()
        dt = time.time() - t0
        print('  ── %s  端口 %d ──' % (label, port))
        if n == 0:
            print('     没有收到任何 UDP 包')
            print()
            continue
        got_any = True
        print('     来源        : %s:%d' % (src[0], src[1]))
        print('     收包        : %d 个 / %.1f s  (约 %.0f 包/秒)' % (n, dt, n / dt if dt else 0))
        print('     报文长度分布: %s' % dict(sizes))
        L = len(first)
        print('     首包长度    : %d 字节' % L)
        hx = ' '.join('%02X' % b for b in first[:64])
        print('     前 64 字节  : %s' % hx)
        # 结构猜测
        if L == 1206:
            print('     >>> 长度 1206 = 镭神 32 线标准 MSOP 包（2 头 + 12×100 块 + 4 尾）')
        elif L == 1248:
            print('     >>> 长度 1248 = 镭神 16/32 线另一种 MSOP 包')
        print('     前两字节    : %02X %02X %s' % (
            first[0], first[1], '(0xFF 0xEE = 镭神标准帧头)' if first[0] == 0xFF and first[1] == 0xEE else ''))
        print()
    if not got_any:
        print('  [x] 两个端口都没收到数据。排查：')
        print('      1) 雷达供电了吗（镭神 C32 需独立 DC 供电，网线不供电）')
        print('      2) 网线插在主板自带 RJ45 口上吗（不是 USB 网卡）')
        print('      3) 本机网卡有没有链路： Get-NetAdapter -Name 以太网')
        print('      4) 本机 IP 是否与雷达同网段（雷达默认 192.168.1.222）')
        print('      5) 防火墙是否拦了 UDP 入站')
        return False
    return True


# ----------------------------------------------------------------------------
# 解码 MSOP -> 点云
# ----------------------------------------------------------------------------
def decode_msop(pkt):
    """解析镭神 C32 MSOP 包，返回 [(x,y,z,intensity)]。失败返回 []。"""
    if len(pkt) < 1206 or pkt[0] != 0xFF or pkt[1] != 0xEE:
        return []
    pts = []
    for blk in range(12):
        off = 2 + blk * 100
        if off + 100 > len(pkt):
            break
        az = struct.unpack_from('<H', pkt, off)[0] / 100.0     # 0.01 度
        for ch in range(32):
            p = off + 2 + ch * 3
            if p + 3 > len(pkt):
                break
            dist = struct.unpack_from('<H', pkt, p)[0]
            inten = pkt[p + 2]
            if dist == 0:
                continue
            r = dist / 100.0                                    # 厘米 -> 米
            if r < 0.2 or r > 200.0:
                continue
            a = math.radians(az)
            e = math.radians(C32_ANGLES[ch])
            x = r * math.cos(e) * math.cos(a)
            y = r * math.cos(e) * math.sin(a)
            z = r * math.sin(e)
            pts.append((x, y, z, float(inten), az, C32_ANGLES[ch]))
    return pts


def view(secs, out):
    import math  # noqa
    print('=== 直连抓包并出点云 ===')
    try:
        s = bind(MSOP_PORT, 2.0)
    except Exception as e:
        print('  [x] 端口 %d 绑定失败: %s' % (MSOP_PORT, e))
        return 2
    allpts = []
    pkts = 0
    sizes = collections.Counter()
    t0 = time.time()
    while time.time() - t0 < secs:
        try:
            data, addr = s.recvfrom(65535)
        except socket.timeout:
            continue
        pkts += 1
        sizes[len(data)] += 1
        allpts.extend(decode_msop(data))
    s.close()
    print('  收包 %d 个，用时 %.1f s' % (pkts, time.time() - t0))
    print('  报文长度分布: %s' % dict(sizes))
    if not allpts:
        print('  [x] 没有解析出点。若长度不是 1206，请先用 --probe 看实际结构。')
        return 2
    pts = [(p[0], p[1], p[2]) for p in allpts]
    inten = [p[3] for p in allpts]
    print('  解析点数 %d' % len(pts))
    # 环形去重：同角度保留最近的点（镭神每圈会重复扫描）
    dedup = {}
    for p in allpts:
        key = (round(p[4] / 0.5), round(p[5] / 0.5))
        if key not in dedup or p[0] ** 2 + p[1] ** 2 < dedup[key][0] ** 2 + dedup[key][1] ** 2:
            dedup[key] = p
    dpts = [(p[0], p[1], p[2]) for p in dedup.values()]
    dint = [p[3] for p in dedup.values()]
    print('  去重后     %d' % len(dpts))

    import lidar_view
    lidar_view.frame = 'laser (直连 UDP)'
    lidar_view.render(dpts, dint, out, title='镭神 C32 · 直连本机')
    return 0


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--probe', action='store_true')
    ap.add_argument('--view', action='store_true')
    ap.add_argument('--secs', type=float, default=5.0)
    ap.add_argument('--out', default=r'E:\AI输出\激光雷达点云\直连点云.png')
    a = ap.parse_args()
    import math  # noqa
    if a.probe:
        sys.exit(0 if probe(a.secs) else 2)
    if a.view:
        sys.exit(view(a.secs, a.out))
    ap.print_help()

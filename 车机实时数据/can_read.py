# -*- coding: utf-8 -*-
"""
创芯科技 CANalyst-II / USBCAN 读取器（ctypes 直连 ControlCAN.dll，无需上位机）
=================================================================
    python can_read.py                       # 500k，抓 8 秒，列出 CAN ID 分布
    python can_read.py --seconds 15
    python can_read.py --bitrate 250k
    python can_read.py --ch 1                # 第二路 CAN
    python can_read.py --listen-only         # 只听不应答（不干扰总线）

注意：DeviceType 4 = VCI_USBCAN2（CANalyst-II 用这个）。
"""

import argparse
import collections
import ctypes
import sys
import time
from ctypes import POINTER, Structure, byref, c_int, c_ubyte, c_uint32, c_uint64

DLL_CANDIDATES = [
    u'新能源汽车智能检测系统-1.0版.html',
    u'新能源汽车智能检测系统-美化，实测改进版.html',
    u'新能源汽车智能检测系统.html',
]

# ---- 设备类型
VCI_USBCAN1 = 3
VCI_USBCAN2 = 4
VCI_USBCAN2A = 4
VCI_USBCAN_E_U = 20
VCI_USBCAN_2E_U = 21
DEV_TYPES = [VCI_USBCAN2, VCI_USBCAN1, VCI_USBCAN_E_U, VCI_USBCAN_2E_U]

# ---- 波特率 -> (Timing0, Timing1)  16MHz 时钟
BITRATE = {
    '1000k': (0x00, 0x14), '800k': (0x00, 0x16), '500k': (0x00, 0x1C),
    '250k': (0x01, 0x1C), '125k': (0x03, 0x1C), '100k': (0x04, 0x1C),
    '50k': (0x09, 0x1C), '20k': (0x18, 0x1C), '10k': (0x31, 0x1C),
}


class VCI_INIT_CONFIG(Structure):
    _fields_ = [('AccCode', c_uint32), ('AccMask', c_uint32), ('Reserved', c_uint32),
                ('Filter', c_ubyte), ('Timing0', c_ubyte), ('Timing1', c_ubyte),
                ('Mode', c_ubyte)]


class VCI_CAN_OBJ(Structure):
    _fields_ = [('ID', c_uint32), ('TimeStamp', c_uint32), ('TimeFlag', c_ubyte),
                ('SendType', c_ubyte), ('RemoteFlag', c_ubyte), ('ExternFlag', c_ubyte),
                ('DataLen', c_ubyte), ('Data', c_ubyte * 8), ('Reserved', c_ubyte * 3)]


class VCI_BOARD_INFO(Structure):
    _fields_ = [('hw_Version', ctypes.c_uint16), ('fw_Version', ctypes.c_uint16),
                ('dr_Version', ctypes.c_uint16), ('in_Version', ctypes.c_uint16),
                ('irq_Num', ctypes.c_uint16), ('can_Num', c_ubyte),
                ('str_Serial_Num', c_ubyte * 20), ('str_hw_Type', c_ubyte * 40),
                ('Reserved', c_ubyte * 4)]


def load_dll():
    for p in DLL_CANDIDATES:
        try:
            d = ctypes.WinDLL(p)
        except OSError:
            continue
        d.VCI_OpenDevice.argtypes = [c_uint32, c_uint32, c_uint32]
        d.VCI_OpenDevice.restype = c_uint32
        d.VCI_CloseDevice.argtypes = [c_uint32, c_uint32]
        d.VCI_CloseDevice.restype = c_uint32
        d.VCI_InitCAN.argtypes = [c_uint32, c_uint32, c_uint32, POINTER(VCI_INIT_CONFIG)]
        d.VCI_InitCAN.restype = c_uint32
        d.VCI_StartCAN.argtypes = [c_uint32, c_uint32, c_uint32]
        d.VCI_StartCAN.restype = c_uint32
        d.VCI_ResetCAN.argtypes = [c_uint32, c_uint32, c_uint32]
        d.VCI_ResetCAN.restype = c_uint32
        d.VCI_ClearBuffer.argtypes = [c_uint32, c_uint32, c_uint32]
        d.VCI_ClearBuffer.restype = c_uint32
        d.VCI_GetReceiveNum.argtypes = [c_uint32, c_uint32, c_uint32]
        d.VCI_GetReceiveNum.restype = c_uint32
        d.VCI_Receive.argtypes = [c_uint32, c_uint32, c_uint32,
                                  POINTER(VCI_CAN_OBJ), c_uint32, c_int]
        d.VCI_Receive.restype = c_uint32
        d.VCI_ReadBoardInfo.argtypes = [c_uint32, c_uint32, POINTER(VCI_BOARD_INFO)]
        d.VCI_ReadBoardInfo.restype = c_uint32
        return d, p
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seconds', type=float, default=8.0)
    ap.add_argument('--bitrate', default='500k')
    ap.add_argument('--ch', type=int, default=0, help='CAN 通道 0 或 1')
    ap.add_argument('--devtype', type=int, default=0, help='0=自动尝试')
    ap.add_argument('--listen-only', action='store_true')
    args = ap.parse_args()

    if args.bitrate not in BITRATE:
        print('不支持的波特率，可选：%s' % ', '.join(BITRATE))
        sys.exit(1)
    t0, t1 = BITRATE[args.bitrate]

    dll, path = load_dll()
    if dll is None:
        print('找不到可加载的 ControlCAN.dll，尝试过：')
        for p in DLL_CANDIDATES:
            print('   ', p)
        sys.exit(2)
    print('已加载驱动: %s' % path)

    devtypes = [args.devtype] if args.devtype else DEV_TYPES
    opened = None
    for dt in devtypes:
        r = dll.VCI_OpenDevice(dt, 0, 0)
        if r == 1:
            opened = dt
            print('打开设备成功  DeviceType=%d' % dt)
            break
        else:
            print('  DeviceType=%d 打开失败 (ret=%d)' % (dt, r))
    if opened is None:
        print('\n所有 DeviceType 都打不开设备。可能原因：')
        print('  · 分析仪没插好 / 没上电')
        print('  · 被上位机软件占用（先关掉 USB_CAN TOOL）')
        print('  · 驱动不对（设备应显示为 Chuangxin Tech USBCAN/CANalyst-II）')
        sys.exit(3)

    info = VCI_BOARD_INFO()
    if dll.VCI_ReadBoardInfo(opened, 0, byref(info)) == 1:
        sn = bytes(bytearray(info.str_Serial_Num)).split(b'\x00')[0].decode('ascii', 'replace')
        hw = bytes(bytearray(info.str_hw_Type)).split(b'\x00')[0].decode('ascii', 'replace')
        print('板卡信息: 硬件=%s 序列号=%s 通道数=%d 固件=0x%04X'
              % (hw, sn, info.can_Num, info.fw_Version))

    cfg = VCI_INIT_CONFIG()
    cfg.AccCode = 0x00000000
    cfg.AccMask = 0xFFFFFFFF          # 接收全部
    cfg.Filter = 1
    cfg.Timing0 = t0
    cfg.Timing1 = t1
    cfg.Mode = 1 if args.listen_only else 0
    r = dll.VCI_InitCAN(opened, 0, args.ch, byref(cfg))
    print('初始化 CAN%d @ %s -> %s' % (args.ch, args.bitrate, '成功' if r == 1 else '失败(%d)' % r))
    if r != 1:
        dll.VCI_CloseDevice(opened, 0)
        sys.exit(4)
    r = dll.VCI_StartCAN(opened, 0, args.ch)
    print('启动 CAN%d -> %s' % (args.ch, '成功' if r == 1 else '失败(%d)' % r))
    if r != 1:
        dll.VCI_CloseDevice(opened, 0)
        sys.exit(5)
    dll.VCI_ClearBuffer(opened, 0, args.ch)

    print('\n开始采集 %.0f 秒 ...\n' % args.seconds)
    ids = collections.Counter()
    last = {}
    buf = (VCI_CAN_OBJ * 2000)()
    total = 0
    t_start = time.time()
    while time.time() - t_start < args.seconds:
        n = dll.VCI_Receive(opened, 0, args.ch, buf, 2000, 50)
        if n <= 0:
            time.sleep(0.005)
            continue
        for i in range(n):
            o = buf[i]
            if o.ExternFlag:
                cid = '%08X' % o.ID
            else:
                cid = '%03X' % (o.ID & 0x7FF)
            ids[cid] += 1
            total += 1
            last[cid] = (bytes(bytearray(o.Data))[:o.DataLen]).hex(' ').upper()

    dll.VCI_CloseDevice(opened, 0)

    elapsed = time.time() - t_start
    print('=' * 76)
    print('采集完成：%d 帧 / %.1f 秒  ≈ %.0f 帧/秒   不同 CAN ID %d 个'
          % (total, elapsed, total / elapsed if elapsed else 0, len(ids)))
    print('=' * 76)
    if not total:
        print('\n没有收到任何帧。可能原因：')
        print('  · 波特率不对（整车/底盘/电池总线常见 500k，也有 250k）')
        print('  · 分析仪的 CANH/CANL 接反了')
        print('  · 接的那对引脚上没有总线（OBD 有 5 对 CAN，接错一对就没数据）')
        print('  · 总线没上电（车处于下电状态）')
        return
    print('\n%-8s %9s  %s' % ('CAN ID', '帧数', '最近一帧数据'))
    print('-' * 76)
    for cid, c in ids.most_common(60):
        print('%-8s %9d  %s' % (cid, c, last.get(cid, '')))


if __name__ == '__main__':
    main()

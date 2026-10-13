# -*- coding: utf-8 -*-
"""
车机 CAN 实时数据桥（创芯 CANalyst-II 直读）
=================================================================
用 ctypes 直连 ControlCAN.dll 读整车 CAN，解码已知帧，并用 HTTP 提供给看板。

    python can_bridge.py --open

接口
    GET /                    看板页面
    GET /api/vehicle         解码后的车辆状态（车速/档位/EPB/巡航/踏板/转向/轮速…）
    GET /api/frames          全部 CAN 帧的实时字节 + 帧率 + 变化位
    GET /api/meta            总线统计

解码依据
    `E:\AI输出\车机调试文档\车机调试完整记录.md` 里**逐字节实测**出来的帧表
    （2026-09-27 实测记录：车辆起步加速时 Can_32A 车速由 1 → 115 → 505 → 567 → 99），
    并用本轮现场抓包复核（32A 静止基线 = 1 完全吻合；226 帧油门/刹车指令逐字节吻合）。
"""

import argparse
import ctypes
import io
import json
import os
import socket
import subprocess
import sys
import threading
import time
from collections import OrderedDict
from ctypes import POINTER, Structure, byref, c_int, c_ubyte, c_uint32, c_uint64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

SITE = os.path.dirname(HERE)
_CAND = [
    u'新能源汽车智能检测系统-1.0版.html',
    u'新能源汽车智能检测系统-美化，实测改进版.html',
    u'新能源汽车智能检测系统.html',
]


def find_html():
    for c in _CAND:
        p = os.path.join(SITE, c)
        if os.path.isfile(p):
            return p
    import glob
    hits = [p for p in glob.glob(os.path.join(SITE, '*.html'))
            if u'智能检测系统' in os.path.basename(p) and u'原版' not in os.path.basename(p)]
    return max(hits, key=os.path.getmtime) if hits else os.path.join(SITE, _CAND[0])


HTML_PATH = find_html()

# ----------------------------------------------------------------- 驱动
# 第一项是「脚本/打包产物所在目录」——打包成 exe 后 ControlCAN.dll 随包放在
# _MEIPASS 里，只写死绝对路径会找不到；放最前面即可同时覆盖源码运行与 exe 运行。
DLL_CANDIDATES = [os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ControlCAN.dll'),
                  r'E:\csblda\ControlCAN.dll', r'E:\xun\CHE\csb\ControlCAN.dll',
                  r'C:\Windows\System32\ControlCAN.dll']
DEVTYPE = 4                       # VCI_USBCAN2 = CANalyst-II
DEVINDEX = 0
TIMING = (0x00, 0x1C)             # 500 kbps @16MHz


class VCI_INIT_CONFIG(Structure):
    _fields_ = [('AccCode', c_uint32), ('AccMask', c_uint32), ('Reserved', c_uint32),
                ('Filter', c_ubyte), ('Timing0', c_ubyte), ('Timing1', c_ubyte), ('Mode', c_ubyte)]


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
        d.VCI_ClearBuffer.argtypes = [c_uint32, c_uint32, c_uint32]
        d.VCI_ClearBuffer.restype = c_uint32
        d.VCI_ReadBoardInfo.argtypes = [c_uint32, c_uint32, POINTER(VCI_BOARD_INFO)]
        d.VCI_ReadBoardInfo.restype = c_uint32
        d.VCI_Receive.argtypes = [c_uint32, c_uint32, c_uint32, POINTER(VCI_CAN_OBJ),
                                  c_uint32, c_int]
        d.VCI_Receive.restype = c_uint32
        return d, p
    return None, None


# ----------------------------------------------------------------- 采集线程
def canalyst_present():
    """CANalyst-II 此刻在不在（PnP 里有 VID_04D8 就说明插着且驱动已装）。

    ★为什么要单独查这个：`VCI_OpenDevice` 失败**只返回 0**，不告诉你原因。
      而 USB-CAN 这类 WinUSB 独占设备**同一时刻只能被一个程序打开** ——
      于是"没插好"和"被别的程序占用"会表现成同一个错误，让人无从下手。
      先用 PnP 确认设备在不在，就能把这两种情况分开：
        设备在   → 一定是被占用（实测常见占用者：Etest 雷达标定工具、CANTest、另一份 can_bridge）
        设备不在 → 线没插好 / 驱动没装
    ★注意：Windows 11 已经没有 wmic 了，必须用 PowerShell Get-PnpDevice。
    ★再注意：**必须用 `Measure-Object` 计数，不能用 `(...).Count`** ——
      实测设备恰好只有 1 个时，`(Get-PnpDevice ... | Where-Object ...).Count`
      会**什么都不输出**（stdout 为空），于是这里恒返回 False，
      把"设备被占用"误报成"找不到分析仪"，反而更难排查。
    """
    if os.name != 'nt':
        return False
    try:
        r = subprocess.run(
            ['powershell', '-NoProfile', '-NonInteractive', '-Command',
             '[Console]::OutputEncoding=[Text.Encoding]::UTF8; '
             '(Get-PnpDevice -PresentOnly -EA SilentlyContinue | '
             'Where-Object { $_.InstanceId -like "*VID_04D8*" } | '
             'Measure-Object).Count'],
            capture_output=True, timeout=20,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        txt = (r.stdout or b'').decode('utf-8', 'replace').strip()
        return txt.isdigit() and int(txt) > 0
    except Exception:
        return False


class CanReader(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self.lock = threading.Lock()
        self.frames = OrderedDict()      # id -> 最近一帧字节
        self.stat = {}                   # id -> {cnt, hz, first, changed, last_t}
        self.ok = False
        self.err = ''
        self.board = ''
        self.hz_total = 0.0
        self.total = 0
        self.stop_flag = False
        self.opened = False          # 本次 _read 是否已经成功打开设备（看门狗用）
        self.ch2 = False             # 通道 1（电池 CAN）是否可用
        self.chan_of = {}            # id -> 来源通道（0/1），仅排查用   # ==== CX-DUALCH BEGIN ====

    def snapshot(self):
        with self.lock:
            now = time.time()
            return {
                'ok': self.ok, 'err': self.err, 'board': self.board,
                'hz_total': round(self.hz_total, 1), 'total': self.total,
                'ch2': self.ch2,
                'frames': OrderedDict(
                    (k, {'data': bytes(bytearray(v)).hex(' ').upper(),
                         'len': len(v),
                         'hz': round(self.stat[k]['hz'], 1),
                         'changed': self.stat[k]['changed'],
                         'ch': self.chan_of.get(k, 0),
                         'age': round(now - self.stat[k]['last_t'], 2)})
                    for k, v in self.frames.items()),
            }

    def run(self):
        while not self.stop_flag:
            self.opened = False
            # ★看门狗：USB-CAN 设备被别的程序占用时，`VCI_OpenDevice` 会
            #   **卡住不返回** —— 既不抛异常也拿不到错误码，界面只会一直"未连接"，
            #   用户完全看不出是被别的软件抢了设备（实测被 Etest 占用就是这样）。
            #   所以只能用超时来提示。
            wd = threading.Timer(6.0, self._warn_if_stuck)
            wd.daemon = True
            wd.start()
            try:
                self._read()
            except Exception as e:
                with self.lock:
                    self.ok = False
                    self.err = '%s: %s' % (type(e).__name__, e)
            finally:
                wd.cancel()
            time.sleep(2.0)

    def _warn_if_stuck(self):
        if self.opened:
            return
        msg = (u'打开 CAN 设备超过 6 秒无响应 —— 设备多半被【别的程序占用】。'
               u'USB-CAN 同一时刻只能被一个进程打开，常见占用者：'
               u'Etest 雷达标定工具、CANTest、另一份 can_bridge。'
               u'把它们关掉后本桥接会自动重连。')
        with self.lock:
            self.err = msg
        print(u'  [!] %s' % msg)

    def _read(self):
        dll, path = load_dll()
        if dll is None:
            raise IOError('找不到 ControlCAN.dll')
        if dll.VCI_OpenDevice(DEVTYPE, DEVINDEX, 0) != 1:
            # VCI_OpenDevice 失败只返回 0、不给原因。用 PnP 把两种情况分开说清楚，
            # 否则用户看到的就是一句含糊的"打开失败"，根本不知道该去查哪里。
            if canalyst_present():
                raise IOError(
                    u'CAN 分析仪被【别的程序占用】—— USB-CAN 设备同一时刻只能被一个进程打开。'
                    u'常见占用者：Etest 雷达标定工具、CANTest、另一份 can_bridge；'
                    u'关掉它们即可（本桥接会自动重连）')
            raise IOError(u'找不到 CAN 分析仪 —— 检查 USB 是否插好、驱动是否安装')
        info = VCI_BOARD_INFO()
        board = 'USBCAN'
        if dll.VCI_ReadBoardInfo(DEVTYPE, DEVINDEX, byref(info)) == 1:
            board = bytes(bytearray(info.str_hw_Type)).split(b'\x00')[0].decode('ascii', 'replace')
        cfg = VCI_INIT_CONFIG()
        cfg.AccCode = 0
        cfg.AccMask = 0xFFFFFFFF
        cfg.Filter = 1
        cfg.Timing0, cfg.Timing1 = TIMING
        cfg.Mode = 0
        if dll.VCI_InitCAN(DEVTYPE, DEVINDEX, 0, byref(cfg)) != 1:
            dll.VCI_CloseDevice(DEVTYPE, DEVINDEX)
            raise IOError('初始化 CAN 失败')
        if dll.VCI_StartCAN(DEVTYPE, DEVINDEX, 0) != 1:
            dll.VCI_CloseDevice(DEVTYPE, DEVINDEX)
            raise IOError('启动 CAN 失败')
        dll.VCI_ClearBuffer(DEVTYPE, DEVINDEX, 0)

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

        with self.lock:
            self.ok = True
            self.err = ''
            self.board = '%s (DeviceType=%d)' % (board, DEVTYPE)
        self.opened = True

        def ingest(ch, objs, cnt, now):
            """把某一通道收到的一批帧记入统计表。ch=0 键名原样，ch=1 键名加 @2。"""
            got = 0
            with self.lock:
                for i in range(cnt):
                    o = objs[i]
                    cid = '%03X' % (o.ID & 0x7FF) if not o.ExternFlag else '%08X' % o.ID
                    b = bytes(bytearray(o.Data))[:o.DataLen]
                    # 记录来源通道（仅排查用）。★不加后缀★：见文件头那段说明 ——
                    # ControlCAN.dll 双通道下数据落到哪个通道不确定，加后缀会把
                    # 整车数据误标成电池通道，并让 decode() 查不到 ID。
                    self.chan_of[cid] = ch
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
                    win_t, win_n = now, 0

    # ------- 取某个 ID 的当前字节
    def b(self, cid):
        with self.lock:
            v = self.frames.get(cid)
        return bytes(v) if v else None


_BOOT = time.time()
READER = CanReader()


# ----------------------------------------------------------------- 解码
def _u16be(b, i):
    return (b[i] << 8) | b[i + 1]


def _u16le(b, i):
    return b[i] | (b[i + 1] << 8)


def decode():
    """按逐字节实测的帧表解码。取不到帧的字段返回 None。"""
    r = {}
    b32 = READER.b('32A')
    b111 = READER.b('111')
    b118 = READER.b('118')
    b208 = READER.b('208')
    b226 = READER.b('226')     # 控制指令（仅控制节点运行时出现）
    b245 = READER.b('245')
    b1A3 = READER.b('1A3')
    b1A5 = READER.b('1A5')
    b23A = READER.b('23A')
    b205 = READER.b('205')
    b668 = READER.b('668')
    b618 = READER.b('618')
    b338 = READER.b('338')     # 电池：SOC
    b636 = READER.b('636')     # 电池：总压
    b45A = READER.b('45A')     # 电池：总压备份
    b264 = READER.b('264')     # 电池：温度
    b235 = READER.b('235')     # 电池：电流/辅助量

    # 车速：Can_32A byte2-3 大端；实测静止基线 = 1
    if b32:
        raw = _u16be(b32, 2)
        r['speed_raw'] = raw
        r['speed_kmh'] = round(max(0, raw - 1) * 0.1, 1)      # 0.1 km/h 标度（按平台惯例）
        r['speed_basis'] = 'Can_32A byte2-3 大端；静止基线 1'

    # 档位：Can_111（实测挂 N 档时 byte4/byte6 变化）
    if b111:
        r['gear_raw'] = b111[6]
        r['gear_b4'] = b111[4]
        r['gear_basis'] = 'Can_111 byte4/byte6，实测 N 档 00..11 → C0..41'

    # 巡航 / EPB：Can_118
    if b118:
        r['cruise_switch'] = (b118[1] >> 2) & 1
        r['cruise_ctrl'] = b118[1]
        r['epb'] = b118[2] & 1
        r['epb_raw_b2'] = b118[2]
        r['cruise_basis'] = 'Can_118 byte1 bit2=巡航开关；byte2 bit0=EPB（实测）'

    # VCU 就绪：Can_208 byte3（实测 00 → 50）
    if b208:
        r['vcu_ready'] = b208[3]
        r['acc_pedal_fb'] = b208[0]
        r['brk_pedal_fb'] = b208[1]
        r['vcu_basis'] = 'Can_208 byte3 非 0 = 整车就绪/自动模式（实测最可靠判据）'

    # 控制指令：Can_226（油门/刹车执行器，实测逐字节吻合）
    if b226:
        r['acc_cmd'] = b226[0]
        r['acc_cmd_inv'] = b226[1]
        r['brk_cmd'] = b226[2]
        r['brk_cmd_inv'] = b226[3]
        r['cmd_basis'] = 'Can_226 byte0=油门位置 byte1=反值 byte2=刹车 byte3=反值（实测吻合）'

    # 转向：Can_245 / 1A3 / 1A5
    if b245:
        r['steer_cmd'] = _u16be(b245, 2)
    if b1A3:
        r['steer_angle_raw'] = _u16be(b1A3, 4)
        r['eps_mode'] = b1A3[2]
        r['steer_basis'] = 'Can_1A3 = EPSDir/EPSMODE/StrAngle；Can_1A5 byte2 = 转向角速度'
    if b1A5:
        r['steer_rate'] = b1A5[2]

    # 四轮轮速：Can_23A
    if b23A:
        r['wheel_raw'] = list(b23A[:4])

    # 横摆角速度 / 纵向加速度：Can_205
    if b205:
        r['yaw_raw'] = list(b205[2:6])
        r['motion_basis'] = 'Can_205 = YawRate / LongAcc'

    # 踏板：Can_668 byte2
    if b668:
        r['pedal_raw'] = b668[2]

    # 刹车灯：Can_618
    if b618:
        r['brake_light_raw'] = b618[2]

    # ---------------- 电池（BMS）----------------
    # ★原 decode 表里没有电池，下面几条是 2026-10-11 用「激励—观测」实测确认的：
    #   0x636 byte0-1 与 0x45A byte2-3 均为 0x0FA0=4000 ⇒ 400.0 V（双报文印证）
    #   0x338 byte4 = 51，与仪表盘 SOC 51% 一致；15 分钟内 52→51 单调下降
    #   0x264 byte2 = 15→17→19→20 ℃，随车动作单调上升
    #   0x235 byte2 静止 0、给油 391/1428；byte5-6 含义未确认，不冒充电压
    #   本平台无官方 DBC，换算系数按行业惯例，信号名未经厂商确认。
    if b636:
        r['pack_voltage'] = round(((b636[0] << 8) | b636[1]) * 0.1, 1)
        r['pack_voltage_basis'] = 'Can_636 byte0-1 x0.1（与 Can_45A byte2-3 一致）'
    if b45A:
        r['pack_voltage_alt'] = round(((b45A[2] << 8) | b45A[3]) * 0.1, 1)
    if b338:
        r['soc_percent'] = b338[4]
        r['soc_basis'] = 'Can_338 byte4 原值 %（与仪表盘 51% 实测一致）'
    if b264:
        r['battery_temp_c'] = b264[2]
    if b235:
        r['battery_current_raw'] = b235[2]
        r['battery_aux_raw'] = (b235[5] << 8) | b235[6]

    return r


# ----------------------------------------------------------------- HTTP
def payload_vehicle():
    snap = READER.snapshot()
    return {'ok': snap['ok'], 'err': snap['err'], 'board': snap['board'],
            'hz_total': snap['hz_total'], 'total': snap['total'],
            'ids': len(snap['frames']),
            'signal': decode(),
            'frames': snap['frames']}


def payload_frames():
    s = READER.snapshot()
    return {'ok': s['ok'], 'err': s['err'], 'board': s['board'],
            'hz_total': s['hz_total'],
            'count': len(s['frames']), 'frames': s['frames']}


def payload_meta():
    s = READER.snapshot()
    f = s['frames']
    live = [k for k, v in f.items() if v['age'] is not None and v['age'] < 3]
    return {'ok': s['ok'], 'err': s['err'], 'board': s['board'],
            'hz_total': s['hz_total'], 'total': s['total'],
            'ids_total': len(f), 'ids_live': len(live),
            'silent': [k for k in f if k not in live],
            'server_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'driver': 'ControlCAN.dll (Chuangxin CANalyst-II, 500kbps)'}


ROUTES = {'/api/vehicle': payload_vehicle, '/api/frames': payload_frames,
          '/api/meta': payload_meta}


class Handler(BaseHTTPRequestHandler):
    server_version = 'ChxzCAN/1.0'

    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype):
        if isinstance(body, str):
            body = body.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Private-Network', 'true')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        try:
            self.wfile.write(body)
        except Exception:
            pass

    def _json(self, o, code=200):
        self._send(code, json.dumps(o, ensure_ascii=False, default=str),
                   'application/json; charset=utf-8')

    def do_OPTIONS(self):
        self._send(200, b'', 'text/plain')

    def do_GET(self):
        p = self.path.split('?')[0].rstrip('/') or '/'
        if p in ROUTES:
            try:
                self._json(ROUTES[p]())
            except Exception as e:
                self._json({'ok': False, 'error': '%s: %s' % (type(e).__name__, e)}, 500)
            return
        if p in ('/', '/index.html'):
            try:
                with io.open(HTML_PATH, encoding='utf-8') as fp:
                    self._send(200, fp.read(), 'text/html; charset=utf-8')
            except Exception as e:
                self._send(500, '读取页面失败: %s' % e, 'text/plain; charset=utf-8')
            return
        if p == '/api/health':
            self._json({'ok': True})
            return
        self._send(404, 'not found', 'text/plain; charset=utf-8')


def pick_port(host, want, tries=12):
    for p in range(want, want + tries):
        s = socket.socket()
        try:
            s.bind((host, p))
            s.close()
            return p
        except OSError:
            s.close()
    raise IOError('端口全占用')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=8780)
    ap.add_argument('--open', action='store_true')
    args = ap.parse_args()

    READER.start()
    time.sleep(3.0)
    port = pick_port(args.host, args.port)
    srv = ThreadingHTTPServer((args.host, port), Handler)
    srv.daemon_threads = True
    url = 'http://%s:%d/' % (args.host, port)
    snap = READER.snapshot()
    print('CAN 采集: %s  %s' % ('OK' if snap['ok'] else '失败', snap['err'] or snap['board']))
    print('总线速率: %.0f 帧/秒   ID 数: %d' % (snap['hz_total'], len(snap['frames'])))
    print('\n看板地址 : %s' % url)
    print('接口     : /api/vehicle  /api/frames  /api/meta\n')
    if args.open:
        os.startfile(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        READER.stop_flag = True
        print('\n已停止')


if __name__ == '__main__':
    main()

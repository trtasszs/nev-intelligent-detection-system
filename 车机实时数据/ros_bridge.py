# -*- coding: utf-8 -*-
"""
车机实时数据桥（零依赖） · v2
=================================================================
从本机直接订阅车机 ROS master 上的话题，把真实数据用 HTTP JSON 暴露给看板。

    python ros_bridge.py --open

接口
    GET /                     看板页面（同源，避免 file:// 跨域）
    GET /api/vehicle          车辆实时状态（姿态/运动/底盘/链路）
    GET /api/faults           真实故障事件流（来自 /fault_info）
    GET /api/topics           话题清单 + 存活/频率/延迟
    GET /api/topic?name=/xxx  单个话题的消息字段结构
    GET /api/nodes            节点与服务清单
    GET /api/series           遥测时间序列（供画曲线）
    GET /api/meta             概览统计（话题数/节点数/故障等级/传感器健康）
"""

import argparse
import io
import json
import os
import socket
import struct
import sys
import threading
import time
import xmlrpc.client
from collections import OrderedDict, deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ros_probe import (split_definition, decode, recv_exact,  # noqa: E402
                       connect_publisher)

SITE = r'E:\！！！高职比赛'
_CANDIDATES = [
    u'新能源汽车智能检测系统-1.0版.html',
    u'新能源汽车智能检测系统-美化，实测改进版.html',
    u'新能源汽车智能检测系统.html',
]


def find_html():
    """页面可能被改名，按优先级 + 修改时间自动识别"""
    for c in _CANDIDATES:
        p = os.path.join(SITE, c)
        if os.path.isfile(p):
            return p
    import glob
    hits = [p for p in glob.glob(os.path.join(SITE, '*.html'))
            if u'智能检测系统' in os.path.basename(p) and u'原版' not in os.path.basename(p)]
    if hits:
        return max(hits, key=os.path.getmtime)
    return os.path.join(SITE, _CANDIDATES[0])


HTML_PATH = find_html()
DEFAULT_MASTER = '192.168.1.102:11311'

LIGHT_BYTES = 12000          # 超过此字节数的消息只统计大小与频率，不解码（点云/图像）
SERIES_HZ = 2.0              # 遥测曲线采样频率
SERIES_LEN = 300             # 环形缓冲长度（默认 150 秒）

# 需要持续订阅并统计存活的话题（覆盖各传感器子系统，用于"在线矩阵"）
WATCH = [
    ('/INS/ASENSING_INS', 'ins'),
    ('/cicv_location', 'ins'),
    ('/odometry', 'ins'),
    ('/control_test', 'control'),
    ('/fault_alarm', 'diag'),
    ('/fault_info', 'diag'),
    ('/tf', 'tf'),
    ('/scan', 'lidar'),
    ('/lslidar_point_cloud', 'lidar'),
    ('/cluster/objects', 'lidar'),
    ('/tracker/objects', 'lidar'),
    ('/camera_image/compressed', 'camera'),
    ('/mipi_four_cameras/compressed', 'camera'),
    ('/camera_obstacles', 'camera'),
    ('/radar_fusion_objects', 'radar'),
    ('/f_radar_objects', 'radar'),
    ('/rl_radar_objects', 'radar'),
    ('/reference_trajectory', 'planning'),
    ('/route_message', 'planning'),
    ('/ult_fault', 'diag'),
]


# ================================================================= 订阅线程
class TopicReader(threading.Thread):
    def __init__(self, master, topic, ttype, group=''):
        threading.Thread.__init__(self)
        self.daemon = True
        self.master_addr = master
        self.topic = topic
        self.ttype = ttype
        self.group = group
        self.lock = threading.Lock()
        self.latest = {}
        self.seq = 0
        self.hz = 0.0
        self.last_rx = 0.0
        self.last_bytes = 0
        self.max_bytes = 0
        self.light = False            # 是否进入轻量模式（不解码）
        self.ok = False
        self.err = ''
        self.mdef = ''
        self.fields = []
        self._stop = False

    def snapshot(self):
        with self.lock:
            age = time.time() - self.last_rx if self.last_rx else None
            return {
                'topic': self.topic, 'type': self.ttype, 'group': self.group,
                'ok': self.ok and age is not None and age < 3.0,
                'hz': round(self.hz, 1),
                'age': round(age, 3) if age else None,
                'frames': self.seq, 'bytes': self.last_bytes, 'max_bytes': self.max_bytes,
                'light': self.light, 'err': self.err, 'data': dict(self.latest),
                'nfields': len(self.fields),
            }

    def run(self):
        while not self._stop:
            try:
                self._read_loop()
            except Exception as e:
                with self.lock:
                    self.ok = False
                    self.err = '%s: %s' % (type(e).__name__, e)
            if not self._stop:
                time.sleep(2.0)

    def _read_loop(self):
        master = xmlrpc.client.ServerProxy('http://%s' % self.master_addr)
        caller = '/dsh_bridge' + self.topic.replace('/', '_')
        code, msg, pubs = master.registerSubscriber(
            caller, self.topic, self.ttype, 'http://127.0.0.1:1/')
        if code != 1:
            raise IOError('registerSubscriber: %s' % msg)
        if not pubs:
            raise IOError('没有发布者')

        last_err = None
        sock = None
        for uri in pubs:
            try:
                sock, hdr = connect_publisher(uri, self.topic, caller)
                break
            except Exception as e:
                last_err = e
        if sock is None:
            raise IOError('发布方连接失败: %s' % last_err)

        mdef = hdr.get('message_definition', '')
        defs, spec = split_definition(mdef)
        with self.lock:
            self.ok = True
            self.err = ''
            self.mdef = mdef
            self.fields = [{'type': t, 'name': n,
                            'array': ('[]' if a == -1 else ('[%d]' % a if a is not None else ''))}
                           for (t, n, a) in spec]

        win_start, win_count = time.time(), 0
        sock.settimeout(8.0)
        while not self._stop:
            (ln,) = struct.unpack('<I', recv_exact(sock, 4))
            body = recv_exact(sock, ln)
            now = time.time()

            if ln <= LIGHT_BYTES:
                try:
                    val, _ = decode(body, 0, spec, defs)
                except Exception:
                    val = None
                    ln_mark = True
                else:
                    ln_mark = False
                with self.lock:
                    if not ln_mark:
                        self.latest = val
                        self.light = False
                    else:
                        self.light = True
            else:
                with self.lock:
                    self.light = True

            win_count += 1
            with self.lock:
                self.seq += 1
                self.last_rx = now
                self.last_bytes = ln
                if ln > self.max_bytes:
                    self.max_bytes = ln
                if now - win_start >= 2.0:
                    self.hz = win_count / (now - win_start)
                    win_start, win_count = now, 0


class FaultCollector(TopicReader):
    """在普通订阅之上，把 /fault_info 里的每条故障记成事件列表。"""

    MAX_EVENTS = 200

    def __init__(self, *a, **kw):
        TopicReader.__init__(self, *a, **kw)
        self.events = deque(maxlen=self.MAX_EVENTS)

    def _read_loop(self):
        master = xmlrpc.client.ServerProxy('http://%s' % self.master_addr)
        caller = '/dsh_bridge_faults'
        code, msg, pubs = master.registerSubscriber(
            caller, self.topic, self.ttype, 'http://127.0.0.1:1/')
        if code != 1:
            raise IOError('registerSubscriber: %s' % msg)
        if not pubs:
            raise IOError('没有发布者')
        last_err = None
        sock = None
        for uri in pubs:
            try:
                sock, hdr = connect_publisher(uri, self.topic, caller)
                break
            except Exception as e:
                last_err = e
        if sock is None:
            raise IOError('发布方连接失败: %s' % last_err)

        defs, spec = split_definition(hdr.get('message_definition', ''))
        with self.lock:
            self.ok = True
            self.err = ''
            self.fields = [{'type': t, 'name': n,
                            'array': ('[]' if a == -1 else ('[%d]' % a if a is not None else ''))}
                           for (t, n, a) in spec]

        win_start, win_count = time.time(), 0
        sock.settimeout(8.0)
        while not self._stop:
            (ln,) = struct.unpack('<I', recv_exact(sock, 4))
            body = recv_exact(sock, ln)
            now = time.time()
            try:
                val, _ = decode(body, 0, spec, defs)
            except Exception:
                val = None
            if val:
                with self.lock:
                    self.latest = val
                    for it in val.get('info_vec', []) or []:
                        self._push(it, now)
            win_count += 1
            with self.lock:
                self.seq += 1
                self.last_rx = now
                self.last_bytes = ln
                if now - win_start >= 2.0:
                    self.hz = win_count / (now - win_start)
                    win_start, win_count = now, 0

    def _push(self, it, now):
        key = (it.get('module_name', ''), it.get('error_code', 0))
        for e in self.events:
            if e['key'] == key:
                e['reports'] += 1
                e['last'] = it.get('timestamp_sec') or now
                e['level'] = it.get('fault_level', 0)
                e['msg'] = it.get('msg', '')
                e['seen_at'] = now
                return
        self.events.appendleft({
            'key': key,
            'module': it.get('module_name', ''),
            'code': it.get('error_code', 0),
            'msg': it.get('msg', ''),
            'level': it.get('fault_level', 0),
            'type': it.get('fault_type', 0),
            'first': it.get('timestamp_sec') or now,   # 车机时钟（未对时，仅作对照）
            'last': it.get('timestamp_sec') or now,
            'first_seen': now,                          # 本机墙钟：首次收集到
            'seen_at': now,                             # 本机墙钟：最近一次上报
            'reports': 1,
        })

    def events_snapshot(self):
        """返回故障列表：active=当前仍在报，duration=持续时长（秒）"""
        now = time.time()
        with self.lock:
            out = []
            for e in self.events:
                d = dict(e)
                d['active'] = (now - e['seen_at']) < 3.0
                d['duration'] = max(0.0, e['seen_at'] - e.get('first_seen', e['seen_at']))
                out.append(d)
            # 逻辑排序：仍在报的排前面 → 等级高的在前 → 持续久的在前
            out.sort(key=lambda x: (not x['active'], -x['level'], -x['duration']))
            return out


# ================================================================= 全局状态
class Hub(object):
    def __init__(self):
        self.readers = OrderedDict()
        self.master = DEFAULT_MASTER
        self.started = time.time()
        self.linked = False          # 是否真的连上过 ROS master（见 payload_meta 注释）
        self.topic_inv = []          # 来自 master 的完整话题清单
        self.topic_types = {}
        self.nodes = []
        self.services = 0
        self.inv_at = 0.0
        self.series = OrderedDict()  # 遥测曲线
        self.series_t = deque(maxlen=SERIES_LEN)
        for k in ('yaw', 'pitch', 'roll', 'ax', 'ay', 'az', 'gx', 'gy', 'gz', 'temp'):
            self.series[k] = deque(maxlen=SERIES_LEN)

    # ---- 话题清单（每 15 秒刷新一次）
    def refresh_inventory(self):
        try:
            m = xmlrpc.client.ServerProxy('http://%s' % self.master)
            _, _, state = m.getSystemState('/dsh_inv')
            _, _, types = m.getTopicTypes('/dsh_inv')
            pubs, subs, srvs = state
            self.topic_types = dict(types)
            inv = []
            nodes = set()
            for t, ns in pubs:
                for n in ns:
                    nodes.add(n)
                inv.append({'name': t, 'type': self.topic_types.get(t, '?'),
                            'pubs': ns, 'subs': dict(subs).get(t, [])})
            inv.sort(key=lambda x: x['name'])
            self.topic_inv = inv
            self.nodes = sorted(nodes)
            self.services = len(srvs)
            self.inv_at = time.time()
        except Exception:
            pass

    def inv_loop(self):
        while True:
            self.refresh_inventory()
            time.sleep(15.0)

    # ---- 遥测采样（2 Hz 写入环形缓冲）
    def sample_loop(self):
        while True:
            try:
                ins = self.readers.get('/INS/ASENSING_INS')
                if ins:
                    d = ins.snapshot()['data'] or {}
                    if d:
                        self.series_t.append(round(time.time(), 2))
                        self.series['yaw'].append(d.get('yaw', 0.0))
                        self.series['pitch'].append(d.get('pitch', 0.0))
                        self.series['roll'].append(d.get('roll', 0.0))
                        self.series['ax'].append(d.get('x_acc', 0.0))
                        self.series['ay'].append(d.get('y_acc', 0.0))
                        self.series['az'].append(d.get('z_acc', 0.0))
                        self.series['gx'].append(d.get('x_angular_velocity', 0.0))
                        self.series['gy'].append(d.get('y_angular_velocity', 0.0))
                        self.series['gz'].append(d.get('z_angular_velocity', 0.0))
                        self.series['temp'].append(d.get('temperature', 0.0))
            except Exception:
                pass
            time.sleep(1.0 / SERIES_HZ)


HUB = Hub()


# ================================================================= 组包
def g(d, path, default=0.0):
    cur = d
    for k in path.split('.'):
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def payload_vehicle():
    def snap(t):
        r = HUB.readers.get(t)
        return (r.snapshot() if r else {'ok': False, 'hz': 0, 'age': None,
                                        'frames': 0, 'data': {}, 'err': '未订阅'})

    i = snap('/INS/ASENSING_INS')['data']
    l = snap('/cicv_location')['data']
    o = snap('/odometry')['data']
    c = snap('/control_test')['data']
    f = snap('/fault_alarm')['data']

    chassis = {
        'speed': g(c, 'VCU1_ICPV_VehSpd'),
        'wheel_fl': g(c, 'VCU1_ICPV_ESCWhlFLSpd'),
        'wheel_fr': g(c, 'VCU1_ICPV_ESCWhlFRSpd'),
        'wheel_rl': g(c, 'VCU1_ICPV_ESCWhlRLSpd'),
        'wheel_rr': g(c, 'VCU1_ICPV_ESCWhlRRSpd'),
        'yawrate': g(c, 'VCU1_ICPV_YawRate'),
        'longacc': g(c, 'VCU1_ICPV_LongAcc'),
        'str_angle': g(c, 'VCU1_ICPV_StrAngle'),
        'str_fb': g(c, 'VCU1_ICPV_StrAngleFb'),
        'eps_mode': g(c, 'VCU1_ICPV_EPSMODE'),
        'eps_dir': g(c, 'VCU1_ICPV_EPSDir'),
        'gear': g(c, 'VCU_ICPV_VCUGearLevPos'),
        'gear_fb': g(c, 'VCU_ICPV_TgtSftFb'),
        'epb': g(c, 'VCU_ICPV_EPBSysVCU'),
        'cruise_sts': g(c, 'VCU_ICPV_CruiseControlSts'),
        'cruise_sw': g(c, 'VCU_ICPV_CruiseSwitchSts'),
        'auto_mod': g(c, 'VCU_ICPV_ATOModFb'),
        'vcu_sta': g(c, 'VCU_ICPV_VCUSta'),
        'acc_pedal': g(c, 'VCU_ICPV_AccPelPosFb'),
        'brk_pedal': g(c, 'VCU_ICPV_BrkPelPosFb'),
        'acc_sta': g(c, 'VCU_ICPV_AccPelSta'),
        'brk_sta': g(c, 'VCU_ICPV_BrkPelSta'),
        'brk_light': g(c, 'VCU_IPCV_BrkLgtSts'),
        'back_door': g(c, 'VCU1_ICPV_BackDoorSts'),
        'tm_dir': g(c, 'PCU_ICPV_TMDirSts'),
    }
    chassis_live = any(abs(v) > 1e-9 for k, v in chassis.items()
                       if k not in ('gear', 'epb', 'vcu_sta')) or abs(chassis['vcu_sta']) > 1e-9

    return {
        'ok': True,
        'server_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'uptime_s': round(time.time() - HUB.started, 1),
        'master': HUB.master,
        'chassis_live': chassis_live,
        'fault_alarm': f.get('data', None) if f else None,
        'chassis': chassis,
        'attitude': {
            'yaw': g(i, 'yaw', g(l, 'yaw')),
            'pitch': g(i, 'pitch', g(l, 'pitch')),
            'roll': g(i, 'roll', g(l, 'roll')),
            'azimuth': g(i, 'azimuth'),
            'yaw_std': g(i, 'yaw_std', g(l, 'yaw_std')),
            'altitude': g(i, 'altitude'),
            'lat': g(i, 'latitude'),
            'lon': g(i, 'longitude'),
            'temp': g(i, 'temperature'),
            'ins_status': g(i, 'ins_status'),
            'wheel_speed_status': g(i, 'wheel_speed_status'),
            'sow': g(i, 'sec_of_week'),
        },
        'motion': {
            'ax': g(i, 'x_acc', g(l, 'accel_x')),
            'ay': g(i, 'y_acc', g(l, 'accel_y')),
            'az': g(i, 'z_acc', g(l, 'accel_z')),
            'gx': g(i, 'x_angular_velocity', g(l, 'angular_velocity_x')),
            'gy': g(i, 'y_angular_velocity', g(l, 'angular_velocity_y')),
            'gz': g(i, 'z_angular_velocity', g(l, 'angular_velocity_z')),
        },
        'odom': {
            'x': g(o, 'pose.pose.position.x'), 'y': g(o, 'pose.pose.position.y'),
            'z': g(o, 'pose.pose.position.z'),
            'qx': g(o, 'pose.pose.orientation.x'), 'qy': g(o, 'pose.pose.orientation.y'),
            'qz': g(o, 'pose.pose.orientation.z'), 'qw': g(o, 'pose.pose.orientation.w'),
            'frame': g(l, 'frame_unmber'),
        },
        'topics': OrderedDict((t, r.snapshot()) for t, r in HUB.readers.items()),
    }


def payload_faults():
    fc = HUB.readers.get('/fault_info')
    if not fc or not isinstance(fc, FaultCollector):
        return {'ok': False, 'events': [], 'level': 0}
    cur = fc.snapshot()['data'] or {}
    events = fc.events_snapshot()
    active = [e for e in events if e['active']]
    # 等级取"当前帧"与"仍在持续的事件"的较大值：
    # 故障是断续上报的，帧间 module_fault_level 会归零，
    # 只看当前帧会出现"表头写无故障、下面却全是 2 级持续中"的矛盾。
    level = cur.get('module_fault_level', 0) or 0
    if active:
        level = max(level, max(e['level'] for e in active))
    return {
        'ok': True,
        'level': level,
        'now': cur.get('info_vec', []) or [],
        'events': events,
        'active': len(active),
        'hz': fc.snapshot()['hz'],
    }


def payload_topics():
    live = {t: r.snapshot() for t, r in HUB.readers.items()}
    out = []
    for it in HUB.topic_inv:
        s = live.get(it['name'])
        out.append({
            'name': it['name'], 'type': it['type'],
            'pubs': it['pubs'], 'npubs': len(it['pubs']),
            'watched': s is not None,
            'ok': (s or {}).get('ok', None),
            'hz': (s or {}).get('hz', None),
            'age': (s or {}).get('age', None),
            'bytes': (s or {}).get('bytes', None),
            'light': (s or {}).get('light', None),
            'err': (s or {}).get('err', ''),
            'nfields': (s or {}).get('nfields', None),
        })
    # 被监视但 master 清单里没有的（极少）
    known = set(it['name'] for it in HUB.topic_inv)
    for t, s in live.items():
        if t not in known:
            out.append({'name': t, 'type': s['type'], 'pubs': [], 'npubs': 0,
                        'watched': True, 'ok': s['ok'], 'hz': s['hz'], 'age': s['age'],
                        'bytes': s['bytes'], 'light': s['light'], 'err': s['err'],
                        'nfields': s['nfields']})
    return {'ok': True, 'count': len(out), 'inventory_age': round(time.time() - HUB.inv_at, 1),
            'topics': out}


def payload_nodes():
    return {'ok': True, 'nodes': HUB.nodes, 'ncount': len(HUB.nodes),
            'services': HUB.services, 'topics': len(HUB.topic_inv)}


def payload_series():
    return {'ok': True, 'hz': SERIES_HZ, 't': list(HUB.series_t),
            'series': {k: list(v) for k, v in HUB.series.items()}}


def payload_meta():
    v = payload_vehicle()
    f = payload_faults()
    snap = v['topics']
    watched = [s for s in snap.values()]
    online = [s for s in watched if s['ok']]
    silent = [t for t, s in snap.items() if not s['ok']]

    # 按子系统归类传感器健康度
    groups = {}
    for t, s in snap.items():
        gname = s.get('group') or 'other'
        d = groups.setdefault(gname, {'total': 0, 'ok': 0, 'topics': []})
        d['total'] += 1
        if s['ok']:
            d['ok'] += 1
        d['topics'].append({'name': t, 'ok': s['ok'], 'hz': s['hz'], 'age': s['age']})

    return {
        'ok': True,
        # ★linked：是否真的连上过 ROS master。桥接进程活着(ok=True)不等于车机连着，
        #   页面要靠这个字段区分「桥接没起」和「桥接正常但车机没连」。
        #   （车机没接时 watched 会是 0，只看 topics_online 分不清。）
        'linked': bool(HUB.linked),
        'server_time': v['server_time'],
        'master': HUB.master,
        'uptime_s': v['uptime_s'],
        'fault_level': f.get('level', 0),
        'fault_alarm': v['fault_alarm'],
        'fault_events': len(f.get('events', [])),
        'topics_total': len(HUB.topic_inv),
        'topics_watched': len(watched),
        'topics_online': len(online),
        'topics_silent': silent,
        'nodes': len(HUB.nodes),
        'services': HUB.services,
        'chassis_live': v['chassis_live'],
        'groups': groups,
        'silent_note': '静默话题：%d 个' % len(silent),
    }


# ================================================================= HTTP
ROUTES = {
    '/api/vehicle': payload_vehicle,
    '/api/faults': payload_faults,
    '/api/topics': payload_topics,
    '/api/nodes': payload_nodes,
    '/api/series': payload_series,
    '/api/meta': payload_meta,
}


class Handler(BaseHTTPRequestHandler):
    server_version = 'ChxzROS/2.0'

    def log_message(self, fmt, *a):
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

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False, default=str),
                   'application/json; charset=utf-8')

    def do_OPTIONS(self):
        self._send(200, b'', 'text/plain')

    def do_GET(self):
        raw = self.path.split('?')[0]
        path = raw.rstrip('/') or '/'

        if path in ROUTES:
            try:
                self._json(ROUTES[path]())
            except Exception as e:
                self._json({'ok': False, 'error': '%s: %s' % (type(e).__name__, e)}, 500)
            return

        if path == '/api/topic':
            from urllib.parse import parse_qs, urlparse
            q = parse_qs(urlparse(self.path).query)
            name = (q.get('name') or [''])[0]
            r = HUB.readers.get(name)
            if not r:
                self._json({'ok': False, 'error': '未订阅该话题', 'name': name}, 404)
                return
            s = r.snapshot()
            self._json({'ok': True, 'name': name, 'type': s['type'], 'group': s['group'],
                        'hz': s['hz'], 'age': s['age'], 'frames': s['frames'],
                        'bytes': s['bytes'], 'max_bytes': s['max_bytes'],
                        'fields': r.fields, 'sample': s['data']})
            return

        if path in ('/', '/index.html'):
            try:
                with io.open(HTML_PATH, encoding='utf-8') as fp:
                    self._send(200, fp.read(), 'text/html; charset=utf-8')
            except Exception as e:
                self._send(500, '读取页面失败: %s' % e, 'text/plain; charset=utf-8')
            return

        if path == '/api/health':
            self._json({'ok': True, 'topics': list(HUB.readers.keys())})
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
    raise IOError('端口 %d-%d 全部被占用' % (want, want + tries))


def try_connect(master):
    """连 master 并取话题类型表。连不上返回 None（不抛异常、不退出）。"""
    try:
        m = xmlrpc.client.ServerProxy('http://%s' % master)
        _, _, types = m.getTopicTypes('/dsh_bridge')
        return dict(types)
    except Exception:
        return None


def start_readers(master, tmap):
    """按 tmap 起话题订阅；已经订上的跳过"""
    n = 0
    for topic, group in WATCH:
        if topic in HUB.readers:
            continue
        if topic not in tmap:
            print('  跳过（话题不存在）: %s' % topic)
            continue
        cls = FaultCollector if topic == '/fault_info' else TopicReader
        r = cls(master, topic, tmap[topic], group)
        r.start()
        HUB.readers[topic] = r
        n += 1
        print('  订阅 %-32s %-42s [%s]' % (topic, tmap[topic], group))
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--master', default=DEFAULT_MASTER)
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=8770)
    ap.add_argument('--open', action='store_true')
    args = ap.parse_args()

    socket.setdefaulttimeout(10)
    HUB.master = args.master
    HUB.started = time.time()

    def connect_once():
        """连一次 master 并把话题订阅起来；返回本次新订阅数"""
        t = try_connect(args.master)
        if not t:
            return 0
        HUB.linked = True
        try:
            HUB.refresh_inventory()
        except Exception:
            pass
        return start_readers(args.master, t)

    def retry_loop():
        first = True
        while True:
            try:
                # 已经有话题在出数据就不用管
                if first or not any(getattr(r, 'ok', False) for r in list(HUB.readers.values())):
                    n = connect_once()
                    if n:
                        print('  [连接] 已连上 ROS master，订阅 %d 个话题' % n)
                    elif not HUB.linked:
                        print('  [连接] 暂时连不上 ROS master %s，5 秒后重试' % args.master)
            except Exception:
                pass
            first = False
            time.sleep(5)

    # ★不再"连不上 master 就 sys.exit(1)"，也**不再在起服务之前同步等连接**。
    #   原来车机没接时：① 桥接直接退出，页面只能显示「桥接未启动」，分不清
    #   "服务没跑"还是"车机没连"；② 即便改成不退出，同步 try_connect 也要等满
    #   10 秒 socket 超时才建 HTTP 服务（实测 8770 要 12.7 秒才就绪）。
    #   现在服务立刻起，连接交给后台线程，并支持连上后自动补订阅。
    threading.Thread(target=retry_loop, daemon=True).start()
    threading.Thread(target=HUB.inv_loop, daemon=True).start()
    threading.Thread(target=HUB.sample_loop, daemon=True).start()

    port = pick_port(args.host, args.port)
    srv = ThreadingHTTPServer((args.host, port), Handler)
    srv.daemon_threads = True

    time.sleep(2.5)
    url = 'http://%s:%d/' % (args.host, port)
    print('\n看板地址 : %s' % url)
    print('接口     : /api/vehicle  /api/faults  /api/topics  /api/topic?name=  /api/nodes  /api/series  /api/meta')
    print('（页面直接从这里打开可避免 file:// 的跨域限制）\n')
    if args.open:
        os.startfile(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print('\n已停止')


if __name__ == '__main__':
    main()

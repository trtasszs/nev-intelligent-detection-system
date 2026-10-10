# -*- coding: utf-8 -*-
"""
激光雷达点云查看器（镭神 C32 / lslidar_c32）
=================================================================
用途：从 Windows 直连车机 ROS（192.168.1.102:11311），订阅
      /lslidar_point_cloud（sensor_msgs/PointCloud2），解码后渲染成图。

用法：
    python lidar_view.py                 # 抓一帧渲染（默认俯视+侧视+立体）
    python lidar_view.py --secs 6        # 采 6 秒后出图
    python lidar_view.py --selftest      # 用合成数据自检解码与渲染（无需网络）
    python lidar_view.py --topic /lslidar_point_cloud --out E:\\AI输出\\lidar.png

输出：一张三联图（俯视 BEV / 侧视 / 立体斜视）+ 终端统计。
"""
import io
import os
import sys
import math
import time
import struct
import argparse

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

MASTER = '192.168.1.102:11311'
TOPIC = '/lslidar_point_cloud'
RTYPE = 'sensor_msgs/PointCloud2'

DT = {1: ('b', 1), 2: ('B', 1), 3: ('h', 2), 4: ('H', 2),
      5: ('i', 4), 6: ('I', 4), 7: ('f', 4), 8: ('d', 8)}
DT_NAME = {1: 'int8', 2: 'uint8', 3: 'int16', 4: 'uint16',
           5: 'int32', 6: 'uint32', 7: 'float32', 8: 'float64'}


# ----------------------------------------------------------------------------
# PointCloud2 二进制解析
# ----------------------------------------------------------------------------
def parse_pointcloud2(buf):
    """返回 dict(height,width,fields,point_step,row_step,data,frame_id,stamp)"""
    o = 0

    def u32():
        nonlocal o
        v = struct.unpack_from('<I', buf, o)[0]
        o += 4
        return v

    def u8():
        nonlocal o
        v = buf[o]
        o += 1
        return v

    def s():
        nonlocal o
        n = u32()
        v = buf[o:o + n].decode('utf-8', 'replace')
        o += n
        return v

    # --- std_msgs/Header ---
    seq = u32()
    secs = u32()
    nsecs = u32()
    frame_id = s()

    height = u32()
    width = u32()
    nfields = u32()
    fields = []
    for _ in range(nfields):
        name = s()
        offset = u32()
        dt = u8()
        count = u32()
        fields.append({'name': name, 'offset': offset, 'datatype': dt, 'count': count})
    is_bigendian = u8()
    point_step = u32()
    row_step = u32()
    data_len = u32()
    data = buf[o:o + data_len]
    o += data_len
    is_dense = u8() if o < len(buf) else 1

    return {'seq': seq, 'stamp': (secs, nsecs), 'frame_id': frame_id,
            'height': height, 'width': width, 'fields': fields,
            'is_bigendian': is_bigendian, 'point_step': point_step,
            'row_step': row_step, 'data': data, 'is_dense': is_dense}


def extract_xyz(pc):
    """从 PointCloud2 抽出 [(x,y,z,intensity)]，跳过 NaN。"""
    fm = {}
    for f in pc['fields']:
        if f['name'] in ('x', 'y', 'z', 'intensity', 'i'):
            fm[f['name']] = f
    if not all(k in fm for k in ('x', 'y', 'z')):
        return [], []
    step = pc['point_step']
    data = pc['data']
    n = len(data) // step if step else 0
    endian = '>' if pc['is_bigendian'] else '<'
    fx = fm['x']; fy = fm['y']; fz = fm['z']
    fi = fm.get('intensity') or fm.get('i')
    if fx['datatype'] != 7 or fy['datatype'] != 7 or fz['datatype'] != 7:
        return [], []
    pts = []
    inten = []
    unp = struct.unpack_from
    for i in range(n):
        b = i * step
        x = unp(endian + 'f', data, b + fx['offset'])[0]
        y = unp(endian + 'f', data, b + fy['offset'])[0]
        z = unp(endian + 'f', data, b + fz['offset'])[0]
        if x != x or y != y or z != z:      # NaN
            continue
        pts.append((x, y, z))
        if fi is not None:
            fmt, sz = DT.get(fi['datatype'], ('f', 4))
            try:
                inten.append(unp(endian + fmt, data, b + fi['offset'])[0])
            except Exception:
                inten.append(0.0)
    return pts, inten


# ----------------------------------------------------------------------------
# 渲染
# ----------------------------------------------------------------------------
def _ramp(t):
    """0~1 -> 冷蓝到暖红的伪彩（点云按高度/强度着色）"""
    t = max(0.0, min(1.0, t))
    stops = [(0.00, (40, 90, 200)), (0.30, (46, 200, 220)), (0.55, (46, 229, 157)),
             (0.78, (232, 196, 60)), (1.00, (224, 87, 74))]
    for i in range(len(stops) - 1):
        a, ca = stops[i]
        b, cb = stops[i + 1]
        if a <= t <= b:
            k = (t - a) / (b - a) if b > a else 0
            return tuple(int(ca[j] + (cb[j] - ca[j]) * k) for j in range(3))
    return stops[-1][1]


def render(pts, inten, out_path, title=''):
    from PIL import Image, ImageDraw, ImageFont
    if not pts:
        print('  [x] 没有点，无法渲染')
        return None

    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; zs = [p[2] for p in pts]
    print('  点数      : %d' % len(pts))
    print('  X 范围    : %.2f ~ %.2f m' % (min(xs), max(xs)))
    print('  Y 范围    : %.2f ~ %.2f m' % (min(ys), max(ys)))
    print('  Z 范围    : %.2f ~ %.2f m' % (min(zs), max(zs)))

    W, H = 1320, 460
    PAN = (W - 40) // 3
    BGC = (11, 13, 17)
    img = Image.new('RGB', (W, H), BGC)
    d = ImageDraw.Draw(img)

    try:
        fnt = ImageFont.truetype(r'C:\Windows\Fonts\msyh.ttc', 15)
        fnt_s = ImageFont.truetype(r'C:\Windows\Fonts\msyh.ttc', 12)
    except Exception:
        fnt = ImageFont.load_default(); fnt_s = fnt

    def panel(px, label):
        d.rectangle([px + 8, 40, px + PAN - 8, H - 30], outline=(52, 60, 72), width=1)
        d.text((px + 16, 14), label, font=fnt, fill=(232, 232, 236))

    def project(vals_h, vals_v, px, py, pw, ph, hmin, hmax, vmin, vmax, flip_v=True):
        sh = pw / (hmax - hmin) if hmax > hmin else 1
        sv = ph / (vmax - vmin) if vmax > vmin else 1
        sc = min(sh, sv)
        cx = px + pw / 2 - (hmin + hmax) / 2 * sc
        cy = py + ph / 2 + (vmin + vmax) / 2 * sc
        res = []
        for i in range(len(vals_h)):
            X = cx + vals_h[i] * sc
            Y = cy - (vals_v[i] * sc if flip_v else -vals_v[i] * sc)
            res.append((X, Y))
        return res

    # ---- ① 俯视 BEV（x-y，按高度着色）----
    px = 8
    panel(px, '① 俯视 BEV  (X→前  Y→左)')
    pw, ph = PAN - 24, H - 90
    py = 50
    zmin, zmax = min(zs), max(zs)
    proj = project(xs, ys, px + 14, py, pw, ph,
                   min(xs), max(xs), min(ys), max(ys), flip_v=False)
    for i, (X, Y) in enumerate(proj):
        t = (zs[i] - zmin) / (zmax - zmin) if zmax > zmin else 0.5
        c = _ramp(t)
        if px + 14 <= X <= px + 14 + pw and py <= Y <= py + ph:
            d.point((X, Y), fill=c)

    # ---- ② 侧视（x-z）----
    px2 = 8 + PAN
    panel(px2, '② 侧视  (X→前  Z→高)')
    proj = project(xs, zs, px2 + 14, py, pw, ph,
                   min(xs), max(xs), min(zs), max(zs))
    for i, (X, Y) in enumerate(proj):
        t = (zs[i] - zmin) / (zmax - zmin) if zmax > zmin else 0.5
        if px2 + 14 <= X <= px2 + 14 + pw and py <= Y <= py + ph:
            d.point((X, Y), fill=_ramp(t))

    # ---- ③ 立体斜视（等距投影）----
    px3 = 8 + PAN * 2
    panel(px3, '③ 立体斜视  (30° 等距)')
    ca, sa = math.cos(math.radians(30)), math.sin(math.radians(30))
    u = [xs[i] * ca - ys[i] * sa for i in range(len(pts))]
    v = [zs[i] + (xs[i] * sa + ys[i] * ca) * 0.42 for i in range(len(pts))]
    proj = project(u, v, px3 + 14, py, pw, ph, min(u), max(u), min(v), max(v))
    # 远的先画（按深度排序，产生遮挡感）
    order = sorted(range(len(pts)), key=lambda i: xs[i] * sa + ys[i] * ca)
    for i in order:
        X, Y = proj[i]
        t = (zs[i] - zmin) / (zmax - zmin) if zmax > zmin else 0.5
        if px3 + 14 <= X <= px3 + 14 + pw and py <= Y <= py + ph:
            d.point((X, Y), fill=_ramp(t))

    # ---- 底部信息条 ----
    info = ('%s   点数 %d   X %.1f~%.1f   Y %.1f~%.1f   Z %.1f~%.1f m   原始 %s'
            % (title or '', len(pts), min(xs), max(xs), min(ys), max(ys),
               min(zs), max(zs), frame or '-'))
    d.text((16, H - 22), info, font=fnt_s, fill=(154, 154, 165))

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    img.save(out_path)
    print('  图像已保存: %s' % out_path)
    return out_path


# ----------------------------------------------------------------------------
# 采集
# ----------------------------------------------------------------------------
def collect(master_addr, topic, secs, max_frames=1):
    import xmlrpc.client
    from ros_probe import connect_publisher, recv_exact

    master = xmlrpc.client.ServerProxy('http://%s' % master_addr, allow_none=True)
    caller = '/dsh_lidar_view'
    t0 = time.time()
    code, msg, pubs = master.registerSubscriber(caller, topic, RTYPE, 'http://127.0.0.1:1/')
    if code != 1:
        raise IOError('registerSubscriber 失败: %s' % msg)
    if not pubs:
        raise IOError('话题 %s 没有发布者（驱动没启动？）' % topic)

    last = None
    for uri in pubs:
        try:
            sock, hdr = connect_publisher(uri, topic, caller)
        except Exception as e:
            last = e
            continue
        print('  已连接发布方: %s' % uri)
        print('  发布方 frame_id 定义: %s' % (hdr.get('type', '?'),))
        sock.settimeout(max(3.0, secs))
        frames = 0
        best = None
        while time.time() - t0 < secs:
            (ln,) = struct.unpack('<I', recv_exact(sock, 4))
            body = recv_exact(sock, ln)
            frames += 1
            pc = parse_pointcloud2(body)
            if pc['width'] * pc['height'] > (best['width'] * best['height'] if best else 0):
                best = pc
            if frames >= max_frames and secs <= 0:
                break
        dt = time.time() - t0
        print('  收到 %d 帧，用时 %.1f s（约 %.1f Hz）' % (frames, dt, frames / dt if dt else 0))
        try:
            sock.close()
        except Exception:
            pass
        if best:
            return best
    raise IOError('连接发布方失败: %s' % last)


def synthesize():
    """合成一帧 32 线雷达数据，用于离线自检解码+渲染链路。"""
    fields = [{'name': 'x', 'offset': 0, 'datatype': 7, 'count': 1},
              {'name': 'y', 'offset': 4, 'datatype': 7, 'count': 1},
              {'name': 'z', 'offset': 8, 'datatype': 7, 'count': 1},
              {'name': 'intensity', 'offset': 12, 'datatype': 7, 'count': 1}]
    step = 16
    rows = []
    ring = []
    for r in range(32):
        elev = math.radians(-25 + r * 1.6)
        for a in range(720):
            az = math.radians(a * 0.5)
            rng = 12.0 + 3.0 * math.sin(az * 3.0) + 1.6 * r
            x = rng * math.cos(elev) * math.cos(az)
            y = rng * math.cos(elev) * math.sin(az)
            z = rng * math.sin(elev)
            if abs(x) < 6 and abs(y) < 4:      # 挖出中间"车辆"空洞
                continue
            rows.append(struct.pack('<ffff', x, y, z, 80.0 + r))
    data = b''.join(rows)
    width = len(rows)
    hdr = struct.pack('<III', 0, int(time.time()), 0) + struct.pack('<I', 5) + b'laser'
    body = hdr + struct.pack('<II', 1, width)
    body += struct.pack('<I', len(fields))
    for f in fields:
        nm = f['name'].encode()
        body += struct.pack('<I', len(nm)) + nm
        body += struct.pack('<IBI', f['offset'], f['datatype'], f['count'])
    body += struct.pack('<BIII', 0, step, step * width, len(data)) + data + struct.pack('<B', 1)
    return parse_pointcloud2(body)


frame = ''
if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--master', default=MASTER)
    ap.add_argument('--topic', default=TOPIC)
    ap.add_argument('--secs', type=float, default=4.0)
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--out', default=r'E:\AI输出\激光雷达点云\点云.png')
    a = ap.parse_args()

    if a.selftest:
        print('=== 自检模式（合成数据，不连网络）===')
        pc = synthesize()
        pts, inte = extract_xyz(pc)
        print('  解析: frame_id=%s  %dx%d  point_step=%d  字段=%s'
              % (pc['frame_id'], pc['width'], pc['height'], pc['point_step'],
                 ','.join(f['name'] for f in pc['fields'])))
        frame = pc['frame_id']
        render(pts, inte, a.out, title='[自检] 合成 32 线雷达')
        sys.exit(0)

    print('=== 连接车机 ROS %s ===' % a.master)
    print('  话题: %s' % a.topic)
    try:
        pc = collect(a.master, a.topic, a.secs)
    except Exception as e:
        print('  [x] 采集失败: %s: %s' % (type(e).__name__, e))
        print()
        print('  排查顺序：')
        print('    1) 本机以太网是否 Unplugged（网线没插）')
        print('    2) ping 192.168.1.102 通不通')
        print('    3) 102 上驱动是否在跑： roslaunch lslidar_c32_decoder lslidar_c32.launch')
        print('    4) rostopic hz %s  应约 10 Hz' % a.topic)
        sys.exit(2)

    print('  frame_id=%s  %dx%d  point_step=%d  字段=%s'
          % (pc['frame_id'], pc['width'], pc['height'], pc['point_step'],
             ','.join(f['name'] for f in pc['fields'])))
    frame = pc['frame_id']
    pts, inte = extract_xyz(pc)
    render(pts, inte, a.out, title='镭神 C32 · ' + a.topic)

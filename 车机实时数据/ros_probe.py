# -*- coding: utf-8 -*-
"""
纯 Python ROS1 订阅器（零依赖）
------------------------------------------------------------------
用途：不装 ROS，直接从本机连车机的 ROS master(11311)，订阅任意话题，
      拿 pub 端下发的 message_definition 动态解码，打印真实字段值。

原理：ROS1 的 master 就是 XMLRPC；话题数据走 TCPROS（4 字节长度前缀 + 二进制）。
      订阅方主动连发布方，连接头里带 message_definition，因此**不需要 .msg 文件**。

    python ros_probe.py --master 192.168.1.102:11311 --topic /control_test --count 3
    python ros_probe.py --list
    python ros_probe.py --topic /tpimu --fields
"""

import argparse
import socket
import struct
import sys
import xmlrpc.client

BASIC = {
    'bool': ('B', 1), 'int8': ('b', 1), 'uint8': ('B', 1), 'byte': ('b', 1), 'char': ('B', 1),
    'int16': ('h', 2), 'uint16': ('H', 2),
    'int32': ('i', 4), 'uint32': ('I', 4),
    'int64': ('q', 8), 'uint64': ('Q', 8),
    'float32': ('f', 4), 'float64': ('d', 8),
}
SEP = '=' * 80


# ----------------------------------------------------------------- 消息定义解析
def split_definition(text):
    """message_definition 用 80 个 = 分隔主消息与依赖消息"""
    blocks, cur, name = [], [], None
    for ln in text.split('\n'):
        s = ln.strip()
        if s == SEP:
            blocks.append((name, cur))
            cur, name = [], None
            continue
        if name is None and s.startswith('MSG: '):
            name = s[5:].strip()
            continue
        cur.append(ln)
    blocks.append((name, cur))

    main = blocks[0][1]
    defs = {}
    for nm, lines in blocks:
        if nm is None:
            nm = '__main__'
        defs[nm] = parse_fields(lines)
        # 同时用短名索引，便于解析时不需要包名前缀
        short = nm.split('/')[-1]
        defs.setdefault(short, defs[nm])
    return defs, parse_fields(main)


def parse_fields(lines):
    spec = []
    for ln in lines:
        ln = ln.split('#')[0].strip()
        if not ln:
            continue
        parts = ln.split()
        if len(parts) < 2:
            continue
        t, n = parts[0], parts[1]
        arrlen = None
        if '[' in t:
            base, rest = t.split('[', 1)
            inner = rest.rstrip(']').strip()
            arrlen = int(inner) if inner else -1
            t = base
        spec.append((t, n, arrlen))
    return spec


def read_one(buf, pos, bt, defs, depth=0):
    if depth > 12:
        raise ValueError('嵌套过深')
    if bt in BASIC:
        fmt, sz = BASIC[bt]
        v = struct.unpack_from('<' + fmt, buf, pos)[0]
        if bt == 'bool':
            v = bool(v)
        return v, pos + sz
    if bt == 'string':
        n = struct.unpack_from('<I', buf, pos)[0]
        pos += 4
        if n > 1 << 20:
            raise ValueError('string 过长')
        return buf[pos:pos + n].decode('utf-8', 'replace'), pos + n
    if bt in ('time', 'duration'):
        f = 'I' if bt == 'time' else 'i'
        a = struct.unpack_from('<' + f, buf, pos)[0]
        b = struct.unpack_from('<' + f, buf, pos + 4)[0]
        return {'secs': a, 'nsecs': b}, pos + 8

    key = bt
    if key not in defs:
        short = key.split('/')[-1]
        key = short if short in defs else None
        if key is None:
            for k in defs:
                if k.endswith('/' + short):
                    key = k
                    break
    if key is None:
        raise KeyError('未知类型 ' + bt)
    return decode(buf, pos, defs[key], defs, depth + 1)


def decode(buf, pos, spec, defs, depth=0):
    out = {}
    for (bt, name, arrlen) in spec:
        if arrlen is None:
            v, pos = read_one(buf, pos, bt, defs, depth)
            out[name] = v
            continue
        n = arrlen
        if n == -1:
            n = struct.unpack_from('<I', buf, pos)[0]
            pos += 4
            if n > 20000:
                raise ValueError('数组过长 %s' % n)
        arr = []
        for _ in range(n):
            v, pos = read_one(buf, pos, bt, defs, depth)
            arr.append(v)
        out[name] = arr
    return out, pos


# ----------------------------------------------------------------- TCPROS 协议
def recv_exact(sock, n):
    chunks = []
    left = n
    while left > 0:
        c = sock.recv(left)
        if not c:
            raise IOError('连接被对端关闭')
        chunks.append(c)
        left -= len(c)
    return b''.join(chunks)


def recv_header(sock):
    (ln,) = struct.unpack('<I', recv_exact(sock, 4))
    fields = {}
    if ln == 0:
        return fields
    raw = recv_exact(sock, ln)
    p = 0
    while p < len(raw):
        (fl,) = struct.unpack_from('<I', raw, p)
        p += 4
        kv = raw[p:p + fl].decode('utf-8', 'replace')
        p += fl
        if '=' in kv:
            k, v = kv.split('=', 1)
            fields[k] = v
    return fields


def send_header(sock, fields):
    body = b''
    for k, v in fields.items():
        kv = ('%s=%s' % (k, v)).encode('utf-8')
        body += struct.pack('<I', len(kv)) + kv
    sock.sendall(struct.pack('<I', len(body)) + body)


def connect_publisher(pub_uri, topic, caller_id):
    """pub_uri 形如 http://host:port/ ；向它要 TCPROS 端口再连"""
    proxy = xmlrpc.client.ServerProxy(pub_uri)
    code, msg, proto = proxy.requestTopic(caller_id, topic, [['TCPROS']])
    if code != 1:
        raise IOError('requestTopic 失败: %s' % msg)
    _, host, port = proto
    s = socket.create_connection((host, int(port)), timeout=10)
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    send_header(s, {
        'callerid': caller_id, 'topic': topic,
        'md5sum': '*', 'type': '*', 'tcp_nodelay': '1', 'message_definition': '',
    })
    hdr = recv_header(s)
    if 'error' in hdr:
        raise IOError('发布方报错: %s' % hdr['error'])
    return s, hdr


# ----------------------------------------------------------------- 主流程
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--master', default='192.168.1.102:11311')
    ap.add_argument('--topic', default='/control_test')
    ap.add_argument('--count', type=int, default=3)
    ap.add_argument('--timeout', type=float, default=10.0)
    ap.add_argument('--list', action='store_true', help='列出所有话题与类型')
    ap.add_argument('--fields', action='store_true', help='只打印字段结构，不解码')
    ap.add_argument('--raw', action='store_true', help='额外打印原始字节(前64)')
    args = ap.parse_args()

    socket.setdefaulttimeout(args.timeout)
    master = xmlrpc.client.ServerProxy('http://%s' % args.master)
    caller = '/dsh_probe'

    if args.list:
        _, _, state = master.getSystemState(caller)
        pubs = dict(state[0])
        _, _, types = master.getTopicTypes(caller)
        tmap = dict(types)
        for t in sorted(pubs):
            print('%-48s %s' % (t, tmap.get(t, '?')))
        return

    _, _, types = master.getTopicTypes(caller)
    tmap = dict(types)
    ttype = tmap.get(args.topic)
    if not ttype:
        print('话题不存在: %s' % args.topic)
        sys.exit(1)

    code, msg, pubs = master.registerSubscriber(caller, args.topic, ttype,
                                                'http://127.0.0.1:1/')
    if code != 1:
        print('注册失败: %s' % msg)
        sys.exit(1)
    if not pubs:
        print('该话题当前没有发布者（节点未运行？）')
        sys.exit(2)

    print('话题 %s   类型 %s   发布者 %d 个' % (args.topic, ttype, len(pubs)))
    sock = None
    last_err = None
    for uri in pubs:
        try:
            sock, hdr = connect_publisher(uri, args.topic, caller)
            print('已连上发布方: %s' % uri)
            break
        except Exception as e:
            last_err = e
    if sock is None:
        print('全部发布方连接失败: %s' % last_err)
        sys.exit(3)

    mdef = hdr.get('message_definition', '')
    defs, main_spec = split_definition(mdef)
    if args.fields or True:
        print('\n字段结构:')
        for (bt, n, al) in main_spec:
            suffix = '' if al is None else ('[%s]' % ('变长' if al == -1 else al))
            print('  %-28s %s%s' % (bt, n, suffix))

    if args.fields:
        sock.close()
        return

    print('\n实时数据:')
    got = 0
    while got < args.count:
        try:
            (ln,) = struct.unpack('<I', recv_exact(sock, 4))
            body = recv_exact(sock, ln)
        except Exception as e:
            print('读取中断: %s' % e)
            break
        got += 1
        try:
            val, consumed = decode(body, 0, main_spec, defs)
            import json
            print('--- #%d  (%d/%d 字节) ---' % (got, consumed, ln))
            print(json.dumps(val, ensure_ascii=False, indent=2, default=str)[:4000])
            if args.raw:
                print('raw:', body[:64].hex())
        except Exception as e:
            print('--- #%d 解码失败: %s (len=%d) ---' % (got, e, ln))
    sock.close()


if __name__ == '__main__':
    main()

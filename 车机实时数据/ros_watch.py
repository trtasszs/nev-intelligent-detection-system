# -*- coding: utf-8 -*-
"""
车况变化观察器：订阅一个或多个 ROS 话题，只报告**发生变化的字段**，
结束时给出"哪些字段真实在动"的清单。用来判定哪些信号随车辆状态改变。

    python ros_watch.py --topics /control_test --seconds 8
    python ros_watch.py --topics /control_test,/fault_alarm,/tpimu --seconds 10
"""

import argparse
import json
import socket
import struct
import sys
import threading
import time
import xmlrpc.client

sys.path.insert(0, __file__.rsplit('\\', 1)[0])
from ros_probe import (split_definition, decode, recv_exact, recv_header,  # noqa: E402
                       send_header, connect_publisher)

FLAT_SEP = '.'


def flatten(d, prefix=''):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(flatten(v, prefix + k + FLAT_SEP))
    elif isinstance(d, list):
        # 数组只关心长度与首元素，避免刷屏
        out[prefix[:-1] + '[len]'] = len(d)
        if d and isinstance(d[0], (int, float, str)):
            out[prefix[:-1] + '[0]'] = d[0]
    else:
        out[prefix[:-1]] = d
    return out


class Watcher(threading.Thread):
    def __init__(self, master, topic, ttype, duration, lock, report):
        threading.Thread.__init__(self)
        self.daemon = True
        self.master, self.topic, self.ttype = master, topic, ttype
        self.duration = duration
        self.lock, self.report = lock, report
        self.prev = {}
        self.first = True
        self.count = 0
        self.changed = {}

    def run(self):
        caller = '/dsh_watch_' + self.topic.strip('/').replace('/', '_')
        # 注意：xmlrpc.client.ServerProxy 不是线程安全的，每个线程必须各建一个
        master = xmlrpc.client.ServerProxy('http://%s' % self.master)
        try:
            code, msg, pubs = master.registerSubscriber(
                caller, self.topic, self.ttype, 'http://127.0.0.1:1/')
            if code != 1 or not pubs:
                with self.lock:
                    self.report.append((self.topic, '无发布者', [], 0))
                return
            sock, hdr = connect_publisher(pubs[0], self.topic, caller)
            defs, spec = split_definition(hdr.get('message_definition', ''))
            sock.settimeout(self.duration + 2)
            t0 = time.time()
            while time.time() - t0 < self.duration:
                try:
                    (ln,) = struct.unpack('<I', recv_exact(sock, 4))
                    body = recv_exact(sock, ln)
                except Exception:
                    break
                val, _ = decode(body, 0, spec, defs)
                flat = flatten(val)
                self.count += 1
                if self.first:
                    self.first = False
                    with self.lock:
                        nz = {k: v for k, v in flat.items() if v not in (0, 0.0, '', False)}
                        self.report.append((self.topic, '首帧字段 %d 个，非零 %d 个'
                                            % (len(flat), len(nz)), sorted(nz.items()), self.count))
                else:
                    for k, v in flat.items():
                        if k in self.prev and self.prev[k] != v:
                            self.changed[k] = v
                self.prev = flat
            sock.close()
            with self.lock:
                self.report.append((self.topic, '共收 %d 帧' % self.count,
                                    sorted(self.changed.items()), self.count))
        except Exception as e:
            with self.lock:
                self.report.append((self.topic, '异常 %s: %s' % (type(e).__name__, e), [], self.count))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--master', default='192.168.1.102:11311')
    ap.add_argument('--topics', default='/control_test')
    ap.add_argument('--seconds', type=float, default=8.0)
    args = ap.parse_args()

    socket.setdefaulttimeout(10)
    master = xmlrpc.client.ServerProxy('http://%s' % args.master)
    _, _, types = master.getTopicTypes('/dsh_watch')
    tmap = dict(types)

    topics = [t.strip() for t in args.topics.split(',') if t.strip()]
    lock, report = threading.Lock(), []
    ws = []
    for t in topics:
        tt = tmap.get(t)
        if not tt:
            print('跳过（话题不存在）: %s' % t)
            continue
        w = Watcher(args.master, t, tt, args.seconds, lock, report)
        w.start()
        ws.append(w)
        print('开始观察 %-28s %s' % (t, tt))

    print('采样 %.0f 秒 ...\n' % args.seconds)
    for w in ws:
        w.join(args.seconds + 4)

    print('=' * 74)
    for topic, note, items, _ in report:
        print('\n【%s】 %s' % (topic, note))
        if items:
            for k, v in items:
                if isinstance(v, float):
                    print('   %-46s %s' % (k, ('%.4f' % v)))
                else:
                    print('   %-46s %s' % (k, v))
        else:
            print('   （没有字段发生变化）')


if __name__ == '__main__':
    main()

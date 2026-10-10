# -*- coding: utf-8 -*-
"""
链路哨兵：等车机连上 -> 立刻跑完整 ROS 探测
==================================================================
为什么需要：网线没插时，一切 ROS 查询都是徒劳（邻居表空 -> ping 不通 ->
11311 不通）。与其反复手动问，不如让脚本盯着 11311，一通就自动把该查的都查掉。

判定依据刻意选「能不能连上 11311」而不是「网卡是否 Up」——
  插上线但车机没开机 / ROS 没起来时，网卡是 Up 的，但 ROS 依然连不上，
  对"ROS 能不能用"这个问题来说，网卡的 Up 是个假信号。
"""
import os
import socket
import subprocess
import sys
import time

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
MASTER = '192.168.1.102'
PORT = 11311
TIMEOUT_MIN = 45          # 最多盯 45 分钟
POLL = 5


def port_open(host, port, t=2.0):
    s = socket.socket()
    s.settimeout(t)
    try:
        s.connect((host, port))
        return True
    except Exception:
        return False
    finally:
        s.close()


def nic_status():
    try:
        out = subprocess.run(
            ['powershell', '-NoProfile', '-Command',
             "(Get-NetAdapter -Name '以太网').Status + '|' + (Get-NetAdapter -Name '以太网').LinkSpeed"],
            capture_output=True, text=True, timeout=20).stdout.strip()
        return out
    except Exception:
        return '?'


def main():
    print(u'[哨兵] 开始盯 %s:%d，最多 %d 分钟（每 %d 秒一次）'
          % (MASTER, PORT, TIMEOUT_MIN, POLL))
    t0 = time.time()
    last_note = 0
    while time.time() - t0 < TIMEOUT_MIN * 60:
        if port_open(MASTER, PORT):
            print(u'\n[哨兵] ★ 连上 ROS master 了（用时 %.0f 秒）' % (time.time() - t0))
            break
        # 每 2 分钟报一次网卡状态，方便判断是"没插线"还是"插了但车机没开"
        if time.time() - t0 - last_note > 120:
            last_note = time.time() - t0
            print(u'[哨兵] 已等 %.0f 分钟 · 以太网=%s · 11311 仍不通'
                  % (last_note / 60.0, nic_status()))
        time.sleep(POLL)
    else:
        print(u'\n[哨兵] 超时：%d 分钟内始终连不上 %s:%d' % (TIMEOUT_MIN, MASTER, PORT))
        print(u'       以太网状态 = %s' % nic_status())
        return 2

    # ---------------- 连上了，跑完整探测 ----------------
    time.sleep(3)
    print(u'\n' + u'=' * 66)
    print(u' 车机在线 · ROS 完整探测')
    print(u'=' * 66)

    def run(script, args=()):
        p = os.path.join(HERE, script)
        if not os.path.exists(p):
            print(u'  [!] 找不到 %s' % script)
            return
        print(u'\n--- %s ---' % script)
        try:
            r = subprocess.run([PY, p] + list(args), capture_output=True, text=True,
                               timeout=300, cwd=HERE,
                               encoding='utf-8', errors='replace')
            print(r.stdout or u'(无输出)')
            if r.stderr.strip():
                print(u'[stderr] ' + r.stderr[:800])
        except Exception as e:
            print(u'  执行失败: %s' % e)

    # 1) 桥接自己的视角（最直观）
    try:
        import urllib.request
        import json
        d = json.load(urllib.request.urlopen('http://127.0.0.1:8770/api/meta', timeout=10))
        print(u'\n[桥接 /api/meta]')
        print(u'  ok=%s  linked=%s  master=%s' % (d.get('ok'), d.get('linked'), d.get('master')))
        print(u'  话题 %s/%s   节点 %s   服务 %s   故障等级 %s   告警 %s'
              % (d.get('topics_online'), d.get('topics_watched'), d.get('nodes'),
                 d.get('services'), d.get('fault_level'), d.get('fault_alarm')))
        g = d.get('groups') or {}
        if g:
            print(u'  分子系统在线率:')
            for k in sorted(g):
                v = g[k]
                print(u'     %-10s %s/%s' % (k, v.get('ok'), v.get('total')))
    except Exception as e:
        print(u'  [桥接 API 取不到] %s' % e)

    # 2) 故障清除能力探测（这正是之前一直卡着的那件事）
    run('probe_fault_services.py')

    print(u'\n' + u'=' * 66)
    print(u' 探测结束')
    print(u'=' * 66)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

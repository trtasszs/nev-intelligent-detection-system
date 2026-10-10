# -*- coding: utf-8 -*-
"""
故障清除能力探测
==================================================================
目的：回答「这个平台到底能不能清故障码、用哪种方式清」。

背景（已查证）：
  · can_bridge.py 只调用了 VCI_Receive，**没有发送能力**（VCI_Transmit 0 次）；
    但 ControlCAN.dll 里 VCI_Transmit 是存在的，硬件层面能发。
  · ros_bridge.py 8 个接口全是只读，没有任何 service 调用。
  · 官方手册里唯一的「故障清除」是**重启对应模块**（roslaunch），
    全篇 DTC / UDS / 0x14 / 诊断服务 / 故障码 均为 0 命中 ⇒ 平台不走标准诊断协议。

本脚本在车机接回来时运行，输出三个判断：
  ① ROS master 上有没有「清除/复位」类服务  → 有就能一键清（最正统）
  ② 故障话题现在是活的还是死的              → 判断能否做"清完再验证"
  ③ 给出结论：走 A（调服务）/ B（重启模块）/ C（CAN UDS，依据不足）

用法：python probe_fault_services.py [--master 192.168.1.102:11311]
"""
import argparse
import re
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# 复用 ros_bridge / ros_probe 里已验证过的连接方式（握手发 md5sum='*'、type='*'）
try:
    from ros_probe import connect_publisher, MASTER
except Exception:
    connect_publisher = None
    MASTER = '192.168.1.102:11311'


# 关键词：命中任意一个就算"可能是清除接口"
KW = [u'clear', u'reset', u'remove', u'delete', u'purge', u'ack', u'recover',
      u'rcover', u'fault', u'dtc', u'diag', u'clean', u'\u6e05', u'\u590d\u4f4d',
      u'\u6062\u590d', u'\u91cd\u7f6e']

# 明确像"清除故障"的强特征（优先级更高）
STRONG = [u'clear_fault', u'fault_clear', u'clearfault', u'reset_fault', u'resetfault',
          u'clear_dtc', u'cleardtc', u'dtc_clear', u'clear_error', u'clearerr',
          u'ack_fault', u'ackfault', u'recover_fault', u'fault_reset',
          u'clear_alarm', u'alarm_clear', u'clearalarm']

# 故障相关话题
FAULT_TOPICS = [u'/fault_info', u'/fault_alarm', u'/ult_fault', u'/fault',
                u'/diagnostic', u'/diag']


def master_call(master, method, *params):
    """直接走 ROS master 的 XMLRPC，和 ros_bridge 同一套做法"""
    import xmlrpc.client
    uri = 'http://' + master.replace('rosmaster://', '').replace('http://', '')
    p = xmlrpc.client.ServerProxy(uri)
    return getattr(p, method)(u'/probe', *params)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--master', default=MASTER)
    a = ap.parse_args()
    M = a.master

    print(u'=' * 68)
    print(u' 故障清除能力探测   master = %s' % M)
    print(u'=' * 68)

    # ---------- 1. 拿系统状态（话题 / 服务 / 节点） ----------
    try:
        code, st, val = master_call(M, 'getSystemState')
    except Exception as e:
        print(u'[x] 连不上 ROS master：%s' % e)
        print(u'    先确认车机以太网已插好、192.168.1.102 可达。')
        return 2

    if code != 1:
        print(u'[x] master 返回 code=%s statusMessage=%s' % (code, st))
        return 2

    topics, services, nodes = val[0], val[1], val[2]
    print(u'\n[1] 系统规模')
    print(u'    话题 %d · 服务 %d · 节点 %d' % (len(topics), len(services), len(nodes)))

    svc_names = sorted(set(s[0] for s in services))
    print(u'\n[2] 全部服务名（%d 个）' % len(svc_names))
    for n in svc_names:
        print(u'      ' + n)

    # ---------- 2. 找清除/复位类服务 ----------
    strong, weak = [], []
    for n in svc_names:
        low = n.lower()
        if any(k in low for k in STRONG):
            strong.append(n)
        elif any(k in low for k in KW):
            weak.append(n)

    print(u'\n[3] 清除/复位类服务筛查')
    print(u'    ★ 强特征（几乎确定是清除接口）: %d 个' % len(strong))
    for n in strong:
        print(u'        ' + n)
    print(u'    · 弱特征（可能相关，需人工看）: %d 个' % len(weak))
    for n in weak:
        print(u'        ' + n)

    # ---------- 3. 故障话题现状 ----------
    print(u'\n[4] 故障相关话题')
    tnames = [t[0] for t in topics]
    alive = []
    for pat in FAULT_TOPICS:
        for n in tnames:
            if n == pat or n.startswith(pat + '/') or pat in n:
                pubs = [p for p in topics if p[0] == n]
                cnt = len(pubs[0][1]) if pubs else 0
                alive.append((n, cnt))
    if alive:
        for n, c in sorted(set(alive)):
            print(u'    %-24s 发布者 %d %s' % (n, c, u'（活）' if c else u'（无发布者=死）'))
    else:
        print(u'    没找到故障话题')

    # ---------- 4. 结论 ----------
    print(u'\n' + u'=' * 68)
    print(u' 结论')
    print(u'=' * 68)
    if strong:
        print(u'  ⇒ 走【方案 A】直接调用清除服务，这是最正统的做法：')
        for n in strong:
            print(u'        rosservice call %s' % n)
        print(u'     实现方式：给 ros_bridge.py 加 /api/faults/clear，内部 XMLRPC/ROSService 调用上述服务。')
    elif weak:
        print(u'  ⇒ 有疑似接口，需逐个确认语义：')
        for n in weak:
            print(u'        ' + n)
        print(u'     确认后按【方案 A】接入。')
    else:
        print(u'  ⇒ master 上没有清除类服务。')
        print(u'     只能走【方案 B：重启故障模块】—— 也就是官方手册 3.2.3.2 的做法：')
        print(u'        ssh nvidia@192.168.1.102  (密码 idriver_bbox)')
        print(u'        cd /work/share/project/Icv && source devel/setup.bash')
        print(u'        roslaunch <对应模块> <对应.launch>')
        print(u'     注意：手册全篇没有 DTC / UDS / 0x14，平台不走标准诊断协议；')
        print(u'           【方案 C：CAN 发 UDS 0x14】虽然 ControlCAN.dll 有 VCI_Transmit，')
        print(u'           但没有协议依据，且抓到的 CAN 都是私有报文、非诊断故障码，不建议做。')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

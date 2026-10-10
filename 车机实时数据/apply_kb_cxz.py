# -*- coding: utf-8 -*-
"""
给车小智页面（车小智.html）的「本地兜底诊断」补上智能网联一级故障条目
==================================================================
背景：页面在**后端不可用**时会回退到自己的 getDiagnosisData()，
      而它原来只有「动力电池 / 充电 / 电池性能 / 通用」四类 ⇒
      问到「一级故障 + 无法 READY + 车身 CAN 线故障 + 前三个感知传感器报损」时
      会退化成通用话术，而不是该给的 4 步。

做法：在 getDiagnosisData() 的**最前面**插一个分支（多信号命中 ≥2 才判），
      返回与后端 knowledge.py 里 nev-level1-can-ads 完全一致的 4 步。
      幂等：靠 BEGIN/END 标记，重复执行不会叠加。

    python apply_kb_cxz.py
"""
import io
import os
import re
import shutil
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

PAGE = r'E:\！！！高职比赛\车小智.html'
BEGIN = '/* ==== CXZ-KB-LOCAL BEGIN（一级故障本地兜底）==== */'
END = '/* ==== CXZ-KB-LOCAL END ==== */'

BRANCH = BEGIN + """
            // ★智能网联平台招牌故障：一级故障 + 无法 READY + 车身 CAN 线故障 + 前向感知传感器报损。
            //   必须放在最前面判 —— 否则会被下面「雷达 / 摄像头 / 无法启动」那几类关键词先吃掉，
            //   退化成通用话术（实测过）。判定用「多信号命中 >=2」，既不漏也不误伤。
            var _q = String(faultDescription || '');
            var _sig = ['一级故障', '无法ready', '无法 ready', 'ready不了', '无法READY',
                        '车身CAN', '车身can', 'CAN线故障', 'can线故障', 'CAN总线故障',
                        '前中毫米波', '前毫米波雷达', '前中超声波', '前超声波雷达',
                        '前摄像头', '前视摄像头', '传感器损坏', '雷达损坏', '智能网联'];
            var _hits = 0;
            for (var _i = 0; _i < _sig.length; _i++) {
                if (_q.indexOf(_sig[_i]) >= 0) _hits++;
            }
            if (_hits >= 2) {
                return {
                    faultType: '智能网联整车一级故障（车身 CAN 链路 + 前向感知传感器）',
                    severityLevel: { text: '高', class: 'text-error font-medium' },
                    possibleCauses: '整车 CAN 总线线束或接插件松动、退针、短路、虚接；CAN-H/CAN-L 电压异常或终端电阻缺失导致通信中断；前中毫米波雷达、前中超声波雷达、前中摄像头供电异常、插头松脱、硬件损坏或安装移位；传感器基础标定丢失或被改写；多传感器融合的时空同步与外参标定不一致；线控转向/线控制动标定失效。多个前向感知传感器同时报损时，优先怀疑公共供电、搭铁或共用 CAN 支路，而不是三个传感器同时坏。',
                    systems: ['整车 CAN 总线', '中央网关', '前中毫米波雷达', '前中超声波雷达',
                              '前中摄像头', 'ADAS 域控', '多传感器融合', '线控转向', '线控制动'],
                    steps: [
                        {
                            title: '排查 CAN 线故障',
                            description: '检查整车 CAN 总线线束、接插件有无松动、退针、短路、虚接；测量 CAN-H、CAN-L 电压与终端电阻，排查通信异常问题。',
                            keyPoints: '断电测 CAN-H 与 CAN-L 之间电阻，应约 60Ω（两端各 120Ω 并联）；上电测对地电压，隐性时两线均约 2.5V，显性时 CAN-H 升、CAN-L 降。接插件重点看退针与虚接，线束重点看有无磨破短路。'
                        },
                        {
                            title: '排查传感器故障（前中毫米波雷达、前中超声波雷达、前中摄像头）',
                            description: '检查各感知传感器供电、插头是否牢靠；读取传感器内部状态报文，检查硬件是否损坏、安装是否移位，核对传感器基础标定状态。',
                            keyPoints: '逐个确认供电与插头是否牢靠；读取传感器内部状态报文，区分是硬件损坏、安装移位还是标定丢失；三个前向传感器同时报损时先查公共供电与搭铁。'
                        },
                        {
                            title: '系统功能测试（多传感器融合标定、线控底盘标定）',
                            description: '开展多传感器融合一致性校验，核查时空同步与外参标定；对线控转向、线控制动执行标定与动态响应测试，观测感知-底盘联动是否存在异常。',
                            keyPoints: '多传感器融合重点核查时间同步与空间外参是否一致；线控转向、线控制动要重新标定并做动态响应测试，观察感知与底盘联动是否异常。'
                        },
                        {
                            title: '专业检查与验证',
                            description: '由专业技术人员结合报文数据、标定记录做深度复现验证；若故障依旧无法定位，送至专业技术服务中心做全面检测。',
                            keyPoints: '把 CAN 报文数据与标定记录一并做深度复现验证；仍无法定位时，再送专业技术服务中心做全面检测。'
                        }
                    ],
                    suggestions: [
                        '先确认 CAN 总线物理层正常，再排查上层传感器与标定问题；物理层不通时上层排查全是无效功',
                        '保留故障发生时的 CAN 报文与标定记录，便于复现与回溯',
                        '三个前向感知传感器同时报损，优先查公共供电、搭铁与共用 CAN 支路，不要按三个独立故障处理',
                        '涉及线控转向、线控制动的标定测试，须在安全场地且由具备资质的人员操作',
                        '车辆无法 READY 属一级故障，禁止强行反复上电，避免扩大损伤'
                    ]
                };
            }
            """ + END + '\n'

ANCHOR = "function getDiagnosisData(faultDescription) {\n"


def main():
    t = io.open(PAGE, encoding='utf-8').read()
    before = len(t)

    if BEGIN in t:
        # 已注入：整体替换掉旧块，保证内容可更新
        t = re.sub(re.escape(BEGIN) + r'.*?' + re.escape(END) + r'\n?',
                   lambda m: BRANCH, t, count=1, flags=re.S)
        action = u'更新'
    else:
        idx = t.find(ANCHOR)
        if idx < 0:
            print(u'  ✗ 找不到锚点 function getDiagnosisData(faultDescription) {')
            return 1
        pos = idx + len(ANCHOR)
        t = t[:pos] + BRANCH + t[pos:]
        action = u'注入'

    if t == io.open(PAGE, encoding='utf-8').read() and action == u'更新':
        print(u'  内容无变化')
    else:
        bak = PAGE + '.bak-kb'
        if not os.path.exists(bak):
            shutil.copy2(PAGE, bak)
        io.open(PAGE, 'w', encoding='utf-8').write(t)

    t2 = io.open(PAGE, encoding='utf-8').read()
    print(u'  %s完成：页面 %.0f KB -> %.0f KB' % (action, before / 1024.0, len(t2) / 1024.0))
    print(u'  标记块数量 = %d（应为 1）' % t2.count(BEGIN))
    for k, v in ((u'一级故障本地兜底', 'CXZ-KB-LOCAL BEGIN'),
                 (u'4 步：CAN', u'排查 CAN 线故障'),
                 (u'4 步：传感器', u'排查传感器故障（前中毫米波雷达'),
                 (u'4 步：系统功能测试', u'系统功能测试（多传感器融合标定'),
                 (u'4 步：专业验证', u'专业检查与验证')):
        print(u'    %-16s %s' % (k, u'✓' if v in t2 else u'✗'))
    return 0


if __name__ == '__main__':
    sys.exit(main())

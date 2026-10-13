# -*- coding: utf-8 -*-
"""
删除 #vehicles（车辆信息管理）里电池相关的硬编码假数据
==================================================================
删三处（都经人工确认过上下文，锚点明确）：
  ① 「充电状态」整张卡片          —— 未充电 / 充电方式无效 / 充电量无效
  ② 「动力蓄电池系统」整张卡片     —— 2级报警 + 电池包基础信息 + 电池包故障表
  ③ 「核心运行数据」里的 总电压 / 总电流 / SOC 三项
     （保留 车速、累计里程 —— 它们不是电池数据）
并在原处留一个指向真数据的提示。
幂等：靠 BEGIN/END 标记。
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

P = r'E:\！！！高职比赛\新能源汽车智能检测系统-1.0版.html'
MK_B = '<!-- ==== CX-FAKEBAT-REMOVED BEGIN ==== -->'
MK_E = '<!-- ==== CX-FAKEBAT-REMOVED END ==== -->'

HINT = (MK_B +
        u'\n<div class="bg-dark-400 p-3 border border-gray-700 text-xs text-gray-400 mb-4">'
        u'<i class="fa fa-info-circle mr-1"></i>'
        u'电池的电压、SOC、温度、电流等数据已改为读取真实 CAN 报文，'
        u'请见左侧导航「<b class="text-gray-300">BMS 实时监测</b>」。'
        u'本页原有的电池演示数据已删除。'
        u'</div>\n' + MK_E)


def main():
    t = io.open(P, encoding='utf-8').read()
    n = 0

    # 清旧标记（幂等）
    t2 = re.sub(re.escape(MK_B) + r'.*?' + re.escape(MK_E) + r'\n?', '', t, count=1, flags=re.S)
    if t2 != t:
        t = t2
        print(u'  摘掉旧提示块')

    # ① 充电状态卡片：从「<!-- 充电状态 -->」到「<!-- 高压系统状态 -->」之前
    m = re.search(r'\s*<!-- 充电状态 -->.*?(?=\s*<!-- 高压系统状态 -->)', t, re.S)
    if m:
        t = t[:m.start()] + t[m.end():]
        n += 1
        print(u'  [1] 「充电状态」卡片已删')
    else:
        print(u'  [1] ✗ 找不到充电状态卡片')

    # ② 动力蓄电池系统卡片：从其注释到下一个同级系统注释之前
    m = re.search(r'\s*<!-- 动力蓄电池系统 -->.*?(?=\s*<!-- [^>]*系统[^>]* -->|\s*</div>\s*<!-- 底盘)', t, re.S)
    if m:
        # 保险：删掉的片段里必须确实含 battery-content，避免误删
        if 'battery-content' in m.group(0):
            t = t[:m.start()] + t[m.end():]
            n += 1
            print(u'  [2] 「动力蓄电池系统」卡片已删（含 %d 字符）' % len(m.group(0)))
        else:
            print(u'  [2] ✗ 锚定的片段里没有 battery-content，放弃删除')
    else:
        print(u'  [2] ✗ 找不到动力蓄电池系统卡片')

    # ③ 核心运行数据里的 总电压 / 总电流 / SOC 三项
    for label in (u'总电压', u'总电流', u'SOC'):
        pat = re.compile(
            r'\s*<div class="flex flex-col">\s*<span class="text-gray-400 text-sm">' +
            re.escape(label) +
            r'</span>\s*<span[^>]*>[^<]*<span[^>]*>[^<]*</span></span>\s*</div>', re.S)
        t2, c = pat.subn('', t, count=1)
        if c:
            t = t2
            n += 1
            print(u'  [3] 核心运行数据里的「%s」已删' % label)
        else:
            print(u'  [3] ✗ 没匹配到「%s」' % label)

    # 在 #vehicles 页开头放提示
    m = re.search(r'(<div id="vehicles" class="page-content[^>]*">)', t)
    if m and MK_B not in t:
        t = t[:m.end()] + u'\n' + HINT + t[m.end():]
        n += 1
        print(u'  [4] 已加"数据已迁移"提示')

    io.open(P, 'w', encoding='utf-8').write(t)
    print(u'\n  已写盘 %d 处' % n)

    # 回读自检
    t3 = io.open(P, encoding='utf-8').read()
    print(u'  回读:')
    for k, v, want in ((u'充电状态卡片', u'未充电', False),
                       (u'battery-content', 'battery-content', False),
                       (u'电池包故障表', u'电池高温报警', False),
                       (u'提示块', MK_B, True),
                       (u'车速还在', u'>车速<', True),
                       (u'累计里程还在', u'累计里程', True)):
        ok = (v in t3)
        print(u'    %-16s %s' % (k, u'✓ 已无' if (not ok and not want) else (u'✓ 在' if ok else u'✗')))


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""
给检测系统看板加一个「关于我们」页面
------------------------------------------------------------------
内容：企业痛点→解法 / 系统能力 / 研发过程 / 核心团队（三张队员照）
接入：侧边栏与移动端菜单各加一个 data-target="about" 的导航项（克隆现有的 settings 项保持样式一致），
      页面容器插在 </main> 之前。
"""
import io
import os
import re
import shutil
import time

PAGE = r'E:\！！！高职比赛\新能源汽车智能检测系统-1.0版.html'
B64 = os.path.join(os.environ['TEMP'], 'cx-boot', 'team_b64.txt')

NAMES = [u'孙仲星', u'徐子晗', u'郑永彬']
ROLES = [
    (u'汽车电子 · CAN 总线', u'CAN / 总线诊断',
     u'负责整车 CAN 报文矩阵解析与线控底盘诊断链路，逐字节标定了 60 余个报文 ID 的物理含义。'),
    (u'嵌入式 · ROS 域控', u'ROS / 域控接入',
     u'负责车机 ROS 域控接入与故障流采集，打通 89 个话题、33 个节点的实时监控链路。'),
    (u'人工智能 · 诊断算法', u'AI / 诊断推理',
     u'负责故障知识库构建与大模型诊断推理，让故障码、波形与自然语言描述互相印证。'),
]

STATS = [
    (u'6', u'类车载总线并行诊断'),
    (u'89', u'ROS 话题实时接入'),
    (u'2450+', u'CAN 帧/秒 实测解析'),
    (u'10 Hz', u'32 线激光雷达成帧'),
    (u'100 Hz', u'组合导航 INS 数据率'),
    (u'5', u'类器件品质检测工位'),
]

PAINS = [
    (u'诊断靠老师傅经验',
     u'故障码要翻手册、波形靠人眼判读，老师傅一走经验就断档。',
     u'总线数据 + AI 推理直接给结论：故障模块、可能原因、分步排查路径一次给出。'),
    (u'工具各自为政',
     u'CAN 分析仪、雷达上位机、标定工具互不相通，一个故障要在四五个软件之间来回切。',
     u'一个看板统一接入整车 / 电池 / 底盘 / 车身 / 私有 CAN 与 ROS 域控，不用来回倒腾。'),
    (u'数据拿不到',
     u'原厂工具只负责"显示"，不开放报文接口，想二次开发无从下手。',
     u'自研 CAN / ROS 双通道桥接层，把总线报文、感知话题与故障码统一成可解释的诊断语言。'),
    (u'现场没网没环境',
     u'诊断软件依赖云端、依赖外网，到了检测工位才发现连不上。',
     u'单文件离线部署，依赖全部内嵌 —— 拷过去双击就能用，不联网也完整可用。'),
    (u'新人上手慢',
     u'一套系统培训要几个月，工位换人就要重新教一遍。',
     u'自然语言问答 + 分步引导，新人照着提示走就能完成一轮检测。'),
]

PHASES = [
    (u'起点', u'发现问题',
     u'车机数据"看得见、用不上"：原厂工具只能显示，不能诊断，更不能追溯。',
     u'把总线数据变成可判断的结论'),
    (u'阶段一', u'打通 CAN 总线',
     u'USBCAN-II @500 kbps 接入整车 CAN，逐字节实测标定报文含义（车速、档位、EPB、巡航、踏板、转向、四轮轮速、横摆）。',
     u'60+ 报文 ID 可读、可解释'),
    (u'阶段二', u'接入 ROS 域控',
     u'直连车机 ROS Master，订阅 89 个话题 / 33 个节点，把组合导航、里程、感知与系统故障汇到同一屏。',
     u'感知与底盘数据统一时基'),
    (u'阶段三', u'多总线扩展',
     u'把诊断链路铺到电池 CAN、底盘 CAN、车身 CAN、智能 CAN 与私有 CAN；接入 32 线激光雷达、毫米波雷达、超声波雷达。',
     u'6 类总线 + 3 类传感器'),
    (u'阶段四', u'从数据到诊断',
     u'对接车机 fault_info / fault_alarm，构建故障知识库与大模型问答，输出可执行的维修步骤。',
     u'故障可溯、步骤可执行'),
    (u'阶段五', u'工程化打磨',
     u'离线单文件部署、日间/夜间双主题、桥接开机自启、一键启动 —— 把实验室原型做成能在检测工位跑的东西。',
     u'拷过去就能用'),
]


def build_team(b64s):
    out = u''
    for i, (b, nm, role) in enumerate(zip(b64s, NAMES, ROLES)):
        out += (
            u'<div class="relative group">'
            u'<div class="relative border border-gray-700 overflow-hidden">'
            u'<span class="absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2 border-primary-500 z-10"></span>'
            u'<span class="absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2 border-primary-500 z-10"></span>'
            u'<span class="absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2 border-primary-500 z-10"></span>'
            u'<span class="absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2 border-primary-500 z-10"></span>'
            u'<img src="data:image/jpeg;base64,%s" alt="%s" loading="lazy" '
            u'style="aspect-ratio:4/5" '
            u'class="w-full object-cover object-top transition-transform duration-700 group-hover:scale-105">'
            u'<span class="absolute top-2 left-2 text-[10px] font-mono tracking-widest bg-black/55 text-white px-2 py-0.5">MEMBER %02d</span>'
            u'</div>'
            u'<div class="pt-4">'
            u'<p class="font-bold text-white text-lg">%s</p>'
            u'<p class="text-sm font-mono tracking-wide mt-1 text-primary-500">%s</p>'
            u'<p class="text-sm text-gray-400 mt-3 leading-relaxed">%s</p>'
            u'</div></div>' % (b, nm, i + 1, nm, role[0], role[1])
        )
    return out


def build_page(b64s):
    stats = u''.join(
        u'<div class="text-center px-4 py-5 border border-gray-700">'
        # data-cx-counted：看板动效层的「数字滚动」会改 card 里的纯数字文本
        # （正则 ^[\d,]+(\.\d+)?%?$ 且 >=3 就滚），打上这个标记它就会跳过，避免数值被动画改写
        u'<p class="text-2xl font-bold text-white tracking-tight" data-cx-counted="1">%s</p>'
        u'<p class="text-xs text-gray-400 mt-1">%s</p></div>' % (n, l) for n, l in STATS)

    pains = u''.join(
        u'<tr class="border-b border-gray-700">'
        u'<td class="py-4 pr-5 align-top"><span class="text-sm text-white font-medium">%s</span></td>'
        u'<td class="py-4 pr-5 align-top text-sm text-gray-400 leading-relaxed">%s</td>'
        u'<td class="py-4 align-top text-sm text-gray-300 leading-relaxed border-l-2 border-primary-500 pl-4">%s</td>'
        u'</tr>' % p for p in PAINS)

    phases = u''.join(
        u'<div class="relative pl-8 pb-7 border-l border-gray-700 last:border-l-transparent last:pb-0">'
        u'<span class="absolute -left-[5px] top-1 w-2.5 h-2.5 bg-primary-500"></span>'
        u'<p class="font-mono text-xs tracking-[0.2em] text-primary-500 mb-1">%s · %s</p>'
        u'<p class="text-white font-medium mb-2">%s</p>'
        u'<p class="text-sm text-gray-400 leading-relaxed mb-2">%s</p>'
        u'<p class="text-xs font-mono text-secondary-500">▸ 产出：%s</p>'
        u'</div>' % (a, b, b, c, d) for a, b, c, d in PHASES)

    return u'''<div id="about" class="page-content hidden">

                    <!-- 标题区 -->
                    <div class="card mb-6">
                        <div class="flex items-start justify-between flex-wrap gap-4">
                            <div class="flex-1 min-w-[280px]">
                                <p class="font-mono text-xs tracking-[0.3em] text-primary-500 mb-2">MODULE 09 / ABOUT US</p>
                                <h3 class="text-2xl font-medium text-white mb-3">关于我们</h3>
                                <p class="text-gray-400 leading-relaxed">
                                    一支把<strong class="text-primary-500">真实车机数据</strong>做进诊断系统的三人团队。
                                    我们不满足于演示级的数据 —— 系统自立项起就<strong class="text-primary-500">直接接入国汽智联「智能网联汽车技术平台」</strong>，
                                    用真车、真总线、真传感器打磨每一处诊断逻辑。
                                </p>
                            </div>
                            <div class="text-right font-mono text-xs text-gray-500 leading-loose shrink-0">
                                SN-ICV-2.3-0909<br>
                                REV.5<br>
                                BUILD 2026.10
                            </div>
                        </div>
                    </div>

                    <!-- 系统能力数据条 -->
                    <div class="card mb-6">
                        <div class="flex items-center mb-5">
                            <span class="font-mono text-xs tracking-[0.25em] text-gray-500">SYSTEM SCALE</span>
                            <span class="flex-1 border-t border-gray-700 ml-4"></span>
                        </div>
                        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-px bg-gray-700">%s</div>
                        <p class="text-xs text-gray-500 mt-3 font-mono">* 以上均为本项目实测值，非设计指标</p>
                    </div>

                    <!-- 企业痛点 → 解法 -->
                    <div class="card mb-6">
                        <div class="flex items-center mb-5">
                            <span class="font-mono text-xs tracking-[0.25em] text-gray-500">PAIN POINT / SOLUTION</span>
                            <span class="flex-1 border-t border-gray-700 ml-4"></span>
                        </div>
                        <h3 class="text-lg font-medium text-white mb-2">企业痛点 · 我们的解法</h3>
                        <p class="text-sm text-gray-400 mb-6">新能源检测工位真正卡住的地方，以及我们对应做了什么。</p>
                        <div class="overflow-x-auto">
                            <table class="w-full min-w-[720px]">
                                <thead>
                                    <tr class="border-b border-gray-600">
                                        <th class="text-left py-3 pr-5 text-xs font-mono tracking-widest text-gray-500">痛点</th>
                                        <th class="text-left py-3 pr-5 text-xs font-mono tracking-widest text-gray-500">现在的做法</th>
                                        <th class="text-left py-3 text-xs font-mono tracking-widest text-primary-500">车小智的解法</th>
                                    </tr>
                                </thead>
                                <tbody>%s</tbody>
                            </table>
                        </div>
                    </div>

                    <!-- 研发过程 -->
                    <div class="card mb-6">
                        <div class="flex items-center mb-5">
                            <span class="font-mono text-xs tracking-[0.25em] text-gray-500">R&amp;D PROCESS</span>
                            <span class="flex-1 border-t border-gray-700 ml-4"></span>
                        </div>
                        <h3 class="text-lg font-medium text-white mb-2">研发过程</h3>
                        <p class="text-sm text-gray-400 mb-8">从"数据看得见但用不上"，到能在检测工位跑起来。</p>
                        <div>%s</div>
                    </div>

                    <!-- 核心团队 -->
                    <div class="card mb-6">
                        <div class="flex items-center mb-5">
                            <span class="font-mono text-xs tracking-[0.25em] text-gray-500">TEAM / 03 MEMBERS</span>
                            <span class="flex-1 border-t border-gray-700 ml-4"></span>
                        </div>
                        <h3 class="text-lg font-medium text-white mb-2">核心团队</h3>
                        <p class="text-sm text-gray-400 mb-8">三人分工覆盖汽车电子、嵌入式系统、人工智能三个方向，从总线物理层一路做到诊断推理层。</p>
                        <div class="grid md:grid-cols-3 gap-8">%s</div>
                    </div>

                    <!-- 收尾三原则 -->
                    <div class="card">
                        <div class="grid md:grid-cols-3 gap-8">
                            <div>
                                <p class="font-mono text-xs tracking-widest text-primary-500 mb-2">01 / 真实数据</p>
                                <p class="text-sm text-gray-400 leading-relaxed">全系统数据来自真实车机总线与感知话题，拒绝模拟值。</p>
                            </div>
                            <div>
                                <p class="font-mono text-xs tracking-widest text-primary-500 mb-2">02 / 可追溯</p>
                                <p class="text-sm text-gray-400 leading-relaxed">每个诊断结论都能回溯到具体的报文 ID、话题名或故障码。</p>
                            </div>
                            <div>
                                <p class="font-mono text-xs tracking-widest text-primary-500 mb-2">03 / 可落地</p>
                                <p class="text-sm text-gray-400 leading-relaxed">面向真实维修工位设计，输出的是可执行的排查与维修步骤。</p>
                            </div>
                        </div>
                    </div>

                </div>

''' % (stats, pains, phases, build_team(b64s))


def main():
    b64s = [l.strip() for l in io.open(B64, encoding='utf-8').read().splitlines() if l.strip()]
    if len(b64s) != 3:
        raise SystemExit(u'[x] 队员照 base64 数量不对: %d' % len(b64s))

    t = io.open(PAGE, encoding='utf-8').read()
    n0 = len(t)
    shutil.copy2(PAGE, PAGE + '.bak-about-' + time.strftime('%Y%m%d-%H%M%S'))

    if u'id="about"' in t and u'data-target="about"' in t:
        print(u'  [!] 关于我们页已存在，先移除再重建')
        t = re.sub(r'\s*<div id="about" class="page-content hidden">.*?</div>\s*(?=</main>)', u'\n', t, flags=re.S)
        t = re.sub(r'\s*<li>\s*<a href="#about"[^>]*data-target="about">.*?</li>', u'', t, flags=re.S)

    # ---- 1. 克隆 settings 导航项，改成 about（桌面 + 移动端各一处）----
    pat = re.compile(r'(<li>\s*<a href="#settings"[^>]*data-target="settings">.*?</li>)', re.S)

    def add_nav(m):
        blk = m.group(1)
        new = (blk.replace('href="#settings"', 'href="#about"')
                  .replace('data-target="settings"', 'data-target="about"')
                  .replace('fa fa-cog sidebar-icon', 'fa fa-users sidebar-icon')
                  .replace(u'系统设置', u'关于我们'))
        return blk + u'\n' + new

    t, nnav = pat.subn(add_nav, t)
    print(u'  导航项新增: %d 处（桌面 + 移动端）' % nnav)

    # ---- 2. 插入页面容器（</main> 之前）----
    t, npage = re.subn(r'(\s*)(</main>)', lambda m: u'\n' + build_page(b64s) + m.group(2), t, count=1)
    print(u'  页面容器插入: %d 处' % npage)

    for k in (u'id="about"', u'data-target="about"', u'</main>', u'id="settings"', u'MEMBER 01', u'孙仲星'):
        if k not in t:
            raise SystemExit(u'[x] 终检失败：缺 %s' % k)
    if t.count(u'data-target="about"') != 2:
        raise SystemExit(u'[x] 导航项数量异常: %d' % t.count(u'data-target="about"'))

    io.open(PAGE, 'w', encoding='utf-8').write(t)
    print(u'  页面  %.0f KB -> %.0f KB' % (n0 / 1024.0, len(t) / 1024.0))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

# -*- coding: utf-8 -*-
"""
重写 车小智.html 的「关于我们」区块
------------------------------------------------------------------
1. 把三张队员照片（HEIC）转成内嵌 base64 JPEG
2. 用真实数据写「吹得起、也站得住」的介绍（数据全部来自本项目实测）
3. 替换 <section id="about">…</section>
"""
import base64
import io
import os
import re
import shutil
import time

from PIL import Image, ImageDraw
from pillow_heif import register_heif_opener

register_heif_opener()

PAGE = r'E:\！！！高职比赛\车小智.html'
SRC = r'D:\Users\ASUS\Documents\xwechat_files\wxid_octmdo6p4uox22_4915\msg\file\2026-10'
PHOTOS = ['IMG_5033(1).HEIC', 'IMG_5042(1).HEIC', 'IMG_5035(1).HEIC']
OUTDIR = r'E:\！！！高职比赛\车小智-后端\team'
os.makedirs(OUTDIR, exist_ok=True)

MEMBERS = [
    {'role': u'汽车电子 · CAN 总线', 'tag': u'CAN / 总线诊断',
     'desc': u'负责整车 CAN 报文矩阵解析与线控底盘诊断链路，完成 60 余个报文 ID 的实测标定。'},
    {'role': u'嵌入式 · ROS 域控', 'tag': u'ROS / 域控接入',
     'desc': u'负责车机 ROS 域控接入与故障流采集，打通 89 个话题、32 个节点的实时监控链路。'},
    {'role': u'人工智能 · 诊断算法', 'tag': u'AI / 诊断推理',
     'desc': u'负责故障知识库构建与大模型诊断推理，让故障码、波形与自然语言描述互相印证。'},
]


def photo_b64(path, w=520, h=680):
    """HEIC -> 居中裁成 4:5 -> JPEG -> base64"""
    im = Image.open(path)
    im.load()
    im = im.convert('RGB')
    target = w / float(h)
    iw, ih = im.size
    cur = iw / float(ih)
    if cur > target:                       # 太宽，裁两边
        nw = int(ih * target)
        im = im.crop(((iw - nw) // 2, 0, (iw + nw) // 2, ih))
    else:                                  # 太高，从上方裁（保留头部）
        nh = int(iw / target)
        top = int((ih - nh) * 0.18)
        im = im.crop((0, top, iw, top + nh))
    im = im.resize((w, h), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=84, optimize=True, progressive=True)
    return base64.b64encode(buf.getvalue()).decode('ascii'), len(buf.getvalue())


def build():
    b64s = []
    for n in PHOTOS:
        b, sz = photo_b64(os.path.join(SRC, n))
        b64s.append(b)
        print(u'  %s -> %d KB (base64 %d KB)' % (n, sz // 1024, len(b) // 1024))

    STATS = [
        ('89', u'ROS 话题实时接入', 'fa-sitemap'),
        ('2450+', u'CAN 帧/秒 实测解析', 'fa-bolt'),
        ('32', u'车机节点在线监控', 'fa-microchip'),
        ('10 Hz', u'32 线激光雷达成帧', 'fa-broadcast-tower'),
        ('100 Hz', u'组合导航 INS 数据率', 'fa-satellite-dish'),
        ('6', u'类车载总线诊断链路', 'fa-project-diagram'),
    ]
    CAPS = [
        (u'整车 CAN 诊断', u'fa-car-side', 'primary',
         u'OBD 直读整车 CAN：车速、档位、EPB、巡航、踏板、转向角、四轮轮速、横摆角速度，全部来自真实总线，非模拟值。'),
        (u'车机 ROS 接入', u'fa-network-wired', 'secondary',
         u'直连车机 ROS 域控，89 个话题、32 个节点一屏呈现；组合导航姿态、里程定位、感知话题、系统故障实时刷新。'),
        (u'激光雷达点云', u'fa-broadcast-tower', 'primary',
         u'32 线激光雷达 10 Hz 成帧，支持俯视 BEV / 侧视 / 30° 立体三视图出图，可导出点云快照用于标定核对。'),
        (u'故障事件链', u'fa-exclamation-triangle', 'warning',
         u'直接对接车机 fault_info / fault_alarm，故障码、等级、模块、时间戳可溯；支持一键生成分步维修建议。'),
        (u'AI 智能问答', u'fa-robot', 'secondary',
         u'大模型 + 自建故障知识库双引擎，可用自然语言描述现象，系统反查总线数据、给出排查路径与维修步骤。'),
        (u'总线品质检测', u'fa-clipboard-check', 'primary',
         u'覆盖毫米波雷达、超声波雷达等器件级品质检测工位：上位机配置、原始报文核对、合格判定全流程记录。'),
    ]
    BASE = [
        (u'被测平台', u'国汽智联 智能网联汽车技术平台'),
        (u'计算平台', u'Jetson 域控 · ROS Master · 多路相机 / 激光雷达'),
        (u'总线体系', u'整车 CAN / 电池 CAN / 底盘 CAN / 车身 CAN / 私有 CAN'),
        (u'自研工具链', u'Python · Qt 上位机 · Web 全栈 · 全部自研'),
    ]

    def card(title, icon, tone, desc):
        c = {'primary': 'text-primary-500', 'secondary': 'text-secondary-500',
             'warning': 'text-warning'}[tone]
        return (u'<div class="bg-gray-100 rounded-none p-6 border border-transparent '
                u'hover:border-primary-500 transition-colors">'
                u'<div class="flex items-center mb-3">'
                u'<i class="fas %s %s text-xl mr-3"></i>'
                u'<h4 class="font-bold">%s</h4></div>'
                u'<p class="text-sm text-gray-600 leading-relaxed">%s</p></div>'
                % (icon, c, title, desc))

    stats_html = u''.join(
        u'<div class="text-center px-4 py-5 border border-gray-200">'
        u'<i class="fas %s text-primary-500 text-lg mb-2 block"></i>'
        u'<p class="text-2xl md:text-3xl font-bold tracking-tight">%s</p>'
        u'<p class="text-xs text-gray-600 mt-1">%s</p></div>' % (ic, num, lbl)
        for num, lbl, ic in STATS)

    caps_html = u''.join(card(*c) for c in CAPS)

    team_html = u''
    for i, (m, b) in enumerate(zip(MEMBERS, b64s)):
        team_html += (
            u'<div class="relative group">'
            u'<div class="relative border border-gray-200 overflow-hidden">'
            # 四角括号（沿用看板的工业构件语言）
            u'<span class="absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2 border-primary-500 z-10"></span>'
            u'<span class="absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2 border-primary-500 z-10"></span>'
            u'<span class="absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2 border-primary-500 z-10"></span>'
            u'<span class="absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2 border-primary-500 z-10"></span>'
            u'<img src="data:image/jpeg;base64,%s" alt="团队成员" loading="lazy" '
            u'class="w-full h-72 object-cover object-top grayscale-[35%%] group-hover:grayscale-0 transition-all duration-500">'
            u'<span class="absolute top-2 left-2 text-[10px] font-mono tracking-widest '
            u'bg-black/55 text-white px-2 py-0.5">MEMBER %02d</span>'
            u'</div>'
            u'<div class="pt-4">'
            u'<p class="font-bold text-lg">【姓名待填】</p>'
            u'<p class="text-sm text-primary-500 font-mono tracking-wide mt-1">%s</p>'
            u'<p class="text-sm text-gray-600 mt-3 leading-relaxed">%s</p>'
            u'</div></div>' % (b, i + 1, m['role'], m['desc']))

    base_html = u''.join(
        u'<div class="flex items-baseline border-b border-dashed border-gray-200 py-3">'
        u'<span class="text-sm text-gray-600 w-28 shrink-0">%s</span>'
        u'<span class="text-sm font-medium">%s</span></div>' % (k, v) for k, v in BASE)

    return u'''    <!-- 关于我们 -->
    <section id="about" class="py-16 bg-white">
        <div class="container mx-auto px-4">

            <!-- 标题 -->
            <div class="text-center mb-14">
                <p class="font-mono text-xs tracking-[0.3em] text-primary-500 mb-3">ABOUT US / TEAM</p>
                <h2 class="text-3xl md:text-4xl font-bold mb-4">关于车小智</h2>
                <p class="text-lg text-gray-600 max-w-3xl mx-auto leading-relaxed">
                    一支把<strong class="text-primary-500">真实车机数据</strong>做进诊断系统的三人团队
                </p>
            </div>

            <!-- 使命 -->
            <div class="grid md:grid-cols-2 gap-10 items-start mb-16">
                <div>
                    <h3 class="text-2xl font-bold mb-6">我们的使命</h3>
                    <p class="text-gray-600 mb-5 leading-relaxed">
                        车小智希望用人工智能重构新能源智能网联车的诊断方式——让故障判断不再依赖老师傅的经验和一块万用表，
                        而是让<strong>总线上真实流动的数据</strong>自己说话。
                    </p>
                    <p class="text-gray-600 mb-5 leading-relaxed">
                        系统自立项起就<strong class="text-primary-500">直接接入国汽智联「智能网联汽车技术平台」</strong>：
                        真车、真总线、真传感器。我们不满足于演示级数据——每一个诊断结论，都要求能追溯到一条实实在在的 CAN 报文或一个 ROS 话题。
                    </p>
                    <p class="text-gray-600 leading-relaxed">
                        我们也相信，好的诊断系统必须<strong>敢接真车</strong>：能读总线、能看感知、能报故障、也能告诉维修人员下一步该做什么。
                    </p>
                </div>
                <div>
                    <h3 class="text-2xl font-bold mb-6">技术底座</h3>
                    <div class="mb-6">''' + base_html + u'''</div>
                    <div class="bg-gray-100 p-5 border-l-2 border-primary-500">
                        <p class="text-sm text-gray-600 leading-relaxed">
                            <i class="fas fa-quote-left text-primary-500 mr-2"></i>
                            系统的 CAN / ROS 双通道桥接层为完全自研：一头接整车 CAN 总线，一头接车机 ROS 域控，
                            把总线报文、感知话题与故障码统一成一套可解释的诊断语言。
                        </p>
                    </div>
                </div>
            </div>

            <!-- 核心数据 -->
            <div class="mb-16">
                <div class="flex items-center mb-6">
                    <span class="font-mono text-xs tracking-[0.25em] text-gray-600">SYSTEM SCALE</span>
                    <span class="flex-1 border-t border-gray-200 ml-4"></span>
                </div>
                <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-px bg-gray-200">''' + stats_html + u'''</div>
                <p class="text-xs text-gray-600 mt-3 font-mono">* 以上均为本项目实测值，非设计指标</p>
            </div>

            <!-- 能力矩阵 -->
            <div class="mb-16">
                <div class="flex items-center mb-6">
                    <span class="font-mono text-xs tracking-[0.25em] text-gray-600">CORE CAPABILITY</span>
                    <span class="flex-1 border-t border-gray-200 ml-4"></span>
                </div>
                <h3 class="text-2xl font-bold mb-6">六大核心能力</h3>
                <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-5">''' + caps_html + u'''</div>
            </div>

            <!-- 团队 -->
            <div>
                <div class="flex items-center mb-6">
                    <span class="font-mono text-xs tracking-[0.25em] text-gray-600">TEAM / 03 MEMBERS</span>
                    <span class="flex-1 border-t border-gray-200 ml-4"></span>
                </div>
                <h3 class="text-2xl font-bold mb-2">核心团队</h3>
                <p class="text-gray-600 mb-8 max-w-3xl">
                    三人分工覆盖<strong>汽车电子、嵌入式系统、人工智能</strong>三个方向，从总线物理层一路做到诊断推理层。
                </p>
                <div class="grid md:grid-cols-3 gap-8">''' + team_html + u'''</div>

                <div class="mt-12 pt-8 border-t border-gray-200 grid md:grid-cols-3 gap-6">
                    <div>
                        <p class="font-mono text-xs tracking-widest text-primary-500 mb-2">01 / 真实数据</p>
                        <p class="text-sm text-gray-600 leading-relaxed">全系统数据来自真实车机总线与感知话题，拒绝模拟值。</p>
                    </div>
                    <div>
                        <p class="font-mono text-xs tracking-widest text-primary-500 mb-2">02 / 可追溯</p>
                        <p class="text-sm text-gray-600 leading-relaxed">每个诊断结论都能回溯到具体的报文 ID、话题名或故障码。</p>
                    </div>
                    <div>
                        <p class="font-mono text-xs tracking-widest text-primary-500 mb-2">03 / 可落地</p>
                        <p class="text-sm text-gray-600 leading-relaxed">面向真实维修工位设计，输出的是可执行的排查与维修步骤。</p>
                    </div>
                </div>
            </div>

        </div>
    </section>
'''


def main():
    print(u'=== 1. 处理照片 ===')
    new_sec = build()

    t = io.open(PAGE, encoding='utf-8').read()
    n0 = len(t)
    shutil.copy2(PAGE, PAGE + '.bak-about-' + time.strftime('%Y%m%d-%H%M%S'))

    # 定位旧 section（从 <!-- 关于我们 --> 到 BD-CAN 模态框之前的 </section>）
    m = re.search(r'[ \t]*<!-- 关于我们 -->\s*<section id="about".*?</section>\s*(?=<!-- BD-CAN)',
                  t, re.S)
    if not m:
        print(u'[x] 没定位到「关于我们」段落，未修改')
        return 1
    old_len = len(m.group())
    t = t[:m.start()] + new_sec + u'\n    ' + t[m.end():]
    print(u'=== 2. 替换段落 ===')
    print(u'   旧段落 %d 字符 -> 新段落 %d 字符' % (old_len, len(new_sec)))

    for k in (u'id="about"', u'</html>', u'id="bd-can-modal"', u'MEMBER 01', u'img src="data:image/jpeg;base64,'):
        if k not in t:
            print(u'[x] 终检失败：缺 %s —— 不写盘' % k)
            return 1
    io.open(PAGE, 'w', encoding='utf-8').write(t)
    print(u'   页面 %d -> %d 字符（+%d KB）' % (n0, len(t), (len(t) - n0) // 1024))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

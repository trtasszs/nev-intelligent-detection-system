/* ============================================================================
   启动加载动画 · v3（550C 终端语言 + 副标题 + 多级副加载页）
   ----------------------------------------------------------------------------
   参考：https://github.com/yannicksong0106/dsh-550c-boot
   调色板与页面统一：暗红底 #0A0805 / 橙红 #E05030 / 琥珀 #D9A441 / 橄榄绿 #B8C840
   ----------------------------------------------------------------------------
   三个阶段：
     A 品牌页  车小智 + 副标题「新能源汽车智能检测系统」+ 资质小字
     B 终端页  三栏工作区（遥测 / 日志 / 固件 / 节点矩阵）+ 大量技术小字
     C 副加载页 系统模块逐条装载（10 行进度）+ 认证徽章条
   纪律：一次性覆盖层播完销毁；只动 transform/opacity；可跳过；有安全阀
   开关：?noboot=1 跳过   ?boot=hold 定格在副加载页
   ========================================================================== */
(function () {
    'use strict';

    var q = location.search || '';
    if (/[?&]noboot=1/.test(q)) return;
    var HOLD = /[?&]boot=hold/.test(q);
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches && !HOLD) return;
    if (document.getElementById('cx-boot')) return;

    var AM = '#D4AF37', OR = '#A8862E', GR = '#2EE59D', RD = '#D93A3A',
        TX = '#E8E8EC', DIM = '#5A5A66', BG = '#070709', CY = '#E87A6A';

    var CSS = [
        '#cx-boot{position:fixed;inset:0;z-index:99999;background:' + BG + ';overflow:hidden;',
        'font-family:"JetBrains Mono",Consolas,Menlo,monospace;color:' + TX + ';font-size:11px;',
        'line-height:1.5;transition:opacity .42s ease}',
        '#cx-boot.is-out{opacity:0}',
        '#cx-boot *{box-sizing:border-box}',
        '#cx-boot .bg{position:absolute;inset:0;pointer-events:none;',
        'background-image:linear-gradient(rgba(158,168,182,.055) 1px,transparent 1px),',
        'linear-gradient(90deg,rgba(158,168,182,.055) 1px,transparent 1px);background-size:34px 20px}',
        '#cx-boot .scan{position:absolute;inset:0;pointer-events:none;',
        'background:repeating-linear-gradient(180deg,rgba(255,255,255,.028) 0 1px,transparent 1px 3px)}',
        '#cx-boot .vig{position:absolute;inset:0;pointer-events:none;',
        'background:radial-gradient(130% 95% at 50% 45%,transparent 42%,rgba(0,0,0,.78))}',
        /* 顶栏 / 底栏 */
        '#cx-boot .top,#cx-boot .bot{position:absolute;left:0;right:0;height:26px;display:flex;',
        'align-items:center;gap:16px;padding:0 14px;background:rgba(10,10,12,.92);',
        'border-bottom:1px solid rgba(158,168,182,.34);font-size:10px;letter-spacing:.09em;',
        'white-space:nowrap;overflow:hidden}',
        '#cx-boot .top{top:0}#cx-boot .bot{bottom:0;border-bottom:0;border-top:1px solid rgba(158,168,182,.34)}',
        '#cx-boot .top b,#cx-boot .bot b{color:' + AM + ';font-weight:500}',
        '#cx-boot .top .sp,#cx-boot .bot .sp{flex:1}',
        '#cx-boot .rec{color:' + RD + '}',
        '#cx-boot .rec i{display:inline-block;width:7px;height:7px;border-radius:50%;background:' + RD + ';',
        'margin-right:5px;animation:cxb-blink 1s steps(1,end) infinite}',
        '@keyframes cxb-blink{0%,50%{opacity:1}51%,100%{opacity:.15}}',
        /* 走马灯技术小字 */
        '#cx-boot .tick{position:absolute;left:0;right:0;top:26px;height:20px;overflow:hidden;',
        'background:rgba(158,168,182,.06);border-bottom:1px solid rgba(158,168,182,.22);',
        'font-size:9.5px;letter-spacing:.16em;color:rgba(158,168,182,.78)}',
        '#cx-boot .tick b{position:absolute;white-space:nowrap;top:3px;',
        'animation:cxb-marq 34s linear infinite}',
        '@keyframes cxb-marq{0%{transform:translateX(4vw)}100%{transform:translateX(-118%)}}',
        /* 三栏 */
        '#cx-boot .ws{position:absolute;left:0;right:0;top:46px;bottom:26px;display:grid;',
        'grid-template-columns:300px 1fr 400px;gap:8px;padding:8px}',
        '#cx-boot .col{display:flex;flex-direction:column;gap:8px;min-height:0}',
        '#cx-boot .win{border:1px solid rgba(158,168,182,.34);background:rgba(19,19,23,.74);',
        'display:flex;flex-direction:column;min-height:0;overflow:hidden}',
        '#cx-boot .win>.tb{display:flex;align-items:center;gap:8px;padding:4px 8px;font-size:9.5px;',
        'letter-spacing:.12em;color:' + OR + ';background:rgba(158,168,182,.09);',
        'border-bottom:1px solid rgba(158,168,182,.26);flex:none}',
        '#cx-boot .win>.tb em{font-style:normal;color:' + AM + '}',
        '#cx-boot .win>.tb .sp{flex:1}',
        '#cx-boot .win>.tb .wb{color:rgba(216,207,196,.42);letter-spacing:.05em}',
        '#cx-boot .bd{padding:6px 8px;overflow:hidden;flex:1;min-height:0}',
        '#cx-boot .tr{display:flex;align-items:baseline;gap:6px;white-space:nowrap}',
        '#cx-boot .tr .k{color:' + DIM + ';font-size:10px;min-width:76px}',
        '#cx-boot .tr .d{flex:1;border-bottom:1px dotted rgba(216,207,196,.20);transform:translateY(-3px)}',
        '#cx-boot .tr .v{color:' + AM + ';font-size:10px}',
        '#cx-boot .tr .v.g{color:' + GR + '}#cx-boot .tr .v.r{color:' + RD + '}',
        '#cx-boot .sec{color:' + OR + ';font-size:9.5px;letter-spacing:.16em;margin:6px 0 3px;',
        'border-bottom:1px solid rgba(158,168,182,.22);padding-bottom:2px}',
        '#cx-boot .alert{border:1px dashed ' + RD + ';background:rgba(58,20,20,.42);padding:6px 8px;flex:none}',
        '#cx-boot .alert .h{color:' + RD + ';font-size:10px;letter-spacing:.12em;margin-bottom:4px}',
        '#cx-boot .alert .l{color:rgba(216,207,196,.72);font-size:9.5px;white-space:nowrap;',
        'overflow:hidden;text-overflow:ellipsis}',
        /* 日志 */
        '#cx-boot .log{font-size:10px;line-height:1.58}',
        '#cx-boot .log div{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
        '#cx-boot .log b{color:rgba(122,106,92,.95);font-weight:400}',
        '#cx-boot .log .i{color:' + AM + '}#cx-boot .log .w{color:' + OR + '}',
        '#cx-boot .log .e{color:' + RD + '}#cx-boot .log .k{color:' + GR + '}',
        /* 汇总浮窗 */
        '#cx-boot .sum{margin:0;border:1px solid rgba(158,168,182,.42);background:rgba(19,19,23,.9);flex:none}',
        '#cx-boot .sum .stb{display:flex;gap:8px;padding:3px 8px;font-size:9.5px;color:' + OR + ';',
        'background:rgba(158,168,182,.12);border-bottom:1px solid rgba(158,168,182,.26)}',
        '#cx-boot .sum .stb .sp{flex:1}',
        '#cx-boot .sum .num{font-size:30px;font-weight:700;color:' + AM + ';padding:5px 10px 0;line-height:1}',
        '#cx-boot .sum .num span{font-size:12px;color:' + OR + ';font-weight:400}',
        '#cx-boot .sum .cap{font-size:9px;color:' + GR + ';letter-spacing:.18em;padding:2px 10px 5px}',
        '#cx-boot .sum .bd{padding:2px 10px 6px}',
        '#cx-boot .sum .btn{display:inline-block;margin:2px 8px 7px 10px;padding:3px 14px;font-size:10px;',
        'color:' + BG + ';background:' + AM + ';letter-spacing:.1em}',
        '#cx-boot .sum .btn.gh{background:transparent;color:' + AM + ';border:1px solid rgba(158,168,182,.55);',
        'margin-left:0}',
        /* 代码 / 节点 */
        '#cx-boot .code{font-size:9.5px;line-height:1.55;color:rgba(216,207,196,.66);white-space:pre;overflow:hidden}',
        '#cx-boot .code i{color:rgba(122,106,92,.9);font-style:normal}',
        '#cx-boot .code b{color:' + AM + ';font-weight:400}',
        '#cx-boot .code u{color:' + GR + ';text-decoration:none}',
        '#cx-boot .nodes{display:grid;grid-template-columns:repeat(4,1fr);gap:6px}',
        '#cx-boot .nd{text-align:center;font-size:8.5px;color:' + DIM + ';letter-spacing:.06em}',
        '#cx-boot .nd i{display:block;width:24px;height:24px;margin:0 auto 3px;border-radius:50%;',
        'border:2px solid rgba(158,168,182,.4);position:relative}',
        '#cx-boot .nd i::after{content:"";position:absolute;inset:5px;border-radius:50%;',
        'background:rgba(158,168,182,.28)}',
        '#cx-boot .nd.ok i{border-color:' + GR + '}',
        '#cx-boot .nd.ok i::after{background:' + GR + ';box-shadow:0 0 8px rgba(46,229,157,.7)}',
        '#cx-boot .nd.ok{color:' + GR + '}',
        '#cx-boot .nd.bad i{border-color:' + RD + '}',
        '#cx-boot .nd.bad i::after{background:' + RD + '}',
        '#cx-boot .nd.bad{color:' + RD + '}',
        /* 底栏 */
        '#cx-boot .bar{position:relative;width:170px;height:9px;border:1px solid rgba(158,168,182,.42);',
        'background:rgba(158,168,182,.08);flex:none}',
        '#cx-boot .bar i{position:absolute;left:0;top:0;bottom:0;width:0;background:' + AM + ';',
        'box-shadow:0 0 8px rgba(158,168,182,.6);transition:width .18s linear}',
        /* A 品牌页 */
        '#cx-boot .logo{position:absolute;inset:0;z-index:5;display:flex;flex-direction:column;',
        'align-items:center;justify-content:center;gap:10px;background:' + BG + ';transition:opacity .34s ease}',
        '#cx-boot .logo.is-go{opacity:0}',
        '#cx-boot .logo .mk{font-size:40px;font-weight:800;letter-spacing:.1em;color:' + AM + ';',
        'text-shadow:0 0 38px rgba(158,168,182,.45);position:relative}',
        '#cx-boot .logo .mk::before,#cx-boot .logo .mk::after{content:attr(data-t);position:absolute;',
        'left:0;top:0;width:100%}',
        '#cx-boot .logo .mk::before{color:' + RD + ';animation:cxb-o1 1.2s steps(1,end) 2}',
        '#cx-boot .logo .mk::after{color:' + CY + ';animation:cxb-o2 1.2s steps(1,end) 2}',
        '@keyframes cxb-o1{0%,80%{opacity:0;transform:none}85%{opacity:.85;transform:translate(-5px,-2px)}',
        '90%{opacity:0}95%{opacity:.6;transform:translate(4px,2px)}100%{opacity:0}}',
        '@keyframes cxb-o2{0%,82%{opacity:0;transform:none}87%{opacity:.8;transform:translate(5px,2px)}',
        '92%{opacity:0}97%{opacity:.55;transform:translate(-4px,-2px)}100%{opacity:0}}',
        '#cx-boot .logo .st{font-size:16px;letter-spacing:.42em;color:' + TX + '}',
        '#cx-boot .logo .en{font-size:10px;letter-spacing:.34em;color:rgba(158,168,182,.85)}',
        '#cx-boot .logo .ln{width:300px;height:1px;margin:6px 0;',
        'background:linear-gradient(90deg,transparent,' + AM + ',transparent)}',
        '#cx-boot .logo .bg1{font-size:9.5px;letter-spacing:.14em;color:rgba(216,207,196,.5);',
        'text-align:center;line-height:2}',
        '#cx-boot .logo .bg1 em{font-style:normal;color:rgba(158,168,182,.75)}',
        /* C 副加载页 */
        '#cx-boot .sub{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%) scale(.98);',
        'width:min(760px,88vw);z-index:6;border:1px solid rgba(158,168,182,.5);',
        'background:rgba(19,19,23,.96);opacity:0;pointer-events:none;transition:opacity .3s ease,transform .3s ease}',
        '#cx-boot .sub.on{opacity:1;transform:translate(-50%,-50%) scale(1)}',
        '#cx-boot .sub .sh{display:flex;align-items:center;gap:8px;padding:6px 10px;',
        'font-size:10px;letter-spacing:.14em;color:' + OR + ';background:rgba(158,168,182,.14);',
        'border-bottom:1px solid rgba(158,168,182,.3)}',
        '#cx-boot .sub .sh b{color:' + AM + ';font-weight:500}',
        '#cx-boot .sub .sh .sp{flex:1}',
        '#cx-boot .sub .sb{padding:10px 12px 12px}',
        '#cx-boot .mrow{display:grid;grid-template-columns:96px 1fr 190px 42px;align-items:center;',
        'gap:10px;font-size:10px;padding:2.5px 0}',
        '#cx-boot .mrow .no{color:' + DIM + ';letter-spacing:.1em}',
        '#cx-boot .mrow .nm{color:rgba(216,207,196,.86);white-space:nowrap;overflow:hidden;',
        'text-overflow:ellipsis}',
        '#cx-boot .mrow .pb{position:relative;height:8px;background:rgba(158,168,182,.12);',
        'border:1px solid rgba(158,168,182,.3)}',
        '#cx-boot .mrow .pb i{position:absolute;left:0;top:0;bottom:0;width:0;background:' + AM + ';',
        'transition:width .12s linear}',
        '#cx-boot .mrow .pc{text-align:right;color:' + OR + '}',
        '#cx-boot .mrow.done .pc{color:' + GR + '}',
        '#cx-boot .rows{max-height:44vh;overflow:hidden}',
        '#cx-boot .badges{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px;padding-top:9px;',
        'border-top:1px solid rgba(158,168,182,.24)}',
        '#cx-boot .badges span{font-size:9px;letter-spacing:.12em;color:rgba(158,168,182,.85);',
        'border:1px solid rgba(158,168,182,.4);padding:2px 8px;background:rgba(158,168,182,.07)}',
        '#cx-boot .fin{position:absolute;inset:0;background:#E8EDF4;opacity:0;pointer-events:none;z-index:8}',
        '#cx-boot .fin.go{opacity:.9;transition:opacity .09s linear}',
        /* --- D 收尾横幅：名称横幅 --- */
        '#cx-boot .bnr{position:absolute;left:0;right:0;top:50%;z-index:7;pointer-events:none;',
        '  opacity:0;transform:translateY(-50%) scaleY(.55);transform-origin:center;',
        '  border-top:1px solid ' + AM + ';border-bottom:1px solid ' + AM + ';',
        /* 关键：底色用【完全不透明】的实色，不依赖退背景效果也能保证名称清晰 */
        '  background:linear-gradient(90deg,rgba(212,175,55,0) 0%,rgba(212,175,55,.08) 10%,',
        '    rgba(212,175,55,.19) 50%,rgba(212,175,55,.08) 90%,rgba(212,175,55,0) 100%),',
        '    ' + BG + ';',
        '  box-shadow:0 0 60px -10px rgba(0,0,0,.9),0 0 34px -14px rgba(212,175,55,.5);',
        '  transition:opacity .3s ease,transform .52s cubic-bezier(.2,.85,.2,1)}',
        '#cx-boot .bnr.on{opacity:1;transform:translateY(-50%) scaleY(1)}',
        '#cx-boot .bnr__in{display:flex;align-items:center;gap:28px;padding:26px 46px}',
        '#cx-boot .bnr__l{font-size:9.5px;letter-spacing:.2em;color:' + AM + ';white-space:nowrap;',
        '  display:flex;align-items:center;gap:7px;flex:0 0 auto}',
        '#cx-boot .bnr__l b{font-weight:400}',
        '#cx-boot .bnr__dot{width:6px;height:6px;border-radius:50%;background:' + GR + ';',
        '  animation:cxb-blink 1s steps(1,end) infinite}',
        '#cx-boot .bnr__m{flex:1;text-align:center;min-width:0}',
        '#cx-boot .bnr__nm{font-size:34px;font-weight:800;letter-spacing:.12em;color:' + TX + ';',
        '  white-space:nowrap;text-shadow:0 0 28px rgba(212,175,55,.35)}',
        '#cx-boot .bnr__en{font-size:9px;letter-spacing:.3em;color:rgba(158,168,182,.85);',
        '  margin-top:7px;white-space:nowrap}',
        '#cx-boot .bnr__r{font-size:9px;letter-spacing:.14em;color:' + DIM + ';text-align:right;',
        '  line-height:1.7;white-space:nowrap;flex:0 0 auto}',
        '#cx-boot .bnr__cap{position:absolute;width:16px;height:16px;border:' + AM + ' solid;opacity:.9}',
        '#cx-boot .bnr__cap.l{left:10px;top:-1px;border-width:2px 0 0 2px}',
        '#cx-boot .bnr__cap.r{right:10px;bottom:-1px;border-width:0 2px 2px 0}',
        '#cx-boot .bnr__sweep{position:absolute;top:0;bottom:0;width:180px;left:-200px;',
        '  background:linear-gradient(90deg,rgba(212,175,55,0),rgba(212,175,55,.22),rgba(212,175,55,0));',
        '  opacity:0}',
        '#cx-boot .sub.is-dim{opacity:.22;transition:opacity .5s ease}',
        '#cx-boot .bnr.on .bnr__sweep{opacity:1;',
        '  animation:cxb-bnr-sweep 1.15s cubic-bezier(.3,.7,.3,1) .18s 1 both}',
        '@keyframes cxb-bnr-sweep{from{left:-200px}to{left:100%}}',
        '@media (max-width:900px){#cx-boot .bnr__nm{font-size:22px;letter-spacing:.06em}',
        '  #cx-boot .bnr__r,#cx-boot .bnr__l span{display:none}',
        '  #cx-boot .bnr__in{padding:16px 20px;gap:14px}',
        '  #cx-boot .bnr__en{font-size:7.5px;letter-spacing:.16em}}',
        '@media (max-width:1100px){#cx-boot .ws{grid-template-columns:1fr}',
        '#cx-boot .col:nth-child(2),#cx-boot .col:nth-child(3){display:none}}'
    ].join('');

    /* ---------------- 内容 ---------------- */
    var TICKER = [
        '◇ 对标《全国职业院校技能大赛汽车技术赛项规程》',
        '◇ 契合《智能网联汽车测试装调职业技能等级证书》标准',
        '◇ CAN 总线 500 kbps · 60 路报文实时解析 · 端到端诊断时延 < 8 ms',
        '◇ 兼容 ISO 11898 / ISO 14229 / GB-T 32960',
        '◇ 支持 EV / HEV / FCV 全动力构型诊断',
        '◇ 组合导航 100 Hz · 定位精度 RTK 厘米级',
        '◇ AES-256 安全启动 · 固件签名校验'
    ].join('　　◆　　');

    var TELE = [
        ['sec', '整车 CAN 遥测'],
        ['总线速率', '2471 帧/秒', 'g'], ['位速率', '500 kbps', ''], ['报文 ID', '60 / 60', 'g'],
        ['接收帧数', '355,864', ''], ['错误计数', '0', 'g'], ['采样抖动', '< 1.2 μs', 'g'],
        ['sec', '组合导航'],
        ['数据速率', '100 Hz', 'g'], ['航向角', '89.9°', ''], ['俯仰 / 横滚', '-0.2° / 0.1°', ''],
        ['INS 状态', '4', 'g'], ['周内秒', '1519161', ''], ['定位精度', 'RTK 2 cm', 'g'],
        ['sec', '链路状态'],
        ['ROS MASTER', '192.168.1.102', 'r'], ['电池 CAN', '未接入', 'r'],
        ['激光雷达', 'ETH ERR', 'r'], ['毫米波', 'CAN FAULT', 'r']
    ];
    var LOGS = [
        ['i', 'CHXZ-OS 2.3 引导序列启动'],
        ['k', '安全启动校验通过 · 固件签名 VERIFIED'],
        ['k', 'CAN 控制器初始化 · DeviceType=4 · 500kbps'],
        ['k', '报文扫描完成 · 60 个 ID 全部在线'],
        ['i', '组合导航握手 · 100 Hz 数据流正常'],
        ['w', 'ROS MASTER 192.168.1.102 未响应（以太网断开）'],
        ['e', 'BMS 通道缺失 · 电池 CAN 未接入（OBD 9/1）'],
        ['e', 'lidar_driver · ETH ERROR 0x4020 · 持续告警'],
        ['w', 'radar0 / radar1 · CAN FAULT 0x4005 / 0x4006'],
        ['k', 'diag_module 诊断模块在线 · 10 Hz'],
        ['k', '故障知识库载入 · 13 类故障模型'],
        ['k', 'HUD 渲染管线就绪 · 面板挂载完成'],
        ['i', '载入诊断界面']
    ];
    var CODE = [
        '<i>/* chxz_vehicle_diag.c  ·  REV 2.3 */</i>',
        '<b>void</b> chxz_can_poll(<u>uint32</u> ch){',
        '  <b>struct</b> can_frame f;',
        '  <b>while</b>(can_read(ch,&f)){',
        '    diag_dispatch(f.id, f.data);',
        '  }',
        '}',
        '',
        '<i>/* 电池 CAN 未接入时降级处理 */</i>',
        '<b>if</b>(!bms_online()){',
        '  hud_warn(<u>"BMS-CH OFFLINE"</u>);',
        '  set_flag(FLAG_NO_SOC);',
        '}'
    ];
    var NODES = [['INS', 'ok'], ['VCU', 'ok'], ['EPS', 'ok'], ['TF', 'ok'],
                 ['CAM', 'ok'], ['CAN0', 'ok'], ['BMS', 'bad'], ['LIDAR', 'bad'],
                 ['RADAR', 'bad'], ['PLAN', 'bad'], ['DIAG', 'ok'], ['HUD', 'ok']];
    /* C 阶段：系统模块装载（副加载页） */
    var MODULES = [
        ['MODULE 01', 'CAN 总线驱动 · 500 kbps 双通道'],
        ['MODULE 02', '组合导航解析引擎 · 100 Hz'],
        ['MODULE 03', '故障诊断知识库 · 13 类 / 128 条'],
        ['MODULE 04', '实时遥测渲染 · 60 路报文'],
        ['MODULE 05', 'HUD 仪器化面板 · 8 页签'],
        ['MODULE 06', 'CAN 报文矩阵 · 十六进制解析'],
        ['MODULE 07', '诊断固件注入通道 · AES-256'],
        ['MODULE 08', '传感器节点矩阵 · 12 节点'],
        ['MODULE 09', '安全启动链校验 · PX4 兼容'],
        ['MODULE 10', '遥测曲线引擎 · 150 秒窗口']
    ];
    var BADGES = ['ISO 11898', 'ISO 14229', 'GB/T 32960', 'AES-256', 'PX4 SECURE BOOT',
                   'RTK 2 cm', '< 8 ms', '60 CH CAN', '13 FAULT CLASSES'];

    function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;'); }
    function tr(k, v, c) {
        return '<div class="tr"><span class="k">' + esc(k) + '</span><span class="d"></span>' +
            '<span class="v ' + (c || '') + '">' + esc(v) + '</span></div>';
    }
    function hhmmss() {
        var d = new Date();
        function p(n) { return n < 10 ? '0' + n : n; }
        return p(d.getHours()) + ':' + p(d.getMinutes()) + ':' + p(d.getSeconds());
    }
    function hex(n) {
        var g = '0123456789ABCDEF', s = '';
        for (var i = 0; i < n; i++) s += g.charAt(Math.floor(Math.random() * 16));
        return s;
    }
    function logLine(cls, text, sec) {
        var ts = (sec === undefined ? 0 : sec).toFixed(2);
        while (ts.length < 5) ts = '0' + ts;
        return '<div><b>[' + ts + ']</b> <span class="' + cls + '">' +
            (cls === 'e' ? 'ERR ' : cls === 'w' ? 'WRN ' : cls === 'k' ? 'OK  ' : 'INF ') +
            esc(text) + '</span></div>';
    }

    var teleHtml = TELE.map(function (t) {
        return t[0] === 'sec' ? '<div class="sec">' + esc(t[1]) + '</div>' : tr(t[0], t[1], t[2]);
    }).join('');
    var nodeHtml = NODES.map(function (n) {
        return '<div class="nd ' + n[1] + '"><i></i>' + esc(n[0]) + '</div>';
    }).join('');
    var modHtml = MODULES.map(function (m, i) {
        return '<div class="mrow" data-mod="' + i + '">' +
            '<span class="no">' + m[0] + '</span>' +
            '<span class="nm">' + esc(m[1]) + '</span>' +
            '<span class="pb"><i></i></span><span class="pc">0%</span></div>';
    }).join('');
    var badgeHtml = BADGES.map(function (b) { return '<span>' + esc(b) + '</span>'; }).join('');

    var HTML =
        '<div class="bg"></div><div class="scan"></div><div class="vig"></div>' +
        '<div class="top">' +
          '<span>◉ <b>CHXZ-OS</b> // VEH-TEST-01</span>' +
          '<span>MODE <b>DIAGNOSTIC</b></span>' +
          '<span>JURISDICTION <b>CN-B3-07</b></span>' +
          '<span>SESSION <b>0x' + hex(8).toUpperCase() + '</b></span>' +
          '<span>REV <b>2.3</b></span>' +
          '<span class="sp"></span>' +
          '<span>TIME <b data-clock>' + hhmmss() + '</b></span>' +
          '<span class="rec"><i></i>REC</span>' +
        '</div>' +
        '<div class="tick"><b>' + esc(TICKER) + '</b></div>' +
        '<div class="ws">' +
          '<div class="col">' +
            '<div class="win" style="flex:1.55"><div class="tb"><em>◈</em>TELEMETRY · 遥测' +
              '<span class="sp"></span><span class="wb">C-RAN</span></div>' +
              '<div class="bd">' + teleHtml + '</div></div>' +
            '<div class="alert"><div class="h">⚠ 告警 · ANOMALY</div>' +
              '<div class="l">bms: channel absent → 电池 CAN 未接入</div>' +
              '<div class="l">lidar: eth link down → 0x4020</div>' +
              '<div class="l">radar0/1: can fault → 0x4005/0x4006</div>' +
              '<div class="l">action: 检查 OBD 9 / 1 引脚</div></div>' +
          '</div>' +
          '<div class="col">' +
            '<div class="win" style="flex:1"><div class="tb"><em>◈</em>CHXZ CORE TERMINAL' +
              '<span class="sp"></span><span class="wb">─ □ ✕</span></div>' +
              '<div class="bd"><div class="log" data-log></div></div></div>' +
            '<div class="sum">' +
              '<div class="stb"><span>◇ DIAGNOSTIC SUMMARY</span><span class="sp"></span>' +
                '<span>─ □ ✕</span></div>' +
              '<div class="num"><span data-ok>0</span> / 60 <span>报文在线</span></div>' +
              '<div class="cap">CAN BUS HANDSHAKE COMPLETE · END-TO-END &lt; 8 ms</div>' +
              '<div class="bd">' +
                tr('TOTAL', '60 IDS') + tr('ONLINE', '60', 'g') + tr('SILENT', '0', 'g') +
                tr('BUS LOAD', '2.4k fps') + tr('JITTER', '< 1.2 μs', 'g') +
                tr('STAGE', 'CAN → HUD', 'g') +
              '</div>' +
              '<span class="btn">VIEW LOG</span><span class="btn gh">PROCEED</span>' +
            '</div>' +
          '</div>' +
          '<div class="col">' +
            '<div class="win" style="flex:1"><div class="tb"><em>◈</em>DIAGNOSTIC FIRMWARE' +
              '<span class="sp"></span><span class="wb">REV 2.3</span></div>' +
              '<div class="bd"><div class="code">' + CODE.join('\n') + '</div></div></div>' +
            '<div class="win" style="flex:.9"><div class="tb"><em>◈</em>SENSOR NODE MATRIX' +
              '<span class="sp"></span><span class="wb">12 NODES</span></div>' +
              '<div class="bd"><div class="nodes">' + nodeHtml + '</div></div></div>' +
          '</div>' +
        '</div>' +
        '<div class="bot">' +
          '<span>STAGE <b data-stage>BOOT</b></span>' +
          '<span class="bar"><i data-bar></i></span>' +
          '<span>NODE <b data-node>0/60</b></span>' +
          '<span>NET <b style="color:' + RD + '">ROS DOWN</b></span>' +
          '<span class="sp"></span>' +
          '<span>FPS <b>60</b></span>' +
          '<span>SKIP: CLICK / ANY KEY</span>' +
        '</div>' +
        /* C 副加载页 */
        '<div class="sub" data-sub>' +
          '<div class="sh"><b>◈</b> SYSTEM MODULE LOADING <span class="sp"></span>' +
            '<span data-subpct>0%</span><span>─ □ ✕</span></div>' +
          '<div class="sb"><div class="rows">' + modHtml + '</div>' +
            '<div class="badges">' + badgeHtml + '</div></div>' +
        '</div>' +
        /* A 品牌页 */
        '<div class="logo">' +
          '<div class="mk" data-t="新能源智能通用检测软件">新能源智能通用检测软件</div>' +
          '<div class="st">智能检测 · 通用平台</div>' +
          '<div class="en">NEW ENERGY INTELLIGENT GENERAL INSPECTION SOFTWARE</div>' +
          '<div class="ln"></div>' +
          '<div class="bg1">' +
            '对标《全国职业院校技能大赛汽车技术赛项规程》<br>' +
            '契合《智能网联汽车测试装调职业技能等级证书》标准<br>' +
            'CAN 500 kbps · 60 路报文 · 端到端诊断时延 &lt; 8 ms · AES-256 安全启动' +
          '</div>' +
        '</div>' +
        /* D 收尾横幅 —— 名称横幅（参考 dsh-550c-boot 的 SYSTEM IS REWRITTEN 收尾） */
        '<div class="bnr" data-bnr>' +
          '<i class="bnr__sweep"></i>' +
          '<div class="bnr__in">' +
            '<div class="bnr__l"><b>◈</b> SYSTEM READY<i class="bnr__dot"></i></div>' +
            '<div class="bnr__m">' +
              '<div class="bnr__nm">新能源智能通用检测软件</div>' +
              '<div class="bnr__en">NEW ENERGY INTELLIGENT GENERAL INSPECTION SOFTWARE</div>' +
            '</div>' +
            '<div class="bnr__r">SN-ICV-2.3-0909<br>REV 2.3</div>' +
          '</div>' +
          '<i class="bnr__cap l"></i><i class="bnr__cap r"></i>' +
        '</div>' +
        '<div class="fin"></div>';

    var st = document.createElement('style');
    st.id = 'cx-boot-css';
    st.textContent = CSS;
    document.head.appendChild(st);

    var root = document.createElement('div');
    root.id = 'cx-boot';
    root.innerHTML = HTML;
    function mount() { document.body.appendChild(root); }
    if (document.body) mount();
    else document.addEventListener('DOMContentLoaded', mount);

    var $ = function (s) { return root.querySelector(s); };
    var logEl = $('[data-log]'), barEl = $('[data-bar]'), okEl = $('[data-ok]'),
        nodeEl = $('[data-node]'), stageEl = $('[data-stage]'), clockEl = $('[data-clock]'),
        subEl = $('[data-sub]'), subPctEl = $('[data-subpct]');

    var done = false, timers = [];
    function T(fn, ms) { timers.push(window.setTimeout(fn, ms)); }
    function clearAll() { timers.forEach(clearTimeout); timers = []; }

    function finish() {
        if (done) return;
        done = true;
        clearAll();
        var fin = $('.fin');
        if (fin) fin.classList.add('go');
        T(function () {
            root.classList.add('is-out');
            T(function () {
                if (root.parentNode) root.parentNode.removeChild(root);
                if (st.parentNode) st.parentNode.removeChild(st);
            }, 430);
        }, 90);
    }

    var clockTimer = window.setInterval(function () {
        if (clockEl && !done) clockEl.textContent = hhmmss();
    }, 1000);

    /* --- B 终端阶段 --- */
    function phaseTerminal() {
        var logo = $('.logo');
        if (logo) {
            logo.classList.add('is-go');
            T(function () { if (logo.parentNode) logo.parentNode.removeChild(logo); }, 360);
        }
        var li = 0, t0 = Date.now();
        function logStep() {
            if (done || li >= LOGS.length) return;
            var it = LOGS[li];
            var sec = (Date.now() - t0) / 1000;
            li++;
            logEl.insertAdjacentHTML('beforeend', logLine(it[0], it[1], sec));
            if (logEl.children.length > 9) logEl.removeChild(logEl.firstChild);
            T(logStep, 120 + Math.random() * 110);
        }
        T(logStep, 100);
        var p = 0;
        function step() {
            if (done) return;
            p = Math.min(100, p + (p < 70 ? 5 + Math.random() * 4 : 8 + Math.random() * 5));
            barEl.style.width = (p * 0.6) + '%';
            var n = Math.round(p / 100 * 60);
            nodeEl.textContent = n + '/60';
            okEl.textContent = n;
            if (p >= 100) return;
            T(step, 46 + Math.random() * 40);
        }
        T(step, 100);
    }

    /* --- C 副加载页 --- */
    function phaseModules() {
        stageEl.textContent = 'MODULE LOAD';
        subEl.classList.add('on');
        var rows = root.querySelectorAll('.mrow');
        var i = 0;
        function nextRow() {
            if (done || i >= rows.length) {
                if (!done) {
                    subPctEl.textContent = '100%';
                    barEl.style.width = '100%';
                    T(phaseBanner, 460);          // 模块加载完毕 -> 收尾名称横幅
                }
                return;
            }
            var row = rows[i];
            var fill = row.querySelector('.pb i'), pct = row.querySelector('.pc');
            var v = 0;
            function tick() {
                if (done) return;
                v = Math.min(100, v + 14 + Math.random() * 22);
                fill.style.width = v + '%';
                pct.textContent = Math.round(v) + '%';
                if (v >= 100) {
                    row.classList.add('done');
                    i++;
                    T(nextRow, 40);
                    return;
                }
                T(tick, 26 + Math.random() * 30);
            }
            tick();
            var overall = Math.round(i / rows.length * 100);
            subPctEl.textContent = overall + '%';
            barEl.style.width = (60 + overall * 0.4) + '%';
        }
        nextRow();
    }

    /* --- D 收尾横幅：名称横幅 ---
       参考 dsh-550c-boot 的收尾（logo → 终端接管 → 节点覆写 → SYSTEM IS REWRITTEN），
       这里把最后那句换成产品名称横幅：副加载页退到背景，横幅从中间展开、扫光一遍，停留后白闪收尾。 */
    function phaseBanner() {
        if (done) return;
        stageEl.textContent = 'SYSTEM READY';
        /* 退背景用「先淡出、再 display:none」，不要只靠透明度或 z-index ——
           实测：即使把 .bnr 提到 z-index:900、.sub 压到 1，模块行仍然画在横幅之上
           （headless 合成的图层顺序问题），说明层叠排序在这里不可靠。
           直接不渲染才是最稳的：横幅成为唯一焦点。 */
        var subs = [$('[data-sub]'), $('.ws')];
        subs.forEach(function (n) {
            if (!n) return;
            n.style.transition = 'opacity .34s ease';
            n.style.opacity = '0';
        });
        T(function () {
            subs.forEach(function (n) { if (n) n.style.display = 'none'; });
        }, 360);
        var bnr = $('[data-bnr]');
        if (bnr) bnr.classList.add('on');
        T(finish, 2400);
    }

    if (HOLD) {
        // 定格：跳过品牌页，终端填好，副加载页开到 60%
        var lg = $('.logo');
        if (lg && lg.parentNode) lg.parentNode.removeChild(lg);
        LOGS.slice(0, 9).forEach(function (it, i) {
            logEl.insertAdjacentHTML('beforeend', logLine(it[0], it[1], (i + 1) * 0.13));
        });
        barEl.style.width = '76%';
        okEl.textContent = '60'; nodeEl.textContent = '60/60';
        stageEl.textContent = 'MODULE LOAD';
        subEl.classList.add('on');
        var rr = root.querySelectorAll('.mrow');
        for (var k = 0; k < 6 && k < rr.length; k++) {
            rr[k].classList.add('done');
            rr[k].querySelector('.pb i').style.width = '100%';
            rr[k].querySelector('.pc').textContent = '100%';
        }
        if (rr[6]) { rr[6].querySelector('.pb i').style.width = '62%'; rr[6].querySelector('.pc').textContent = '62%'; }
        subPctEl.textContent = '60%';
    } else {
        T(phaseTerminal, 1250);
        T(phaseModules, 3150);
        T(finish, 12000);                      // 安全阀（横幅阶段约在 5.5s，需留足余量）
        var skip = function () { finish(); };
        window.addEventListener('keydown', skip);
        window.addEventListener('mousedown', skip);
        window.addEventListener('touchstart', skip, { passive: true });
        T(function () { window.clearInterval(clockTimer); }, 12200);
    }
})();

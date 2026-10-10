/* ============================================================================
   CX-FLOW · 数据管线粒子（被真实数据驱动，不是装饰背板）
   ----------------------------------------------------------------------------
   设计要点（对应「要数据加载的感觉，不要事先背板」）：
     · 粒子的**发射速率由真实总线帧率决定** —— can_bridge 报多少帧/秒，就流多少粒子
     · 管线三段：CAN BUS → DECODE → HUD，粒子逐段推进，到达 HUD 时闪一下计数
     · **桥接断开时粒子立刻停**，界面显示「等待数据」—— 动效本身携带状态
     · 帧率异常（< 300 帧/秒）时粒子转为琥珀色，堵住/掉线转红
     · 不用背景贴图、不做全屏色带；粒子只在本面板的 canvas 内
   性能：粒子数硬上限 260，devicePixelRatio 上限 2，单 rAF 循环，
        reduced-motion 时只画静态管线。
   ========================================================================== */
(function () {
    'use strict';

    if (document.getElementById('cx-flow-card')) return;
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    var PORT = 8780;
    /* BASE_FIXED: CAN 桥接固定 8780 端口。不能用 location.origin ——
       页面可能由任意服务提供（桌面版 exe 的静态服务、CAN 桥接、file://），
       一旦原样用 origin，请求会打到那个端口、全部 404。 */
    var BASE = 'http://127.0.0.1:8780';
    void (location.protocol);

    // 日/夜模式取色（canvas 的颜色 CSS 管不到，只能在这里按模式取）
    function C() {
        var day = document.documentElement.dataset.cxMode === 'day';
        return day
            ? { BLUE: '#1E6FD9', GREEN: '#0E9F6E', AMBER: '#B8600F', RED: '#C93A2E',
                LINE: 'rgba(15,23,42,.18)', TXT: 'rgba(85,96,111,.9)', NODE: 'rgba(15,23,42,.35)' }
            : { BLUE: '#3D9BFF', GREEN: '#2EE59D', AMBER: '#D4762A', RED: '#E0574A',
                LINE: 'rgba(158,168,182,.16)', TXT: 'rgba(158,168,182,.75)', NODE: 'rgba(158,168,182,.5)' };
    }
    var BLUE = '#3D9BFF', GREEN = '#2EE59D', AMBER = '#D4762A', RED = '#E0574A';
    var MAXP = 260;

    function el(t, c, h) {
        var d = document.createElement(t);
        if (c) d.className = c;
        if (h !== undefined) d.innerHTML = h;
        return d;
    }

    /* ---------- 卡片 ---------- */
    var card = el('div', 'card cx-live mb-6');
    card.id = 'cx-flow-card';
    card.innerHTML =
        '<div class="cx-live__head">' +
          '<div class="cx-live__title"><span class="cx-live__dot"></span>数据管线 · 实时吞吐' +
            '<span class="cx-live__state" data-s>连接中…</span>' +
            '<span class="cx-livebadge"><i></i>CAN LIVE</span></div>' +
          '<div class="cx-live__meta">CAN BUS <b data-bus>--</b> · 帧/秒 → DECODE → HUD</div>' +
        '</div>' +
        '<div style="position:relative;height:132px;border:1px solid var(--cx-hair);' +
          'background:rgba(7,7,9,.55)">' +
          '<canvas data-cv style="display:block;width:100%;height:100%"></canvas>' +
          '<div data-stages style="position:absolute;inset:auto 0 0 0;display:flex;' +
            'justify-content:space-between;padding:4px 10px;font-family:var(--cx-mono);' +
            'font-size:9.5px;letter-spacing:.18em;color:var(--cx-tx-l)">' +
            '<span>CAN BUS · 500 kbps</span><span>DECODE · 报文解析</span><span>HUD · 面板渲染</span>' +
          '</div>' +
        '</div>';

    /* ---------- 注入：放在实时面板之后，避免抢首屏 ---------- */
    function mount() {
        var p = document.getElementById('dashboard');
        if (!p) { p = document.querySelector('.page-content'); }
        if (!p) return false;
        var live = p.querySelector('.cx-live');
        if (live && live.nextSibling) p.insertBefore(card, live.nextSibling);
        else if (live) p.appendChild(card);
        else p.insertBefore(card, p.firstChild);
        return true;
    }
    if (!mount()) document.addEventListener('DOMContentLoaded', mount);

    var cv = card.querySelector('[data-cv]');
    var ctx = cv.getContext('2d');
    var stateEl = card.querySelector('[data-s]');
    var busEl = card.querySelector('[data-bus]');

    var W = 0, H = 0, DPR = 1;
    function resize() {
        DPR = Math.min(2, window.devicePixelRatio || 1);
        W = cv.clientWidth || 600;
        H = cv.clientHeight || 132;
        cv.width = Math.round(W * DPR);
        cv.height = Math.round(H * DPR);
        ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    }
    resize();
    window.addEventListener('resize', resize);

    /* ---------- 三段节点（按宽度比例定位） ---------- */
    function nodes() {
        return [W * 0.13, W * 0.5, W * 0.87];
    }

    /* ---------- 数据状态 ---------- */
    var S = {
        fps: 0,            // 真实总线帧率
        total: 0,
        ok: false,
        arrived: 0,        // 累计到达 HUD 的粒子
        rate: 0,           // 本次统计窗口的到达数
        lastTotal: 0
    };

    function poll() {
        fetch(BASE + '/api/frames?t=' + Date.now(), { cache: 'no-store' })
            .then(function (r) { return r.json(); })
            .then(function (d) {
                if (!d || !d.ok) { S.ok = false; return; }
                S.ok = true;
                S.fps = d.hz_total || 0;
                S.total = d.total || 0;
                busEl.textContent = Math.round(S.fps);
                stateEl.textContent = S.fps > 300 ? '数据流正常' : '数据流偏低';
                card.classList.add('is-ok'); card.classList.remove('is-bad');
            })
            .catch(function () {
                S.ok = false;
                stateEl.textContent = '等待数据（CAN 采集未启动）';
                busEl.textContent = '0';
                card.classList.remove('is-ok'); card.classList.add('is-bad');
            })
            .then(function () { window.setTimeout(poll, 1000); });
    }
    poll();

    /* ---------- 粒子 ---------- */
    var P = [];
    function spawn(nx, ny, tx, ty, color) {
        if (P.length >= MAXP) return;
        P.push({ x: nx, y: ny, tx: tx, ty: ty, t: 0, sp: 0.9 + Math.random() * 0.5,
                 c: color, px: nx, py: ny, leg: 0 });
    }

    var last = performance.now(), acc = 0, flash = { a: 0, t: 0 };
    function frame(now) {
        var dt = Math.min(60, now - last) / 1000;
        last = now;
        if (W !== (cv.clientWidth || 600)) resize();

        var M = C();
        var N = nodes();
        var midY = H * 0.42;
        var jitter = function () { return (Math.random() - 0.5) * H * 0.34; };

        // 发射：速率完全由真实帧率决定（0 帧 = 0 粒子）
        var color = !S.ok ? M.RED : (S.fps > 300 ? M.BLUE : M.AMBER);
        var perSec = S.ok ? Math.min(150, S.fps / 22) : 0;
        acc += perSec * dt;
        while (acc >= 1) {
            acc -= 1;
            var y0 = midY + jitter();
            spawn(N[0], y0, N[1], midY + jitter(), color);
        }

        ctx.clearRect(0, 0, W, H);

        // 管线基线
        ctx.strokeStyle = M.LINE;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(N[0], midY); ctx.lineTo(N[2], midY);
        ctx.stroke();

        // 节点
        for (var i = 0; i < 3; i++) {
            var act = S.ok ? 1 : 0.25;
            ctx.beginPath();
            ctx.arc(N[i], midY, 4.5, 0, Math.PI * 2);
            ctx.fillStyle = S.ok ? (i === 2 ? M.GREEN : M.BLUE) : M.NODE;
            ctx.globalAlpha = act;
            ctx.fill();
            ctx.globalAlpha = 1;
            ctx.beginPath();
            ctx.arc(N[i], midY, 9, 0, Math.PI * 2);
            ctx.strokeStyle = (i === 2 ? 'rgba(14,159,110,.4)' : 'rgba(30,111,217,.35)');
            ctx.stroke();
        }

        // 粒子：逐段推进 CAN → DECODE → HUD
        var arrived = 0;
        for (var k = P.length - 1; k >= 0; k--) {
            var p = P[k];
            p.px = p.x; p.py = p.y;
            p.t += p.sp * dt;
            var e = p.t;
            if (e >= 1) {
                if (p.leg === 0) {                    // 第一段到达 → 转第二段
                    p.leg = 1; p.t = 0;
                    p.x = N[1]; p.y = p.ty;
                    p.tx = N[2]; p.ty = midY + jitter();
                } else {                              // 到达 HUD
                    arrived++;
                    P.splice(k, 1);
                    continue;
                }
            } else {
                p.x = p.px + (p.tx - p.px) * e;
                p.y = p.py + (p.ty - p.py) * e;
            }
            // 尾迹
            ctx.strokeStyle = p.c;
            ctx.globalAlpha = 0.55;
            ctx.lineWidth = 1.4;
            ctx.beginPath();
            ctx.moveTo(p.px, p.py); ctx.lineTo(p.x, p.y);
            ctx.stroke();
            // 头
            ctx.globalAlpha = 1;
            ctx.beginPath();
            ctx.arc(p.x, p.y, 1.5, 0, Math.PI * 2);
            ctx.fillStyle = p.c;
            ctx.fill();
        }
        ctx.globalAlpha = 1;

        if (arrived) {
            S.arrived += arrived;
            flash.a = 1; flash.t = now;
        }
        // HUD 节点到达闪光
        if (flash.a > 0) {
            var age = (now - flash.t) / 420;
            if (age >= 1) { flash.a = 0; }
            else {
                ctx.globalAlpha = (1 - age) * 0.7;
                ctx.beginPath();
                ctx.arc(N[2], midY, 4.5 + age * 22, 0, Math.PI * 2);
                ctx.strokeStyle = M.GREEN; ctx.lineWidth = 1.5; ctx.stroke();
                ctx.globalAlpha = 1;
            }
        }

        // 计数
        ctx.font = '10px "JetBrains Mono", Consolas, monospace';
        ctx.fillStyle = M.TXT;
        ctx.textAlign = 'right';
        ctx.fillText('已渲染 ' + S.arrived.toLocaleString() + ' 单位', W - 10, 14);
        ctx.textAlign = 'left';
        ctx.fillStyle = S.ok ? (S.fps > 300 ? M.BLUE : M.AMBER) : M.RED;
        ctx.fillText(S.ok ? (Math.round(S.fps) + ' 帧/秒 注入') : '无数据注入', 10, 14);

        requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
})();

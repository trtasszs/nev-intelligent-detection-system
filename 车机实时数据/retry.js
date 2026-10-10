/* ============================================================================
   CX-RETRY · 页内「重连诊断」按钮
   ----------------------------------------------------------------------------
   作用：不用刷新页面、不用等，点一下立刻探测两个数据源并给出结论。
      CAN 桥接  : 8780   ← 需要 USB CAN 分析仪（can_bridge.py）
      ROS 桥接  : 8770   ← 需要网线 / 车机 192.168.1.102（ros_bridge.py）
   说明：各面板本来就在 0.5~2 秒轮询一次，所以桥接一旦起来，**数据会自动恢复**；
        这个按钮解决的是「立刻知道通没通、没通是哪一环」——即调试可见性。
   ========================================================================== */
(function () {
    'use strict';
    if (document.getElementById('cx-retry-btn')) return;

    var SRC = [
        { key: 'can', name: 'CAN 桥接', port: 8780, base: 'http://127.0.0.1:8780',
          need: 'USB CAN 分析仪', start: 'python can_bridge.py --open' },
        { key: 'ros', name: 'ROS 桥接', port: 8770, base: 'http://127.0.0.1:8770',
          need: '网线 / 车机 192.168.1.102', start: 'python ros_bridge.py --port 8770' }
    ];

    function el(t, c, h) {
        var d = document.createElement(t);
        if (c) d.className = c;
        if (h !== undefined) d.innerHTML = h;
        return d;
    }

    /* ---------------- 探测单个源 ---------------- */
    function probe(s) {
        var t0 = performance.now();
        var ctl = ('AbortController' in window) ? new AbortController() : null;
        var timer = window.setTimeout(function () { if (ctl) ctl.abort(); }, 3500);
        return fetch(s.base + '/api/meta?t=' + Date.now(),
                     { cache: 'no-store', signal: ctl ? ctl.signal : undefined })
            .then(function (r) { return r.json(); })
            .then(function (d) {
                window.clearTimeout(timer);
                if (!d || d.ok === false) throw new Error('接口返回 ok=false');
                /* ★关键：桥接进程活着 ≠ 车机在线。
                   ros_bridge.py 在车机网线拔掉时照样返回 ok:true（那只是 HTTP 服务在），
                   返回的数值全是几十分钟前的陈旧缓存。两种离线都要认出来：
                     · linked=false —— 桥接起来了但根本没连上 ROS master（车机没接）
                     · w>0 且 o=0  —— 连上过，但现在所有话题全静默（中途拔线）
                   （只看 w>0&&o==0 会漏掉第一种：车机没接时 w 本身就是 0。） */
                var w = d.topics_watched || 0, o = d.topics_online || 0;
                var offMaster = (d.linked === false);
                if (offMaster || (w > 0 && o === 0)) {
                    return { ok: false, soft: true, ms: Math.round(performance.now() - t0),
                             err: offMaster ? '车机未连接（未连上 ROS master）'
                                            : '车机未连接（话题 0/' + w + ' 全静默）',
                             data: d };
                }
                return { ok: true, ms: Math.round(performance.now() - t0), data: d };
            })
            .catch(function (e) {
                window.clearTimeout(timer);
                return { ok: false, soft: false, ms: Math.round(performance.now() - t0),
                         err: (e && e.name) || 'Error' };
            });
    }

    /* ---------------- 结果面板 ---------------- */
    var panel = null;
    function ensurePanel() {
        if (panel) return panel;
        panel = el('div', 'cx-retry-panel');
        panel.id = 'cx-retry-panel';
        panel.innerHTML =
            '<div class="cx-retry-panel__hd">' +
              '<span>◈ 数据链路诊断</span>' +
              '<span class="cx-retry-live" data-live title="自动刷新中"></span>' +
              '<span class="sp"></span>' +
              '<span data-clock>--:--:--</span>' +
              '<button type="button" data-refresh title="立即刷新">⟳</button>' +
              '<button type="button" data-close title="关闭">✕</button>' +
            '</div>' +
            '<div class="cx-retry-panel__bd" data-bd></div>' +
            '<div class="cx-retry-panel__ft" data-ft></div>';
        document.body.appendChild(panel);
        panel.querySelector('[data-close]').addEventListener('click', function () {
            panel.classList.remove('on');
            // 关掉面板后降到低频，不用再盯得那么勤
            schedule(IDLE_MS);
        });
        panel.querySelector('[data-refresh]').addEventListener('click', function () { run(false); });
        return panel;
    }

    function row(s, r) {
        var st = r.ok
            ? '<span class="ok">● 在线</span>'
            : (r.soft ? '<span class="bad">● 车机未连接</span>' : '<span class="bad">● 离线</span>');
        var detail = '';
        if (r.ok) {
            var d = r.data || {};
            if (s.key === 'can') {
                detail = '设备 <b>' + (d.board || '--') + '</b>' +
                    (d.hz_total !== undefined ? ' · 总线 <b>' + Math.round(d.hz_total) + '</b> 帧/秒' : '') +
                    (d.ids_live !== undefined ? ' · 报文 <b>' + d.ids_live + '/' + d.ids_total + '</b>' : '');
            } else {
                detail = 'master <b>' + (d.master || '--') + '</b>' +
                    ' · 话题 <b>' + (d.topics_online || 0) + '/' + (d.topics_watched || 0) + '</b>' +
                    ' · 节点 <b>' + (d.nodes || 0) + '</b>' +
                    ' · 告警 <b>' + (d.fault_alarm || 0) + '</b>';
            }
        } else if (r.soft) {
            // 桥接在跑，但车机没连上：报文/话题全都取不到，页面上的数值是旧缓存
            var d2 = r.data || {};
            var w2 = d2.topics_watched || 0;
            detail = 'master <b>' + (d2.master || '--') + '</b>' +
                (w2 > 0 ? ' · 话题 <b>0/' + w2 + '</b> 全静默'
                        : ' · <b>未连上 ROS master</b>') +
                ' · 桥接进程正常，<b style="color:#E0574A">请检查车机网线 / ROS Master</b>';
        } else {
            detail = '需要 <b>' + s.need + '</b> · 启动 <code>' + s.start + '</code>';
        }
        return '<div class="cx-retry-row">' +
            '<div class="cx-retry-row__n">' + s.name + ' <em>:' + s.port + '</em></div>' +
            '<div class="cx-retry-row__s">' + st + ' <u>' + r.ms + ' ms</u></div>' +
            '<div class="cx-retry-row__d">' + detail + '</div>' +
            '</div>';
    }

    function render(results, openIt) {
        var p = ensurePanel();
        var d = new Date();
        function z(n) { return n < 10 ? '0' + n : n; }
        var hhmmss = z(d.getHours()) + ':' + z(d.getMinutes()) + ':' + z(d.getSeconds());
        p.querySelector('[data-clock]').textContent = '更新 ' + hhmmss;
        ensureTicker();

        var allOk = results.every(function (r) { return r.ok; });
        var anyOk = results.some(function (r) { return r.ok; });
        // 桥接在跑但车机没连上的那种"软离线"
        var softN = results.filter(function (r) { return !r.ok && r.soft; }).length;
        var softOnly = !anyOk && softN > 0;

        p.querySelector('[data-bd]').innerHTML = SRC.map(function (s, i) {
            return row(s, results[i]);
        }).join('');

        var ft = p.querySelector('[data-ft]');
        if (allOk) {
            ft.innerHTML = '<span class="ok">两路数据源均在线</span> · 面板数据会在 1~2 秒内自动刷新';
        } else if (softOnly) {
            ft.innerHTML = '<span class="warn">桥接进程正常，但车机未连接</span> · ' +
                '请检查车机网线 / ROS Master <code>192.168.1.102:11311</code> —— ' +
                '此时页面上的数值是上一次的缓存，不是实时值';
        } else if (anyOk) {
            ft.innerHTML = '<span class="warn">部分数据源离线</span> · 按上方提示启动对应桥接即可，无需重启页面';
        } else {
            ft.innerHTML = '<span class="bad">两路数据源均离线</span> · 先启动桥接：<code>启动数据桥接.cmd</code>';
        }
        // 只有手动触发才拉开面板；自动刷新只更新按钮颜色，绝不弹窗遮挡

        if (openIt) p.classList.add('on');

        // 让按钮也显示总体状态
        var b = document.getElementById('cx-retry-btn');
        if (b) {
            b.dataset.state = allOk ? 'ok' : ((anyOk || softOnly) ? 'warn' : 'bad');
            b.title = allOk ? '两路数据源均在线'
                : (softOnly ? '桥接正常但车机未连接（点击查看）'
                : (anyOk ? '部分数据源离线（点击查看）' : '两路数据源均离线（点击查看）'));
        }
    }

    /* ---------------- 执行 ---------------- */
    /* 每秒把"更新于 Xs 前"重算一次，让人一眼看出它真的在自动刷新 */
    function ensureTicker() {
        if (ticker) return;
        ticker = window.setInterval(function () {
            var p2 = document.getElementById('cx-retry-panel');
            if (!p2 || !lastAt) return;
            var el2 = p2.querySelector('[data-clock]');
            if (!el2) return;
            var d2 = new Date(lastAt);
            function z2(n) { return n < 10 ? '0' + n : n; }
            var ago = Math.round((Date.now() - lastAt) / 1000);
            el2.textContent = '更新 ' + z2(d2.getHours()) + ':' + z2(d2.getMinutes()) + ':' + z2(d2.getSeconds()) +
                              (ago >= 2 ? ' · ' + ago + 's 前' : '');
        }, 1000);
    }

    /* ★ 自动刷新（本次核心改动）
       原来只在打开页面时探一次 + 点击时探一次 —— 拔插网线后必须手动点才更新，
       看着像"卡住了"。现在：
         · 面板打开时每 2s 重探一次
         · 面板关着时每 5s 也轻量探一次，让右上角按钮颜色始终反映真实链路
         · 标签页切到后台自动降频，避免白烧 CPU
         · silent=true 时不闪"诊断中…"，避免每 2 秒抖一下 */
    var LIVE_MS = 2000, IDLE_MS = 5000;
    var timer = null, lastAt = 0, ticker = null;

    function schedule(ms) {
        if (timer) window.clearTimeout(timer);
        timer = window.setTimeout(function () {
            if (document.hidden) { schedule(1500); return; }
            run(true);
        }, ms);
    }

    var busy = false;
    function run(silent) {
        if (busy) return;
        busy = true;
        var b = document.getElementById('cx-retry-btn');
        if (b && !silent) { b.dataset.state = 'busy'; b.querySelector('[data-t]').textContent = '诊断中…'; }
        Promise.all(SRC.map(probe)).then(function (rs) {
            busy = false;
            lastAt = Date.now();
            render(rs, !silent);
            if (b) {
                b.querySelector('[data-t]').textContent = '重连诊断';
                try {
                    window.dispatchEvent(new CustomEvent('cx-retry', { detail: { results: rs } }));
                } catch (e) { }
            }
            // 面板开着就高频，关着就低频 —— 始终挂着，不用手动点；自动刷新不会把面板弹出来
            var open = panel && panel.classList.contains('on');
            schedule(open ? LIVE_MS : IDLE_MS);
        });
    }

    /* ---------------- 按钮 ---------------- */
    var CSS = [
        '#cx-retry-btn{display:inline-flex;align-items:center;gap:6px;height:28px;padding:0 10px;',
        '  border:1px solid rgba(148,163,184,.32);background:transparent;color:#9A9AA5;',
        '  font-family:"JetBrains Mono",Consolas,monospace;font-size:11px;letter-spacing:.1em;',
        '  cursor:pointer;transition:color .18s,border-color .18s,background .18s}',
        '#cx-retry-btn:hover{border-color:#3D9BFF;color:#3D9BFF;background:rgba(61,155,255,.08)}',
        '#cx-retry-btn[data-state="ok"]{border-color:rgba(46,229,157,.5);color:#2EE59D}',
        '#cx-retry-btn[data-state="warn"]{border-color:rgba(212,118,42,.55);color:#D4762A}',
        '#cx-retry-btn[data-state="bad"]{border-color:rgba(224,87,74,.55);color:#E0574A}',
        '#cx-retry-btn[data-state="busy"]{opacity:.7}',
        'html[data-cx-mode="day"] #cx-retry-btn{border-color:rgba(15,23,42,.18);color:#55606F}',
        'html[data-cx-mode="day"] #cx-retry-btn:hover{border-color:#1E6FD9;color:#1E6FD9}',
        /* 诊断面板 */
        '.cx-retry-panel{position:fixed;right:22px;top:70px;width:min(460px,92vw);z-index:9000;',
        '  background:rgba(11,14,19,.97);border:1px solid rgba(148,163,184,.28);',
        '  box-shadow:0 18px 50px -22px rgba(0,0,0,.85);opacity:0;visibility:hidden;',
        '  transform:translateY(-6px);transition:opacity .18s ease,transform .18s ease,visibility .18s;',
        '  font-family:"JetBrains Mono",Consolas,monospace;font-size:11.5px;color:#E8E8EC}',
        '.cx-retry-panel.on{opacity:1;visibility:visible;transform:none}',
        '.cx-retry-panel__hd{display:flex;align-items:center;gap:8px;padding:7px 10px;',
        '  font-size:10px;letter-spacing:.16em;color:#9A9AA5;background:rgba(148,163,184,.08);',
        '  border-bottom:1px solid rgba(148,163,184,.2)}',
        '.cx-retry-panel__hd .sp{flex:1}',
        '.cx-retry-panel__hd button{background:none;border:0;color:#9A9AA5;cursor:pointer;font-size:12px}',
        '.cx-retry-panel__hd button:hover{color:#E0574A}',
        '.cx-retry-panel__hd button[data-refresh]:hover{color:#3D9BFF}',
        /* 自动刷新指示：呼吸的绿点，让人一眼看出它是活的 */
        '.cx-retry-live{width:6px;height:6px;border-radius:50%;background:#2EE59D;',
        '  box-shadow:0 0 0 0 rgba(46,229,157,.6);animation:cx-retry-pulse 2s ease-out infinite}',
        '@keyframes cx-retry-pulse{0%{box-shadow:0 0 0 0 rgba(46,229,157,.55)}',
        '  70%{box-shadow:0 0 0 6px rgba(46,229,157,0)}100%{box-shadow:0 0 0 0 rgba(46,229,157,0)}}',
        '@media (prefers-reduced-motion:reduce){.cx-retry-live{animation:none}}',
        '.cx-retry-panel__bd{padding:8px 10px}',
        '.cx-retry-panel__ft{padding:7px 10px;border-top:1px solid rgba(148,163,184,.18);',
        '  font-size:10.5px;color:#9A9AA5;line-height:1.7}',
        '.cx-retry-row{padding:7px 0;border-bottom:1px dashed rgba(148,163,184,.16)}',
        '.cx-retry-row:last-child{border-bottom:0}',
        '.cx-retry-row__n{letter-spacing:.1em;color:#E8E8EC}',
        '.cx-retry-row__n em{font-style:normal;color:#5A5A66}',
        '.cx-retry-row__s{margin-top:2px;font-size:10.5px}',
        '.cx-retry-row__s u{text-decoration:none;color:#5A5A66;margin-left:6px}',
        '.cx-retry-row__d{margin-top:2px;font-size:10.5px;color:#9A9AA5;line-height:1.65}',
        '.cx-retry-row__d b{color:#3D9BFF;font-weight:500}',
        '.cx-retry-row__d code,.cx-retry-panel__ft code{background:rgba(148,163,184,.12);',
        '  padding:1px 5px;color:#8CC6FF}',
        '.cx-retry-panel .ok{color:#2EE59D}.cx-retry-panel .bad{color:#E0574A}',
        '.cx-retry-panel .warn{color:#D4762A}',
        'html[data-cx-mode="day"] .cx-retry-panel{background:rgba(255,255,255,.98);',
        '  border-color:rgba(15,23,42,.14);color:#1A2230;box-shadow:0 18px 44px -20px rgba(15,23,42,.3)}',
        'html[data-cx-mode="day"] .cx-retry-panel__hd{background:rgba(15,23,42,.04);',
        '  border-bottom-color:rgba(15,23,42,.1);color:#55606F}',
        'html[data-cx-mode="day"] .cx-retry-row__n{color:#1A2230}',
        'html[data-cx-mode="day"] .cx-retry-row__d{color:#55606F}',
        'html[data-cx-mode="day"] .cx-retry-row__d b{color:#1E6FD9}',
        'html[data-cx-mode="day"] .cx-retry-panel .ok{color:#0E9F6E}',
        'html[data-cx-mode="day"] .cx-retry-panel .bad{color:#C93A2E}',
        'html[data-cx-mode="day"] .cx-retry-panel__ft{color:#55606F;border-top-color:rgba(15,23,42,.1)}'
    ].join('\n');

    var st = document.createElement('style');
    st.id = 'cx-retry-css';
    st.textContent = CSS;
    document.head.appendChild(st);

    function mount() {
        if (document.getElementById('cx-retry-btn')) return true;
        var host = document.querySelector('header .flex.items-center.space-x-4')
            || document.querySelector('header .flex.items-center.justify-between > div:last-child')
            || document.querySelector('header');
        if (!host) return false;
        var b = document.createElement('button');
        b.id = 'cx-retry-btn';
        b.type = 'button';
        b.innerHTML = '<i class="fa fa-refresh"></i><span data-t>重连诊断</span>';
        // 注意：不能直接传 run，否则 run 的第一个参数会收到 click 事件对象（被当成 silent=true）
        b.addEventListener('click', function () { run(false); });
        host.insertBefore(b, host.firstChild);
        return true;
    }

    function boot() {
        if (!mount()) {
            var tries = 0;
            var t = window.setInterval(function () {
                if (mount() || ++tries > 20) window.clearInterval(t);
            }, 250);
        }
        // 打开页面先自动诊断一次（**静默**，只更新按钮颜色，不弹面板）
        // 随后由 schedule() 自维持：面板开着 2s 一次、关着 5s 一次，全程不打扰
        window.setTimeout(function () { run(true); }, 1200);
        // Ctrl+Alt+R 手动强制刷新
        window.addEventListener('keydown', function (e) {
            if (e.ctrlKey && e.altKey && (e.key === 'r' || e.key === 'R')) { e.preventDefault(); run(false); }
        });
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
    else boot();
})();

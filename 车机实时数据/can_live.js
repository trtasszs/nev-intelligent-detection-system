/* ============================================================================
   车机 CAN 实时数据渲染（数据源：can_bridge.py ← 创芯 CANalyst-II 直读整车CAN）
   本层会接管原先基于 ROS 的面板（ROS 那条以太网当前未接），全站改为 CAN 真数据。
   ========================================================================== */
(function () {
    'use strict';

    var PORT = 8780;
    /* BASE_FIXED: CAN 桥接固定 8780 端口。不能用 location.origin ——
       页面可能由任意服务提供（桌面版 exe 的静态服务、CAN 桥接、file://），
       一旦原样用 origin，请求会打到那个端口、全部 404。 */
    var BASE = 'http://127.0.0.1:8780';
    void (location.protocol);

    var ROS_PANEL_IDS = ['cx-live', 'cx-faultlog', 'cx-iot', 'cx-topics', 'cx-telemetry', 'cx-bridge'];

    /* ---------------------------------------------------------------- 工具 */
    function el(t, c, h) {
        var d = document.createElement(t);
        if (c) d.className = c;
        if (h !== undefined) d.innerHTML = h;
        return d;
    }
    function pad(n) { return n < 10 ? '0' + n : String(n); }
    function fmt(v, d) {
        if (v === null || v === undefined || (typeof v === 'number' && isNaN(v))) return '--';
        if (typeof v !== 'number') return String(v);
        return v.toFixed(d === undefined ? 2 : d);
    }
    function head(title, sub) {
        var h = el('div', 'cx-live__head');
        h.appendChild(el('div', 'cx-live__title',
            '<span class="cx-live__dot"></span>' + title +
            '<span class="cx-live__state" data-s>连接中…</span>'));
        h.appendChild(el('div', 'cx-live__meta', sub || ''));
        var b = el('span', 'cx-livebadge', '<i></i>CAN LIVE');
        h.querySelector('.cx-live__title').appendChild(b);
        return h;
    }
    function row(k, unit, dec) {
        var r = el('div', 'cx-row');
        r.appendChild(el('span', 'cx-row__k', k));
        var v = el('span', 'cx-row__v', '--' + (unit ? '<u>' + unit + '</u>' : ''));
        r.appendChild(v);
        r._dec = dec === undefined ? 2 : dec; r._v = v;
        return r;
    }
    function setRow(r, val) {
        if (!r || !r._v || !r._v.firstChild) return;
        var s = (val === null || val === undefined || isNaN(val)) ? '--' : Number(val).toFixed(r._dec);
        if (r._v.firstChild.nodeValue === s) return;
        r._v.firstChild.nodeValue = s;
        r._v.classList.add('is-tick');
        window.setTimeout(function () { r._v.classList.remove('is-tick'); }, 420);
    }
    function poll(path, ms, fn) {
        var u = BASE + path + (path.indexOf('?') < 0 ? '?' : '&') + 't=';
        (function once() {
            fetch(u + Date.now(), { cache: 'no-store' })
                .then(function (r) { return r.json(); })
                .then(fn)
                .catch(function () { try { fn(null); } catch (e) { } })
                .then(function () { window.setTimeout(once, ms); });
        })();
    }
    function takeOver() {
        // 移除原来基于 ROS 的面板，避免两套数据源并存
        ROS_PANEL_IDS.forEach(function (id) {
            var n = document.getElementById(id);
            if (n && n.parentNode) n.parentNode.removeChild(n);
        });
        var s = document.querySelector('.cx-strip-live');
        if (s && s.parentNode) s.parentNode.removeChild(s);
        var t = document.getElementById('cx-can-strip');
        if (t && t.parentNode) t.parentNode.removeChild(t);
    }
    function activePage() {
        var p = document.querySelector('.page-content:not(.hidden)');
        return p ? p.id : null;
    }
    function page(id) { return document.getElementById(id); }
    function group(sig) {
        return {
            speed: sig.speed_raw === undefined ? null : sig.speed_kmh,
            gear: sig.gear_raw,
            epb: sig.epb,
            cruise: sig.cruise_switch,
            vcu: sig.vcu_ready,
            acc: sig.acc_cmd,
            brk: sig.brk_cmd,
            steer: sig.steer_angle_raw,
            rate: sig.steer_rate,
            wheel: sig.wheel_raw,
            yaw: sig.yaw_raw,
            pedal: sig.pedal_raw
        };
    }

    /* ==================================================================
       ① 系统概览：CAN 状态带
       ================================================================== */
    function buildStrip() {
        var p = page('dashboard');
        if (!p || document.getElementById('cx-can-strip')) return;
        var bar = el('div', 'cx-strip-live');
        bar.id = 'cx-can-strip';
        bar.innerHTML =
            '<span class="cx-strip-live__i">总线 <b data-hz>--</b> 帧/秒</span>' +
            '<span class="cx-strip-live__i">报文 ID <em data-ids>--</em></span>' +
            '<span class="cx-strip-live__i">车速 <b data-spd>--</b></span>' +
            '<span class="cx-strip-live__i">档位 <b data-gear>--</b></span>' +
            '<span class="cx-strip-live__i">EPB <b data-epb>--</b></span>' +
            '<span class="cx-strip-live__sp"></span>' +
            '<span class="cx-strip-live__i" data-board>--</span>';
        p.insertBefore(bar, p.firstChild);

        poll('/api/meta', 1500, function (m) {
            if (!m || !m.ok) { bar.querySelector('[data-hz]').textContent = '链路中断'; return; }
            bar.querySelector('[data-hz]').textContent = Math.round(m.hz_total);
            bar.querySelector('[data-ids]').textContent = m.ids_live + '/' + m.ids_total;
            bar.querySelector('[data-board]').textContent = m.board;
        });
        poll('/api/vehicle', 700, function (v) {
            if (!v || !v.ok) return;
            var s = v.signal;
            bar.querySelector('[data-spd]').innerHTML = fmt(s.speed_kmh, 1) + ' km/h';
            bar.querySelector('[data-gear]').innerHTML = '0x' + (s.gear_raw === undefined ? '--' :
                ('0' + Number(s.gear_raw).toString(16).toUpperCase()).slice(-2));
            bar.querySelector('[data-epb]').innerHTML = s.epb ? '已拉紧' : '已释放';
        });
    }

    /* ==================================================================
       ② 车辆信息管理：整车实时状态（CAN 真数据）
       ================================================================== */
    function buildVehicle() {
        var p = page('vehicles');
        if (!p || document.getElementById('cx-can-veh')) return;
        var card = el('div', 'card cx-live mb-6');
        card.id = 'cx-can-veh';
        card.appendChild(head('整车实时状态（CAN 总线直读）', 'ROS MASTER <b data-m>--</b>'));

        var grid = el('div', 'cx-live__grid');
        card.appendChild(grid);

        var G1 = el('div', 'cx-live__box');
        G1.appendChild(el('div', 'cx-live__boxhd', '<i></i>VEHICLE · 整车状态'));
        var big = el('div', 'cx-big');
        var cSpeed = el('div', 'cx-big__c');
        cSpeed.appendChild(el('div', 'cx-big__n', '--'));
        cSpeed.appendChild(el('div', 'cx-big__u', 'km/h'));
        cSpeed.appendChild(el('div', 'cx-big__l', '车速'));
        big.appendChild(cSpeed);
        var cGear = el('div', 'cx-big__c');
        cGear.appendChild(el('div', 'cx-big__n', '--'));
        cGear.appendChild(el('div', 'cx-big__u', '原始值'));
        cGear.appendChild(el('div', 'cx-big__l', '档位'));
        big.appendChild(cGear);
        G1.appendChild(big);
        var rG = {};
        [['vcu', 'VCU 就绪', '', 0], ['epb', 'EPB 电子手刹', '', 0],
         ['cruise', '巡航开关', '', 0], ['pedal', '踏板原始值', '', 0]].forEach(function (x) {
            var r = row(x[1], x[2], x[3]); G1.appendChild(r); rG[x[0]] = r;
        });
        grid.appendChild(G1);

        var G2 = el('div', 'cx-live__box');
        G2.appendChild(el('div', 'cx-live__boxhd', '<i></i>ACTUATOR · 线控执行器指令'));
        var rA = {};
        [['acc', '油门执行器', '%', 0], ['acci', '油门反值', '', 0],
         ['brk', '刹车执行器', '%', 0], ['brki', '刹车反值', '', 0],
         ['steer', '转向角指令', '', 0], ['rate', '转向角速度', '', 0]].forEach(function (x) {
            var r = row(x[1], x[2], x[3]); G2.appendChild(r); rA[x[0]] = r;
        });
        grid.appendChild(G2);

        var G3 = el('div', 'cx-live__box');
        G3.appendChild(el('div', 'cx-live__boxhd', '<i></i>MOTION · 底盘动态'));
        var rM = {};
        [['w0', '轮速原始 0', '', 0], ['w1', '轮速原始 1', '', 0],
         ['y0', '横摆/加速度 A', '', 0], ['y1', '横摆/加速度 B', '', 0],
         ['y2', '横摆/加速度 C', '', 0]].forEach(function (x) {
            var r = row(x[1], x[2], x[3]); G3.appendChild(r); rM[x[0]] = r;
        });
        grid.appendChild(G3);

        var G4 = el('div', 'cx-live__box');
        G4.appendChild(el('div', 'cx-live__boxhd', '<i></i>BUS · 总线概览'));
        var rB = {};
        [['hz', '总线速率', '帧/秒', 0], ['ids', '在线报文 ID', '个', 0],
         ['total', '累计帧数', '', 0]].forEach(function (x) {
            var r = row(x[1], x[2], x[3]); G4.appendChild(r); rB[x[0]] = r;
        });
        var w = el('div', 'cx-live__warn is-info', '<i class="fa fa-info-circle"></i>' +
            '<span>解码依据：实测帧表（车机调试完整记录.md）</span>');
        G4.appendChild(w);
        grid.appendChild(G4);

        p.insertBefore(card, p.firstChild);

        poll('/api/vehicle', 500, function (v) {
            var c = card;
            if (!v || !v.ok) {
                c.classList.remove('is-ok'); c.classList.add('is-bad');
                c.querySelector('[data-s]').textContent = 'CAN 采集未启动';
                return;
            }
            c.classList.add('is-ok'); c.classList.remove('is-bad');
            c.querySelector('[data-s]').textContent = 'CAN 实时采集中';
            c.querySelector('[data-m]').textContent = v.board || '--';
            var s = v.signal, g = group(s);
            function setBig(node, val, d) {
                var t = fmt(val, d);
                if (node.textContent === t) return;
                node.textContent = t;
                node.classList.add('is-tick');
                window.setTimeout(function () { node.classList.remove('is-tick'); }, 420);
            }
            setBig(cSpeed.firstChild, g.speed, 1);
            setBig(cGear.firstChild, g.gear, 0);
            setRow(rG.vcu, g.vcu); setRow(rG.epb, g.epb);
            setRow(rG.cruise, g.cruise); setRow(rG.pedal, g.pedal);
            setRow(rA.acc, s.acc_cmd); setRow(rA.acci, s.acc_cmd_inv);
            setRow(rA.brk, s.brk_cmd); setRow(rA.brki, s.brk_cmd_inv);
            setRow(rA.steer, s.steer_angle_raw); setRow(rA.rate, s.steer_rate);
            var w0 = (g.wheel || [])[0], w1 = (g.wheel || [])[1];
            setRow(rM.w0, w0); setRow(rM.w1, w1);
            var y = g.yaw || [];
            setRow(rM.y0, y[0]); setRow(rM.y1, y[1]); setRow(rM.y2, y[2]);
            setRow(rB.hz, v.hz_total); setRow(rB.ids, v.ids); setRow(rB.total, v.total);
        });
    }

    /* ==================================================================
       ③ 通信协议：真实 CAN 报文矩阵
       ================================================================== */
    function buildCanMatrix() {
        var p = page('protocol');
        if (!p || document.getElementById('cx-can-matrix')) return;
        var card = el('div', 'card cx-live mb-6');
        card.id = 'cx-can-matrix';
        card.appendChild(head('整车 CAN 报文矩阵（实时）', '<span data-meta>--</span>'));

        var bar = el('div', 'flex items-center justify-between mb-3');
        var filters = el('div', 'cx-filters');
        var modes = [['all', '全部'], ['fast', '高频 (>50Hz)'], ['mid', '中频'], ['slow', '低频 (<20Hz)']];
        modes.forEach(function (m) {
            var b = el('button', m[0] === 'all' ? 'on' : '', m[1]);
            b.addEventListener('click', function () {
                Array.prototype.forEach.call(filters.children, function (x) { x.classList.remove('on'); });
                b.classList.add('on'); S.mode = m[0]; render();
            });
            filters.appendChild(b);
        });
        bar.appendChild(filters);
        bar.appendChild(el('div', 'cx-live__meta', '<span data-count>--</span>'));
        card.appendChild(bar);
        var wrap = el('div', '');
        card.appendChild(wrap);
        p.insertBefore(card, p.firstChild);

        var S = { mode: 'all', frames: {} };

        function render() {
            var keys = Object.keys(S.frames);
            keys = keys.filter(function (k) {
                var hz = S.frames[k].hz || 0;
                if (S.mode === 'fast') return hz > 50;
                if (S.mode === 'mid') return hz > 20 && hz <= 50;
                if (S.mode === 'slow') return hz < 20;
                return true;
            }).sort(function (a, b) { return (S.frames[b].hz || 0) - (S.frames[a].hz || 0); });

            var html = '<table class="cx-tbl"><thead><tr><th>CAN ID</th><th>帧率</th>' +
                '<th>数据长度</th><th>实时数据（十六进制）</th><th>字节变化</th><th>延迟</th></tr></thead><tbody>';
            keys.forEach(function (k) {
                var f = S.frames[k];
                var chg = f.changed > 0 ? '<span style="color:var(--cx-cy)">' + f.changed + '</span>' : '<span class="dim">恒定</span>';
                html += '<tr><td class="mono nw">0x' + k + '</td>' +
                    '<td class="mono nw">' + fmt(f.hz, 1) + ' Hz</td>' +
                    '<td class="mono nw dim">' + f.len + ' B</td>' +
                    '<td class="mono">' + f.data + '</td>' +
                    '<td class="nw">' + chg + '</td>' +
                    '<td class="mono dim nw">' + (f.age != null ? Math.round(f.age * 1000) + ' ms' : '--') + '</td></tr>';
            });
            html += '</tbody></table>';
            wrap.innerHTML = html;
            card.querySelector('[data-count]').textContent = keys.length + ' / ' + Object.keys(S.frames).length + ' 条报文';
        }

        poll('/api/frames', 1000, function (d) {
            if (!d || !d.ok) {
                card.classList.remove('is-ok'); card.classList.add('is-bad');
                wrap.innerHTML = '<div class="cx-live__warn"><span>CAN 采集未启动（请运行 can_bridge.py）</span></div>';
                return;
            }
            card.classList.add('is-ok');
            S.frames = d.frames || {};
            card.querySelector('[data-meta]').innerHTML =
                '板卡 <b>' + (d.board || '--') + '</b> &nbsp;·&nbsp; 总线 <b>' + Math.round(d.hz_total) +
                '</b> 帧/秒 &nbsp;·&nbsp; 报文 <b>' + d.count + '</b> 条 &nbsp;·&nbsp; 500 kbps';
            render();
        });
    }

    /* ==================================================================
       ④ 智能网联管理：底盘电子系统状态
       ================================================================== */
    function buildChassis() {
        var p = page('iot');
        if (!p || document.getElementById('cx-can-iot')) return;
        var card = el('div', 'card cx-live mb-6');
        card.id = 'cx-can-iot';
        card.appendChild(head('底盘电子系统状态（CAN 直读）', '<span data-m>--</span>'));
        var grid = el('div', 'cx-live__grid');
        card.appendChild(grid);

        var A = el('div', 'cx-live__box');
        A.appendChild(el('div', 'cx-live__boxhd', '<i></i>EPS · 电动转向系统'));
        var rA = {};
        [['mode', 'EPS 模式原始', '', 0], ['angle', '转向角原始', '', 0],
         ['rate', '转向角速度', '', 0], ['cmd', '转向指令', '', 0]].forEach(function (x) {
            var r = row(x[1], x[2], x[3]); A.appendChild(r); rA[x[0]] = r;
        });
        grid.appendChild(A);

        var B = el('div', 'cx-live__box');
        B.appendChild(el('div', 'cx-live__boxhd', '<i></i>WHEEL · 轮速信号'));
        var rB = {};
        [['w0', '轮速 0', '', 0], ['w1', '轮速 1', '', 0], ['w2', '轮速 2', '', 0], ['w3', '轮速 3', '', 0]].forEach(function (x) {
            var r = row(x[1], x[2], x[3]); B.appendChild(r); rB[x[0]] = r;
        });
        grid.appendChild(B);

        var C = el('div', 'cx-live__box');
        C.appendChild(el('div', 'cx-live__boxhd', '<i></i>IMU · 横摆与加速度'));
        var rC = {};
        [['a', '通道 A', '', 0], ['b', '通道 B', '', 0], ['c', '通道 C', '', 0], ['d', '通道 D', '', 0]].forEach(function (x) {
            var r = row(x[1], x[2], x[3]); C.appendChild(r); rC[x[0]] = r;
        });
        grid.appendChild(C);

        var D = el('div', 'cx-live__box');
        D.appendChild(el('div', 'cx-live__boxhd', '<i></i>STATUS · 整车信号'));
        var rD = {};
        [['gear', '档位原始', '', 0], ['vcu', 'VCU 就绪', '', 0], ['epb', 'EPB 状态', '', 0],
         ['pedal', '踏板原始', '', 0], ['bl', '刹车灯原始', '', 0]].forEach(function (x) {
            var r = row(x[1], x[2], x[3]); D.appendChild(r); rD[x[0]] = r;
        });
        grid.appendChild(D);

        p.insertBefore(card, p.firstChild);

        poll('/api/vehicle', 700, function (v) {
            if (!v || !v.ok) {
                card.classList.remove('is-ok'); card.classList.add('is-bad');
                card.querySelector('[data-s]').textContent = 'CAN 采集未启动';
                return;
            }
            card.classList.add('is-ok');
            card.querySelector('[data-s]').textContent = 'CAN 实时采集中';
            card.querySelector('[data-m]').textContent = v.board || '--';
            var s = v.signal;
            setRow(rA.mode, s.eps_mode); setRow(rA.angle, s.steer_angle_raw);
            setRow(rA.rate, s.steer_rate); setRow(rA.cmd, s.steer_cmd);
            var w = s.wheel_raw || [];
            setRow(rB.w0, w[0]); setRow(rB.w1, w[1]); setRow(rB.w2, w[2]); setRow(rB.w3, w[3]);
            var y = s.yaw_raw || [];
            setRow(rC.a, y[0]); setRow(rC.b, y[1]); setRow(rC.c, y[2]); setRow(rC.d, y[3]);
            setRow(rD.gear, s.gear_raw); setRow(rD.vcu, s.vcu_ready); setRow(rD.epb, s.epb);
            setRow(rD.pedal, s.pedal_raw); setRow(rD.bl, s.brake_light_raw);
        });
    }

    /* ==================================================================
       ⑤ 数据分析：真实 CAN 曲线
       ================================================================== */
    function buildChart() {
        var p = page('statistics');
        if (!p || document.getElementById('cx-can-chart') || typeof Chart === 'undefined') return;
        var card = el('div', 'card cx-live mb-6');
        card.id = 'cx-can-chart';
        card.appendChild(head('整车 CAN 实时曲线', '<span data-meta>--</span>'));
        var grid = el('div', 'cx-charts');
        card.appendChild(grid);

        var defs = [
            { id: 'hz', title: 'BUS LOAD · 总线帧率', key: 'hz', color: '#3D9BFF' },
            { id: 'spd', title: 'VEHICLE SPEED · 车速', key: 'spd', color: '#3D9BFF' },
            { id: 'steer', title: 'STEER · 转向角原始', key: 'steer', color: '#D4762A' },
            { id: 'yaw', title: 'YAW/ACC · 横摆通道', key: 'yaw', color: '#D93A3A' }
        ];
        var charts = {};
        defs.forEach(function (d) {
            var box = el('div', 'cx-chartbox');
            box.appendChild(el('div', 'cx-chartbox__h', '<span>' + d.title + '</span><span data-cur>--</span>'));
            var cv = document.createElement('canvas');
            box.appendChild(cv);
            grid.appendChild(box);
            charts[d.key] = {
                chart: new Chart(cv.getContext('2d'), {
                    type: 'line',
                    data: { labels: [], datasets: [{ label: d.title.split(' ')[0], data: [],
                            borderColor: d.color, borderWidth: 1.4, pointRadius: 0, tension: .35, fill: false }] },
                    options: {
                        responsive: true, maintainAspectRatio: false, animation: false,
                        plugins: { legend: { display: false } },
                        scales: {
                            x: { display: false },
                            y: { ticks: { color: '#86775A', font: { size: 9 }, maxTicksLimit: 5 },
                                 grid: { color: 'rgba(158,168,182,.07)' } }
                        }
                    }
                }),
                box: box, buf: []
            };
        });
        card.appendChild(grid);
        p.insertBefore(card, p.firstChild);

        var N = 120;
        poll('/api/vehicle', 1000, function (v) {
            if (!v || !v.ok) return;
            card.classList.add('is-ok');
            var s = v.signal;
            var yaw = (s.yaw_raw || [0])[0] || 0;
            var pts = { hz: v.hz_total, spd: s.speed_kmh || 0, steer: s.steer_angle_raw || 0, yaw: yaw };
            Object.keys(charts).forEach(function (k) {
                var c = charts[k];
                c.buf.push(pts[k]);
                if (c.buf.length > N) c.buf.shift();
                c.chart.data.labels = c.buf.map(function (_, i) { return i; });
                c.chart.data.datasets[0].data = c.buf.slice();
                c.chart.update('none');
                c.box.querySelector('[data-cur]').textContent = fmt(c.buf[c.buf.length - 1], 1);
            });
            card.querySelector('[data-meta]').textContent = N + ' 点窗口 · 1 Hz 采样';
        });
    }

    /* ==================================================================
       ⑥ 检测记录管理：CAN 链路质量与异常监测
       ================================================================== */
    function buildHealth() {
        var p = page('detection');
        if (!p || document.getElementById('cx-can-health')) return;
        var card = el('div', 'card cx-live mb-6');
        card.id = 'cx-can-health';
        card.appendChild(head('CAN 链路质量监测', '<span data-m>--</span>'));
        var wrap = el('div', '');
        card.appendChild(wrap);
        p.insertBefore(card, p.firstChild);

        var hist = [];
        poll('/api/meta', 1500, function (m) {
            if (!m || !m.ok) {
                card.classList.remove('is-ok'); card.classList.add('is-bad');
                wrap.innerHTML = '<div class="cx-live__warn"><span>CAN 采集未启动</span></div>';
                return;
            }
            card.classList.add('is-ok');
            var hz = Math.round(m.hz_total);
            hist.push(hz);
            if (hist.length > 60) hist.shift();
            var avg = hist.reduce(function (a, b) { return a + b; }, 0) / hist.length;
            var diff = avg > 0 ? Math.abs(hz - avg) / avg : 0;
            var level = m.silent.length === 0 ? 0 : 1;
            if (diff > 0.25) level = 2;

            card.querySelector('[data-m]').innerHTML =
                '在线 <em>' + m.ids_live + '</em>/' + m.ids_total + ' &nbsp;·&nbsp; 采样 ' + hist.length + ' 次';
            var html = '<table class="cx-tbl"><thead><tr><th>监测项</th><th>当前值</th>' +
                '<th>基准</th><th>状态</th></tr></thead><tbody>';
            html += '<tr><td>总线速率</td><td class="mono">' + hz + ' 帧/秒</td><td class="mono dim">' +
                Math.round(avg) + ' 帧/秒(均值)</td><td>' +
                (diff > 0.25 ? '<span style="color:var(--cx-rd)">波动 ' + Math.round(diff * 100) + '%</span>'
                             : '<span style="color:var(--cx-gr)">稳定</span>') + '</td></tr>';
            html += '<tr><td>在线报文</td><td class="mono">' + m.ids_live + ' 条</td><td class="mono dim">' +
                m.ids_total + ' 条</td><td>' + (m.silent.length === 0
                    ? '<span style="color:var(--cx-gr)">全部在线</span>'
                    : '<span style="color:var(--cx-am)">' + m.silent.length + ' 条静默</span>') + '</td></tr>';
            html += '<tr><td>累计接收</td><td class="mono">' + m.total.toLocaleString() + ' 帧</td>' +
                '<td class="mono dim">--</td><td><span style="color:var(--cx-gr)">正常</span></td></tr>';
            html += '<tr><td>采集驱动</td><td class="mono dim">' + m.driver + '</td><td></td>' +
                '<td><span style="color:var(--cx-gr)">已连接</span></td></tr>';
            html += '</tbody></table>';
            wrap.innerHTML = html;
        });
    }

    /* ==================================================================
       ⑦ 电池管理：如实说明数据边界
       ================================================================== */
    function buildBattery() {
        var p = page('battery');
        if (!p || document.getElementById('cx-can-bat')) return;
        var card = el('div', 'card cx-live mb-6');
        card.id = 'cx-can-bat';
        var h = head('动力电池数据链路', '<span data-m>--</span>');
        h.querySelector('.cx-livebadge').outerHTML = '';
        card.appendChild(h);
        var body = el('div', '');
        card.appendChild(body);
        p.insertBefore(card, p.firstChild);

        body.innerHTML =
            '<div class="cx-live__warn" style="background:rgba(158, 168, 182, 0.070)">' +
            '<i class="fa fa-exclamation-triangle"></i><span>' +
            '<b>BMS 不在当前这条总线上。</b>按平台手册，电池管理系统走独立的「电池CAN」总线：' +
            'BMS 连接器 <b>C54 引脚 8/9</b>、OBD 诊断口 <b>C39 引脚 9/1</b>。' +
            '当前分析仪接的是 OBD 标准 CAN 脚（6/14）= 整车CAN，因此读不到电池报文。' +
            '</span></div>' +
            '<div class="cx-cfg"><span class="cx-cfg__k">要接入电池数据</span>' +
            '<span class="cx-cfg__v">把分析仪 CANH / CANL 接到 OBD 的 9 脚 / 1 脚，接好后本页可即时出数</span></div>';

        poll('/api/vehicle', 3000, function (v) {
            if (!v || !v.ok) return;
            card.classList.add('is-ok');
            card.querySelector('[data-m]').textContent = '整车CAN 在线 · 电池CAN 未接入';
        });
    }

    /* ==================================================================
       ⑧ 系统设置：CAN 桥接配置
       ================================================================== */
    function buildCfg() {
        var p = page('settings');
        if (!p || document.getElementById('cx-can-cfg')) return;
        var card = el('div', 'card cx-live mb-6');
        card.id = 'cx-can-cfg';
        card.appendChild(head('车机 CAN 数据桥接', '<span data-m>--</span>'));
        var body = el('div', '');
        card.appendChild(body);
        p.insertBefore(card, p.firstChild);

        var eps = ['/api/vehicle', '/api/frames', '/api/meta'];
        poll('/api/meta', 2000, function (m) {
            if (!m || !m.ok) {
                card.classList.remove('is-ok'); card.classList.add('is-bad');
                body.innerHTML = '<div class="cx-live__warn"><i class="fa fa-plug"></i><span>' +
                    'CAN 采集未启动。启动命令：<code>python can_bridge.py --open</code></span></div>';
                return;
            }
            card.classList.add('is-ok');
            card.querySelector('[data-m]').textContent = m.server_time.slice(11);
            var rows = [
                ['数据采集卡', m.board],
                ['驱动库', 'ControlCAN.dll（ctypes 直连，无需上位机）'],
                ['总线波特率', '500 kbps'],
                ['总线速率', Math.round(m.hz_total) + ' 帧/秒'],
                ['在线报文 ID', m.ids_live + ' / ' + m.ids_total],
                ['累计接收', m.total.toLocaleString() + ' 帧'],
                ['本机接口地址', BASE],
                ['服务时间', m.server_time]
            ];
            var html = '';
            rows.forEach(function (r) {
                html += '<div class="cx-cfg"><span class="cx-cfg__k">' + r[0] +
                    '</span><span class="cx-cfg__v">' + r[1] + '</span></div>';
            });
            html += '<div class="cx-cfg" style="align-items:flex-start"><span class="cx-cfg__k">数据接口</span>' +
                '<span class="cx-cfg__v">' + eps.map(function (e) { return '<code>' + e + '</code>'; }).join('') +
                '</span></div>';
            body.innerHTML = html;
        });
    }

    /* ==================================================================
       注册与懒加载
       ================================================================== */
    var PAGES = {
        dashboard: buildStrip,
        vehicles: buildVehicle,
        protocol: buildCanMatrix,
        iot: buildChassis,
        statistics: buildChart,
        detection: buildHealth,
        battery: buildBattery,
        settings: buildCfg
    };
    var built = {};

    function activate(id) {
        if (!id || built[id] || !PAGES[id]) return;
        built[id] = true;
        try { PAGES[id](); } catch (e) { built[id] = false; }
    }
    function activeId() {
        var p = document.querySelector('.page-content:not(.hidden)');
        return p ? p.id : null;
    }

    function boot() {
        if (document.documentElement.dataset.cxCanBooted) return;
        document.documentElement.dataset.cxCanBooted = '1';
        takeOver();
        activate(activeId());
        if (!('MutationObserver' in window)) return;
        var mo = new MutationObserver(function (recs) {
            for (var i = 0; i < recs.length; i++) {
                var e = recs[i].target;
                if (e.classList && !e.classList.contains('hidden') &&
                    e.classList.contains('page-content')) { activate(e.id); }
            }
        });
        Array.prototype.forEach.call(document.querySelectorAll('.page-content'), function (p) {
            mo.observe(p, { attributes: true, attributeFilter: ['class'] });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})();

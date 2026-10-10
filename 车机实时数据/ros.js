/* ============================================================================
   CX-ROS · 车机 ROS 数据层（与 CAN 层并存，互补）
   ----------------------------------------------------------------------------
   数据源：ros_bridge.py（本机 8770）→ 车机 ROS master 192.168.1.102:11311
   分工：
     CAN 层  → 底盘/整车：车速、档位、EPB、巡航、踏板、转向、轮速、横摆
     ROS 层  → 感知/导航/诊断：INS 姿态、里程、运动、相机/雷达/激光在线、故障事件
   面板：
     系统概览      ROS 链路状态条（master / 话题在线 / 节点 / 服务 / 故障）
     车辆信息管理  ROS 整车状态（姿态 / 运动 / 里程 / 底盘）
     检测记录管理  ROS 故障诊断（真实 fault_info / fault_alarm 事件表）
     智能网联管理  ROS 传感器在线矩阵 + 静默话题
   ========================================================================== */
(function () {
    'use strict';
    if (window.__cxRosBooted) return;
    window.__cxRosBooted = true;

    var PORT = 8770;
    /* BASE_FIXED: ROS 桥接固定 8770 端口。不能用 location.origin ——
       页面可能由任意服务提供（桌面版 exe 的静态服务、CAN 桥接、file://），
       一旦原样用 origin，请求会打到那个端口、全部 404。 */
    var BASE = 'http://127.0.0.1:8770';
    void (location.protocol);
    /* ★ROS 桥接固定在 8770，页面可能由「任意」服务提供，所以不能拿 location.origin 当借口。
       原来的写法只在"页面由 CAN 桥接 8780 提供"时才指向 8770，一旦页面由别的端口提供
       （例如桌面版 exe 的静态服务 8800），请求就会打到那个端口去、全部 404，
       表现是仪表条一直是 `--`、诊断面板显示离线。这里统一指向 8770。 */
    var ROSBASE = ('http://127.0.0.1:' + PORT);

    function el(t, c, h) {
        var d = document.createElement(t);
        if (c) d.className = c;
        if (h !== undefined) d.innerHTML = h;
        return d;
    }
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
        var b = el('span', 'cx-livebadge', '<i></i>ROS LIVE');
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
        var u = ROSBASE + path;
        (function once() {
            fetch(u + (u.indexOf('?') < 0 ? '?' : '&') + 't=' + Date.now(), { cache: 'no-store' })
                .then(function (r) { return r.json(); })
                .then(fn)
                .catch(function () { try { fn(null); } catch (e) { } })
                .then(function () { window.setTimeout(once, ms); });
        })();
    }
    function page(id) { return document.getElementById(id); }
    function okBadge(node, ok) {
        if (!node) return;
        if (ok) { node.textContent = ok === true ? 'ROS 链路正常' : ok; node.style.color = ''; }
        else { node.textContent = 'ROS 未连接'; }
    }

    /* ------------------------------------------------------------------
       ★ 链路活性判据（关键）
       ------------------------------------------------------------------
       ros_bridge.py 的 ok 只表示「HTTP 服务在响应」，**不等于车机连着**。
       实测：拔掉车机网线后桥接仍返回 ok:true，但全部监控话题都
       TimeoutError（topics_online=0），且各话题带着几十分钟前的
       陈旧缓存值。所以「是否在线」必须看话题是不是真的在出数据。
       全局 LINK 由 /api/meta 轮询统一维护，各面板共用。           */
    var LINK = { known: false, ok: false, live: false, online: 0, watched: 0, master: '', meta: null };

    function updateLink(m) {
        if (!m || !m.ok) {
            LINK.known = true; LINK.ok = false; LINK.live = false; return false;
        }
        var w = m.topics_watched || 0, o = m.topics_online || 0;
        LINK.known = true; LINK.ok = true;
        LINK.online = o; LINK.watched = w;
        LINK.master = m.master || '';
        LINK.meta = m;
        /* ★优先采信桥接上报的 linked（是否真的连上过 ROS master）。
           只看 topics_online 有个漏洞：车机没接时桥接根本没订阅任何话题，
           topics_watched=0，会被下面那句"没监控话题就信任桥接"误判成在线。
           所以：有 linked 字段就以它为准（w=0 时视为未连接）；没有才退回旧判据。 */
        if (typeof m.linked === 'boolean') {
            LINK.live = m.linked ? (w > 0 ? (o > 0) : true) : false;
        } else {
            LINK.live = (w > 0) ? (o > 0) : true;
        }
        return LINK.live;
    }

    /* /api/vehicle 自带 topics 明细，用它独立判断一次 */
    function vehicleLive(v) {
        if (!v || !v.ok) return false;
        var ts = v.topics || {}, any = false, n = 0;
        for (var k in ts) { if (!Object.prototype.hasOwnProperty.call(ts, k)) continue; n++; if (ts[k] && ts[k].ok) any = true; }
        return n > 0 ? any : (LINK.known ? LINK.live : true);
    }

    /* 统一的状态文案 */
    function linkText() {
        if (!LINK.known) return '连接中…';
        if (!LINK.ok) return 'ROS 未连接';
        if (!LINK.live) return '车机未连接';
        return '链路正常';
    }

    /* ==================================================================
       ① 系统概览：ROS 链路状态条
       ================================================================== */
    function buildStrip() {
        var p = page('dashboard');
        if (!p || document.getElementById('cx-ros-strip')) return;
        var bar = el('div', 'cx-strip-live');
        bar.id = 'cx-ros-strip';
        bar.innerHTML =
            '<span class="cx-strip-live__i">ROS <b data-m>--</b></span>' +
            '<span class="cx-strip-live__i">话题 <em data-t>--</em></span>' +
            '<span class="cx-strip-live__i">节点 <b data-n>--</b></span>' +
            '<span class="cx-strip-live__i">服务 <b data-sv>--</b></span>' +
            '<span class="cx-strip-live__i">故障 <u data-f>--</u></span>' +
            '<span class="cx-strip-live__sp"></span>' +
            '<span class="cx-strip-live__i" data-st>连接中…</span>';
        p.insertBefore(bar, p.firstChild);

        // 顶部汇总：CAN 总线 + ROS 是否同时在
        poll('/api/meta', 1500, function (m) {
            updateLink(m);
            var stEl = bar.querySelector('[data-st]');
            if (!m || !m.ok) {
                stEl.textContent = 'ROS 未连接';
                stEl.style.color = '#E0574A';
                return;
            }
            bar.querySelector('[data-m]').textContent = (m.master || '').split(':')[0];
            bar.querySelector('[data-t]').textContent = m.topics_online + '/' + m.topics_watched;
            bar.querySelector('[data-n]').textContent = m.nodes;
            bar.querySelector('[data-sv]').textContent = m.services;
            bar.querySelector('[data-f]').textContent = m.fault_alarm;
            stEl.textContent = linkText();
            stEl.style.color = LINK.live ? '' : '#E0574A';
        });
    }

    /* ==================================================================
       ② 车辆信息管理：ROS 整车状态
       ================================================================== */
    function buildVehicle() {
        var p = page('vehicles');
        if (!p || document.getElementById('cx-ros-veh')) return;
        var card = el('div', 'card cx-live mb-6');
        card.id = 'cx-ros-veh';
        card.appendChild(head('ROS 整车状态（车机 · 网络直读）', 'MASTER <b data-m>--</b>'));
        var grid = el('div', 'cx-live__grid');
        card.appendChild(grid);

        var A = el('div', 'cx-live__box');
        A.appendChild(el('div', 'cx-live__boxhd', '<i></i>ATTITUDE · 姿态'));
        var rA = {};
        [['yaw', '航向角', '°', 2], ['pitch', '俯仰角', '°', 2], ['roll', '横滚角', '°', 2],
         ['yawstd', '航向标准差', '', 3]].forEach(function (x) {
            var r = row(x[1], x[2], x[3]); A.appendChild(r); rA[x[0]] = r;
        });
        grid.appendChild(A);

        var B = el('div', 'cx-live__box');
        B.appendChild(el('div', 'cx-live__boxhd', '<i></i>MOTION · 惯性'));
        var rB = {};
        [['ax', '加速度 X', 'g', 4], ['ay', '加速度 Y', 'g', 4], ['az', '加速度 Z', 'g', 4],
         ['gz', '角速度 Z', '°/s', 3]].forEach(function (x) {
            var r = row(x[1], x[2], x[3]); B.appendChild(r); rB[x[0]] = r;
        });
        grid.appendChild(B);

        var C = el('div', 'cx-live__box');
        C.appendChild(el('div', 'cx-live__boxhd', '<i></i>ODOMETRY · 里程定位'));
        var rC = {};
        [['x', '位置 X', 'm', 2], ['y', '位置 Y', 'm', 2], ['z', '位置 Z', 'm', 2],
         ['qw', '姿态 W', '', 4]].forEach(function (x) {
            var r = row(x[1], x[2], x[3]); C.appendChild(r); rC[x[0]] = r;
        });
        grid.appendChild(C);

        var D = el('div', 'cx-live__box');
        D.appendChild(el('div', 'cx-live__boxhd', '<i></i>CHASSIS · 底盘（ROS 侧）'));
        var rD = {};
        [['spd', '车速', 'km/h', 2], ['yawr', '横摆角速度', '°/s', 3],
         ['lac', '纵向加速度', 'g', 4], ['wfl', '轮速 FL', '', 2]].forEach(function (x) {
            var r = row(x[1], x[2], x[3]); D.appendChild(r); rD[x[0]] = r;
        });
        var warn = el('div', 'cx-live__warn is-info',
            '<i class="fa fa-info-circle"></i><span data-cw>底盘话题未在线，车速/档位请看 CAN 面板</span>');
        D.appendChild(warn);
        grid.appendChild(D);

        p.insertBefore(card, p.firstChild.nextSibling || p.firstChild);

        poll('/api/vehicle', 800, function (v) {
            if (!vehicleLive(v)) {
                card.classList.remove('is-ok'); card.classList.add('is-bad');
                card.querySelector('[data-s]').textContent =
                    (v && v.ok) ? '车机未连接（话题全静默）' : 'ROS 未连接';
                return;
            }
            card.classList.add('is-ok'); card.classList.remove('is-bad');
            card.querySelector('[data-s]').textContent = 'ROS 数据采集中';
            card.querySelector('[data-m]').textContent = v.master || '--';
            var a = v.attitude || {}, g = v.motion || {}, o = v.odom || {}, c = v.chassis || {};
            setRow(rA.yaw, a.yaw); setRow(rA.pitch, a.pitch); setRow(rA.roll, a.roll); setRow(rA.yawstd, a.yaw_std);
            setRow(rB.ax, g.ax); setRow(rB.ay, g.ay); setRow(rB.az, g.az); setRow(rB.gz, g.gz);
            setRow(rC.x, o.x); setRow(rC.y, o.y); setRow(rC.z, o.z); setRow(rC.qw, o.qw);
            setRow(rD.spd, c.speed); setRow(rD.yawr, c.yawrate); setRow(rD.lac, c.longacc);
            setRow(rD.wfl, c.wheel_fl);
            var cw = card.querySelector('[data-cw]');
            if (cw) cw.textContent = v.chassis_live
                ? '底盘话题在线，数据为车机 ROS 实际值'
                : '底盘话题未在线（chassis_live=false），车速/档位请看 CAN 面板';
        });
    }

    /* ==================================================================
       ③ 检测记录管理：ROS 故障诊断（真实 fault_info）
       ================================================================== */
    function buildFaults() {
        var p = page('detection');
        if (!p || document.getElementById('cx-ros-fault')) return;
        var card = el('div', 'card cx-live mb-6');
        card.id = 'cx-ros-fault';
        card.appendChild(head('ROS 故障诊断（车机 fault_info / fault_alarm）', '<span data-m>--</span>'));
        var wrap = el('div', '');
        card.appendChild(wrap);
        p.insertBefore(card, p.firstChild);

        var LV = ['正常', '1 级提示', '2 级告警', '3 级严重'];
        poll('/api/faults', 1500, function (d) {
            // 故障接口本身没有话题明细，靠全局 LINK 判断车机是否真的连着：
            // 桥接在、但车机网线拔了 —— 此时 events 是上一次的陈旧缓存，不能当实时故障展示
            if (!d || !d.ok || (LINK.known && LINK.ok && !LINK.live)) {
                card.classList.remove('is-ok'); card.classList.add('is-bad');
                var off = (d && d.ok);
                card.querySelector('[data-s]').textContent = off ? '车机未连接' : 'ROS 未连接';
                wrap.innerHTML = '<div class="cx-live__warn"><span>' +
                    (off ? '桥接进程正常，但车机未连接（话题全静默）—— 请检查车机网线 / ROS Master'
                         : 'ROS 桥接未启动（ros_bridge.py）') + '</span></div>';
                return;
            }
            card.classList.add('is-ok'); card.classList.remove('is-bad');
            card.querySelector('[data-s]').textContent = '故障流 ' + fmt(d.hz, 1) + ' Hz';
            card.querySelector('[data-m]').innerHTML =
                '告警等级 <em style="color:' + (d.level >= 2 ? '#E0574A' : '#2EE59D') + '">' +
                (LV[d.level] || d.level) + '</em> &nbsp;·&nbsp; 活动故障 <em>' + d.active + '</em>';

            var ev = d.events || [];
            var html = '<table class="cx-tbl"><thead><tr><th>等级</th><th>模块</th>' +
                '<th>故障码</th><th>描述</th><th>类型</th></tr></thead><tbody>';
            if (!ev.length) {
                html += '<tr><td colspan="5" style="color:#2EE59D">当前无故障事件</td></tr>';
            }
            ev.slice(0, 20).forEach(function (e) {
                var col = e.level >= 2 ? '#E0574A' : (e.level === 1 ? '#D4762A' : '#2EE59D');
                html += '<tr><td style="color:' + col + '">' + (LV[e.level] || e.level) + '</td>' +
                    '<td class="mono">' + (e.module || '--') + '</td>' +
                    '<td class="mono">' + (e.code !== undefined ? '0x' + Number(e.code).toString(16).toUpperCase() : '--') + '</td>' +
                    '<td>' + (e.msg || '--') + '</td>' +
                    '<td class="dim">' + (e.type || '--') + '</td></tr>';
            });
            html += '</tbody></table>';
            wrap.innerHTML = html;
        });
    }

    /* ==================================================================
       ④ 智能网联管理：ROS 传感器在线矩阵
       ================================================================== */
    function buildSensors() {
        var p = page('iot');
        if (!p || document.getElementById('cx-ros-sensor')) return;
        var card = el('div', 'card cx-live mb-6');
        card.id = 'cx-ros-sensor';
        card.appendChild(head('ROS 传感器与话题在线矩阵', '<span data-m>--</span>'));
        var grid = el('div', 'cx-live__grid');
        card.appendChild(grid);
        var boxG = el('div', 'cx-live__box');
        boxG.appendChild(el('div', 'cx-live__boxhd', '<i></i>GROUPS · 分组在线率'));
        var groupsWrap = el('div', '');
        boxG.appendChild(groupsWrap);
        grid.appendChild(boxG);
        var boxS = el('div', 'cx-live__box');
        boxS.appendChild(el('div', 'cx-live__boxhd', '<i></i>SILENT · 静默话题'));
        var silentWrap = el('div', '');
        boxS.appendChild(silentWrap);
        grid.appendChild(boxS);

        p.insertBefore(card, p.firstChild.nextSibling || p.firstChild);

        poll('/api/meta', 2000, function (m) {
            if (!m || !m.ok) {
                card.classList.remove('is-ok'); card.classList.add('is-bad');
                card.querySelector('[data-s]').textContent = 'ROS 未连接';
                return;
            }
            card.classList.add('is-ok'); card.classList.remove('is-bad');
            card.querySelector('[data-s]').textContent = 'ROS 数据采集中';
            card.querySelector('[data-m]').innerHTML =
                '话题 <b>' + m.topics_online + '/' + m.topics_watched + '</b> · 节点 <b>' + m.nodes +
                '</b> · 服务 <b>' + m.services + '</b> · master <b>' + (m.master || '--') + '</b>';

            var g = m.groups || {}, h = '';
            Object.keys(g).forEach(function (k) {
                var v = g[k] || {};
                var ok = v.ok === v.total && v.total > 0;
                var col = ok ? '#2EE59D' : (v.ok > 0 ? '#D4762A' : '#E0574A');
                h += '<div class="tr"><span class="k">' + k.toUpperCase() +
                    '</span><span class="d"></span><span class="v" style="color:' + col + '">' +
                    v.ok + ' / ' + v.total + '</span></div>';
            });
            groupsWrap.innerHTML = h || '<div class="dim">无分组数据</div>';

            var s = m.topics_silent || [];
            silentWrap.innerHTML = s.length
                ? s.map(function (t) {
                    return '<div class="tr"><span class="k mono" style="min-width:auto">' + t +
                        '</span><span class="d"></span><span class="v" style="color:#E0574A">静默</span></div>';
                }).join('')
                : '<div style="color:#2EE59D" class="dim">全部话题在线</div>';
        });
    }

    /* ==================================================================
       懒加载
       ================================================================== */
    var PAGES = {
        dashboard: buildStrip,
        vehicles: buildVehicle,
        detection: buildFaults,
        iot: buildSensors
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
        activate(activeId());
        if (!('MutationObserver' in window)) return;
        var mo = new MutationObserver(function (recs) {
            for (var i = 0; i < recs.length; i++) {
                var e = recs[i].target;
                if (e.classList && !e.classList.contains('hidden') &&
                    e.classList.contains('page-content')) activate(e.id);
            }
        });
        Array.prototype.forEach.call(document.querySelectorAll('.page-content'), function (p) {
            mo.observe(p, { attributes: true, attributeFilter: ['class'] });
        });
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
    else boot();
})();

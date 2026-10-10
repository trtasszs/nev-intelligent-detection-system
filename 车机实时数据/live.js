/* ============================================================================
   车机实时数据渲染（轮询 ros_bridge.py 的接口）
   原则：真实面板打 LIVE 标记；只更新发生变化的数值；变化提示是局部一次性变色
   面板按页签懒加载：切到哪一页才建哪一页的面板
   ========================================================================== */
(function () {
    'use strict';

    var PORT = 8770;
    var BASE = (location.protocol === 'http:' || location.protocol === 'https:')
        ? location.origin : ('http://127.0.0.1:' + PORT);

    var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* ---------------------------------------------------------------- 工具 */
    function el(tag, cls, html) {
        var d = document.createElement(tag);
        if (cls) d.className = cls;
        if (html !== undefined) d.innerHTML = html;
        return d;
    }
    function fmt(v, dec) {
        if (v === null || v === undefined || (typeof v === 'number' && isNaN(v))) return '--';
        if (typeof v !== 'number') return String(v);
        return v.toFixed(dec === undefined ? 2 : dec);
    }
    function pad(n) { return n < 10 ? '0' + n : String(n); }
    function dur(s) {
        s = Math.max(0, Math.round(s || 0));
        var m = Math.floor(s / 60), r = s % 60;
        return pad(m) + ':' + pad(r);
    }
    function hex4(n) { return '0x' + ('0000' + (Number(n) || 0).toString(16).toUpperCase()).slice(-4); }
    function hhmmss(ts) {
        if (!ts) return '--:--:--';
        var d = new Date(ts * 1000);
        return pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds());
    }
    function live(host, text) {
        var b = el('span', 'cx-livebadge', '<i></i>' + (text || 'LIVE'));
        if (host) host.appendChild(b);
        return b;
    }
    function poll(path, ms, fn) {
        var url = BASE + path + (path.indexOf('?') < 0 ? '?' : '&') + 't=';
        function once() {
            fetch(url + Date.now(), { cache: 'no-store' })
                .then(function (r) { return r.json(); })
                .then(fn)
                .catch(function () { try { fn(null); } catch (e) { } })
                .then(function () { window.setTimeout(once, ms); });
        }
        once();
    }
    function row(k, unit, dec) {
        var r = el('div', 'cx-row');
        r.appendChild(el('span', 'cx-row__k', k));
        var v = el('span', 'cx-row__v', '--' + (unit ? '<u>' + unit + '</u>' : ''));
        r.appendChild(v);
        r._dec = dec === undefined ? 2 : dec;
        r._v = v;
        return r;
    }
    function setRow(r, val) {
        if (!r || !r._v) return;
        var s = (val === null || val === undefined || isNaN(val)) ? '--' : Number(val).toFixed(r._dec);
        if (!r._v.firstChild) return;
        if (r._v.firstChild.nodeValue === s) return;
        r._v.firstChild.nodeValue = s;
        r._v.classList.add('is-tick');
        window.setTimeout(function () { r._v.classList.remove('is-tick'); }, 420);
    }
    function setBig(node, val, dec) {
        if (!node) return;
        var s = fmt(val, dec === undefined ? 2 : dec);
        if (node.textContent === s) return;
        node.textContent = s;
        node.classList.add('is-tick');
        window.setTimeout(function () { node.classList.remove('is-tick'); }, 420);
    }
    function head(title, sub) {
        var h = el('div', 'cx-live__head');
        var t = el('div', 'cx-live__title', '<span class="cx-live__dot"></span>' + title);
        h.appendChild(t);
        if (sub) h.appendChild(el('div', 'cx-live__meta', sub));
        return h;
    }
    function lvBadge(lv) {
        var n = Number(lv) || 0;
        var txt = n === 0 ? '无故障' : (n + ' 级');
        return '<span class="cx-lv cx-lv--' + Math.max(0, Math.min(3, n)) + '">' + txt + '</span>';
    }
    var GROUP_CN = {
        ins: '组合导航 INS', control: '整车控制 VCU', diag: '诊断 DIAG', tf: '坐标变换 TF',
        lidar: '激光雷达 LIDAR', camera: '相机 CAMERA', radar: '毫米波 RADAR',
        planning: '决策规划 PLANNING', other: '其他 OTHER'
    };

    /* ==================================================================
       ① 车辆信息管理：实时车况（已有）
       ================================================================== */
    function buildVehicles() {
        var box = document.getElementById('cx-live');
        if (!box) return null;
        box.className = 'card cx-live mb-6';
        box.innerHTML = '';

        var h = head('车机实时数据', 'ROS MASTER <b data-m>--</b>');
        h.querySelector('.cx-live__title').appendChild(el('span', 'cx-live__state', '连接中…'));
        box.appendChild(h);
        live(h.querySelector('.cx-live__title'));

        var grid = el('div', 'cx-live__grid');
        box.appendChild(grid);

        var attitude = el('div', 'cx-live__box');
        attitude.appendChild(el('div', 'cx-live__boxhd', '<i></i>ATTITUDE · 车辆姿态'));
        var big = el('div', 'cx-big'), cells = {};
        [['yaw', '航向角', '°'], ['pitch', '俯仰角', '°'], ['roll', '横滚角', '°']].forEach(function (c) {
            var d = el('div', 'cx-big__c');
            d.appendChild(el('div', 'cx-big__n', '--'));
            d.appendChild(el('div', 'cx-big__u', c[2]));
            d.appendChild(el('div', 'cx-big__l', c[1]));
            big.appendChild(d);
            cells[c[0]] = d.firstChild;
        });
        attitude.appendChild(big);
        var aRows = {};
        [['yaw_std', '航向精度', '°', 2], ['temp', 'INS 温度', '℃', 1], ['ins_status', 'INS 状态', '', 0],
         ['wheel_speed_status', '轮速源状态', '', 0], ['sow', 'GPS 周内秒', 's', 0]].forEach(function (r) {
            var x = row(r[1], r[2], r[3]); attitude.appendChild(x); aRows[r[0]] = x;
        });
        grid.appendChild(attitude);

        var motion = el('div', 'cx-live__box');
        motion.appendChild(el('div', 'cx-live__boxhd', '<i></i>MOTION · 运动传感器'));
        var mRows = {};
        [['ax', '纵向加速度', 'g', 4], ['ay', '横向加速度', 'g', 4], ['az', '垂向加速度', 'g', 4],
         ['gx', '角速度 X', '°/s', 3], ['gy', '角速度 Y', '°/s', 3], ['gz', '角速度 Z', '°/s', 3]
        ].forEach(function (r) {
            var x = row(r[1], r[2], r[3]);
            if (r[0] === 'az') { var b = el('div', 'cx-bar', '<i></i>'); x.appendChild(b); x._bar = b.firstChild; }
            motion.appendChild(x); mRows[r[0]] = x;
        });
        grid.appendChild(motion);

        var chassis = el('div', 'cx-live__box');
        chassis.appendChild(el('div', 'cx-live__boxhd', '<i></i>CHASSIS · 底盘状态'));
        var cRows = {};
        [['speed', '车速', 'km/h', 1], ['gear', '挡位', '', 0], ['epb', 'EPB 手刹', '', 0],
         ['cruise_sts', '巡航状态', '', 0], ['auto_mod', 'AUTO 模式', '', 0],
         ['acc_pedal', '油门踏板', '%', 1], ['brk_pedal', '刹车踏板', '%', 1],
         ['str_angle', '转向角', '°', 1], ['yawrate', '横摆角速度', '°/s', 2]].forEach(function (r) {
            var x = row(r[1], r[2], r[3]); chassis.appendChild(x); cRows[r[0]] = x;
        });
        var wheels = row('四轮轮速 FL/FR/RL/RR', 'km/h', 1); chassis.appendChild(wheels);
        var warn = el('div', 'cx-live__warn', '<i class="fa fa-exclamation-triangle"></i><span>底盘数据等待中</span>');
        chassis.appendChild(warn);
        grid.appendChild(chassis);

        var link = el('div', 'cx-live__box');
        link.appendChild(el('div', 'cx-live__boxhd', '<i></i>LINK · 话题链路'));
        var linkBody = el('div', '');
        link.appendChild(linkBody);
        grid.appendChild(link);

        box._refs = { state: h.querySelector('.cx-live__state'), master: h.querySelector('[data-m]'),
            cells: cells, aRows: aRows, mRows: mRows, cRows: cRows, wheels: wheels, warn: warn, link: linkBody };

        poll('/api/vehicle', 450, function (d) {
            var r = box._refs;
            if (!d || !d.ok) { box.classList.remove('is-ok'); box.classList.add('is-bad');
                r.state.textContent = '桥接服务未启动'; r.master.textContent = '--'; return; }
            var okAny = false, badAny = false;
            r.link.innerHTML = '';
            Object.keys(d.topics || {}).forEach(function (t) {
                var s = d.topics[t] || {};
                var L = el('div', 'cx-link' + (s.ok ? ' is-ok' : ' is-bad'));
                L.appendChild(el('span', 'cx-link__n', t));
                L.appendChild(el('span', 'cx-link__s', (s.hz !== undefined ? s.hz + ' Hz' : '--') +
                    ' · ' + (s.age != null ? Math.round(s.age * 1000) + ' ms' : '--') + (s.ok ? ' ✓' : ' ✗')));
                r.link.appendChild(L);
                if (s.ok) okAny = true; else badAny = true;
            });
            box.classList.toggle('is-ok', okAny && !badAny);
            box.classList.toggle('is-bad', !okAny);
            r.state.textContent = okAny ? (badAny ? '链路部分中断' : '实时采集中') : '链路中断';
            r.master.textContent = d.master || '--';

            var a = d.attitude || {};
            setBig(r.cells.yaw, a.yaw); setBig(r.cells.pitch, a.pitch); setBig(r.cells.roll, a.roll);
            setRow(r.aRows.yaw_std, a.yaw_std); setRow(r.aRows.temp, a.temp);
            setRow(r.aRows.ins_status, a.ins_status);
            setRow(r.aRows.wheel_speed_status, a.wheel_speed_status); setRow(r.aRows.sow, a.sow);

            var m = d.motion || {};
            ['ax', 'ay', 'az', 'gx', 'gy', 'gz'].forEach(function (k) { setRow(r.mRows[k], m[k]); });
            if (r.mRows.az._bar) {
                var pct = Math.max(0, Math.min(100, Math.abs(m.az || 0) * 100));
                r.mRows.az._bar.style.width = (pct / 2) + '%';
                r.mRows.az._bar.style.left = (50 - pct / 2) + '%';
                r.mRows.az._bar.style.background = Math.abs(m.az || 0) > 1.2 ? 'var(--cx-am)' : 'var(--cx-cy)';
            }
            var c = d.chassis || {};
            ['speed', 'gear', 'epb', 'cruise_sts', 'auto_mod', 'acc_pedal', 'brk_pedal',
             'str_angle', 'yawrate'].forEach(function (k) { setRow(r.cRows[k], c[k]); });
            var txt = [c.wheel_fl, c.wheel_fr, c.wheel_rl, c.wheel_rr]
                .map(function (v) { return (v == null) ? '--' : Number(v).toFixed(1); }).join(' / ');
            if (r.wheels._v.firstChild && r.wheels._v.firstChild.nodeValue !== txt)
                r.wheels._v.firstChild.nodeValue = txt;

            var liveOk = !!d.chassis_live;
            r.warn.className = 'cx-live__warn' + (liveOk ? ' is-ok' : '');
            r.warn.querySelector('span').textContent = liveOk
                ? '底盘数据已接入（VCU 正常上报）'
                : '底盘数据等待中：VCU 未上报实车数据（车速/挡位/EPB/巡航全为 0）';
        });
        return box;
    }

    /* ==================================================================
       ② 系统概览：车机实时状态带
       ================================================================== */
    function buildStatusbar() {
        var page = document.getElementById('dashboard');
        if (!page || page.querySelector('.cx-strip-live')) return null;
        var bar = el('div', 'cx-strip-live');
        bar.innerHTML =
            '<span class="cx-strip-live__i">车机 <b data-master>--</b></span>' +
            '<span class="cx-strip-live__i">故障 <span data-fault>--</span></span>' +
            '<span class="cx-strip-live__i">传感器 <em data-sensor>--</em></span>' +
            '<span class="cx-strip-live__i">静默 <u data-silent>--</u></span>' +
            '<span class="cx-strip-live__i">姿态 <b data-att>--</b></span>' +
            '<span class="cx-strip-live__sp"></span>' +
            '<span class="cx-strip-live__i" data-t>--:--:--</span>';
        page.insertBefore(bar, page.firstChild);

        poll('/api/meta', 1500, function (m) {
            if (!m || !m.ok) {
                bar.querySelector('[data-master]').textContent = '未连接';
                bar.querySelector('[data-sensor]').textContent = '--';
                bar.querySelector('[data-fault]').innerHTML = '<span class="cx-lv cx-lv--3">离线</span>';
                return;
            }
            bar.querySelector('[data-master]').textContent = m.master;
            bar.querySelector('[data-fault]').innerHTML = lvBadge(m.fault_level);
            bar.querySelector('[data-sensor]').innerHTML =
                '<em>' + m.topics_online + '</em>/' + m.topics_watched + ' 在线';
            bar.querySelector('[data-silent]').textContent = m.topics_silent.length + ' 个';
            bar.querySelector('[data-t]').textContent = m.server_time.slice(11);
        });
        poll('/api/vehicle', 1200, function (v) {
            if (!v || !v.ok) return;
            var a = v.attitude || {};
            bar.querySelector('[data-att]').innerHTML =
                'YAW <b>' + fmt(a.yaw, 1) + '°</b> · PITCH <b>' + fmt(a.pitch, 1) +
                '°</b> · ROLL <b>' + fmt(a.roll, 1) + '°</b>';
        });
        return bar;
    }

    /* ==================================================================
       ③ 检测记录管理：真实故障事件流
       ================================================================== */
    function buildFaultLog() {
        var page = document.getElementById('detection');
        if (!page || document.getElementById('cx-faultlog')) return null;
        var card = el('div', 'card cx-live mb-6');
        card.id = 'cx-faultlog';
        var h = head('车机实时故障', '<span data-meta>--</span>');
        live(h.querySelector('.cx-live__title'));
        card.appendChild(h);
        var wrap = el('div', '');
        card.appendChild(wrap);
        page.insertBefore(card, page.firstChild);

        poll('/api/faults', 1500, function (f) {
            if (!f || !f.ok) {
                card.classList.remove('is-ok'); card.classList.add('is-bad');
                wrap.innerHTML = '<div class="cx-live__warn"><i class="fa fa-plug"></i><span>桥接服务未启动</span></div>';
                return;
            }
            card.classList.toggle('is-ok', !(f.events || []).some(function (e) { return e.active; }));
            card.classList.toggle('is-bad', (f.events || []).some(function (e) { return e.active; }));
            var act = (f.events || []).filter(function (e) { return e.active; }).length;
            h.querySelector('[data-meta]').innerHTML =
                '模块等级 ' + lvBadge(f.level) + ' &nbsp;·&nbsp; 上报 ' + f.hz + ' Hz &nbsp;·&nbsp; 共 ' +
                (f.events || []).length + ' 条' + (act ? '（持续中 ' + act + '）' : '');

            var rows = (f.events || []);
            if (!rows.length) {
                wrap.innerHTML = '<div class="cx-live__warn is-ok"><i class="fa fa-check"></i>' +
                    '<span>当前无故障上报</span></div>';
                return;
            }
            // 诊断台惯用的列：故障源 / 故障码 / 描述 / 状态 / 首次发生 / 持续时长
            var html = '<table class="cx-tbl"><thead><tr>' +
                '<th>等级</th><th>故障源</th><th>故障码</th><th>故障描述</th>' +
                '<th>状态</th><th>首次观测</th><th>持续</th>' +
                '</tr></thead><tbody>';
            rows.forEach(function (e) {
                html += '<tr><td class="nw">' + lvBadge(e.level) + '</td>' +
                    '<td class="mono nw">' + (e.module || '--') + '</td>' +
                    '<td class="mono dim nw">' + hex4(e.code) + '</td>' +
                    '<td>' + (e.msg || '') + '</td>' +
                    '<td class="nw">' + (e.active
                        ? '<span style="color:var(--cx-rd)">● 持续中</span>'
                        : '<span class="dim">○ 已恢复</span>') + '</td>' +
                    '<td class="mono dim nw">' + hhmmss(e.first_seen) + '</td>' +
                    '<td class="mono nw">' + dur(e.duration) + '</td></tr>';
            });
            html += '</tbody></table>';
            wrap.innerHTML = html;
        });
        return card;
    }

    /* ==================================================================
       ④ 智能网联管理：真实定位 + 传感器在线矩阵
       ================================================================== */
    function buildIot() {
        var page = document.getElementById('iot');
        if (!page || document.getElementById('cx-iot')) return null;
        var card = el('div', 'card cx-live mb-6');
        card.id = 'cx-iot';
        var h = head('车载定位与传感器链路', 'ROS MASTER <b data-m>--</b>');
        live(h.querySelector('.cx-live__title'));
        card.appendChild(h);

        var grid = el('div', 'cx-locgrid');
        card.appendChild(grid);

        var loc = el('div', 'cx-live__box');
        loc.appendChild(el('div', 'cx-live__boxhd', '<i></i>LOCATION · 组合导航定位'));
        var lRows = {};
        [['lon', '经度', '°', 6], ['lat', '纬度', '°', 6], ['alt', '海拔', 'm', 2],
         ['yaw', '航向角', '°', 2], ['pitch', '俯仰角', '°', 2], ['roll', '横滚角', '°', 2],
         ['sow', 'GPS 周内秒', 's', 0], ['ins_status', '定位状态', '', 0],
         ['temp', 'INS 温度', '℃', 1]].forEach(function (r) {
            var x = row(r[1], r[2], r[3]); loc.appendChild(x); lRows[r[0]] = x;
        });
        grid.appendChild(loc);

        var odo = el('div', 'cx-live__box');
        odo.appendChild(el('div', 'cx-live__boxhd', '<i></i>ODOMETRY · 里程计位姿'));
        var oRows = {};
        [['x', '位置 X', 'm', 3], ['y', '位置 Y', 'm', 3], ['z', '位置 Z', 'm', 3],
         ['qx', '四元数 X', '', 4], ['qy', '四元数 Y', '', 4], ['qz', '四元数 Z', '', 4],
         ['qw', '四元数 W', '', 4], ['frame', '定位帧号', '', 0]].forEach(function (r) {
            var x = row(r[1], r[2], r[3]); odo.appendChild(x); oRows[r[0]] = x;
        });
        grid.appendChild(odo);

        var sens = el('div', 'cx-live__box');
        sens.appendChild(el('div', 'cx-live__boxhd', '<i></i>SENSORS · 传感器在线矩阵'));
        var sensBody = el('div', 'cx-sensors');
        sens.appendChild(sensBody);
        grid.appendChild(sens);
        page.insertBefore(card, page.firstChild);

        poll('/api/vehicle', 900, function (d) {
            if (!d || !d.ok) return;
            h.querySelector('[data-m]').textContent = d.master || '--';
            var a = d.attitude || {}, o = d.odom || {};
            setRow(lRows.lon, a.lon); setRow(lRows.lat, a.lat); setRow(lRows.alt, a.altitude);
            setRow(lRows.yaw, a.yaw); setRow(lRows.pitch, a.pitch); setRow(lRows.roll, a.roll);
            setRow(lRows.sow, a.sow); setRow(lRows.ins_status, a.ins_status); setRow(lRows.temp, a.temp);
            setRow(oRows.x, o.x); setRow(oRows.y, o.y); setRow(oRows.z, o.z);
            setRow(oRows.qx, o.qx); setRow(oRows.qy, o.qy); setRow(oRows.qz, o.qz); setRow(oRows.qw, o.qw);
            setRow(oRows.frame, o.frame);
        });

        poll('/api/meta', 2500, function (m) {
            if (!m || !m.ok) { sensBody.innerHTML = '<div class="cx-live__warn"><span>桥接服务未启动</span></div>'; return; }
            sensBody.innerHTML = '';
            Object.keys(m.groups || {}).forEach(function (g) {
                var d = m.groups[g];
                var cls = d.ok === d.total ? 'is-ok' : (d.ok === 0 ? 'is-bad' : 'is-part');
                var s = el('div', 'cx-sensor ' + cls);
                var hd = el('div', 'cx-sensor__h');
                hd.appendChild(el('span', 'cx-sensor__n', GROUP_CN[g] || g.toUpperCase()));
                hd.appendChild(el('span', 'cx-sensor__r', d.ok + '/' + d.total));
                s.appendChild(hd);
                var rows = el('div', 'cx-sensor__t');
                d.topics.forEach(function (t) {
                    var r = el('div', 'cx-sensor__row ' + (t.ok ? 'ok' : 'bad'));
                    r.appendChild(el('span', '', t.name));
                    r.appendChild(el('span', '', t.ok ? (t.hz + ' Hz') : '无数据'));
                    rows.appendChild(r);
                });
                s.appendChild(rows);
                sensBody.appendChild(s);
            });
        });
        return card;
    }

    /* ==================================================================
       ⑤ 通信协议及数据导入：真实话题矩阵
       ================================================================== */
    function buildTopics() {
        var page = document.getElementById('protocol');
        if (!page || document.getElementById('cx-topics')) return null;
        var card = el('div', 'card cx-live mb-6');
        card.id = 'cx-topics';
        var h = head('车机真实 ROS 通信矩阵', '<span data-meta>--</span>');
        live(h.querySelector('.cx-live__title'));
        card.appendChild(h);

        var bar = el('div', 'flex items-center justify-between mb-3');
        var filters = el('div', 'cx-filters');
        var modes = [['all', '全部'], ['watched', '已订阅'], ['ok', '在线'], ['silent', '静默']];
        modes.forEach(function (m) {
            var b = el('button', m[0] === 'all' ? 'on' : '', m[1]);
            b.setAttribute('data-mode', m[0]);
            b.addEventListener('click', function () {
                Array.prototype.forEach.call(filters.children, function (x) { x.classList.remove('on'); });
                b.classList.add('on');
                state.mode = m[0];
                renderList();
            });
            filters.appendChild(b);
        });
        bar.appendChild(filters);
        bar.appendChild(el('div', 'cx-live__meta', '<span data-count>--</span>'));
        card.appendChild(bar);

        var tblWrap = el('div', '');
        card.appendChild(tblWrap);
        page.insertBefore(card, page.firstChild);

        var state = { mode: 'all', topics: [] };

        function renderList() {
            var list = state.topics.filter(function (t) {
                if (state.mode === 'watched') return t.watched;
                if (state.mode === 'ok') return t.watched && t.ok;
                if (state.mode === 'silent') return t.watched && !t.ok;
                return true;
            });
            var html = '<table class="cx-tbl"><thead><tr><th>话题</th><th>消息类型</th><th>发布节点</th>' +
                '<th>状态</th><th>频率</th><th>延迟</th><th>大小</th></tr></thead><tbody>';
            list.forEach(function (t) {
                var st, cls = '';
                if (!t.watched) { st = '<span class="dim">未监视</span>'; }
                else if (t.ok) { st = '<span style="color:var(--cx-gr)">在线</span>'; }
                else { st = '<span style="color:var(--cx-rd)">静默</span>'; cls = ' dim'; }
                html += '<tr class="clickable" data-topic="' + t.name + '">' +
                    '<td class="mono nw">' + t.name + '</td>' +
                    '<td class="mono dim nw">' + t.type + '</td>' +
                    '<td class="mono dim nw">' + (t.pubs && t.pubs.length ? t.pubs.join(', ') : '--') + '</td>' +
                    '<td class="nw">' + st + '</td>' +
                    '<td class="mono nw">' + (t.hz != null ? t.hz + ' Hz' : '--') + '</td>' +
                    '<td class="mono dim nw">' + (t.age != null ? Math.round(t.age * 1000) + ' ms' : '--') + '</td>' +
                    '<td class="mono dim nw">' + (t.bytes != null ? (t.bytes > 1024 ? (t.bytes / 1024).toFixed(1) + ' KB' : t.bytes + ' B') : '--') + '</td>' +
                    '</tr>';
            });
            html += '</tbody></table>';
            tblWrap.innerHTML = html;
            card.querySelector('[data-count]').textContent = list.length + ' / ' + state.topics.length + ' 个话题';

            Array.prototype.forEach.call(tblWrap.querySelectorAll('tr[data-topic]'), function (tr) {
                tr.addEventListener('click', function () { showDetail(tr, tr.getAttribute('data-topic')); });
            });
        }

        function showDetail(tr, name) {
            var nxt = tr.nextSibling;
            if (nxt && nxt.classList && nxt.classList.contains('cx-detailrow')) {
                nxt.parentNode.removeChild(nxt); return;
            }
            var dtr = el('tr', 'cx-detailrow');
            var td = el('td'); td.colSpan = 7;
            td.innerHTML = '<div class="cx-detail"><div class="cx-detail__t">载入中…</div></div>';
            dtr.appendChild(td);
            tr.parentNode.insertBefore(dtr, tr.nextSibling);

            fetch(BASE + '/api/topic?name=' + encodeURIComponent(name) + '&t=' + Date.now())
                .then(function (r) { return r.json(); })
                .then(function (d) {
                    if (!d || !d.ok) {
                        td.querySelector('.cx-detail').innerHTML =
                            '<div class="cx-detail__t">该话题未被监视，无字段结构（' + name + '）</div>';
                        return;
                    }
                    var box = td.querySelector('.cx-detail');
                    var fhtml = '<div class="cx-detail__cols">';
                    (d.fields || []).forEach(function (f) {
                        var v = f.name.split('.').reduce(function (o, k) { return (o == null ? o : o[k]); }, d.sample);
                        var vs = (v === undefined || v === null) ? '' :
                            (typeof v === 'number' ? (+v.toFixed(4)) : (typeof v === 'object' ? '[…]' : String(v)));
                        fhtml += '<div class="cx-detail__f"><em>' + f.type + f.array + ' ' + f.name +
                            '</em><span>' + vs + '</span></div>';
                    });
                    fhtml += '</div>';
                    box.innerHTML = '<div class="cx-detail__t">' + d.name + ' · ' + d.type +
                        ' · ' + d.group + ' · ' + d.hz + ' Hz · ' + d.frames + ' 帧 · 最近 ' + d.bytes +
                        ' B · 峰值 ' + d.max_bytes + ' B · ' + (d.fields || []).length + ' 个字段</div>' + fhtml;
                })
                .catch(function () { });
        }

        poll('/api/topics', 3000, function (d) {
            if (!d || !d.ok) {
                card.classList.remove('is-ok'); card.classList.add('is-bad');
                tblWrap.innerHTML = '<div class="cx-live__warn"><span>桥接服务未启动</span></div>';
                return;
            }
            card.classList.add('is-ok');
            state.topics = d.topics || [];
            var on = state.topics.filter(function (t) { return t.watched && t.ok; }).length;
            card.querySelector('[data-meta]').textContent =
                '共 ' + d.count + ' 个话题 · ' + on + ' 个在线监视中 · 清单刷新 ' + d.inventory_age + 's 前';
            renderList();
        });
        return card;
    }

    /* ==================================================================
       ⑥ 数据分析：真实遥测曲线
       ================================================================== */
    function buildTelemetry() {
        var page = document.getElementById('statistics');
        if (!page || document.getElementById('cx-telemetry')) return null;
        if (typeof Chart === 'undefined') return null;

        var card = el('div', 'card cx-live mb-6');
        card.id = 'cx-telemetry';
        var h = head('车机实时遥测曲线', '<span data-meta>--</span>');
        live(h.querySelector('.cx-live__title'));
        card.appendChild(h);

        var grid = el('div', 'cx-charts');
        var defs = [
            { id: 'cx-ch-att', title: 'ATTITUDE · 姿态角', keys: [['yaw', '航向角', '#38E1FF'], ['pitch', '俯仰角', '#2CE59A'], ['roll', '横滚角', '#FFB020']] },
            { id: 'cx-ch-acc', title: 'ACCEL · 三轴加速度 (g)', keys: [['ax', '纵向', '#38E1FF'], ['ay', '横向', '#2CE59A'], ['az', '垂向', '#FF5470']] },
            { id: 'cx-ch-gyro', title: 'GYRO · 三轴角速度 (°/s)', keys: [['gx', 'X', '#38E1FF'], ['gy', 'Y', '#2CE59A'], ['gz', 'Z', '#FFB020']] },
            { id: 'cx-ch-temp', title: 'INS TEMP · 温度 (℃)', keys: [['temp', '温度', '#FFB020']] }
        ];
        var charts = {};
        defs.forEach(function (d) {
            var box = el('div', 'cx-chartbox');
            box.appendChild(el('div', 'cx-chartbox__h', '<span>' + d.title + '</span><span data-cur>--</span>'));
            var cv = document.createElement('canvas');
            box.appendChild(cv);
            grid.appendChild(box);
            charts[d.id] = {
                chart: new Chart(cv.getContext('2d'), {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: d.keys.map(function (k) {
                            return { label: k[1], data: [], borderColor: k[2], borderWidth: 1.4,
                                     pointRadius: 0, tension: .35, fill: false };
                        })
                    },
                    options: {
                        responsive: true, maintainAspectRatio: false, animation: false,
                        interaction: { intersect: false, mode: 'index' },
                        plugins: { legend: { labels: { color: '#8FA6BE', font: { size: 10 }, boxWidth: 10, padding: 8 } } },
                        scales: {
                            x: { display: false },
                            y: { ticks: { color: '#5A6E86', font: { size: 9 }, maxTicksLimit: 5 },
                                 grid: { color: 'rgba(120,200,255,.07)' } }
                        }
                    }
                }),
                box: box, keys: d.keys.map(function (k) { return k[0]; })
            };
        });
        card.appendChild(grid);
        page.insertBefore(card, page.firstChild);

        poll('/api/series', 2000, function (d) {
            if (!d || !d.ok) return;
            card.classList.toggle('is-ok', (d.t || []).length > 0);
            card.classList.toggle('is-bad', !(d.t || []).length);
            var n = (d.t || []).length;
            card.querySelector('[data-meta]').textContent =
                n + ' 个采样点 · ' + d.hz + ' Hz · 窗口约 ' + Math.round(n / d.hz) + ' 秒';
            Object.keys(charts).forEach(function (id) {
                var c = charts[id];
                var labels = (d.t || []).map(function (t) { return hhmmss(t); });
                c.chart.data.labels = labels;
                c.chart.data.datasets.forEach(function (ds, i) {
                    ds.data = (d.series[c.keys[i]] || []);
                });
                c.chart.update('none');
                var last = c.chart.data.datasets.map(function (ds) {
                    var a = ds.data; return a.length ? (+a[a.length - 1]).toFixed(2) : '--';
                }).join(' / ');
                c.box.querySelector('[data-cur]').textContent = last;
            });
        });
        return card;
    }

    /* ==================================================================
       ⑦ 系统设置：桥接服务配置
       ================================================================== */
    function buildBridge() {
        var page = document.getElementById('settings');
        if (!page || document.getElementById('cx-bridge')) return null;
        var card = el('div', 'card cx-live mb-6');
        card.id = 'cx-bridge';
        var h = head('车机数据桥接服务', '<span data-meta>--</span>');
        live(h.querySelector('.cx-live__title'));
        card.appendChild(h);
        var body = el('div', '');
        card.appendChild(body);
        page.insertBefore(card, page.firstChild);

        var eps = ['/api/vehicle', '/api/faults', '/api/topics', '/api/topic?name=<话题>',
                   '/api/nodes', '/api/series', '/api/meta'];
        poll('/api/meta', 2000, function (m) {
            if (!m || !m.ok) {
                card.classList.remove('is-ok'); card.classList.add('is-bad');
                body.innerHTML = '<div class="cx-live__warn"><i class="fa fa-plug"></i>' +
                    '<span>桥接服务未启动。启动命令：<code>python ros_bridge.py --open</code></span></div>';
                return;
            }
            card.classList.add('is-ok');
            h.querySelector('[data-meta]').textContent = '运行 ' + Math.round(m.uptime_s) + ' 秒';
            var rows = [
                ['ROS Master', m.master],
                ['本机接口地址', BASE],
                ['话题总数', m.topics_total + ' 个'],
                ['已订阅监视', m.topics_watched + ' 个（在线 ' + m.topics_online + ' 个）'],
                ['静默话题', m.topics_silent.length + ' 个'],
                ['ROS 节点', m.nodes + ' 个'],
                ['ROS 服务', m.services + ' 个'],
                ['当前故障等级', String(m.fault_level)],
                ['底盘 VCU 上报', m.chassis_live ? '已接入' : '未上报'],
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
        return card;
    }

    /* ==================================================================
       面板注册与页签懒加载
       ================================================================== */
    var PAGES = {
        dashboard: buildStatusbar,
        vehicles: buildVehicles,
        detection: buildFaultLog,
        iot: buildIot,
        protocol: buildTopics,
        statistics: buildTelemetry,
        settings: buildBridge
    };
    var built = {};

    function activate(pageId) {
        if (!pageId || built[pageId] || !PAGES[pageId]) return;
        built[pageId] = true;
        try { PAGES[pageId](); } catch (e) { built[pageId] = false; }
    }
    function activePageId() {
        var p = document.querySelector('.page-content:not(.hidden)');
        return p ? p.id : null;
    }

    function initSwitch() {
        activate(activePageId());
        if (!('MutationObserver' in window)) return;
        var mo = new MutationObserver(function (recs) {
            for (var i = 0; i < recs.length; i++) {
                var el2 = recs[i].target;
                if (el2.classList && !el2.classList.contains('hidden') &&
                    el2.classList.contains('page-content')) { activate(el2.id); }
            }
        });
        Array.prototype.forEach.call(document.querySelectorAll('.page-content'), function (p) {
            mo.observe(p, { attributes: true, attributeFilter: ['class'] });
        });
    }

    function boot() {
        if (document.documentElement.dataset.cxLiveBooted) return;
        document.documentElement.dataset.cxLiveBooted = '1';
        initSwitch();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})();

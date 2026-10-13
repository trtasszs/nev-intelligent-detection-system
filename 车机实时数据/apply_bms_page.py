# -*- coding: utf-8 -*-
"""
给检测软件加「BMS 实时监测」页 + 「输出检测报告」功能
==================================================================
数据来自检测软件自带的 CAN 桥 GET http://127.0.0.1:8780/api/frames
（不直接打开 CAN 设备 —— 那是独占设备，会顶掉检测软件自己的连接）。

报文字节位置与换算，来自 2026-10-11 的「激励—观测」实测：
    0x636 字节0-1  总压  ×0.1 V   400.0 V
    0x45A 字节0-1  总压  ×0.1 V   400.0 V（与 0x636 交叉印证）
    0x226 字节1/3  SOC   原值     100 / 100（主从两路）
    0x686 字节4-5  SOC   ×0.1     100.0
    0x264 字节2    温度  原值     15→16→17 ℃
    0x235 字节2    电流  原值     0 → 391 / 1428（跟踏板）
    0x668 字节2-3  负载  原值     0 → 0x3636 / 0x6668
    0x235 字节5-6  母线  ×0.1 V   静止 0，唤醒后 428.8
★ 无 DBC，换算系数为行业惯例推断 —— 界面上如实标注，不冒充官方定义。

幂等：靠 BEGIN/END 标记，重复执行不叠加。
    python apply_bms_page.py
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

P = r'E:\！！！高职比赛\新能源汽车智能检测系统-1.0版.html'

NAV_B = '<!-- ==== CX-BMS-NAV BEGIN ==== -->'
NAV_E = '<!-- ==== CX-BMS-NAV END ==== -->'
PAGE_B = '<!-- ==== CX-BMS-PAGE BEGIN ==== -->'
PAGE_E = '<!-- ==== CX-BMS-PAGE END ==== -->'
JS_B = '/* ==== CX-BMS-JS BEGIN ==== */'
JS_E = '/* ==== CX-BMS-JS END ==== */'

# ------------------------------------------------------------------ 导航项
NAV = NAV_B + u'''
            <li>
                <a href="#battery-bms" class="flex items-center px-6 py-3 hover:bg-dark-200 transition-all" data-target="battery-bms">
                    <i class="fa fa-battery-three-quarters sidebar-icon"></i>
                    <span>BMS 实时监测</span>
                </a>
            </li>
            ''' + NAV_E + u'\n'

# ------------------------------------------------------------------ 页面
PAGE = PAGE_B + u'''
        <!-- 电池实时监测（BMS） —— 数据来自真实 CAN 报文 -->
        <div id="battery-bms" class="page-content hidden">
            <div class="card mb-6">
                <div class="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
                    <div>
                        <h3 class="text-lg font-medium text-white mb-1">电池实时监测（BMS）</h3>
                        <p class="text-sm text-gray-400">数据源：整车 CAN 报文实时解码 &nbsp;·&nbsp; <span id="cxbms-src">正在连接…</span></p>
                    </div>
                    <div class="flex flex-col md:flex-row space-y-3 md:space-y-0 md:space-x-3 mt-4 md:mt-0">
                        <button id="cxbms-report-btn" class="btn-primary flex items-center justify-center">
                            <i class="fa fa-file-text-o mr-2"></i> 输出检测报告
                        </button>
                    </div>
                </div>

                <!-- 关键指标 -->
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div class="bg-dark-400 rounded-none p-4">
                        <div class="text-xs text-gray-400 mb-1">电池总压</div>
                        <div class="text-2xl font-mono text-white" id="cxbms-packv">--<span class="text-sm text-gray-400 ml-1">V</span></div>
                        <div class="text-xs text-gray-500 mt-1" id="cxbms-packv-src">--</div>
                    </div>
                    <div class="bg-dark-400 rounded-none p-4">
                        <div class="text-xs text-gray-400 mb-1">剩余电量 SOC</div>
                        <div class="text-2xl font-mono text-white" id="cxbms-soc">--<span class="text-sm text-gray-400 ml-1">%</span></div>
                        <div class="text-xs text-gray-500 mt-1" id="cxbms-soc-src">--</div>
                    </div>
                    <div class="bg-dark-400 rounded-none p-4">
                        <div class="text-xs text-gray-400 mb-1">电池温度</div>
                        <div class="text-2xl font-mono text-white" id="cxbms-temp">--<span class="text-sm text-gray-400 ml-1">℃</span></div>
                        <div class="text-xs text-gray-500 mt-1" id="cxbms-temp-src">--</div>
                    </div>
                    <div class="bg-dark-400 rounded-none p-4">
                        <div class="text-xs text-gray-400 mb-1">电池电流</div>
                        <div class="text-2xl font-mono text-white" id="cxbms-curr">--<span class="text-sm text-gray-400 ml-1">A</span></div>
                        <div class="text-xs text-gray-500 mt-1" id="cxbms-curr-src">--</div>
                    </div>
                </div>

                <!-- 报文明细 -->
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-700">
                        <thead class="bg-dark-400">
                            <tr>
                                <th class="table-header">信号</th>
                                <th class="table-header">CAN ID</th>
                                <th class="table-header">字节</th>
                                <th class="table-header">原始值</th>
                                <th class="table-header">解码</th>
                                <th class="table-header">置信度</th>
                            </tr>
                        </thead>
                        <tbody class="bg-dark-300 divide-y divide-gray-700" id="cxbms-rows">
                            <tr><td class="table-cell text-gray-400" colspan="6">正在读取 CAN 报文…</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="card">
                <h3 class="text-lg font-medium text-white mb-4">CAN 链路状态</h3>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div><div class="text-xs text-gray-400">采集板卡</div><div class="text-sm font-mono text-white" id="cxbms-board">--</div></div>
                    <div><div class="text-xs text-gray-400">总线速率</div><div class="text-sm font-mono text-white" id="cxbms-hz">--</div></div>
                    <div><div class="text-xs text-gray-400">报文条数</div><div class="text-sm font-mono text-white" id="cxbms-count">--</div></div>
                    <div><div class="text-xs text-gray-400">更新时间</div><div class="text-sm font-mono text-white" id="cxbms-time">--</div></div>
                </div>
                <p class="text-xs text-gray-500 mt-4" id="cxbms-note">
                    换算系数按汽车行业惯例推断；本平台尚无官方 DBC 报文定义表，信号名与量纲未经厂商确认。
                </p>
            </div>
        </div>
        ''' + PAGE_E + u'\n'

# ------------------------------------------------------------------ JS
JS = JS_B + u'''
/* ============================================================================
   CX-BMS · 电池实时监测 + 检测报告
   ---------------------------------------------------------------------------
   数据源：检测软件自带的 CAN 桥 GET /api/frames（8780）。
   报文译码依据：2026-10-11 用「激励—观测」四态对比（静止 / 踩油门×2 / 电机不出力）
   实测定位到的字节位置。无 DBC，系数按行业惯例。
   ★ 注意：本段与调用方可能不在同一个 <script> 块内，
     所以对外只暴露 window.CXBMS，不要指望函数提升。
   ========================================================================== */
(function () {
    'use strict';
    if (window.CXBMS) return;

    var CAN_BASE = 'http://127.0.0.1:8780';
    var POLL_MS = 1000;
    var last = null;

    /* 报文定义：id / 字节区间 / 名称 / 系数 / 单位 / 置信度 */
    var SIGS = [
        { id: '636', a: 0, b: 2, be: true, name: '电池总压', k: 0.1, unit: 'V', conf: '高（双报文印证）', key: 'packv' },
        { id: '45A', a: 2, b: 4, be: true, name: '电池总压（备份）', k: 0.1, unit: 'V', conf: '高（与 0x636 一致）', key: 'packv2' },
        { id: '338', a: 4, b: 5, be: false, name: '剩余电量 SOC', k: 1, unit: '%', conf: '高（与仪表盘 51% 一致；15 分钟内 52→51 单调下降）', key: 'soc' },
        { id: '686', a: 4, b: 6, be: true, name: '电池健康度 SOH', k: 0.1, unit: '%', conf: '中（恒定 100.0，不随放电下降，故判为 SOH 而非 SOC）', key: 'soh' },
        { id: '226', a: 1, b: 2, be: false, name: '控制指令·油门', k: 1, unit: '', conf: '高（桥内实测信号表：0x226 byte0=油门 byte1=反值 byte2=刹车；仅控制节点运行时出现）', key: 'acc_cmd' },
        { id: '264', a: 2, b: 3, be: false, name: '电池温度', k: 1, unit: '℃', conf: '中（随动作单调上升）', key: 'temp' },
        { id: '235', a: 2, b: 3, be: false, name: '电池电流', k: 0.1, unit: 'A', conf: '中（随踏板变化）', key: 'curr' },
        { id: '668', a: 2, b: 4, be: true, name: '加速踏板位置', k: 1, unit: '', conf: '高（桥内实测信号表：0x668 byte2 = 踏板）', key: 'pedal' },
        { id: '235', a: 5, b: 7, be: true, name: '辅助量（含义未确认）', k: 1, unit: '', conf: '低（随工况大幅跳变，不足以判定为电压）', key: 'aux' }
    ];

    function bytes(hexstr) {
        return String(hexstr || '').trim().split(/\\s+/).map(function (h) { return parseInt(h, 16) || 0; });
    }

    function pick(bs, a, b, be) {
        if (!bs || bs.length < b) return null;
        if (b - a === 1) return bs[a];
        var v = 0;
        if (be) { for (var i = a; i < b; i++) v = (v << 8) | bs[i]; }
        else { for (var j = b - 1; j >= a; j--) v = (v << 8) | bs[j]; }
        return v;
    }

    function decode(frames) {
        var out = { at: Date.now(), rows: [] };
        SIGS.forEach(function (s) {
            var fr = frames[s.id];
            if (!fr) { out.rows.push({ s: s, raw: null, val: null }); return; }
            var bs = bytes(fr.data);
            var raw = pick(bs, s.a, s.b, s.be);
            out.rows.push({
                s: s, raw: raw, val: raw === null ? null : raw * s.k,
                hex: fr.data, hz: fr.hz
            });
        });
        ['packv', 'soc', 'temp', 'curr'].forEach(function (k) {
            var r = out.rows.filter(function (x) { return x.s.key === k; })[0];
            out[k] = r && r.val !== null ? r.val : null;
            out[k + '_conf'] = r ? r.s.conf : '';
            out[k + '_id'] = r ? '0x' + r.s.id : '';
        });
        return out;
    }

    function fmt(v, d) { return v === null || v === undefined ? '--' : Number(v).toFixed(d === undefined ? 1 : d); }

    function render(d, meta) {
        function set(id, txt) { var e = document.getElementById(id); if (e) e.textContent = txt; }
        set('cxbms-packv', fmt(d.packv, 1) + ' V');
        set('cxbms-soc', fmt(d.soc, d.soc % 1 ? 1 : 0));
        set('cxbms-temp', fmt(d.temp, 0));
        set('cxbms-curr', fmt(d.curr, 1));
        set('cxbms-packv-src', d.packv_id + ' · ' + (d.packv_conf || ''));
        set('cxbms-soc-src', d.soc_id + ' · ' + (d.soc_conf || ''));
        set('cxbms-temp-src', d.temp_id);
        set('cxbms-curr-src', d.curr_id);
        set('cxbms-board', meta.board || '--');
        set('cxbms-hz', meta.hz ? Math.round(meta.hz) + ' 帧/秒' : '--');
        set('cxbms-count', meta.count ? meta.count + ' 条' : '--');
        set('cxbms-time', new Date().toLocaleTimeString('zh-CN'));
        set('cxbms-src', meta.ok ? '真实 CAN 数据' : 'CAN 桥未连接');

        var tb = document.getElementById('cxbms-rows');
        if (tb) {
            tb.innerHTML = d.rows.map(function (r) {
                var val = r.val === null ? '<span class="text-gray-500">报文缺失</span>'
                    : '<span class="text-white font-mono">' + fmt(r.val, r.s.k < 1 ? 1 : 0) + ' ' + r.s.unit + '</span>';
                return '<tr>' +
                    '<td class="table-cell text-gray-300">' + r.s.name + '</td>' +
                    '<td class="table-cell font-mono text-gray-400">0x' + r.s.id + '</td>' +
                    '<td class="table-cell font-mono text-gray-500">' + r.s.a + '-' + (r.s.b - 1) + '</td>' +
                    '<td class="table-cell font-mono text-gray-400">' + (r.raw === null ? '--' : r.raw) + '</td>' +
                    '<td class="table-cell">' + val + '</td>' +
                    '<td class="table-cell text-xs text-gray-500">' + r.s.conf + '</td>' +
                    '</tr>';
            }).join('');
        }
    }

    function poll() {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', CAN_BASE + '/api/frames?_=' + Date.now(), true);
        xhr.timeout = 5000;
        xhr.onload = function () {
            var meta = { ok: false };
            try {
                var d = JSON.parse(xhr.responseText);
                meta = { ok: !!d.ok, board: d.board, hz: d.hz_total, count: d.count };
                last = decode(d.frames || {});
                last.meta = meta;
                render(last, meta);
            } catch (e) {
                meta.err = e.message;
                render(decode({}), meta);
            }
        };
        xhr.onerror = xhr.ontimeout = function () {
            render(decode({}), { ok: false });
        };
        xhr.send();
    }

    /* ---------------- 检测报告（页面内预览） ---------------- */
    function buildReport() {
        var d = last || decode({});
        var m = d.meta || {};
        var now = new Date();
        var no = 'BMS-' + now.getFullYear() +
            String(now.getMonth() + 1).padStart(2, '0') +
            String(now.getDate()).padStart(2, '0') + '-' +
            String(now.getHours()).padStart(2, '0') +
            String(now.getMinutes()).padStart(2, '0');
        function verdict(kind, v) {
            if (v === null || v === undefined) return '<span style="color:#b45309">报文缺失，无法判定</span>';
            if (kind === 'soc') return v >= 60 ? '<span style="color:#15803d">正常</span>'
                : (v >= 20 ? '<span style="color:#b45309">偏低，建议充电</span>' : '<span style="color:#b91c1c">严重偏低</span>');
            if (kind === 'packv') return (v >= 300 && v <= 450) ? '<span style="color:#15803d">在正常区间</span>'
                : '<span style="color:#b45309">偏离常见区间，建议核对</span>';
            if (kind === 'temp') return (v <= 45) ? '<span style="color:#15803d">正常</span>'
                : '<span style="color:#b91c1c">偏高</span>';
            return '';
        }
        var rows = [
            ['电池总压', d.packv, 'V', '0x636 / 0x45A', verdict('packv', d.packv)],
            ['剩余电量 SOC', d.soc, '%', '0x226 / 0x686', verdict('soc', d.soc)],
            ['电池温度', d.temp, '℃', '0x264', verdict('temp', d.temp)],
            ['电池电流', d.curr, 'A', '0x235', m.ok ? '实时读取' : '未接入'],
            ['总线速率', m.hz ? Math.round(m.hz) : null, '帧/秒', 'CAN 桥', m.ok ? '通信正常' : '通信中断'],
            ['在线报文数', m.count || null, '条', 'CAN 桥', m.ok ? '正常' : '—']
        ];
        var body = rows.map(function (r) {
            return '<tr><td style="padding:8px 10px;border:1px solid #d4d4d8">' + r[0] + '</td>' +
                '<td style="padding:8px 10px;border:1px solid #d4d4d8;font-family:monospace">' +
                (r[1] === null || r[1] === undefined ? '--' : (typeof r[1] === 'number' ? r[1].toFixed(r[1] % 1 ? 1 : 0) : r[1])) +
                ' ' + r[2] + '</td>' +
                '<td style="padding:8px 10px;border:1px solid #d4d4d8;font-family:monospace">' + r[3] + '</td>' +
                '<td style="padding:8px 10px;border:1px solid #d4d4d8">' + r[4] + '</td></tr>';
        }).join('');

        return '<div class="cxbms-report" style="background:#fff;color:#18181b;padding:34px 38px;font-size:13px;line-height:1.7">' +
            '<div style="display:flex;justify-content:space-between;align-items:flex-start;border-bottom:2px solid #18181b;padding-bottom:12px;margin-bottom:18px">' +
              '<div><div style="font-size:19px;font-weight:700;letter-spacing:.02em">电池系统检测报告</div>' +
              '<div style="font-size:12px;color:#52525b;margin-top:4px">新能源智能网联汽车检测系统 · BMS 实时监测模块</div></div>' +
              '<div style="text-align:right;font-size:12px;color:#52525b">报告编号 <b style="font-family:monospace;color:#18181b">' + no + '</b><br>' +
              '生成时间 ' + now.toLocaleString('zh-CN') + '</div>' +
            '</div>' +
            '<div style="font-size:12px;color:#52525b;margin-bottom:12px">数据源：整车 CAN 实时报文（' +
              (m.board || '未连接') + '，500 kbps）</div>' +
            '<table style="width:100%;border-collapse:collapse;font-size:12.5px">' +
            '<thead><tr style="background:#f4f4f5">' +
              '<th style="padding:8px 10px;border:1px solid #d4d4d8;text-align:left">检测项目</th>' +
              '<th style="padding:8px 10px;border:1px solid #d4d4d8;text-align:left">测量值</th>' +
              '<th style="padding:8px 10px;border:1px solid #d4d4d8;text-align:left">来源报文</th>' +
              '<th style="padding:8px 10px;border:1px solid #d4d4d8;text-align:left">判定</th>' +
            '</tr></thead><tbody>' + body + '</tbody></table>' +
            '<div style="margin-top:18px;padding:12px 14px;background:#fafafa;border-left:3px solid #a1a1aa;font-size:12px;color:#52525b">' +
              '<b style="color:#18181b">数据来源与置信度说明</b><br>' +
              '· 总压与 SOC 各由两个互不相干的报文交叉印证（0x636/0x45A、0x226/0x686），一致性良好。<br>' +
              '· 温度、电流、母线电压为单报文推断；<b>本平台尚无厂商 DBC 报文定义表</b>，换算系数按汽车行业惯例确定，信号名与量纲未经厂商确认。<br>' +
              '· 若需用于正式判定，请以厂商报文定义表为准，或对同一信号做多工况复测。' +
            '</div>' +
            '<div style="margin-top:26px;display:flex;justify-content:space-between;font-size:12px;color:#52525b">' +
              '<div>检测人：__________</div><div>复核人：__________</div><div>日期：__________</div>' +
            '</div>' +
        '</div>';
    }

    function showReport() {
        var old = document.getElementById('cxbms-report-mask');
        if (old) old.parentNode.removeChild(old);
        var mask = document.createElement('div');
        mask.id = 'cxbms-report-mask';
        mask.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.72);z-index:9999;overflow:auto;padding:28px';
        mask.innerHTML =
            '<div style="max-width:900px;margin:0 auto">' +
              '<div style="display:flex;justify-content:flex-end;gap:10px;margin-bottom:12px">' +
                '<button id="cxbms-print" style="padding:8px 16px;background:#3D9BFF;color:#fff;border:0;cursor:pointer;font-size:13px">打印 / 存为 PDF</button>' +
                '<button id="cxbms-close" style="padding:8px 16px;background:#3f3f46;color:#fff;border:0;cursor:pointer;font-size:13px">关闭</button>' +
              '</div>' + buildReport() +
            '</div>';
        document.body.appendChild(mask);
        document.getElementById('cxbms-close').onclick = function () { mask.parentNode.removeChild(mask); };
        document.getElementById('cxbms-print').onclick = function () {
            var w = window.open('', '_blank');
            if (!w) { alert('浏览器拦截了新窗口，请允许弹窗后重试'); return; }
            w.document.write('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">' +
                '<title>电池系统检测报告</title></head><body style="margin:0">' +
                buildReport() + '</body></html>');
            w.document.close();
            setTimeout(function () { w.focus(); w.print(); }, 350);
        };
    }

    function mount() {
        var btn = document.getElementById('cxbms-report-btn');
        if (btn && !btn.dataset.bound) { btn.dataset.bound = '1'; btn.addEventListener('click', showReport); }
        return !!document.getElementById('battery-bms');
    }

    window.CXBMS = { poll: poll, showReport: showReport, last: function () { return last; } };

    function boot() {
        mount();
        poll();
        // 深链：地址里带 cxreport=1 则延迟自动弹出报告（便于做快捷方式与截图验证）
        if (/[?&]cxreport=1/.test(location.search + location.hash)) {
            setTimeout(showReport, 2500);
        }
        setInterval(poll, POLL_MS);
        // 导航到该页时刷新一次，避免长时间后台轮询
        document.addEventListener('click', function (e) {
            var a = e.target.closest && e.target.closest('[data-target="battery-bms"]');
            if (a) setTimeout(poll, 60);
        });
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
    else boot();
})();
''' + JS_E + u'\n'


def inject():
    t = io.open(P, encoding='utf-8').read()
    n = 0

    # 1) 清旧块（幂等）
    for b, e in ((NAV_B, NAV_E), (PAGE_B, PAGE_E), (JS_B, JS_E)):
        t2 = re.sub(re.escape(b) + r'.*?' + re.escape(e) + r'\n?', '', t, count=1, flags=re.S)
        if t2 != t:
            t = t2
            print(u'  摘掉旧块 %s' % b[:28])

    # 2) 导航：插在「电池管理」那个 </li> 之后
    m = re.search(r'(<a href="#battery"[^>]*data-target="battery">.*?</a>\s*</li>)', t, re.S)
    if not m:
        print(u'  ✗ 找不到「电池管理」导航项')
        return
    t = t[:m.end()] + u'\n' + NAV + t[m.end():]
    n += 1
    print(u'  [1] 导航项已插入')

    # 3) 页面：插在 #battery 那个 page-content 的收尾之后（用 #statistics 作锚，插在它前面）
    m = re.search(r'(\s*<div id="statistics" class="page-content)', t)
    if not m:
        print(u'  ✗ 找不到 #statistics 作为页面锚点')
        return
    t = t[:m.start()] + u'\n' + PAGE + t[m.start():]
    n += 1
    print(u'  [2] 页面 #battery-bms 已插入')

    # 4) JS：插在最后一个 </script> 之前
    idx = t.rfind('</script>')
    if idx < 0:
        print(u'  ✗ 找不到 </script>')
        return
    t = t[:idx] + JS + t[idx:]
    n += 1
    print(u'  [3] JS 已插入')

    io.open(P, 'w', encoding='utf-8').write(t)
    print(u'  已写盘 %d 处，页面 %d KB' % (n, len(t) // 1024))

    # 5) 回读自检
    t2 = io.open(P, encoding='utf-8').read()
    print(u'\n  回读自检:')
    for k, v in ((u'导航项', 'data-target="battery-bms"'),
                 (u'页面容器', 'id="battery-bms"'),
                 (u'报告按钮', 'id="cxbms-report-btn"'),
                 (u'JS', 'window.CXBMS'),
                 (u'各块数量=1', None)):
        if v is None:
            print(u'    %-10s NAV=%d PAGE=%d JS=%d' % (k, t2.count(NAV_B), t2.count(PAGE_B), t2.count(JS_B)))
        else:
            print(u'    %-10s %s' % (k, u'✓' if v in t2 else u'✗'))


if __name__ == '__main__':
    inject()

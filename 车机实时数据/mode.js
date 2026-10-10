/* ============================================================================
   CX-MODE · 日间 / 夜间 模式切换
   ----------------------------------------------------------------------------
   夜间（默认）：墨色底 + 科技蓝 + 安全绿 + 警示红
   日间        ：浅灰底 + 同语义的加深色（保证浅底上的对比度）
   要点：
     · 全部规则挂在 html[data-cx-mode="day"] 下，且选择器比既有的
       `.bg-dark-* !important` 更具体 —— CSS 中同为 !important 时具体者胜，
       所以能稳定覆盖，不会与 CX-INK 打架
     · 明确排除 #cx-boot（开机动画按用户要求保持原样，不随模式变）
     · 图表由 JS 重着色（Chart.js 的色是写死在配置里的，CSS 管不到）
   开关：localStorage['cx-mode']，可用 ?mode=day|night 强制，默认跟随系统
   ========================================================================== */
(function () {
    'use strict';

    var KEY = 'cx-mode';
    var q = location.search || '';
    var forced = (q.match(/[?&]mode=(day|night)/) || [])[1];

    function systemMode() {
        return (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches)
            ? 'day' : 'night';
    }
    function readMode() {
        if (forced) return forced;
        try {
            var v = localStorage.getItem(KEY);
            if (v === 'day' || v === 'night') return v;
        } catch (e) { }
        return systemMode();
    }

    var CSS = [
        /* ---------------- 变量 ---------------- */
        'html[data-cx-mode="day"] {',
        '  --cx-cy: #1E6FD9; --cx-cy-l: #4A93E8; --cx-cy-d: #14539E;',
        '  --cx-gr: #0E9F6E; --cx-am: #B8600F; --cx-rd: #C93A2E;',
        '  --cx-ok: #0E9F6E; --cx-ok-d: #0B7F58;',
        '  --cx-ok-glow: rgba(14,159,110,.55); --cx-ok-soft: rgba(14,159,110,.22);',
        '  --cx-bg0: #EEF1F5; --cx-hair: rgba(15,23,42,.13); --cx-hair-s: rgba(15,23,42,.07);',
        '  --cx-tx: #1A2230; --cx-tx-m: #55606F; --cx-tx-l: #7C8798;',
        '}',
        /* ---------------- 底 ---------------- */
        'html[data-cx-mode="day"] body { background: #EEF1F5 !important; color: #1A2230 !important; }',
        'html[data-cx-mode="day"] .bg-dark-100 { background-color: #FFFFFF !important; }',
        'html[data-cx-mode="day"] .bg-dark-200 { background-color: #FFFFFF !important; }',
        'html[data-cx-mode="day"] .bg-dark-300 { background-color: #F5F7FA !important; }',
        'html[data-cx-mode="day"] .bg-dark-400 { background-color: #FFFFFF !important; }',
        'html[data-cx-mode="day"] .bg-dark-500 { background-color: #E9EDF3 !important; }',
        'html[data-cx-mode="day"] .bg-dark-200\\/50,html[data-cx-mode="day"] .bg-dark-300\\/50 { background-color: rgba(255,255,255,.8) !important; }',
        /* 卡片 / 面板 */
        'html[data-cx-mode="day"] .card { background-color: #FFFFFF !important; border-color: rgba(15,23,42,.10) !important; }',
        'html[data-cx-mode="day"] .cx-live__box { background: #F7F9FC !important; border-color: rgba(15,23,42,.10) !important; }',
        'html[data-cx-mode="day"] .cx-strip-live { background: rgba(255,255,255,.92) !important; }',
        /* ---------------- 字 ---------------- */
        'html[data-cx-mode="day"] .text-white { color: #1A2230 !important; }',
        'html[data-cx-mode="day"] .text-gray-300 { color: #3A4552 !important; }',
        'html[data-cx-mode="day"] .text-gray-400 { color: #55606F !important; }',
        'html[data-cx-mode="day"] .text-gray-500 { color: #7C8798 !important; }',
        'html[data-cx-mode="day"] .text-gray-600 { color: #8A94A3 !important; }',
        /* ---------------- 线 ---------------- */
        'html[data-cx-mode="day"] .border-gray-700 { border-color: rgba(15,23,42,.12) !important; }',
        'html[data-cx-mode="day"] .border-gray-800 { border-color: rgba(15,23,42,.10) !important; }',
        'html[data-cx-mode="day"] .border-white\\/5 { border-color: rgba(15,23,42,.10) !important; }',
        'html[data-cx-mode="day"] .divide-gray-700 > * + * { border-color: rgba(15,23,42,.12) !important; }',
        /* ---------------- 表单 ---------------- */
        'html[data-cx-mode="day"] .input-field { background-color: #FFFFFF !important; color: #1A2230 !important; }',
        'html[data-cx-mode="day"] .input-field::placeholder { color: #98A2B3 !important; }',
        'html[data-cx-mode="day"] select.input-field option { background: #FFFFFF; color: #1A2230; }',
        /* ---------------- 侧栏 / 顶栏 ---------------- */
        'html[data-cx-mode="day"] nav a { color: #3A4552; }',
        'html[data-cx-mode="day"] nav a:hover { background: rgba(30,111,217,.06); }',
        'html[data-cx-mode="day"] .sidebar-active { background: rgba(30,111,217,.10) !important; }',
        'html[data-cx-mode="day"] .sidebar-active span,html[data-cx-mode="day"] .sidebar-active i { color: #1E6FD9 !important; }',
        /* ---------------- 实时面板 ---------------- */
        'html[data-cx-mode="day"] .cx-live__boxhd { color: #7C8798 !important; }',
        'html[data-cx-mode="day"] .cx-row__k { color: #55606F !important; }',
        'html[data-cx-mode="day"] .cx-tbl thead th { background: #F1F4F8 !important; color: #55606F !important; }',
        'html[data-cx-mode="day"] .cx-tbl tbody tr:hover { background: rgba(30,111,217,.05) !important; }',
        'html[data-cx-mode="day"] .cx-tbl td,html[data-cx-mode="day"] .cx-tbl th { border-color: rgba(15,23,42,.10) !important; }',
        'html[data-cx-mode="day"] .cx-live__warn { background: rgba(201,58,46,.07) !important; }',
        'html[data-cx-mode="day"] .cx-live__warn.is-info { background: rgba(120,135,155,.09) !important; border-color: rgba(120,135,155,.3) !important; }',
        /* 数据管线画布 */
        'html[data-cx-mode="day"] #cx-flow-card canvas { filter: none; }',
        /* 滚动条 */
        'html[data-cx-mode="day"] ::-webkit-scrollbar { width: 10px; height: 10px; }',
        'html[data-cx-mode="day"] ::-webkit-scrollbar-track { background: #EEF1F5; }',
        'html[data-cx-mode="day"] ::-webkit-scrollbar-thumb { background: #C3CBD6; border: 2px solid #EEF1F5; }',
        'html[data-cx-mode="day"] ::-webkit-scrollbar-thumb:hover { background: #A9B3C0; }',
        /* 图表容器底色 */
        'html[data-cx-mode="day"] .cx-chartbox,html[data-cx-mode="day"] .cx-live__chart { background: #FFFFFF !important; }',

        /* ---- @apply 编译出的独立规则（.bg-dark-* 覆盖够不到） ---- */
        'html[data-cx-mode="day"] .btn-secondary { background-color: #FFFFFF !important; color: #3A4552 !important; border-color: rgba(15,23,42,.14) !important; }',
        'html[data-cx-mode="day"] .btn-secondary:hover { background-color: #F1F4F8 !important; border-color: rgba(30,111,217,.4) !important; color: #1E6FD9 !important; }',
        /* ---- 硬编码的近白色，日间会看不见 ---- */
        'html[data-cx-mode="day"] .cx-live__title { color: #1A2230 !important; }',
        'html[data-cx-mode="day"] .cx-row__v { color: #1A2230 !important; }',
        'html[data-cx-mode="day"] .cx-big__n { color: #1A2230 !important; }',
        'html[data-cx-mode="day"] .cx-live__meta { color: #7C8798 !important; }',
        'html[data-cx-mode="day"] .cx-live__meta b { color: #1E6FD9 !important; }',
        /* ---- 数据管线画布容器：内联背景只能靠结构选择器压过去 ---- */
        'html[data-cx-mode="day"] #cx-flow-card > div[style] { background: #FFFFFF !important; border-color: rgba(15,23,42,.12) !important; }',
        'html[data-cx-mode="day"] #cx-flow-card canvas { background: #FFFFFF; }',
        /* ---- 其它面板容器 ---- */
        'html[data-cx-mode="day"] .cx-live { background-color: #FFFFFF !important; }',
        'html[data-cx-mode="day"] .cx-live__boxhd { border-bottom-color: rgba(15,23,42,.10) !important; }',
        'html[data-cx-mode="day"] .cx-live__head { border-bottom-color: rgba(15,23,42,.10) !important; }',
        'html[data-cx-mode="day"] .cx-livebadge { color: #1E6FD9 !important; background: rgba(30,111,217,.07) !important; border-color: rgba(30,111,217,.28) !important; }',
        'html[data-cx-mode="day"] .cx-livebadge i { background: #0E9F6E !important; }',
        'html[data-cx-mode="day"] .cx-filters button { color: #55606F !important; border-color: rgba(15,23,42,.14) !important; }',
        'html[data-cx-mode="day"] .cx-filters button.on { background: rgba(30,111,217,.10) !important; border-color: rgba(30,111,217,.45) !important; color: #1E6FD9 !important; }',
        'html[data-cx-mode="day"] .cx-cfg__k { color: #7C8798 !important; }',
        'html[data-cx-mode="day"] .cx-cfg__v { color: #1A2230 !important; }',
        'html[data-cx-mode="day"] .cx-chartbox__h { color: #55606F !important; }',
        /* ---------------- 切换按钮 ---------------- */
        '#cx-mode-btn{display:inline-flex;align-items:center;gap:6px;height:28px;padding:0 10px;',
        '  border:1px solid rgba(148,163,184,.32);background:transparent;color:#9A9AA5;',
        '  font-family:"JetBrains Mono",Consolas,monospace;font-size:11px;letter-spacing:.1em;',
        '  cursor:pointer;transition:color .18s,border-color .18s,background .18s}',
        '#cx-mode-btn:hover{border-color:#3D9BFF;color:#3D9BFF;background:rgba(61,155,255,.08)}',
        '#cx-mode-btn i{font-size:12px}',
        'html[data-cx-mode="day"] #cx-mode-btn{border-color:rgba(15,23,42,.18);color:#55606F}',
        'html[data-cx-mode="day"] #cx-mode-btn:hover{border-color:#1E6FD9;color:#1E6FD9;background:rgba(30,111,217,.07)}',
        /* 切模式时的短促过渡（一次性的，不是常驻闪烁） */
        'html.cx-mode-anim,html.cx-mode-anim *{transition:background-color .22s ease,color .22s ease,border-color .22s ease !important}'
    ].join('\n');

    function apply(mode) {
        var root = document.documentElement;
        root.dataset.cxMode = mode;
        try { localStorage.setItem(KEY, mode); } catch (e) { }
        var btn = document.getElementById('cx-mode-btn');
        if (btn) {
            btn.innerHTML = mode === 'day'
                ? '<i class="fa fa-moon-o"></i>夜间'
                : '<i class="fa fa-sun-o"></i>日间';
            btn.title = mode === 'day' ? '切换到夜间模式' : '切换到日间模式';
        }
        recolorCharts(mode);
        try {
            window.dispatchEvent(new CustomEvent('cx-mode-change', { detail: { mode: mode } }));
        } catch (e) { }
        // 一次性过渡
        root.classList.add('cx-mode-anim');
        window.setTimeout(function () { root.classList.remove('cx-mode-anim'); }, 260);
    }

    /* ---------- 图表重着色（Chart.js 的色写死在配置里，CSS 管不到） ---------- */
    function recolorCharts(mode) {
        if (typeof window.Chart === 'undefined') return;
        var day = mode === 'day';
        var tick = day ? '#55606F' : '#5A6E86';
        var grid = day ? 'rgba(15,23,42,.09)' : 'rgba(120,200,255,.07)';
        var canvases = document.querySelectorAll('canvas');
        Array.prototype.forEach.call(canvases, function (cv) {
            var ch;
            try { ch = window.Chart.getChart(cv); } catch (e) { return; }
            if (!ch) return;
            var o = ch.options || {};
            if (o.scales) {
                Object.keys(o.scales).forEach(function (k) {
                    var sc = o.scales[k];
                    if (!sc) return;
                    sc.ticks = sc.ticks || {};
                    sc.ticks.color = tick;
                    sc.grid = sc.grid || {};
                    sc.grid.color = grid;
                });
            }
            o.plugins = o.plugins || {};
            o.plugins.legend = o.plugins.legend || {};
            o.plugins.legend.labels = o.plugins.legend.labels || {};
            o.plugins.legend.labels.color = tick;
            o.plugins.tooltip = o.plugins.tooltip || {};
            o.plugins.tooltip.backgroundColor = day ? 'rgba(255,255,255,.97)' : 'rgba(12,9,6,.95)';
            o.plugins.tooltip.titleColor = day ? '#1A2230' : '#FFC043';
            o.plugins.tooltip.bodyColor = day ? '#3A4552' : '#E8E8EC';
            o.plugins.tooltip.borderColor = day ? 'rgba(15,23,42,.14)' : '#26262C';
            o.plugins.tooltip.borderWidth = 1;
            try { ch.update('none'); } catch (e) { }
        });
    }

    /* ---------- 按钮 ---------- */
    function mountBtn() {
        if (document.getElementById('cx-mode-btn')) return true;
        var host = document.querySelector('header .flex.items-center.space-x-4')
            || document.querySelector('header .flex.items-center.justify-between > div:last-child')
            || document.querySelector('header');
        if (!host) return false;
        var b = document.createElement('button');
        b.id = 'cx-mode-btn';
        b.type = 'button';
        b.addEventListener('click', function () {
            apply(document.documentElement.dataset.cxMode === 'day' ? 'night' : 'day');
        });
        host.insertBefore(b, host.firstChild);
        return true;
    }

    /* ---------- 启动 ---------- */
    var st = document.createElement('style');
    st.id = 'cx-mode-css';
    st.textContent = CSS;
    document.head.appendChild(st);

    // 尽早设上，避免闪一下白/黑
    document.documentElement.dataset.cxMode = readMode();

    function boot() {
        // 先挂按钮再赋值，否则按钮建出来是空的
        if (!mountBtn()) {
            var tries = 0;
            var t = window.setInterval(function () {
                if (mountBtn() || ++tries > 20) window.clearInterval(t);
                apply(document.documentElement.dataset.cxMode);
            }, 250);
        }
        apply(document.documentElement.dataset.cxMode);
        // 图表是异步初始化的，稍后再着一次色
        window.setTimeout(function () { recolorCharts(document.documentElement.dataset.cxMode); }, 1200);
        window.setTimeout(function () { recolorCharts(document.documentElement.dataset.cxMode); }, 3000);
        // 跟随系统（用户没手动设过时）
        if (window.matchMedia) {
            try {
                window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', function () {
                    var saved = null;
                    try { saved = localStorage.getItem(KEY); } catch (e) { }
                    if (!saved && !forced) apply(systemMode());
                });
            } catch (e) { }
        }
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
    else boot();
})();

/* ============================================================================
   CXZ-MODE · 车小智页 日间/夜间模式（与检测看板同一套交互）
   ----------------------------------------------------------------------------
   该页用 :root 的 --cy/--gr/--bg0..3/--hair/--tx 系列变量 + Tailwind 色阶，
   日间只需换变量 + 覆盖浅色/深色面板类。
   开关：localStorage['cxz-mode']，?mode=day|night 可强制，默认跟随系统
   ========================================================================== */
(function () {
    'use strict';
    if (document.documentElement.dataset.cxzBooted) return;
    document.documentElement.dataset.cxzBooted = '1';

    var KEY = 'cxz-mode';
    var forced = (location.search.match(/[?&]mode=(day|night)/) || [])[1];
    function sysMode() {
        return (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches)
            ? 'day' : 'night';
    }
    function readMode() {
        if (forced) return forced;
        try { var v = localStorage.getItem(KEY); if (v === 'day' || v === 'night') return v; } catch (e) { }
        return sysMode();
    }

    var CSS = [
        '#cxz-mode-btn{display:inline-flex;align-items:center;gap:6px;height:32px;padding:0 12px;',
        '  border:1px solid rgba(148,163,184,.32);background:transparent;color:#9A9AA5;',
        '  font-family:"JetBrains Mono",Consolas,monospace;font-size:12px;letter-spacing:.08em;',
        '  cursor:pointer;transition:color .18s,border-color .18s,background .18s}',
        '#cxz-mode-btn:hover{border-color:#3D9BFF;color:#3D9BFF;background:rgba(61,155,255,.08)}',
        'html[data-cxz-mode="day"] #cxz-mode-btn{border-color:rgba(15,23,42,.18);color:#55606F}',
        'html[data-cxz-mode="day"] #cxz-mode-btn:hover{border-color:#1E6FD9;color:#1E6FD9}',
        'html.cxz-anim,html.cxz-anim *{transition:background-color .22s ease,color .22s ease,border-color .22s ease !important}',

        /* ---------------- 日间 ---------------- */
        'html[data-cxz-mode="day"]{',
        '  --cy:#1E6FD9; --cy-l:#4A93E8; --cy-d:#14539E;',
        '  --gr:#0E9F6E; --am:#B8600F; --rd:#C93A2E;',
        '  --bg0:#EEF1F5; --bg1:#FFFFFF; --bg2:#F5F7FA; --bg3:#E9EDF3;',
        '  --hair:rgba(15,23,42,.13); --hair-s:rgba(15,23,42,.07);',
        '  --tx:#1A2230; --tx-m:#55606F; --tx-l:#7C8798;',
        '}',
        'html[data-cxz-mode="day"] body{background:#EEF1F5 !important;color:#1A2230 !important}',
        'html[data-cxz-mode="day"] .bg-white{background-color:#FFFFFF !important}',
        'html[data-cxz-mode="day"] .bg-neutral-light{background-color:#F5F7FA !important}',
        'html[data-cxz-mode="day"] .bg-neutral-dark{background-color:#FFFFFF !important;color:#1A2230 !important}',
        'html[data-cxz-mode="day"] nav.bg-white{background-color:rgba(255,255,255,.96) !important;',
        '  border-bottom:1px solid rgba(15,23,42,.10);box-shadow:none !important}',
        'html[data-cxz-mode="day"] .text-gray-600,html[data-cxz-mode="day"] .text-gray-500{color:#55606F !important}',
        'html[data-cxz-mode="day"] .text-gray-400{color:#7C8798 !important}',
        'html[data-cxz-mode="day"] .text-gray-700,html[data-cxz-mode="day"] .text-gray-800{color:#3A4552 !important}',
        'html[data-cxz-mode="day"] .text-white{color:#1A2230 !important}',
        'html[data-cxz-mode="day"] .text-gray-900{color:#1A2230 !important}',
        'html[data-cxz-mode="day"] .border-gray-200,html[data-cxz-mode="day"] .border-gray-300{border-color:rgba(15,23,42,.12) !important}',
        'html[data-cxz-mode="day"] .bg-gray-50,html[data-cxz-mode="day"] .bg-gray-100{background-color:#F5F7FA !important}',
        'html[data-cxz-mode="day"] .shadow-md,html[data-cxz-mode="day"] .shadow-lg,html[data-cxz-mode="day"] .shadow-xl{box-shadow:0 6px 20px -12px rgba(15,23,42,.22) !important}',
        'html[data-cxz-mode="day"] footer{background:#FFFFFF !important;color:#55606F !important}',
        'html[data-cxz-mode="day"] footer .text-white,html[data-cxz-mode="day"] footer h3{color:#1A2230 !important}'
    ].join('\n');

    function apply(mode) {
        document.documentElement.dataset.cxzMode = mode;
        try { localStorage.setItem(KEY, mode); } catch (e) { }
        var b = document.getElementById('cxz-mode-btn');
        if (b) {
            b.innerHTML = mode === 'day'
                ? '<i class="fas fa-moon"></i> 夜间'
                : '<i class="fas fa-sun"></i> 日间';
            b.title = mode === 'day' ? '切换到夜间模式' : '切换到日间模式';
        }
        var r = document.documentElement;
        r.classList.add('cxz-anim');
        window.setTimeout(function () { r.classList.remove('cxz-anim'); }, 260);
    }

    var st = document.createElement('style');
    st.id = 'cxz-mode-css';
    st.textContent = CSS;
    document.head.appendChild(st);
    document.documentElement.dataset.cxzMode = readMode();

    function mount() {
        if (document.getElementById('cxz-mode-btn')) return true;
        var nav = document.querySelector('nav');
        if (!nav) return false;
        // 放在导航右侧那一组里（登录按钮旁）
        var host = nav.querySelector('.flex.items-center.space-x-4')
            || nav.querySelector('.flex.items-center.space-x-6')
            || nav.querySelector('div:last-child')
            || nav;
        var b = document.createElement('button');
        b.id = 'cxz-mode-btn';
        b.type = 'button';
        b.addEventListener('click', function () {
            apply(document.documentElement.dataset.cxzMode === 'day' ? 'night' : 'day');
        });
        host.insertBefore(b, host.firstChild);
        return true;
    }

    function boot() {
        if (!mount()) {
            var n = 0;
            var t = window.setInterval(function () {
                if (mount() || ++n > 20) window.clearInterval(t);
            }, 250);
        }
        apply(document.documentElement.dataset.cxzMode);
        if (window.matchMedia) {
            try {
                window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', function () {
                    var saved = null;
                    try { saved = localStorage.getItem(KEY); } catch (e) { }
                    if (!saved && !forced) apply(sysMode());
                });
            } catch (e) { }
        }
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
    else boot();
})();

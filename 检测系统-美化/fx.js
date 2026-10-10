/* ============================================================================
   新能源汽车智能检测系统 · 看板动效层（零依赖）
   ----------------------------------------------------------------------------
   原则（遵循用户既定红线）：
     · 不做横穿整屏 / 全屏覆盖 / 持续闪烁的效果
     · 动效只发生在 ① 用户触发（悬停、移动光标、点击）或 ② 元素局部且一次性
     · 渐进增强：脚本不跑时页面完全可用；页面切换时只对当前页生效
   模块：仪表条 / 卡片角标 / 入场揭示 / 数字滚动 / 悬停聚光 / 时钟 / 页面切换联动
   ========================================================================== */
(function () {
    'use strict';

    var root = document.documentElement;
    root.classList.add('cx-js');

    var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var revealed = {};          // 已播放过入场动画的页面

    /* ------------------------------------------------------------------ 页面元数据 */
    function pageIds() {
        return Array.prototype.map.call(document.querySelectorAll('.page-content'), function (p) { return p.id; });
    }
    function activePage() {
        var el = document.querySelector('.page-content:not(.hidden)');
        return el || document.querySelector('.page-content');
    }

    /* ------------------------------------------------------------------ 1. 仪表条 */
    function initStrip() {
        var header = document.querySelector('header');
        if (!header || header.querySelector('.cx-strip')) return;

        var strip = document.createElement('div');
        strip.className = 'cx-strip';
        strip.setAttribute('aria-hidden', 'true');
        strip.innerHTML =
            '<span class="cx-strip__i"><i></i>SYS <em>ONLINE</em></span>' +
            '<span class="cx-strip__i" data-cx-module>MODULE -- · ---</span>' +
            '<span class="cx-strip__i" data-cx-panels>PANELS <b>0</b></span>' +
            '<span class="cx-strip__i" data-cx-rows>RECORDS <b>0</b></span>' +
            '<span class="cx-strip__ruler"></span>' +
            '<span class="cx-strip__i" data-cx-clock>--:--:--</span>';
        header.appendChild(strip);
        syncStrip();
    }

    function syncStrip() {
        var strip = document.querySelector('.cx-strip');
        if (!strip) return;
        var page = activePage();
        if (!page) return;

        var ids = pageIds();
        var idx = ids.indexOf(page.id) + 1;
        var title = (document.getElementById('page-title') || {}).textContent || page.id;
        var mod = strip.querySelector('[data-cx-module]');
        if (mod) {
            mod.innerHTML = 'MODULE <b>' + (idx < 10 ? '0' + idx : idx) + '</b> · ' +
                String(title).trim().toUpperCase();
        }

        var panels = strip.querySelector('[data-cx-panels] b');
        if (panels) panels.textContent = page.querySelectorAll('.card').length;

        var rows = strip.querySelector('[data-cx-rows] b');
        if (rows) {
            // 只统计页面自身的记录行；实时数据面板里的表格不算检测记录
            var n = 0;
            Array.prototype.forEach.call(page.querySelectorAll('tbody tr'), function (tr) {
                if (!tr.closest('.cx-live')) n++;
            });
            rows.textContent = n;
        }
    }

    /* ------------------------------------------------------------------ 2. 卡片角标 */
    function initCardChrome() {
        var ids = pageIds();
        Array.prototype.forEach.call(document.querySelectorAll('.page-content'), function (page) {
            var pi = ids.indexOf(page.id) + 1;
            Array.prototype.forEach.call(page.querySelectorAll('.card'), function (card, ci) {
                if (!card.classList.contains('cx-panel')) {
                    card.classList.add('cx-panel');
                    var sn = document.createElement('span');
                    sn.className = 'cx-sn';
                    sn.setAttribute('aria-hidden', 'true');
                    sn.innerHTML = '<i></i>' +
                        (pi < 10 ? '0' + pi : pi) + '-' + (ci + 1 < 10 ? '0' + (ci + 1) : (ci + 1));
                    card.appendChild(sn);
                }
                card.setAttribute('data-cx', '');
                // 图表卡片单独打类，供 CSS 画测量刻度尺（避免在 CSS 里用 :has()）
                if (card.querySelector('canvas')) card.classList.add('cx-chart');
            });
            Array.prototype.forEach.call(page.querySelectorAll('tbody tr'), function (tr) {
                tr.setAttribute('data-cx', '');
            });
        });
    }

    /* ------------------------------------------------------------------ 3. 入场揭示（一次性） */
    function revealPage(page, force) {
        if (!page) return;
        if (revealed[page.id] && !force) return;
        revealed[page.id] = true;

        var items = page.querySelectorAll('[data-cx]');
        if (!items.length) return;

        Array.prototype.forEach.call(items, function (el) { el.classList.remove('cx-in'); });

        if (reduceMotion || !('IntersectionObserver' in window)) {
            Array.prototype.forEach.call(items, function (el) { el.classList.add('cx-in'); });
            return;
        }

        var n = 0;
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (e) {
                if (!e.isIntersecting) return;
                var el = e.target;
                el.style.transitionDelay = Math.min(n++ % 8, 7) * 45 + 'ms';
                el.classList.add('cx-in');
                io.unobserve(el);
            });
        }, { rootMargin: '0px 0px -6% 0px', threshold: 0.06 });

        Array.prototype.forEach.call(items, function (el) { io.observe(el); });

        // 视口内的立即揭示，避免首屏空白
        window.setTimeout(function () {
            Array.prototype.forEach.call(items, function (el) {
                if (el.getBoundingClientRect().top < window.innerHeight) el.classList.add('cx-in');
            });
        }, 60);
    }

    /* ------------------------------------------------------------------ 4. 数字滚动（一次性） */
    function runCounters(page) {
        if (!page || reduceMotion) return;
        Array.prototype.forEach.call(page.querySelectorAll('.card'), function (card) {
            Array.prototype.forEach.call(card.querySelectorAll('p, span, div'), function (el) {
                if (el.children.length || el.dataset.cxCounted) return;
                var t = el.textContent.trim();
                var m = t.match(/^([\d,]+(?:\.\d+)?)(%?)$/);
                if (!m) return;
                var num = parseFloat(m[1].replace(/,/g, ''));
                if (!isFinite(num) || num < 3) return;
                var dec = (m[1].split('.')[1] || '').length;
                var comma = m[1].indexOf(',') >= 0;
                el.dataset.cxCounted = '1';

                var start = performance.now(), dur = 900;
                function frame(now) {
                    var p = Math.min(1, (now - start) / dur);
                    var e = 1 - Math.pow(1 - p, 3);
                    var v = num * e;
                    var s = dec > 0 ? v.toFixed(dec) : String(Math.round(v));
                    if (comma) s = Number(s).toLocaleString('en-US');
                    el.textContent = s + m[2];
                    if (p < 1) requestAnimationFrame(frame);
                    else el.textContent = (comma ? num.toLocaleString('en-US') : (dec > 0 ? num.toFixed(dec) : String(num))) + m[2];
                }
                requestAnimationFrame(frame);
            });
        });
    }

    /* ------------------------------------------------------------------ 5. 卡片悬停聚光（单个委托监听，避免给 30+ 张卡各挂一个） */
    function initSpotlight() {
        if (reduceMotion) return;
        var current = null, raf = 0, px = 0, py = 0, rect = null;

        document.addEventListener('mousemove', function (e) {
            var card = e.target && e.target.closest ? e.target.closest('.card') : null;
            if (card !== current) {
                current = card;
                rect = card ? card.getBoundingClientRect() : null;
            }
            if (!current || !rect || !rect.width) return;
            px = (e.clientX - rect.left) / rect.width * 100;
            py = (e.clientY - rect.top) / rect.height * 100;
            if (raf) return;
            raf = requestAnimationFrame(function () {
                raf = 0;
                if (!current) return;
                current.style.setProperty('--cx-mx', px.toFixed(1) + '%');
                current.style.setProperty('--cx-my', py.toFixed(1) + '%');
            });
        }, { passive: true });
    }

    /* ------------------------------------------------------------------ 6. 时钟（仅仪表条上的一行小字） */
    function initClock() {
        var el = document.querySelector('[data-cx-clock]');
        if (!el) return;
        function tick() {
            var d = new Date();
            function p(n) { return n < 10 ? '0' + n : String(n); }
            el.textContent = p(d.getHours()) + ':' + p(d.getMinutes()) + ':' + p(d.getSeconds());
        }
        tick();
        window.setInterval(tick, 1000);
    }

    /* ------------------------------------------------------------------ 7. 页面切换联动 */
    var activating = false;      // 防止 activate() 改类名再次触发观察器，形成无限回环

    function activate(page) {
        if (!page || activating) return;
        activating = true;
        try {
            var first = !revealed[page.id];
            syncStrip();
            // 页面里的实时数据面板是异步插入的，稍后再数一次卡片数
            window.setTimeout(syncStrip, 600);
            if (first) {
                revealPage(page);
                runCounters(page);
            } else if (!reduceMotion) {
                page.classList.remove('cx-entering');
                void page.offsetWidth;               // 重启动画
                page.classList.add('cx-entering');
            }
        } finally {
            // 观察器回调是微任务，等这一轮类名变更被消费完再解锁
            window.setTimeout(function () { activating = false; }, 0);
        }
    }

    function initPageSwitch() {
        var pages = document.querySelectorAll('.page-content');
        if (!('MutationObserver' in window)) { activate(activePage()); return; }
        var mo = new MutationObserver(function (records) {
            if (activating) return;
            for (var i = 0; i < records.length; i++) {
                var el = records[i].target;
                if (!el.classList || el.classList.contains('hidden')) continue;
                if (el.classList.contains('page-content')) { activate(el); break; }
            }
        });
        Array.prototype.forEach.call(pages, function (p) {
            mo.observe(p, { attributes: true, attributeFilter: ['class'] });
        });
    }

    /* ------------------------------------------------------------------ 8. 深层链接：?page=statistics 或 #statistics 直接打开某个页签 */
    function initDeepLink() {
        var m = /[?&]page=([\w-]+)/.exec(window.location.search) ||
                /^#([\w-]+)$/.exec(window.location.hash);
        if (!m) return;
        var link = document.querySelector('a[data-target="' + m[1] + '"]');
        if (link) link.click();
    }

    /* ------------------------------------------------------------------ 启动 */
    function boot() {
        if (root.dataset.cxBooted) return;
        root.dataset.cxBooted = '1';

        try { initCardChrome(); } catch (e) { }
        try { initStrip(); } catch (e) { }
        try { initClock(); } catch (e) { }
        try { initSpotlight(); } catch (e) { }
        try { initPageSwitch(); } catch (e) { }

        var page = activePage();
        try { initDeepLink(); } catch (e) { }
        page = activePage();
        try { revealPage(page); } catch (e) { }
        try { runCounters(page); } catch (e) { }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})();

/* ============================================================================
   车小智 · CYBER FX
   零依赖动效层。原则：
     · 不做覆盖全屏、横穿视线、持续闪烁的效果
     · 动效只发生在"用户主动触发"或"局部小范围"，且必须可预期
     · 渐进增强：脚本不跑时页面内容完整可见
   模块：滚动进度 / HUD 构件注入 / 滚动揭示 / 标题解码 / 数字滚动
        首屏粒子场 / 视差 / 遥测跑马灯 / 光标准星 / 卡片聚光 / 按钮磁吸 / 状态条
   ========================================================================== */
(function () {
    'use strict';

    var root = document.documentElement;
    root.classList.add('cy-js');

    var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* ------------------------------------------------------------------ 1. 滚动进度 */
    function initProgress() {
        var bar = document.createElement('div');
        bar.className = 'cy-progress';
        document.body.appendChild(bar);
        function upd() {
            var h = document.documentElement.scrollHeight - window.innerHeight;
            var p = h > 0 ? Math.min(1, Math.max(0, window.pageYOffset / h)) : 0;
            bar.style.width = (p * 100).toFixed(2) + '%';
        }
        window.addEventListener('scroll', upd, { passive: true });
        window.addEventListener('resize', upd);
        upd();
    }

    /* ------------------------------------------------------------------ 2. 章节 HUD 构件 */
    var MODULES = {
        features: ['01', 'CORE CAPABILITY', '核心能力'],
        demo: ['02', 'FAULT DIAGNOSIS', '智能诊断'],
        chat: ['03', 'AI CONVERSATION', '智能对话'],
        'diagnosis-network': ['04', 'NETWORK TOPOLOGY', '诊断网络'],
        about: ['05', 'ABOUT SYSTEM', '关于我们']
    };

    function initHudChrome() {
        Object.keys(MODULES).forEach(function (id) {
            var sec = document.getElementById(id);
            if (!sec) return;
            var head = sec.querySelector('.text-center');
            var h2 = head && head.querySelector('h2');
            if (!h2) return;

            var tag = document.createElement('span');
            tag.className = 'hud-tag';
            tag.setAttribute('data-reveal', '');
            tag.innerHTML = '<i></i>MODULE ' + MODULES[id][0] + ' / ' + MODULES[id][1];
            head.insertBefore(tag, h2);

            var ghost = document.createElement('span');
            ghost.className = 'hud-ghost';
            ghost.setAttribute('aria-hidden', 'true');
            ghost.textContent = MODULES[id][0];
            head.insertBefore(ghost, head.firstChild);

            var rule = document.createElement('div');
            rule.className = 'hud-rule';
            rule.setAttribute('data-reveal', '');
            var p = head.querySelector('p');
            if (p && p.parentNode === head) head.insertBefore(rule, p.nextSibling);
            else head.appendChild(rule);

            var sn = document.createElement('span');
            sn.className = 'hud-sn';
            sn.textContent = 'SN-' + MODULES[id][0] + '-' + id.toUpperCase().slice(0, 6) + ' / REV.2';
            sec.appendChild(sn);
        });
    }

    /* ------------------------------------------------------------------ 3. 标题通道分离（仅悬停触发） */
    function initSplit() {
        Array.prototype.forEach.call(document.querySelectorAll('section h2'), function (h) {
            if (h.children.length) return;
            h.setAttribute('data-text', h.textContent);
            h.classList.add('cy-split');
        });
        var logo = document.querySelector('nav .gradient-text');
        if (logo && !logo.children.length) logo.setAttribute('data-text', logo.textContent);
    }

    /* ------------------------------------------------------------------ 4. 滚动揭示 */
    var revealTargets = [];

    function initReveal() {
        var sels = [
            '.hud-tag', '.hud-rule',
            'section .text-center h2', 'section .text-center p',
            '.card-hover',
            '#features .grid > div',
            '#diagnosis-network .grid > div',
            'footer .grid > div'
        ];
        var set = [];
        sels.forEach(function (s) {
            Array.prototype.forEach.call(document.querySelectorAll(s), function (el) {
                if (set.indexOf(el) >= 0) return;
                set.push(el);
                if (!el.hasAttribute('data-reveal')) el.setAttribute('data-reveal', '');
                el.style.transitionDelay = Math.min(set.length % 6, 5) * 60 + 'ms';
                revealTargets.push(el);
            });
        });

        if (!('IntersectionObserver' in window) || reduceMotion) {
            revealTargets.forEach(function (el) { el.classList.add('cy-in'); });
            return;
        }

        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (e) {
                if (!e.isIntersecting) return;
                e.target.classList.add('cy-in');
                if (e.target.tagName === 'H2') decodeText(e.target);
                io.unobserve(e.target);
            });
        }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });

        revealTargets.forEach(function (el) { io.observe(el); });

        window.setTimeout(function () {
            revealTargets.forEach(function (el) {
                var r = el.getBoundingClientRect();
                if (r.top < window.innerHeight) {
                    el.classList.add('cy-in');
                    if (el.tagName === 'H2') decodeText(el);
                }
            });
        }, 60);
    }

    /* ------------------------------------------------------------------ 5. 标题解码（一次性入场） */
    var GLYPHS = '01▚▞░▒▓/\\<>*#+=';
    function decodeText(el) {
        if (reduceMotion || el.dataset.cyDecoded) return;
        el.dataset.cyDecoded = '1';
        var target = el.textContent;
        if (!target || target.length > 40) return;
        var len = target.length;
        var start = performance.now();
        var dur = 620;
        function frame(now) {
            var p = Math.min(1, (now - start) / dur);
            var keep = Math.floor(len * p);
            var out = target.slice(0, keep);
            for (var i = keep; i < len; i++) {
                out += GLYPHS.charAt(Math.floor(Math.random() * GLYPHS.length));
            }
            el.textContent = out;
            if (p < 1) requestAnimationFrame(frame);
            else el.textContent = target;      // 必定还原
        }
        requestAnimationFrame(frame);
    }

    /* ------------------------------------------------------------------ 6. 数字滚动 */
    function initCounters() {
        var scope = document.querySelectorAll('#home, #about');
        var items = [];
        Array.prototype.forEach.call(scope, function (box) {
            Array.prototype.forEach.call(box.querySelectorAll('span, div, p'), function (el) {
                if (el.children.length) return;
                var t = el.textContent.trim();
                var m = t.match(/^([\d,]+)([KkMm%+]?)$/);
                if (!m) return;
                var n = parseInt(m[1].replace(/,/g, ''), 10);
                if (!isFinite(n) || n < 10 || m[1].replace(/,/g, '').length > 6) return;
                items.push({ el: el, n: n, suffix: m[2], comma: m[1].indexOf(',') >= 0, done: false });
            });
        });
        if (!items.length) return;

        function run(it) {
            if (it.done) return;
            it.done = true;
            if (reduceMotion) return;
            var start = performance.now(), dur = 1100;
            function frame(now) {
                var p = Math.min(1, (now - start) / dur);
                var e = 1 - Math.pow(1 - p, 3);
                var v = Math.round(it.n * e);
                it.el.textContent = (it.comma ? v.toLocaleString('en-US') : String(v)) + it.suffix;
                if (p < 1) requestAnimationFrame(frame);
                else it.el.textContent = (it.comma ? it.n.toLocaleString('en-US') : String(it.n)) + it.suffix;
            }
            requestAnimationFrame(frame);
        }

        if (!('IntersectionObserver' in window)) { items.forEach(run); return; }
        var io = new IntersectionObserver(function (es) {
            es.forEach(function (e) {
                if (!e.isIntersecting) return;
                items.forEach(function (it) { if (it.el === e.target) run(it); });
                io.unobserve(e.target);
            });
        }, { threshold: 0.4 });
        items.forEach(function (it) { io.observe(it.el); });
    }

    /* ------------------------------------------------------------------ 7. 首屏粒子场（局部，不挡内容） */
    function initParticles() {
        var host = document.getElementById('home');
        if (!host || reduceMotion) return;
        if (host.querySelector('#cy-fx')) return;
        var canvas = document.createElement('canvas');
        canvas.id = 'cy-fx';
        host.insertBefore(canvas, host.firstChild);

        var ctx = canvas.getContext('2d');
        if (!ctx) return;

        var W = 0, H = 0, dpr = Math.min(window.devicePixelRatio || 1, 2);
        var pts = [], mouse = { x: -9999, y: -9999 };

        function resize() {
            W = host.clientWidth;
            H = host.clientHeight;
            canvas.width = W * dpr;
            canvas.height = H * dpr;
            canvas.style.width = W + 'px';
            canvas.style.height = H + 'px';
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
            var n = Math.max(24, Math.min(66, Math.round(W * H / 26000)));
            pts = [];
            for (var i = 0; i < n; i++) {
                pts.push({
                    x: Math.random() * W,
                    y: Math.random() * H,
                    vx: (Math.random() - .5) * .26,
                    vy: (Math.random() - .5) * .26,
                    r: Math.random() * 1.3 + .6
                });
            }
        }
        resize();
        window.addEventListener('resize', resize);

        host.addEventListener('mousemove', function (e) {
            var r = host.getBoundingClientRect();
            mouse.x = e.clientX - r.left;
            mouse.y = e.clientY - r.top;
        });
        host.addEventListener('mouseleave', function () { mouse.x = mouse.y = -9999; });

        var LINK = 130;
        function tick() {
            ctx.clearRect(0, 0, W, H);
            for (var i = 0; i < pts.length; i++) {
                var p = pts[i];
                p.x += p.vx; p.y += p.vy;
                if (p.x < 0 || p.x > W) p.vx *= -1;
                if (p.y < 0 || p.y > H) p.vy *= -1;
                var dx = p.x - mouse.x, dy = p.y - mouse.y;
                var md = Math.sqrt(dx * dx + dy * dy);
                if (md < 150 && md > 0.1) { p.x += dx / md * .5; p.y += dy / md * .5; }
            }
            for (var a = 0; a < pts.length; a++) {
                for (var b = a + 1; b < pts.length; b++) {
                    var ddx = pts[a].x - pts[b].x, ddy = pts[a].y - pts[b].y;
                    var d = Math.sqrt(ddx * ddx + ddy * ddy);
                    if (d < LINK) {
                        ctx.strokeStyle = 'rgba(53,224,255,' + ((1 - d / LINK) * .18).toFixed(3) + ')';
                        ctx.lineWidth = 1;
                        ctx.beginPath();
                        ctx.moveTo(pts[a].x, pts[a].y);
                        ctx.lineTo(pts[b].x, pts[b].y);
                        ctx.stroke();
                    }
                }
                ctx.fillStyle = 'rgba(168,242,255,.6)';
                ctx.beginPath();
                ctx.arc(pts[a].x, pts[a].y, pts[a].r, 0, 6.2832);
                ctx.fill();
            }
            requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
    }

    /* ------------------------------------------------------------------ 8. 首屏视差 */
    function initParallax() {
        var host = document.getElementById('home');
        var visual = document.querySelector('.cy-visual');
        if (!host || !visual || reduceMotion) return;
        var tx = 0, ty = 0, cx = 0, cy = 0;
        host.addEventListener('mousemove', function (e) {
            var r = host.getBoundingClientRect();
            tx = ((e.clientX - r.left) / r.width - .5) * 14;
            ty = ((e.clientY - r.top) / r.height - .5) * 9;
        });
        host.addEventListener('mouseleave', function () { tx = ty = 0; });
        (function loop() {
            cx += (tx - cx) * .07;
            cy += (ty - cy) * .07;
            visual.style.transform = 'translate3d(' + cx.toFixed(2) + 'px,' + cy.toFixed(2) + 'px,0)';
            requestAnimationFrame(loop);
        })();
    }

    /* ------------------------------------------------------------------ 9. 遥测跑马灯 */
    function initTicker() {
        var host = document.getElementById('home');
        if (!host || host.querySelector('.cy-ticker')) return;
        var items = [
            'BUS <b>CAN-ISO 11898</b> 500 kbps',
            'SAMPLING <b>1 kHz</b>',
            'NODES <b>17</b> ONLINE',
            'BMS <em>SOC 72%</em> · <em>SOH 98%</em>',
            'DTC <b>0x0000</b> NO FAULT',
            'INSULATION <em>OK</em>',
            'CELL ΔV <b>12 mV</b>',
            'MOTOR TEMP <b>46℃</b>',
            'OBC <b>6.6 kW</b> READY',
            'ADAS <b>4D RADAR</b> TRACKING',
            'LATENCY <b>8 ms</b>',
            'CHXZ-OS <b>v1.0</b> · SECURE BOOT OK'
        ];
        // 静态"损坏字符"点缀：故障感靠排版，不靠闪烁
        var line = items.join('&nbsp;&nbsp;◆&nbsp;&nbsp;') + '&nbsp;&nbsp;◆&nbsp;&nbsp;';
        var box = document.createElement('div');
        box.className = 'cy-ticker';
        box.setAttribute('aria-hidden', 'true');
        var track = document.createElement('div');
        track.className = 'cy-ticker__track';
        track.innerHTML = '<span>' + line + '</span><span>' + line + '</span>';
        box.appendChild(track);
        host.appendChild(box);
    }

    /* ------------------------------------------------------------------ 10. 光标准星 */
    function initCursor() {
        if (reduceMotion) return;
        if (!window.matchMedia) return;
        if (!window.matchMedia('(hover: hover) and (pointer: fine)').matches) return;
        if (window.matchMedia('(pointer: coarse)').matches) return;
        if (document.querySelector('.cy-cur')) return;

        var ring = document.createElement('div');
        ring.className = 'cy-cur';
        ring.innerHTML = '<span class="cy-cur__ring"></span><span class="cy-cur__label">ACCESS</span>';
        var dot = document.createElement('div');
        dot.className = 'cy-cur__dot';
        document.body.appendChild(ring);
        document.body.appendChild(dot);
        // 元素与定位就绪后才隐藏原生光标
        root.classList.add('cy-cursor');

        var label = ring.querySelector('.cy-cur__label');
        var mx = window.innerWidth / 2, my = window.innerHeight / 2;
        var rx = mx, ry = my, shown = false, overField = false;

        window.addEventListener('mousemove', function (e) {
            mx = e.clientX; my = e.clientY;
            if (!shown) { shown = true; rx = mx; ry = my; ring.style.opacity = '1'; dot.style.opacity = '1'; }
        }, { passive: true });

        document.addEventListener('mouseleave', function () {
            ring.style.opacity = '0'; dot.style.opacity = '0';
        });
        document.addEventListener('mouseenter', function () {
            if (shown && !overField) { ring.style.opacity = '1'; dot.style.opacity = '1'; }
        });

        (function loop() {
            rx += (mx - rx) * .18;
            ry += (my - ry) * .18;
            ring.style.transform = 'translate3d(' + rx.toFixed(2) + 'px,' + ry.toFixed(2) + 'px,0)';
            dot.style.transform = 'translate3d(' + mx + 'px,' + my + 'px,0)';
            requestAnimationFrame(loop);
        })();

        var TAGS = [
            ['.gradient-bg', 'EXEC'],
            ['.chat-chip', 'QUERY'],
            ['nav a', 'NAV'],
            ['button', 'EXEC'],
            ['a', 'LINK']
        ];
        function classify(el) {
            for (var i = 0; i < TAGS.length; i++) {
                if (el.closest && el.closest(TAGS[i][0])) return TAGS[i][1];
            }
            return '';
        }
        document.addEventListener('mouseover', function (e) {
            var el = e.target;
            if (!el || !el.closest) return;
            if (el.closest('input, textarea, select, [contenteditable]')) {
                overField = true;
                ring.classList.remove('is-link');
                ring.style.opacity = '0'; dot.style.opacity = '0';
                return;
            }
            if (overField) { overField = false; ring.style.opacity = '1'; dot.style.opacity = '1'; }
            var tag = classify(el);
            if (tag) {
                label.textContent = tag;
                ring.classList.add('is-link');
            } else {
                ring.classList.remove('is-link');
            }
        });
        document.addEventListener('mouseout', function (e) {
            if (e.target && e.target.closest && e.target.closest('input, textarea, select')) {
                overField = false;
                ring.style.opacity = '1'; dot.style.opacity = '1';
            }
        });
        window.addEventListener('mousedown', function () { ring.classList.add('is-down'); });
        window.addEventListener('mouseup', function () { ring.classList.remove('is-down'); });
    }

    /* ------------------------------------------------------------------ 11. 卡片聚光 + 轻微倾斜 */
    function initProximity() {
        if (reduceMotion) return;
        Array.prototype.forEach.call(document.querySelectorAll('.card-hover'), function (card) {
            var raf = 0, tx = 0, ty = 0, lx = 0, ly = 0;
            card.addEventListener('mousemove', function (e) {
                var r = card.getBoundingClientRect();
                if (!r.width || !r.height) return;
                var px = (e.clientX - r.left) / r.width;
                var py = (e.clientY - r.top) / r.height;
                card.style.setProperty('--mx', (px * 100).toFixed(1) + '%');
                card.style.setProperty('--my', (py * 100).toFixed(1) + '%');
                if (r.width > 900) return;            // 大面板只聚光，不倾斜
                tx = (px - .5) * 2;
                ty = (py - .5) * 2;
                if (!raf) raf = requestAnimationFrame(apply);
            });
            function apply() {
                raf = 0;
                lx += (tx - lx) * .14;
                ly += (ty - ly) * .14;
                card.style.transform = 'perspective(900px) rotateY(' + (lx * 2).toFixed(2) +
                    'deg) rotateX(' + (-ly * 2).toFixed(2) + 'deg) translateY(-5px)';
                if (Math.abs(lx - tx) > .003 || Math.abs(ly - ty) > .003) raf = requestAnimationFrame(apply);
            }
            card.addEventListener('mouseleave', function () {
                tx = ty = 0;
                card.style.transform = '';
            });
        });
    }

    /* ------------------------------------------------------------------ 12. 按钮磁吸 */
    function initMagnetic() {
        if (reduceMotion) return;
        var els = Array.prototype.slice.call(document.querySelectorAll('.gradient-bg'));
        if (!els.length) return;
        var rects = [];
        function measure() {
            rects = els.map(function (el) { return el.getBoundingClientRect(); });
        }
        measure();
        window.addEventListener('resize', measure);
        window.addEventListener('scroll', function () { window.requestAnimationFrame(measure); }, { passive: true });

        var pending = false, px = 0, py = 0;
        window.addEventListener('mousemove', function (e) {
            px = e.clientX; py = e.clientY;
            if (pending) return;
            pending = true;
            window.requestAnimationFrame(function () {
                pending = false;
                for (var i = 0; i < els.length; i++) {
                    var r = rects[i];
                    if (!r || !r.width) continue;
                    var cx = r.left + r.width / 2, cy = r.top + r.height / 2;
                    var dx = px - cx, dy = py - cy;
                    var d = Math.sqrt(dx * dx + dy * dy);
                    if (d < 100) {
                        var f = (1 - d / 100) * 6;
                        els[i].style.transform = 'translate(' + (dx / d * f).toFixed(2) + 'px,' +
                            (dy / d * f).toFixed(2) + 'px)';
                    } else if (els[i].style.transform) {
                        els[i].style.transform = '';
                    }
                }
            });
        }, { passive: true });
    }

    /* ------------------------------------------------------------------ 13. 左下角静态状态条 */
    function initStatus() {
        if (document.querySelector('.cy-status')) return;
        var status = document.createElement('div');
        status.className = 'cy-status';
        status.setAttribute('aria-hidden', 'true');
        status.innerHTML = '<span class="cy-status__dot"></span>' +
            '<span class="cy-status__t">LINK OK · 12ms</span>';
        document.body.appendChild(status);
    }

    /* ------------------------------------------------------------------ 启动 */
    var revealReady = false;

    function boot() {
        if (root.dataset.cyFxBooted) return;      // 幂等
        root.dataset.cyFxBooted = '1';

        try { initHudChrome(); } catch (e) { }
        try { initSplit(); } catch (e) { }
        try { initReveal(); revealReady = true; } catch (e) { }
        try { initCounters(); } catch (e) { }
        try { initTicker(); } catch (e) { }
        try { initProgress(); } catch (e) { }
        try { initParticles(); } catch (e) { }
        try { initParallax(); } catch (e) { }
        try { initCursor(); } catch (e) { }
        try { initProximity(); } catch (e) { }
        try { initMagnetic(); } catch (e) { }
        try { initStatus(); } catch (e) { }

        window.setTimeout(function () {
            if (!revealReady) root.classList.remove('cy-js');
        }, 1500);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})();

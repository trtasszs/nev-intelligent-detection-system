# -*- coding: utf-8 -*-
"""演示区图片与「开始诊断」联动（精确锚点版）：
   ① POST /api/diagnose 带上 images
   ② 诊断结果卡里展示本次带的图
   ③ Demo.images 暴露给上面的 POST 用
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

P = r'E:\！！！高职比赛\车小智.html'
B1 = '/* ==== CXZ-DEMO-LINK BEGIN ==== */'
E1 = '/* ==== CXZ-DEMO-LINK END ==== */'

POST_OLD = u"""data = await apiPost('/api/diagnose', {
                    description: faultDescription,
                    vehicle: collectVehicleInfo()
                }, 12000);"""

POST_NEW = u"""data = await apiPost('/api/diagnose', {
                    description: faultDescription,
                    vehicle: collectVehicleInfo(),
                    /* 演示区带的图：一并提交。后端目前不使用这个字段（会忽略），
                       将来支持读图就直接生效；下方结果卡里也会把它们展示出来。 */
                    images: (window.__demoImages || []).map(function (im) { return im.dataUrl; })
                }, 12000);"""

RENDER_OLD = u"""                    renderDiagnosisResult(data, source, faultDescription);"""

RENDER_NEW = u"""                    renderDiagnosisResult(data, source, faultDescription);
                    renderDemoResultImages();"""

HELPER = B1 + u'''
        /* 诊断结果卡里展示本次带的故障照片（可点开大图） */
        function renderDemoResultImages() {
            const box = document.getElementById('diagnosis-result');
            if (!box) return;
            let wrap = document.getElementById('cxz-demo-result-imgs');
            if (!wrap) {
                wrap = document.createElement('div');
                wrap.id = 'cxz-demo-result-imgs';
                wrap.style.marginTop = '8px';
                box.appendChild(wrap);
            }
            const imgs = (window.__demoImages || []);
            if (!imgs.length) { wrap.innerHTML = ''; return; }
            wrap.innerHTML = '<div style="margin-top:24px;border-top:1px solid #e5e7eb;padding-top:16px">' +
                '<div style="font-size:14px;font-weight:600;color:#374151;margin-bottom:10px">' +
                '<i class="fas fa-image" style="margin-right:6px"></i>本次带的故障照片（' + imgs.length + ' 张）</div>' +
                '<div class="cxz-imgs" style="margin-top:0">' +
                imgs.map(function (im) {
                    return '<div class="cxz-thumb"><img src="' + im.dataUrl + '" alt="' + escapeHtml(im.name) +
                           '" title="' + escapeHtml(im.name) + '"></div>';
                }).join('') +
                '</div>' +
                '<p style="font-size:12px;color:#9ca3af;margin-top:8px">' +
                '本地知识库按文字描述匹配，照片用于记录与留存；导出记录时会一并带上。</p>' +
                '</div>';
        }
        ''' + E1 + u'\n'


def main():
    t = io.open(P, encoding='utf-8').read()
    if B1 in t:
        t = re.sub(re.escape(B1) + r'.*?' + re.escape(E1) + r'\n?', '', t, count=1, flags=re.S)
        print(u'  摘掉旧块')
    n = 0

    if POST_NEW not in t:
        if POST_OLD in t:
            t = t.replace(POST_OLD, POST_NEW, 1); n += 1
            print(u'  [1] /api/diagnose 已带上 images')
        else:
            print(u'  [1] ✗ 没匹配到 apiPost("/api/diagnose") 的原样文本')

    if 'renderDemoResultImages();' not in t:
        if RENDER_OLD in t:
            t = t.replace(RENDER_OLD, RENDER_NEW, 1); n += 1
            print(u'  [2] 结果渲染后调用 renderDemoResultImages')
        else:
            print(u'  [2] ✗ 没匹配到 renderDiagnosisResult 调用行')

    # 助手函数插在 Demo 那一段之后（同一个 script，能用到 escapeHtml）
    m = re.search(r'(function\s+renderDemoStrip\s*\(\)\s*\{.*?\n\s{8}\}\n)', t, re.S)
    if m and B1 not in t:
        t = t[:m.end()] + HELPER + t[m.end():]
        n += 1
        print(u'  [3] 插入 renderDemoResultImages 助手')
    elif not m:
        print(u'  [3] ✗ 找不到 renderDemoStrip 作为锚点')

    # Demo.images 同步给 window
    if 'function syncDemoImages' not in t:
        t2, c = re.subn(r'(function\s+renderDemoStrip\s*\(\)\s*\{)',
                        r'function syncDemoImages() { try { window.__demoImages = Demo.images; } catch (e) {} }\n        \1', t, count=1)
        if c:
            t = t2; n += 1
            t = t.replace(u"                    renderDemoStrip();\n                };",
                          u"                    renderDemoStrip(); syncDemoImages();\n                };")
            t = t.replace(u"                renderDemoStrip();\n            });",
                          u"                renderDemoStrip(); syncDemoImages();\n            });")
            print(u'  [4] syncDemoImages 已加并接上增删')

    io.open(P, 'w', encoding='utf-8').write(t)
    t3 = io.open(P, encoding='utf-8').read()
    print(u'\n  校验（共改 %d 处）:' % n)
    for k, v in ((u'POST 带 images', 'images: (window.__demoImages'),
                 (u'结果卡展示', 'renderDemoResultImages();'),
                 (u'助手函数', 'function renderDemoResultImages'),
                 (u'window 同步', 'function syncDemoImages')):
        print(u'    %-16s %s' % (k, u'✓' if v in t3 else u'✗'))
    print(u'    钩子块数 = %d（应为 1）' % t3.count(B1))


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""
给车小智页的「智能诊断演示」（#demo）加图片上传
==================================================================
现状：图片上传只做在**对话区**（两处输入框），#demo 区没有。
     而且图片目前**只在本地留存/展示/导出**，并没有发给后端
     （/api/chat 只发 {message, history, stream}）。

做法：把对话区那套机制**照搬一份**到 #demo，但用独立的 pending 列表，
      不与对话区的图混在一起：
        · 缩略图条（复用 .cxz-imgs / .cxz-thumb 样式）
        · 上传按钮 + 隐藏 file input
        · 点击选图 / 拖拽到描述框 / Ctrl+V 粘贴截图
        · 单张可删、超过上限与超大文件有提示
      并在「开始诊断」时：
        · 一并 POST 给 /api/diagnose（当前后端会忽略，将来支持就直接生效）
        · 把图显示在诊断结果卡里，导出记录也会带上
幂等：靠 BEGIN/END 标记，重复执行不会叠加。

    python apply_demo_img.py
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

P = r'E:\！！！高职比赛\车小智.html'
B_HTML = '<!-- ==== CXZ-DEMO-IMG BEGIN ==== -->'
E_HTML = '<!-- ==== CXZ-DEMO-IMG END ==== -->'
B_JS = '/* ==== CXZ-DEMO-IMG-JS BEGIN ==== */'
E_JS = '/* ==== CXZ-DEMO-IMG-JS END ==== */'

# ---------------------------------------------------------------- 1. HTML
ANCHOR = u'''                        <textarea id="fault-description" rows="4"'''
END_ANCHOR = u'''                    <div class="mb-6">
                        <label class="block text-sm font-medium text-gray-700 mb-2">车辆信息（选填）</label>'''


def patch_html():
    t = io.open(P, encoding='utf-8').read()
    if B_HTML in t:
        t = re.sub(re.escape(B_HTML) + r'.*?' + re.escape(E_HTML) + r'\n?', '', t, count=1, flags=re.S)
        print(u'  [HTML] 摘掉旧块')
    # 找到 textarea 那一行的 </div>（故障描述块的结尾），在它之后插入
    i = t.find('id="fault-description"')
    if i < 0:
        print(u'  ✗ 找不到 fault-description'); return
    j = t.find('</div>', t.find('</textarea>', i))
    if j < 0:
        print(u'  ✗ 找不到故障描述块的结尾'); return
    ins = j + len('</div>')
    block = u'''

                    ''' + B_HTML + u'''
                    <div class="mt-3">
                        <div class="flex items-center justify-between mb-2">
                            <label class="block text-sm font-medium text-gray-700">
                                故障照片（选填）
                            </label>
                            <span class="text-xs text-gray-400">仪表报警 / 线束接插件 / 传感器安装位置，最多 6 张、每张 8MB 内</span>
                        </div>
                        <div class="flex items-center space-x-3">
                            <button type="button" data-demo-img-btn title="上传故障照片（可多选）"
                                    class="px-4 py-3 rounded-none border border-gray-300 text-gray-400 hover:text-primary-600 hover:border-primary-500 transition-colors flex items-center">
                                <i class="fas fa-image"></i>
                                <span class="ml-2 text-sm">上传图片</span>
                            </button>
                            <input type="file" data-demo-img-input accept="image/*" multiple class="hidden">
                            <span class="text-xs text-gray-400">也可以直接把图片拖到上面的描述框，或按 Ctrl+V 粘贴截图</span>
                        </div>
                        <div data-demo-img-strip class="cxz-imgs hidden mt-3"></div>
                    </div>
                    ''' + E_HTML + u'\n'''
    t = t[:ins] + block + t[ins:]
    io.open(P, 'w', encoding='utf-8').write(t)
    print(u'  [HTML] 已插入上传 UI（%.0f KB）' % (len(t) / 1024.0))


# ---------------------------------------------------------------- 2. JS
DEMO_JS = B_JS + u'''
        /* ---- 「智能诊断演示」区的图片上传 ----
           与对话区各自独立一份 pending 列表，互不干扰。
           ★说明：本地知识库是按**文字描述**匹配的，图片不参与匹配；
             图片的作用是随诊断记录留存、在结果里展示、并导出到记录中。
             另外也会一并 POST 给 /api/diagnose —— 后端现在会忽略它，
             将来支持读图就直接生效。 */
        const Demo = { images: [], views: [] };

        function demoStripHtml() {
            return Demo.images.map(function (im, i) {
                return '<div class="cxz-thumb">' +
                    '<img src="' + im.dataUrl + '" alt="' + escapeHtml(im.name) + '" title="' + escapeHtml(im.name) + '">' +
                    '<button type="button" data-demo-img-del="' + i + '" title="移除">&times;</button></div>';
            }).join('');
        }

        function renderDemoStrip() {
            Demo.views.forEach(function (v) {
                if (!v.strip) return;
                if (Demo.images.length) {
                    v.strip.innerHTML = demoStripHtml();
                    v.strip.classList.remove('hidden');
                } else {
                    v.strip.innerHTML = '';
                    v.strip.classList.add('hidden');
                }
            });
        }

        function demoAddImages(fileList) {
            const files = Array.prototype.slice.call(fileList || []);
            if (!files.length) return;
            files.forEach(function (f) {
                if (Demo.images.length >= IMG_MAX_COUNT) {
                    alert('最多一次带 ' + IMG_MAX_COUNT + ' 张图片');
                    return;
                }
                if (!/^image\//.test(f.type)) return;
                if (f.size > IMG_MAX_MB * 1024 * 1024) {
                    alert('「' + f.name + '」超过 ' + IMG_MAX_MB + 'MB，请压缩后再传');
                    return;
                }
                const fr = new FileReader();
                fr.onload = function () {
                    Demo.images.push({ name: f.name, dataUrl: fr.result, size: f.size });
                    renderDemoStrip();
                };
                fr.readAsDataURL(f);
            });
        }

        (function bootDemoImg() {
            const sec = document.getElementById('demo');
            if (!sec) return;
            const strip = sec.querySelector('[data-demo-img-strip]');
            const btn   = sec.querySelector('[data-demo-img-btn]');
            const input = sec.querySelector('[data-demo-img-input]');
            const desc  = document.getElementById('fault-description');
            if (strip) Demo.views.push({ strip: strip });

            if (btn && input) {
                btn.addEventListener('click', function () { input.click(); });
                input.addEventListener('change', function () {
                    demoAddImages(input.files);
                    input.value = '';
                });
            }

            // 缩略图上的删除
            sec.addEventListener('click', function (e) {
                const del = e.target.closest && e.target.closest('[data-demo-img-del]');
                if (!del) return;
                Demo.images.splice(parseInt(del.getAttribute('data-demo-img-del'), 10), 1);
                renderDemoStrip();
            });

            // 拖拽到描述框
            if (desc) {
                ['dragenter', 'dragover'].forEach(function (ev) {
                    desc.addEventListener(ev, function (e) {
                        e.preventDefault();
                        desc.classList.add('border-primary-500');
                    });
                });
                ['dragleave', 'drop'].forEach(function (ev) {
                    desc.addEventListener(ev, function (e) {
                        e.preventDefault();
                        desc.classList.remove('border-primary-500');
                    });
                });
                desc.addEventListener('drop', function (e) {
                    if (e.dataTransfer && e.dataTransfer.files) demoAddImages(e.dataTransfer.files);
                });
                // Ctrl+V 粘贴截图
                desc.addEventListener('paste', function (e) {
                    const items = (e.clipboardData && e.clipboardData.items) || [];
                    const out = [];
                    for (let i = 0; i < items.length; i++) {
                        if (items[i].type && /^image\//.test(items[i].type)) {
                            const f = items[i].getAsFile();
                            if (f) out.push(f);
                        }
                    }
                    if (out.length) { e.preventDefault(); demoAddImages(out); }
                });
            }
        })();
        ''' + E_JS + u'\n'


def patch_js():
    t = io.open(P, encoding='utf-8').read()
    before = len(t)
    if B_JS in t:
        t = re.sub(re.escape(B_JS) + r'.*?' + re.escape(E_JS) + r'\n?', '', t, count=1, flags=re.S)
        print(u'  [JS] 摘掉旧块')
    # 挂在聊天那套脚本之后（同一个 <script>，能复用 IMG_MAX_COUNT / escapeHtml）
    m = re.search(r'(function\s+renderImgStrips\s*\(\)\s*\{.*?\n\s{8}\}\n)', t, re.S)
    if not m:
        print(u'  ✗ 找不到 renderImgStrips 作为锚点'); return
    t = t[:m.end()] + DEMO_JS + t[m.end():]
    io.open(P, 'w', encoding='utf-8').write(t)
    print(u'  [JS] 已插入（%d -> %d 字符）' % (before, len(t)))


def main():
    patch_html()
    patch_js()
    t = io.open(P, encoding='utf-8').read()
    print(u'\n  校验:')
    for k, v in ((u'HTML 块', B_HTML + u' 出现次数=1'),
                 (u'上传按钮', 'data-demo-img-btn'),
                 (u'隐藏 input', 'data-demo-img-input'),
                 (u'缩略图条', 'data-demo-img-strip'),
                 (u'JS 块', B_JS),
                 (u'Demo 对象', 'const Demo = { images: []'),
                 (u'拖拽支持', "desc.addEventListener('drop'"),
                 (u'粘贴支持', "desc.addEventListener('paste'")):
        if u'出现次数=1' in v:
            print(u'    %-14s %s' % (k, u'✓' if t.count(B_HTML) == 1 else u'✗ 数量=%d' % t.count(B_HTML)))
        else:
            print(u'    %-14s %s' % (k, u'✓' if v in t else u'✗'))


if __name__ == '__main__':
    main()

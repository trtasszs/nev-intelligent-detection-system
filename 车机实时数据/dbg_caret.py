# -*- coding: utf-8 -*-
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

for lab, path in ((u'页面', r'E:\！！！高职比赛\车小智.html'),
                  (u'片段', r'E:\！！！高职比赛\车小智-后端\boot_cxz.html')):
    t = io.open(path, encoding='utf-8').read()
    ms = list(re.finditer(r'<i[^>]*class="[^"]*cxb-caret[^"]*"[^>]*>', t))
    print(u'=== %s：<i class="cxb-caret"> 元素 %d 个 ===' % (lab, len(ms)))
    for m in ms:
        a = max(0, m.start() - 200)
        print(u'   元素: %s' % m.group(0))
        print(u'   上文: …%s' % ' '.join(t[a:m.start()].split())[-170:])
        print()
    # 反查：所有含 cxb-zhwrap 的地方
    print(u'   cxb-zhwrap 出现 %d 次' % t.count('cxb-zhwrap'))
    # 检查 caret 是否真的在 zhwrap 里（用括号配对大法不靠谱，直接看上下文）
    i = t.find('data-cxb-caret')
    if i > 0:
        print(u'   data-cxb-caret 上下文: …%s' % ' '.join(t[max(0, i - 300):i + 60].split())[-300:])
    print()

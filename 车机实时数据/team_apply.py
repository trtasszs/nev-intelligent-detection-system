# -*- coding: utf-8 -*-
"""把统一处理后的三张队员照与真实姓名写入 车小智.html 的「核心团队」区块"""
import io
import os
import re
import shutil
import time

PAGE = r'E:\！！！高职比赛\车小智.html'
B64 = os.environ['TEMP'] + r'\cx-boot\team_b64.txt'
NAMES = [u'孙仲星', u'徐子晗', u'郑永彬']          # 用户给定：从左往右

t = io.open(PAGE, encoding='utf-8').read()
n0 = len(t)
shutil.copy2(PAGE, PAGE + '.bak-team-' + time.strftime('%Y%m%d-%H%M%S'))

new_b64 = [l.strip() for l in io.open(B64, encoding='utf-8').read().splitlines() if l.strip()]
assert len(new_b64) == 3, u'base64 数量不对: %d' % len(new_b64)

# ---- ① 按顺序替换三张图片的 base64 ----
found = re.findall(r'data:image/jpeg;base64,([A-Za-z0-9+/=]{500,})', t)
print(u'   页面内原有大图 %d 张' % len(found))
for i, old in enumerate(found[:3]):
    t = t.replace(u'data:image/jpeg;base64,' + old,
                  u'data:image/jpeg;base64,' + new_b64[i], 1)
    print(u'   已替换第 %d 张' % (i + 1))

# ---- ② 图片样式：改为按 4:5 原生比例显示，别用固定高度把下半身裁掉 ----
old_img = (u'class="w-full h-72 object-cover object-top grayscale-[35%%] '
           u'group-hover:grayscale-0 transition-all duration-500"')
new_img = (u'style="aspect-ratio:4/5" '
           u'class="w-full object-cover object-top transition-transform duration-700 group-hover:scale-105"')
if old_img in t:
    t = t.replace(old_img, new_img)
    print(u'   图片样式已改为 4:5 原生比例 + 悬停轻推近')
else:
    # 兜底：按 class 里含 h-72 的那处改
    t2, n = re.subn(r'class="w-full h-72[^"]*"', new_img, t)
    if n:
        t = t2
        print(u'   图片样式已改（兜底匹配 %d 处）' % n)
    else:
        print(u'   [!] 没找到图片样式，跳过')

# ---- ③ 填名字 ----
n = 0
for nm in NAMES:
    if u'【姓名待填】' in t:
        t = t.replace(u'【姓名待填】', nm, 1)
        n += 1
print(u'   姓名占位符已替换 %d 处 -> %s' % (n, u' / '.join(NAMES)))

# ---- ④ alt 补上姓名 ----
for nm in NAMES:
    t = t.replace(u'alt="团队成员"', u'alt="%s"' % nm, 1)

# ---- 终检 ----
for k in (u'id="about"', u'</html>', u'id="bd-can-modal"', u'孙仲星', u'徐子晗', u'郑永彬'):
    if k not in t:
        print(u'[x] 终检失败：缺 %s —— 不写盘' % k)
        raise SystemExit(1)
if u'【姓名待填】' in t:
    print(u'[x] 仍有姓名占位符残留 —— 不写盘')
    raise SystemExit(1)

io.open(PAGE, 'w', encoding='utf-8').write(t)
print(u'   页面 %d -> %d 字符 (%.0f KB)' % (n0, len(t), len(t) / 1024.0))

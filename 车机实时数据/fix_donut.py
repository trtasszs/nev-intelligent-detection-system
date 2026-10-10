# -*- coding: utf-8 -*-
"""环形图四段配色去重（黑金红体系下要能分辨）"""
import io
import re

P = r'E:\！！！高职比赛\新能源汽车智能检测系统-1.0版.html'
t = io.open(P, encoding='utf-8').read()

# 第 1 个环形图：良好 / 正常 / 注意 / 需维护  → 浅金 / 深金 / 琥珀 / 红
D1 = u"backgroundColor: ['#E8D08A', '#A8862E', '#D4762A', '#D93A3A']"
# 第 2 个环形图：金 / 红 / 浅金 / 琥珀  → 深金 / 红 / 浅金 / 琥珀
D2 = u"backgroundColor: ['#A8862E', '#D93A3A', '#E8D08A', '#D4762A']"

seen = [0]


def rep(m):
    seen[0] += 1
    return D1 if seen[0] == 1 else D2


t2, n = re.subn(r'backgroundColor\s*:\s*\[[^\]]*\]', rep, t, count=2)
io.open(P, 'w', encoding='utf-8').write(t2)
print(u'环形图配色替换: %d 组' % n)
for m in re.finditer(r'backgroundColor\s*:\s*\[[^\]]*\]', t2):
    print(u'  ', m.group()[:120])

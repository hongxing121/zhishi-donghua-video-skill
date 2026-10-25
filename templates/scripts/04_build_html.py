"""第 4 步：pages.json + subs.json + voice.wav -> work/project/index.html（HyperFrames 合成页）。
pages.json：[{"start": 剪后秒数, "ch": 章节序号, "html": "页面HTML"}]
页面 HTML 里任何带 data-anim="up|scale|draw|bar|pill" + data-t="秒" 的元素，会在该时间进场
（data-t 用剪后时间轴，对照 subs.json / words.json 找到关键词被念出的时刻）。
用法：python3 scripts/04_build_html.py config.json"""
import json, os, re, html, math, shutil
import numpy as np
from common import *
C = load(); HERE = os.path.dirname(os.path.abspath(__file__)); TPL = os.path.join(HERE, '..', 'project')
proj = W(C, 'project'); os.makedirs(os.path.join(proj, 'assets'), exist_ok=True)
for f in ['assets/gsap.min.js', 'hyperframes.json', 'package.json', 'meta.json']:
    shutil.copy(os.path.join(TPL, f), os.path.join(proj, f))
shutil.copy(W(C, 'voice.wav'), os.path.join(proj, 'assets', 'voice.wav'))
cover = W(C, 'cover_9x16.png')
if os.path.exists(cover): shutil.copy(cover, os.path.join(proj, 'assets', 'cover.png'))
TOT = round(duration(W(C, 'voice.wav')), 3); COVER = C.get('cover', {}).get('duration', 0.3) if os.path.exists(cover) else 0
pages_path = P(C, C.get('pages', 'pages.json'))
pages = json.load(open(pages_path, encoding='utf-8'))
subs = json.load(open(W(C, 'subs.json'), encoding='utf-8'))
HL = C.get('subs', {}).get('highlight', [])
css = open(os.path.join(TPL, 'style.css'), encoding='utf-8').read()
extra = P(C, C['extra_css']) if C.get('extra_css') else None
if extra and os.path.exists(extra): css += '\n' + open(extra, encoding='utf-8').read()

js = []; body = ['<div class="page" id="p0"></div>']; el = []; cnt = [0]
for i, pg in enumerate(pages):
    st = pg['start']
    def rep(m):
        cnt[0] += 1; tag = m.group(0); a = re.search(r'data-anim="(\w+)"', tag).group(1)
        tm = re.search(r'data-t="([\d.]+)"', tag); t = float(tm.group(1)) if tm else st
        el.append((f'e{cnt[0]}', a, max(t - 0.08, st)))
        return tag.replace('<' + m.group(1), f'<{m.group(1)} id="e{cnt[0]}"', 1)
    body.append(f'<div class="page" id="p{i+1}">' + re.sub(r'<(\w+)(?=[^>]*data-anim=)[^>]*>', rep, pg['html']) + '</div>')
pl = [(e, t) for e, a, t in el if a == 'pill']
for (e1, t1), (e2, t2) in zip(pl, pl[1:]):          # 下一个药丸被念到时，上一个取消黄色高亮
    if 0 < t2 - t1 < 6: js.append(f'tl.to("#{e1}",{{backgroundColor:"rgba(246,212,74,0)",duration:.25}},{t2});')
for e, a, t in el:
    if a == 'up': js.append(f'tl.fromTo("#{e}",{{y:60,autoAlpha:0}},{{y:0,autoAlpha:1,duration:.55,ease:"power3.out"}},{t});')
    elif a == 'scale': js.append(f'tl.fromTo("#{e}",{{scale:.4,autoAlpha:0,transformOrigin:"50% 50%"}},{{scale:1,autoAlpha:1,duration:.6,ease:"back.out(1.6)"}},{t});')
    elif a == 'draw': js.append(f'(function(){{var el=document.getElementById("{e}");var L=el.getTotalLength?el.getTotalLength():1000;gsap.set(el,{{strokeDasharray:L,strokeDashoffset:L}});tl.set(el,{{opacity:1}},{t});tl.fromTo(el,{{strokeDashoffset:L}},{{strokeDashoffset:0,duration:.8,ease:"power2.inOut"}},{t});}})();')
    elif a == 'bar': js.append(f'tl.fromTo("#{e}",{{scaleX:0,transformOrigin:"0% 50%"}},{{scaleX:1,duration:.9,ease:"power3.out"}},{t});')
    elif a == 'pill': js.append(f'tl.fromTo("#{e}",{{y:40,autoAlpha:0}},{{y:0,autoAlpha:1,duration:.45,ease:"power3.out"}},{t});tl.to("#{e}",{{backgroundColor:"#F6D44A",borderColor:"#222",scale:1.08,duration:.3}},{t+0.05});tl.to("#{e}",{{scale:1,duration:.3}},{t+0.4});')
prev = '#p0'
for i, pg in enumerate(pages):                      # 换页：旧页上滑淡出，新页从下滑入
    t0 = max(COVER, pg['start'] - 0.3) if i else COVER
    js.append(f'tl.to("{prev}",{{y:-120,autoAlpha:0,duration:.3,ease:"power2.in"}},{t0});tl.fromTo("#p{i+1}",{{y:120,autoAlpha:0}},{{y:0,autoAlpha:1,duration:.35,ease:"power2.out"}},{t0+0.2});'); prev = f'#p{i+1}'
last = None
for i, pg in enumerate(pages):                      # 章节导航：当前章节标红
    if pg['ch'] != last:
        t = COVER if i == 0 else max(COVER, pg['start'] - 0.1)
        js.append(f'tl.set(".nav",{{color:"#999",fontWeight:400}},{t});tl.set(".n{pg["ch"]}",{{color:"#B22222",fontWeight:700}},{t});'); last = pg['ch']
sh_ = ''
for k, s in enumerate(subs):
    t = html.escape(s['text'])
    for h in HL: t = t.replace(html.escape(h), f'<span class="hl">{html.escape(h)}</span>')
    sh_ += f'<div class="subt" id="s{k}">{t}</div>'
    js.append(f'tl.set("#s{k}",{{autoAlpha:1}},{max(s["start"], COVER)});tl.set("#s{k}",{{autoAlpha:0}},{s["end"]});')
# 头像光圈 + 4 根声波条：跟随配音音量（15Hz RMS 包络）
x, sr = read_wav_mono(W(C, 'voice.wav')); hop = sr // 15; n = len(x) // hop
db = 20 * np.log10(np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-9) / 32768); v = np.clip((db + 45) / 30, 0, 1)
env = []; a = 0
for y in v: a = a + (y - a) * (0.6 if y > a else 0.25); env.append(float(a))
for k, vv in enumerate(env):
    t = round(k / 15, 3)
    if t < COVER: continue
    js.append(f'tl.to("#glow",{{opacity:{0.15+0.85*vv:.2f},duration:.067,ease:"none"}},{t});' + ''.join(
        f'tl.to("#wave i:nth-child({i+1})",{{scaleY:{0.15+0.85*vv*(0.55+0.45*abs(math.sin(k*1.3+i*1.9))):.2f},duration:.067,ease:"none"}},{t});' for i in range(4)))
js.append(f'tl.set("#av",{{autoAlpha:0}},0);tl.set("#av",{{autoAlpha:1}},{COVER});')
if COVER: js.append(f'tl.set("#cov",{{autoAlpha:0}},{COVER});')
js.append(f'tl.set("#endpad",{{opacity:1}},{TOT-0.01});')
ch = C.get('chapters', [])
navs = ''.join(f'<span class="nav n{k}">{html.escape(c)}</span>' + ('<span class="sep">/</span>' if k < len(ch) - 1 else '') for k, c in enumerate(ch))
cz = C.get('circle', {}); AVX, AVY, AVS = cz.get('x', 110), cz.get('y', 1208), cz.get('size', 190) + 2 * cz.get('ring', 5)
FPS = C.get('fps', 30)
doc = f'''<!doctype html><html><head><meta charset="utf-8"><style>{css}
#av{{left:{AVX}px;top:{AVY}px;width:{AVS}px;height:{AVS}px}}</style></head><body>
<div id="main" data-composition-id="main" data-start="0" data-duration="{TOT}" data-fps="{FPS}" data-width="1080" data-height="1920">
<div class="topbar"><div class="ttl">{html.escape(C.get('title',''))}</div><div class="navrow">{navs}</div></div>
<div class="stage withav">{''.join(body)}</div>
<div class="subs">{sh_}</div>
<div id="av"><div id="glow"></div><div id="avs"><div id="avhole"></div><div class="ring"></div></div><div id="wave"><i></i><i></i><i></i><i></i></div></div>
{'<img id="cov" src="assets/cover.png">' if COVER else ''}<div id="endpad"></div>
<audio id="vo" src="assets/voice.wav" data-start="0" data-duration="{TOT}" data-track-index="1"></audio>
<script src="assets/gsap.min.js"></script>
<script>
var tl=gsap.timeline({{paused:true}});
gsap.set(".page,.subt",{{autoAlpha:0}});
{chr(10).join(js)}
window.__timelines=window.__timelines||{{}};window.__timelines.main=tl;
</script></div></body></html>'''
open(os.path.join(proj, 'index.html'), 'w', encoding='utf-8').write(doc)
print(f'ok {len(pages)} 页, {len(subs)} 行字幕, {TOT}s -> {proj}/index.html')

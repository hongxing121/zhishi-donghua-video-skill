"""第 8 步：QA。抽 12 帧拼成联系表（qa_sheet.png），并在每帧上画出安全区参考线（qa_guides.png）。
红色半透明 = 禁区（顶部 0–170 状态栏；右下时间标签区）；绿色框 = 内容区 350–1200；蓝线 = 字幕区 1400–1490。
用法：python3 scripts/08_qa.py config.json [视频路径，默认 out/final.mp4]"""
import os, sys
from PIL import Image, ImageDraw
from common import *
C = load(); out = P(C, C.get('out_dir', 'out'))
v = sys.argv[2] if len(sys.argv) > 2 else os.path.join(out, 'final.mp4'); D = duration(v)
ts = [0.05] + [D * (i + 0.5) / 11 for i in range(11)]
frames = []
for i, t in enumerate(ts):
    f = W(C, f'qa_{i:02d}.png'); sh(['ffmpeg', '-y', '-v', 'error', '-ss', f'{t:.2f}', '-i', v, '-frames:v', '1', f]); frames.append(Image.open(f).convert('RGB'))
def guides(im):
    ov = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rectangle((0, 0, 1080, 170), fill=(255, 0, 0, 70))
    d.rectangle((0, 350, 1079, 1200), outline=(0, 160, 0, 255), width=4)
    d.rectangle((0, 1400, 1079, 1490), outline=(0, 90, 255, 255), width=4)
    d.rectangle((900, 1400, 1080, 1490), fill=(255, 0, 0, 60))
    d.line((97, 0, 97, 1920), fill=(255, 128, 0, 200), width=3); d.line((983, 0, 983, 1920), fill=(255, 128, 0, 200), width=3)
    return Image.alpha_composite(im.convert('RGBA'), ov).convert('RGB')
th = [f.resize((270, 480)) for f in frames]
sheet = Image.new('RGB', (270 * 6, 480 * 2), 'white')
for i, t in enumerate(th): sheet.paste(t, ((i % 6) * 270, (i // 6) * 480))
sheet.save(os.path.join(out, 'qa_sheet.png'))
g = [guides(f).resize((360, 640)) for f in frames[1:5]]
gs = Image.new('RGB', (360 * 4, 640), 'white')
for i, t in enumerate(g): gs.paste(t, (i * 360, 0))
gs.save(os.path.join(out, 'qa_guides.png'))
print('ok ->', os.path.join(out, 'qa_sheet.png'), os.path.join(out, 'qa_guides.png'))

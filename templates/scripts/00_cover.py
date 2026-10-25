"""封面：照片铺满 + 中下部深色圆角框 + 两行黄色粗体字。输出 work/cover_9x16.png 和 work/cover_3x4.png。
照片来源：config.cover.photo（图片路径）；为 null 时从原视频 photo_time 秒截一帧（建议另找清晰照片）。
用法：python3 scripts/00_cover.py config.json"""
import subprocess
from PIL import Image, ImageDraw, ImageFont
from common import *
C = load(); c = C.get('cover', {})
src = P(C, c['photo']) if c.get('photo') else None
if not src:
    src = W(C, 'cover_src.png')
    sh(['ffmpeg', '-y', '-v', 'error', '-ss', str(c.get('photo_time', 1.0)), '-i', P(C, C['source_video']), '-frames:v', '1', src])
im0 = Image.open(src).convert('RGB')
def font_path():
    for q in ['Noto Sans CJK SC:style=Bold', 'Source Han Sans SC:style=Bold', 'PingFang SC:style=Semibold', 'sans-serif:lang=zh-cn:style=Bold']:
        try:
            p = subprocess.check_output(['fc-match', '-f', '%{file}', q]).decode().strip()
            if p: return p
        except Exception: pass
    raise SystemExit('找不到中文粗体字体，请先按 INSTALL.md 安装 Noto Sans CJK SC')
fp = font_path(); size = c.get('font_size', 110)
def load_font():
    for idx in range(0, 12):            # .ttc 里找简体中文那个 face
        try:
            f = ImageFont.truetype(fp, size, index=idx)
            if 'SC' in ' '.join(f.getname()) or not fp.endswith('.ttc'): return f
        except Exception: break
    return ImageFont.truetype(fp, size)
font = load_font()
def fit(Wd, Ht):
    im = im0.copy(); s = max(Wd / im.width, Ht / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x0 = (im.width - Wd) // 2; y0 = int((im.height - Ht) * c.get('focus_y', 0.35)); return im.crop((x0, y0, x0 + Wd, y0 + Ht))
def draw(im, box):
    ov = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(ov).rounded_rectangle(box, radius=24, fill=(28, 28, 28, 240))
    im = Image.alpha_composite(im.convert('RGBA'), ov); dr = ImageDraw.Draw(im)
    lines = c.get('lines', []); lh = size * 1.3; y = (box[1] + box[3]) / 2 - lh * len(lines) / 2 + lh / 2
    for l in lines:
        dr.text(((box[0] + box[2]) / 2, y), l, font=font, fill=(255, 206, 0), anchor='mm'); y += lh
    return im.convert('RGB')
draw(fit(1080, 1920), (32, 988, 1048, 1404)).save(W(C, 'cover_9x16.png'))
draw(fit(1080, 1440), (32, 780, 1048, 1196)).save(W(C, 'cover_3x4.png'))
print('ok ->', W(C, 'cover_9x16.png'), W(C, 'cover_3x4.png'), '字体:', fp)

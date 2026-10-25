"""第 7 步：合成成片。base.mp4（排版动画）+ circ.mp4（圆形遮罩，盖在头像灰圆位置）+ voice.wav
-> out/final.mp4（1080x1920 30fps H.264+AAC）和 out/preview_540.mp4（小样）。
speed != 1 时整片同步变速（setpts + atempo，变速不变调），画面/字幕/口型仍然对齐。
用法：python3 scripts/07_compose.py config.json"""
import os, shutil
from PIL import Image, ImageDraw
from common import *
C = load(); cz = C.get('circle', {}); S = cz.get('size', 190); R = cz.get('ring', 5)
X, Y = cz.get('x', 110) + R, cz.get('y', 1208) + R
SP = float(C.get('speed', 1.0)); FPS = C.get('fps', 30)
m = Image.new('L', (S * 4, S * 4), 0); ImageDraw.Draw(m).ellipse((0, 0, S * 4 - 1, S * 4 - 1), fill=255)
m.resize((S, S), Image.LANCZOS).save(W(C, 'mask.png'))          # 4x 超采样，边缘抗锯齿
cover = W(C, 'cover_9x16.png'); CD = C.get('cover', {}).get('duration', 0.3)
out = P(C, C.get('out_dir', 'out')); os.makedirs(out, exist_ok=True)
sp_v = f',setpts=PTS/{SP}' if SP != 1 else ''; sp_a = f'atempo={SP},' if SP != 1 else ''
fc = (f'[1:v]format=rgba[c];[2:v]format=gray,scale={S}:{S}[m];[c][m]alphamerge[cm];'
      f'[0:v][cm]overlay={X}:{Y}:shortest=1:enable=\'gte(t,{CD})\'[v1];')
inputs = ['-i', W(C, 'base.mp4'), '-i', W(C, 'circ.mp4'), '-loop', '1', '-i', W(C, 'mask.png'), '-i', W(C, 'voice.wav')]
if os.path.exists(cover):
    inputs += ['-loop', '1', '-t', str(CD), '-i', cover]
    fc += f'[4:v]scale=1080:1920,setsar=1[cv];[v1][cv]overlay=enable=\'lt(t,{CD})\':eof_action=pass[v2];[v2]fps={FPS}{sp_v},format=yuv420p[vo];'
else:
    fc += f'[v1]fps={FPS}{sp_v},format=yuv420p[vo];'
fc += f'[3:a]{sp_a}aresample=48000,pan=stereo|c0=c0|c1=c0[ao]'
sh(['ffmpeg', '-y', '-v', 'error', *inputs, '-filter_complex', fc, '-map', '[vo]', '-map', '[ao]',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-r', str(FPS), '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', os.path.join(out, 'final.mp4')])
sh(['ffmpeg', '-y', '-v', 'error', '-i', os.path.join(out, 'final.mp4'), '-vf', 'scale=540:960', '-c:v', 'libx264', '-crf', '23', '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', os.path.join(out, 'preview_540.mp4')])
for f in ['cover_9x16.png', 'cover_3x4.png', 'final.srt']:
    if os.path.exists(W(C, f)): shutil.copy(W(C, f), out)
print('ok ->', out, f'{duration(os.path.join(out, "final.mp4")):.2f}s')

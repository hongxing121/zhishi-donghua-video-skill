"""第 6 步：真人圆窗素材 work/circ.mp4（size x size，30fps，与剪后时间轴逐帧对齐）。
关键：手机录的视频常是 VFR（可变帧率），不能按「帧号/帧率」算时间。这里先用 ffprobe 读出每一帧真实的
时间戳（pts），再对剪后时间轴的每个输出帧 k：原片时间 = cut2src(k/fps)，取 pts ≤ 该时间的最后一帧。
这样跳剪后嘴型与配音始终对齐，不会越往后越错位。
crop = [x, y, 边长]（原视频像素，取脸部正方形）；null 时自动取画面上部居中的正方形。
用法：python3 scripts/06_circle.py config.json"""
import bisect, json, subprocess
from common import *
C = load(); K = keep(C); cz = C.get('circle', {}); S = cz.get('size', 190); FPS = C.get('fps', 30)
src = P(C, C['source_video'])
info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height:stream_tags=rotate:stream_side_data=rotation', '-of', 'json', src]))['streams'][0]
w, h = info['width'], info['height']
rot = abs(int(float((info.get('tags') or {}).get('rotate', 0) or next((s.get('rotation', 0) for s in info.get('side_data_list', [])), 0))))
if rot in (90, 270): w, h = h, w
crop = cz.get('crop') or [0, int(h * 0.12), min(w, h)]
if not cz.get('crop'): crop[0] = (w - crop[2]) // 2
x, y, s = crop
print('crop', crop, 'src', w, 'x', h)
# 1) 每帧真实时间戳（与解码出的帧一一对应）
pts = [float(v.strip(',')) for v in subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'frame=best_effort_timestamp_time', '-of', 'csv=p=0', src]).decode().split() if v.strip(',') not in ('', 'N/A')]
pts = [p - pts[0] for p in pts]
open(W(C, 'pts.txt'), 'w').write('\n'.join(f'{p:.6f}' for p in pts))
D = sum(b - a for a, b in K); N = int(round(D * FPS))
# 2) 解码全部帧（passthrough，不补帧不丢帧）→ 按时间戳挑帧 → 编码成恒定 30fps
dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', src, '-vf', f'crop={s}:{s}:{x}:{y},scale={S}:{S}:flags=lanczos', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-fps_mode', 'passthrough', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{S}x{S}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '14', '-pix_fmt', 'yuv420p', W(C, 'circ.mp4')], stdin=subprocess.PIPE)
fs = S * S * 3; cur = -1; buf = None
for k in range(N):
    want = max(0, bisect.bisect_right(pts, cut2src(K, k / FPS) + 0.5 / FPS) - 1)
    while cur < want:
        b = dec.stdout.read(fs)
        if len(b) < fs: break
        buf = b; cur += 1
    enc.stdin.write(buf)
enc.stdin.close(); enc.wait(); dec.kill()
print(f'ok {N} 帧 -> {W(C, "circ.mp4")}（用到原片第 {cur} 帧 / 共 {len(pts)} 帧）')

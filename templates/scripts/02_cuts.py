"""第 2 步：剪掉停顿/口误，生成 work/cuts.json（保留段，原片秒数）和 work/voice.wav（剪后配音）。
- 自动：能量低于（第10百分位+4dB）且长于 min_silence 秒的静音段，两端各留 pad 秒。
- 手动：config.cuts.manual_remove = [[开始,结束], ...]（原片秒数，听 words.json 找口误/重复）。
- trim = [开头, 结尾]，结尾 null 表示到片尾。
用法：python3 scripts/02_cuts.py config.json"""
import json, numpy as np
from common import *
C = load(); cc = C.get('cuts', {})
x, sr = read_wav_mono(W(C, 'a16.wav')); A = x / 32768
D = len(A) / sr
f = int(0.02 * sr); n = len(A) // f
e = 20 * np.log10(np.sqrt((A[:n * f].reshape(n, f) ** 2).mean(1)) + 1e-9)
th = np.percentile(e, 10) + 4
rm = []
if cc.get('auto_silence', True):
    q = e < th; i = 0
    while i < n:
        if q[i]:
            j = i
            while j < n and q[j]: j += 1
            a, b = i * .02, j * .02
            if b - a > cc.get('min_silence', 0.3): rm.append([a + cc.get('pad', .07), b - cc.get('pad', .07)])
            i = j
        else: i += 1
t0, t1 = (cc.get("trim") or [0, None])
t1 = D if t1 is None else min(t1, D)
rm += [list(r) for r in cc.get('manual_remove', [])] + [[0, t0], [t1, D + 1]]
rm.sort(); m = []
for a, b in rm:
    if b <= a: continue
    if m and a <= m[-1][1] + 0.05: m[-1][1] = max(m[-1][1], b)
    else: m.append([a, b])
K = []; t = 0
for a, b in m:
    if a - t > 0.06: K.append([round(t, 3), round(a, 3)])
    t = b
if D - t > 0.06: K.append([round(t, 3), round(D, 3)])
json.dump({'keep': K, 'removed': m}, open(W(C, 'cuts.json'), 'w'), indent=1)
# 剪配音（48k），每个接缝 12ms 淡入淡出防爆音
x, sr = read_wav_mono(W(C, 'a48.wav')); F = int(0.012 * sr); out = []
for a, b in K:
    s = x[int(a * sr):int(b * sr)].copy()
    if len(s) > 2 * F:
        r = np.linspace(0, 1, F); s[:F] *= r; s[-F:] *= r[::-1]
    out.append(s)
write_wav_mono(W(C, 'voice_raw.wav'), np.concatenate(out), sr)
sh(['ffmpeg', '-y', '-v', 'error', '-i', W(C, 'voice_raw.wav'), '-af',
    'highpass=f=70,afftdn=nf=-28,loudnorm=I=-16:TP=-1.5:LRA=11', '-ar', '48000', '-ac', '1', W(C, 'voice.wav')])
print(f'保留 {len(K)} 段，剪后 {sum(b-a for a,b in K):.2f}s（原 {D:.2f}s）')

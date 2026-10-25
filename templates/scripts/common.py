"""公共工具：读取 config.json、路径、ffmpeg 调用、剪辑时间映射。"""
import json, os, subprocess, sys

def load(cfg_path=None):
    cfg_path = os.path.abspath(cfg_path or (sys.argv[1] if len(sys.argv) > 1 else 'config.json'))
    C = json.load(open(cfg_path, encoding='utf-8'))
    C['_root'] = os.path.dirname(cfg_path)
    C['_work'] = P(C, C.get('work_dir', 'work'))
    os.makedirs(C['_work'], exist_ok=True)
    return C

def P(C, rel):
    return rel if os.path.isabs(rel) else os.path.join(C['_root'], rel)

def W(C, name):
    return os.path.join(C['_work'], name)

def sh(cmd, **kw):
    print('+', cmd if isinstance(cmd, str) else ' '.join(map(str, cmd)), flush=True)
    subprocess.run(cmd, shell=isinstance(cmd, str), check=True, **kw)

def duration(f):
    return float(subprocess.check_output(['ffprobe', '-v', '0', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]).decode())

def keep(C):
    return json.load(open(W(C, 'cuts.json')))['keep']

def src2cut(K, t):
    """原片时间 -> 剪后时间（落在被剪掉区间里的点会贴到下一个保留段开头）"""
    acc = 0.0
    for a, b in K:
        if t < a: return acc
        if t <= b: return acc + t - a
        acc += b - a
    return acc

def cut2src(K, t):
    """剪后时间 -> 原片时间"""
    for a, b in K:
        if t < b - a: return a + t
        t -= b - a
    return K[-1][1]

def read_wav_mono(path):
    import numpy as np, wave
    w = wave.open(path); sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype('float32')
    if w.getnchannels() > 1: x = x.reshape(-1, w.getnchannels()).mean(1)
    return x, sr

def write_wav_mono(path, x, sr):
    import numpy as np, wave
    w = wave.open(path, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes(np.clip(x, -32768, 32767).astype(np.int16).tobytes()); w.close()

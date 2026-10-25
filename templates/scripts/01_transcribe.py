"""第 1 步：抽音频 + faster-whisper 逐字转写（本地开源模型，不需要任何 API Key）。
输出 work/a16.wav（16k 单声道）、work/a48.wav（48k 单声道，成片用）、work/words.json
用法：python3 scripts/01_transcribe.py config.json"""
import json
from common import *
C = load()
src = P(C, C['source_video'])
sh(['ffmpeg', '-y', '-v', 'error', '-i', src, '-vn', '-ac', '1', '-ar', '16000', W(C, 'a16.wav')])
sh(['ffmpeg', '-y', '-v', 'error', '-i', src, '-vn', '-ac', '1', '-ar', '48000', W(C, 'a48.wav')])
from faster_whisper import WhisperModel
wc = C.get('whisper', {})
m = WhisperModel(wc.get('model', 'medium'), device=wc.get('device', 'cpu'), compute_type=wc.get('compute_type', 'int8'))
x, sr = read_wav_mono(W(C, 'a16.wav'))
segs, _ = m.transcribe(x / 32768, language=wc.get('language', 'zh'), word_timestamps=True, vad_filter=False,
                       condition_on_previous_text=False, beam_size=5, initial_prompt=wc.get('initial_prompt') or None)
out = []
for g in segs:
    out.append({'s': g.start, 'e': g.end, 't': g.text, 'w': [[w.start, w.end, w.word] for w in g.words]})
    print(f'{g.start:7.2f}-{g.end:7.2f} {g.text}', flush=True)
json.dump(out, open(W(C, 'words.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok ->', W(C, 'words.json'))

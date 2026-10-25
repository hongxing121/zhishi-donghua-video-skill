"""第 3 步：由 words.json + cuts.json 生成字幕（剪后时间轴）。
输出 work/subs.json（可手工改字/改时间，再跑 04 即生效）和 work/final.srt。
规则：单行 ≤ max_chars 字；优先在标点/停顿处断；不在数字中间断；去掉句末标点。
已存在 subs.json 时不覆盖（加 --force 重新生成）。
用法：python3 scripts/03_subs.py config.json [--force]"""
import json, re, sys, os
from common import *
C = load(); K = keep(C); MX = C.get('subs', {}).get('max_chars', 16)
out_json = W(C, 'subs.json')
if os.path.exists(out_json) and '--force' not in sys.argv:
    print('subs.json 已存在，保留手工修改；要重建请加 --force'); S = json.load(open(out_json, encoding='utf-8'))
else:
    words = [w for g in json.load(open(W(C, 'words.json'), encoding='utf-8')) for w in g['w']]
    PUNC = '，。！？、,.!?；;：:'
    lines = []; cur = []
    def flush():
        global cur
        if cur:
            txt = re.sub(f'[{re.escape(PUNC)}]', ' ', ''.join(w[2] for w in cur)).strip()
            txt = re.sub(r'\s+', ' ', txt)
            if txt: lines.append([cur[0][0], cur[-1][1], txt])
        cur = []
    for i, w in enumerate(words):
        w = [w[0], w[1], w[2].strip()]
        if not w[2]: continue
        ln = len(''.join(x[2] for x in cur))
        gap = w[0] - cur[-1][1] if cur else 0
        digit_join = cur and re.search(r'[\d.]$', cur[-1][2]) and re.match(r'^[\d.%]', w[2])
        if cur and not digit_join and (ln + len(w[2]) > MX or gap > 0.35): flush()
        cur.append(w)
        if w[2][-1] in PUNC and len(''.join(x[2] for x in cur)) >= 4: flush()
    flush()
    S = []
    for a, b, t in lines:
        x, y = src2cut(K, a), src2cut(K, b)
        if y - x >= 0.2: S.append({'start': round(x, 3), 'end': round(y, 3), 'text': t})
    for i in range(len(S) - 1):          # 前一句一直显示到下一句开始（间隔 <0.6s 时）
        if 0 < S[i + 1]['start'] - S[i]['end'] < 0.6: S[i]['end'] = S[i + 1]['start']
    json.dump(S, open(out_json, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
def ts(t):
    return f'{int(t//3600):02d}:{int(t%3600//60):02d}:{int(t%60):02d},{int(round((t%1)*1000))%1000:03d}'
open(W(C, 'final.srt'), 'w', encoding='utf-8').write('\n'.join(f"{i+1}\n{ts(s['start'])} --> {ts(s['end'])}\n{s['text']}\n" for i, s in enumerate(S)))
bad = [s['text'] for s in S if len(s['text'].replace(' ', '')) > MX]
print(f'{len(S)} 行字幕 -> {out_json}', '；超长：' + str(bad) if bad else '')

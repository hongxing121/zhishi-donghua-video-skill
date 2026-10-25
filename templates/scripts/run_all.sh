#!/usr/bin/env bash
# 一键跑完整流程（转写 → 剪辑 → 字幕 → 封面 → HTML → 渲染 → 圆窗 → 合成 → QA）
# 注意：第一次跑时，在 03 之后应先人工检查 work/subs.json 并写好 pages.json，再继续。
# 用法：bash scripts/run_all.sh config.json [起始步骤号，默认 1]
set -euo pipefail
D=$(cd "$(dirname "$0")" && pwd); CFG=${1:-config.json}; FROM=${2:-1}
step(){ [ "$1" -ge "$FROM" ]; }
step 1 && python3 "$D/01_transcribe.py" "$CFG"
step 2 && python3 "$D/02_cuts.py" "$CFG"
step 3 && python3 "$D/03_subs.py" "$CFG"
step 4 && python3 "$D/00_cover.py" "$CFG" && python3 "$D/04_build_html.py" "$CFG"
step 5 && bash "$D/05_render.sh" "$CFG"
step 6 && python3 "$D/06_circle.py" "$CFG"
step 7 && python3 "$D/07_compose.py" "$CFG"
step 8 && python3 "$D/08_qa.py" "$CFG"
echo "全部完成"

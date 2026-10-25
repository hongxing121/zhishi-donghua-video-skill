#!/usr/bin/env bash
# 第 5 步：HyperFrames 渲染 work/project/index.html -> work/base.mp4（只有排版动画 + 头像占位灰圆）
# 用法：bash scripts/05_render.sh config.json
set -euo pipefail
CFG=$(cd "$(dirname "${1:-config.json}")" && pwd)/$(basename "${1:-config.json}")
read -r WORK VER NODEBIN FPS < <(python3 - "$CFG" <<'PY'
import json,os,sys
c=json.load(open(sys.argv[1]));r=os.path.dirname(sys.argv[1]);w=c.get('work_dir','work')
w=w if os.path.isabs(w) else os.path.join(r,w);h=c.get('hyperframes',{})
print(w,h.get('version','0.8.190'),h.get('node_bin') or '-',c.get('fps',30))
PY
)
[ "$NODEBIN" != "-" ] && export PATH="$NODEBIN:$PATH"
node -v | grep -q '^v2[2-9]' || { echo "需要 Node 22+（当前 $(node -v 2>/dev/null)）"; exit 1; }
export HYPERFRAMES_SKIP_SKILLS=1 HYPERFRAMES_NO_TELEMETRY=1 DO_NOT_TRACK=1
cd "$WORK/project"
npx --yes "hyperframes@$VER" render . -o ../base.mp4 --quality delivery --fps "$FPS"
echo "ok -> $WORK/base.mp4"

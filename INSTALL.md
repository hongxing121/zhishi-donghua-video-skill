# 环境安装（Linux / macOS）

需要：**Node 22+、ffmpeg（含 ffprobe，需 libass/libx264）、Python 3.9+（faster-whisper、numpy、Pillow）、中文字体 Noto Sans/Serif CJK SC**。HyperFrames 首次运行会自动下载无头 Chromium。

## Linux（Ubuntu/Debian）
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg python3 python3-pip python3-venv fonts-noto-cjk fonts-noto-cjk-extra fontconfig
# Node 22（任选其一）
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - && sudo apt-get install -y nodejs
#   或无 root：npm 包形式装一个局部 Node 22
#   mkdir -p ~/node22 && cd ~/node22 && npm i node@22   →  bin 在 ~/node22/node_modules/node/bin
# Chromium 运行库（无头渲染需要；HyperFrames 缺库时会提示）
sudo apt-get install -y libnss3 libatk-bridge2.0-0 libgbm1 libxkbcommon0 libasound2 || sudo apt-get install -y libasound2t64
```

## macOS（Homebrew）
```bash
brew install ffmpeg node@22 python
brew link --overwrite node@22
brew install --cask font-noto-sans-cjk-sc font-noto-serif-cjk-sc
```

## Python 依赖
```bash
python3 -m venv ~/.venv/kt && source ~/.venv/kt/bin/activate
pip install -U faster-whisper numpy pillow
# 国内网络：pip install -i https://pypi.tuna.tsinghua.edu.cn/simple ...；模型下载可 export HF_ENDPOINT=https://hf-mirror.com
```
有 NVIDIA GPU 时可在 config 里设 `"whisper": {"device": "cuda", "compute_type": "float16"}`。

## HyperFrames（HTML + GSAP → MP4 渲染器）
无需全局安装，脚本用 `npx --yes hyperframes@0.8.190` 自动拉取：
```bash
node -v          # 必须 v22 或更高
npx --yes hyperframes@0.8.190 --help
```
（建议固定版本号 0.8.190，这是套件验证过的版本。环境变量 `HYPERFRAMES_NO_TELEMETRY=1 HYPERFRAMES_SKIP_SKILLS=1` 已在脚本里设置。）
GSAP 3.15 已随套件放在 `templates/project/assets/gsap.min.js`，离线可用。

## 自检
```bash
ffmpeg -hide_banner -filters | grep -E " ass | alphamerge | loudnorm"   # 三个都要有
fc-match "Noto Serif CJK SC:style=Bold"; fc-match "Noto Sans CJK SC:style=Bold"
python3 -c "import faster_whisper, numpy, PIL; print('python ok')"
cd example && bash ../templates/scripts/run_all.sh config.json   # 跑通示例（见 README）
```

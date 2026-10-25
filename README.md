# 知识动画视频套件

把真人口播视频做成 9:16 视频号「知识动画」短视频（米白底黑红排版动画 + 字幕 + 真人圆窗 + 照片封面）。

- `SKILL.md`  —— 给智能体的完整步骤、安全区规范、QA 清单、发布规则（**先读这个**）
- `INSTALL.md` —— Linux / macOS 环境安装
- `templates/` —— 复制它来开新项目
  - `config.json` 唯一配置文件；`pages.example.json` 页面示例
  - `project/` style.css（版式）、gsap.min.js、HyperFrames 项目文件；`index.example.html` 是生成出来的合成页示例
  - `scripts/` 00_cover → 01_transcribe → 02_cuts → 03_subs → 04_build_html → 05_render → 06_circle → 07_compose → 08_qa，`run_all.sh` 一键串起来
- `example/` —— 10 秒示例（输入片段、config、pages、校对后的字幕、成片 `out/final.mp4` 和 QA 图）

## 跑示例
```bash
cd example
# 如系统 node 不是 22+，把 config.json 里 hyperframes.node_bin 改成你的 Node 22 bin 目录（或留空）
bash scripts/run_all.sh config.json        # 从转写开始全流程
bash scripts/run_all.sh config.json 4      # 已有 work/subs.json 时从第 4 步（封面+HTML）开始
```
`example/scripts` 是指向 `../templates/scripts` 的软链接；若解压后软链接丢失，用 `python3 ../templates/scripts/XX.py config.json` 代替。
注意：03 默认不覆盖已存在的 subs.json（保留人工校对），示例里的 `work/subs.json` 就是人工校对后的版本。

示例素材为真人出镜片段，仅用于验证流程，请勿对外发布。

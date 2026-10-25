---
name: 知识动画短视频
description: 把一段真人口播视频（或「选题+配音」）做成 9:16 视频号「知识动画」短视频：米白底黑红排版动画 + 逐句字幕 + 左下真人圆窗 + 照片封面。用户明确要求「做成知识动画/排版动画视频」时使用。
---

# 知识动画短视频（9:16 视频号）制作流程

> 本套件与具体 AI 工具无关：任何能运行命令行（Linux/macOS/云电脑）的智能体都可以照做。
> 先按 `INSTALL.md` 装好环境，再把 `templates/` 复制成一个新项目目录。所有脚本都只读 `config.json`，没有写死的路径和密钥。

## 0. 成品长什么样
- 1080x1920，30fps，H.264 + AAC，建议 60–120 秒。
- 第 1 帧是**照片封面**（0.3 秒）：照片铺满，中下部深色圆角框，两行黄色粗体字。另导出一张 3:4 封面。
- 顶部**标题栏全程不动**：宋体主标题 + 「01/02/03」章节导航，讲到哪章哪章标红。
- 中部**内容区**：元素随口播逐个进场（超大数字、对比卡、对比条、药丸标签、金句、盖章、手绘下划线……），换页时内容区上滑切换，镜头不动。
- 底部**单行字幕**：白字黑描边，每行 ≤16 字，重点词黄色。
- 字幕左上方**真人圆窗**（直径约 190–200px），口型与声音对齐，旁边有随音量跳动的光圈和 4 根声波条。
- 配色：米白底 `#F5EFE3`，正文 `#222`，强调深红 `#B22222`，药丸被念到时临时变黄 `#F6D44A`。

## 1. 输入（二选一）
**A. 真人口播视频**（主流程）：竖屏或横屏均可，手机录的 `.mov/.mp4`（常为可变帧率 VFR，脚本已处理）。
**B. 选题 + 配音**（没有真人画面）：
1. 先核实素材，不编造任何数字；写文字稿，每页写成「【画面】+ 口播」：开头一个反常识数字 → 分章节讲 → 结尾金句 → 抛一个问题。**先给用户确认稿子**。
2. 用任意 TTS 生成配音（可选：用户授权的声音克隆服务；没有就用普通 TTS）。稿子里的数字写成中文读法。
3. 把配音当作 `source_video`（纯音频也可以：先用 ffmpeg 生成一段配一张头像图的视频，`ffmpeg -loop 1 -i face.jpg -i voice.mp3 -shortest -r 30 -pix_fmt yuv420p src.mp4`），后续流程完全相同；圆窗里就是那张头像。

## 2. 新建项目
```bash
cp -r templates/ ~/videos/my-topic/ && cd ~/videos/my-topic/
mkdir -p input && cp /path/to/口播.mov input/source.mov
cp pages.example.json pages.json
# 编辑 config.json：source_video、title（≤12字）、chapters（3–4个）、cover.lines、circle.crop
```
`config.json` 关键字段：
| 字段 | 含义 |
|---|---|
| `source_video` | 原始视频，相对 config.json |
| `whisper.model` | faster-whisper 模型：`small`/`medium`/`large-v3`（越大越准越慢；CPU 上 medium 约 1x 实时） |
| `whisper.initial_prompt` | 写进专有名词、人名、品牌，显著提高识别率 |
| `cuts.trim` | `[开头秒, 结尾秒或 null]` |
| `cuts.manual_remove` | `[[a,b],...]` 手动剪掉口误/重复（原片秒数） |
| `subs.highlight` | 字幕里要标黄的词 |
| `circle.crop` | `[x, y, 边长]` 原片像素中脸部的正方形；`null`=自动取上部居中 |
| `circle.x/y/size/ring` | 圆窗在成片中的位置（默认 x110 y1208，直径 190 + 5px 白边 ≈ 200） |
| `cover.photo` / `cover.lines` | 封面照片（null=从视频截帧）与两行标题 |
| `speed` | 整片变速（如 1.2，变速不变调）；1.0=原速 |
| `hyperframes.node_bin` | Node 22 的 bin 目录（系统 node 已是 22+ 时留空） |

## 3. 转写（开源 ASR，不需要任何 API Key）
```bash
python3 scripts/01_transcribe.py config.json     # → work/words.json（逐字时间戳）
```
首次运行会自动下载 faster-whisper 模型（medium ≈1.5GB）。国内网络可设 `HF_ENDPOINT=https://hf-mirror.com`。

## 4. 剪辑（去停顿、去口误）
```bash
python3 scripts/02_cuts.py config.json           # → work/cuts.json + work/voice.wav（已降噪、响度 -16 LUFS）
```
- 自动剪掉 >0.3 秒的静音（两端各留 0.07 秒气口）。
- 读 `words.json`，把口误、重复、「呃/那个」等区间写进 `cuts.manual_remove` 后重跑。
- **之后所有时间都用「剪后时间轴」**（字幕、页面 data-t、圆窗都按它对齐）。

## 5. 字幕
```bash
python3 scripts/03_subs.py config.json           # → work/subs.json + work/final.srt
```
- 自动按 ≤16 字、标点、停顿断行，不在数字中间断。
- **必须人工校对 `work/subs.json`**：ASR 常把专有名词、数字听错（例如「第14届」听成「91届」）。只改 `text`，时间一般不用动。改完后重跑 03（不加 `--force` 不会覆盖你的修改）。
- 字幕显示数字用阿拉伯数字（「11月23、24号」「200人」），每行 ≤16 字。

## 6. 页面设计（pages.json）
每页一条：`{"start": 剪后秒, "ch": 章节序号, "html": "..."}`。
- 页面里的元素加 `data-anim` + `data-t`（剪后秒，对照 subs.json 找到关键词被念出的时刻）就会准时进场：
  - `up` 上浮淡入（文字）｜`scale` 弹出（大数字、卡片、盖章）｜`bar` 条形从左长出｜`pill` 药丸进场并高亮黄色（下一个药丸出现时上一个恢复）｜`draw` SVG 线条手绘（下划线、箭头）。
- 可用样式类（见 `templates/project/style.css`）：
  `kicker`（小引题）`giant g3/g4`（超大数字 400/220/180px）`sub2`（宋体副标题）`quote q2`（金句）`question`（提问框）
  `vs > card > cl + cv`（对比卡）`barrow > blabel + bar(dark/red, --w:50%) + bval`（对比条）`pills / pills h > pill`（药丸，竖排/横排）
  `box / box.red` `plus` `stamp`（盖章）`note`（引用）`list > li > no + lt + ls`（编号列表）`uline`（手绘下划线 SVG）`em.red`（强调色）。
- 一页 2–5 个元素，节奏 1–3 秒一个；每 4–10 秒换一页；同一章节内用 `ch` 相同。
- 版式原则：**大字、有冲击力、留白清爽**。位置不对时**只移动不缩字号**；某页实在太高，只给那一页加 `style="zoom:.88"`（不低于 .88）。
- 页面专属微调写进单独的 css 文件，在 config 里设 `"extra_css": "extra.css"`。

## 7. 安全区规范（1080x1920，按手机视频号实际显示校准）
| 区域 | 范围 | 规则 |
|---|---|---|
| 顶部禁区 | y 0–170 | **什么都不放**（状态栏、返回键、「…」会挡） |
| 标题栏 | y ≈176–346 | 上下细黑线；主标题 54px，章节导航 34px；底线与导航文字间距 ≥20px，文字不压线 |
| 内容区 | y ≈350–1200 | 保持原大小，不为省地方整体缩小 |
| 头像圆窗 | 左侧，y ≈1208–1408，直径 190–200 | 字幕正上方；不压内容 |
| 字幕 | 单行，中心 y ≈1420–1460，底边 ≤1490 | 与视频号右下播放时间标签同高，长句别伸到右侧 |
| 左右边缘 | 两侧各约 97px | 部分机型/封面会裁掉，标题和导航**居中**，重要内容不贴边 |

## 8. 封面
```bash
python3 scripts/00_cover.py config.json          # → work/cover_9x16.png、cover_3x4.png
```
- 最好用一张清晰、人物醒目的照片（`cover.photo`）；没有就从视频截帧（`cover.photo_time`）。
- 两行黄字（每行 ≤7 字左右），第二行常用问句制造悬念；`focus_y` 调人脸在画面中的上下位置。

## 9. 生成合成页 + 渲染
```bash
python3 scripts/04_build_html.py config.json     # → work/project/index.html
bash    scripts/05_render.sh     config.json     # → work/base.mp4（HyperFrames：HTML+GSAP 逐帧渲染）
```
- 想实时预览：`cd work/project && npx hyperframes@0.8.190 preview`。
- 单帧检查：`npx hyperframes@0.8.190 snapshot --at 1,5,9`。

## 10. 真人圆窗（VFR 时间戳映射）
```bash
python3 scripts/06_circle.py config.json         # → work/circ.mp4
```
原理（自己实现时务必照做）：手机视频是**可变帧率**，「帧号 ÷ 帧率」算出来的时间会越来越偏，剪辑后口型对不上。正确做法：
1. `ffprobe -show_entries frame=best_effort_timestamp_time` 读出每一帧真实时间戳 pts；
2. 用 `-fps_mode passthrough` 解码全部帧（不补帧不丢帧，与 pts 一一对应）；
3. 对成片第 k 帧：剪后时间 `t=k/30` → 原片时间 `src=cut2src(t)` → 取 `pts ≤ src+半帧` 的最后一帧；
4. 编码为恒定 30fps 的正方形视频，再用圆形遮罩叠到头像位置。

## 11. 合成成片
```bash
python3 scripts/07_compose.py config.json        # → out/final.mp4、out/preview_540.mp4、封面、srt
```
圆形遮罩（4 倍超采样抗锯齿）叠到 `circle.x+ring, circle.y+ring`；前 0.3 秒盖封面；配音转立体声 AAC。`speed≠1` 时整片同步变速。

## 12. QA 检查清单（每版都过一遍）
```bash
python3 scripts/08_qa.py config.json             # → out/qa_sheet.png（12 帧联系表）、out/qa_guides.png（叠安全区参考线）
```
- [ ] 第 1 帧是照片封面，不出现头像；3:4 封面也已导出
- [ ] y 0–170 没有任何元素；标题、导航文字不压线，导航当前章节标红正确
- [ ] 内容不进入圆窗/字幕区，不被 `.stage` 裁切（文字没缺上半截/下半截）；超大数字不换行
- [ ] 字幕单行、≤16 字、无错别字、不在数字中间断行，底边 ≤1490，右侧不碰时间标签
- [ ] 圆窗口型与声音对齐（看片头、片中、片尾各一处）；光圈/声波随声音跳动
- [ ] 元素在关键词被念出时进场（误差 <0.3 秒），药丸高亮顺序正确
- [ ] 数字与原话一致，没有编造
- [ ] 全片无黑帧、无爆音，结尾不被截断；时长、分辨率、帧率符合规格（`ffprobe out/final.mp4`）
- [ ] 最好用手机截一张视频号播放页截图叠在成片上，确认遮挡
- 先发 540p 小样（`preview_540.mp4`）给用户确认，按反馈修改；每一版另存（如 `out_v2/`）。

## 13. 视频号发布文案规则
- **标题 ≤16 个字，不能有逗号**（可用空格、问号）。
- 描述：一两句概括 + 一个提问引导评论 + 2–4 个话题（`#AI #电商`）；声明原创。
- 发布前检查标题是否真的填进去了；封面选 3:4 那张。
- 发布是对外可见操作：**发布前必须让用户确认**。

## 14. 常见问题
- 字体显示成方块/宋体不对：没装 Noto CJK 字体，见 INSTALL.md。
- `05_render.sh` 报 Node 版本：需要 Node 22+；在 `hyperframes.node_bin` 填 Node 22 的 bin 目录。
- 渲染卡住或黑屏：确认 `work/project/assets/gsap.min.js` 存在（离线可用，不依赖 CDN）。
- 口型逐渐错位：确认用的是 06_circle.py 的时间戳映射，而不是按固定帧率 trim。
- ASR 很差：换 `large-v3`，并在 `initial_prompt` 写专有名词；字幕最终以人工校对为准。

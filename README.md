# Nature Love

把两个人的微信聊天记录整理成图表，再写成一篇属于自己的文章。

项目会生成八组图、中英文初稿和可编辑的 LaTeX 文件。先从微信导出记录，再按下面的步骤运行。所有分析都在本地完成。页面上的预览使用合成数据。

[获取记录](#获取聊天记录) · [安装](#安装) · [开始分析](#开始分析) · [修改图表](#图表怎么改) · [继续写作](#文章怎么写)

## 先看效果

| 聊天量与连续性 | 聊天时段 |
|---|---|
| [![聊天量与连续性](docs/assets/demo-overview.png)](docs/assets/demo-overview.png) | [![聊天时段](docs/assets/demo-rhythm.png)](docs/assets/demo-rhythm.png) |
| **双方怎样参与聊天** | **词汇与表达方式** |
| [![消息、字符和发言回合](docs/assets/demo-preview.png)](docs/assets/demo-preview.png) | [![词汇重叠与虚词匹配](docs/assets/demo-language.png)](docs/assets/demo-language.png) |

以上四组图来自 822 条合成记录，点击可看大图。完整输出还包括常用表达、媒体消息、话题和个人喜好页。

## 获取聊天记录

### 1. 把手机上的历史记录导入电脑微信

如果手机上的记录最全，先做这一步。手机和电脑登录同一微信账号，连接同一网络。

1. 在手机微信进入 **我 → 设置 → 聊天记录管理 → 导入与导出 → 导出到电脑**。
2. 选择要分析的那位联系人，时间范围选全部。
3. 在电脑微信确认接收，保持两端微信运行，等传输结束。
4. 打开电脑上的这段聊天，检查最早日期，并抽查几张旧照片、一段视频和一条语音。

不同微信版本的入口可能在“聊天”或“通用”下面，名称也可能是“聊天记录迁移与备份”。这里需要的是**导入后能在电脑微信里浏览的记录**。“备份到电脑”保存的是用于恢复的加密备份，不能直接作为本项目的 JSON 输入。相关入口可参考[设备厂商的操作说明](https://consumer.huawei.com/cn/support/content/zh-cn01118496/)。

### 2. 从电脑微信导出 JSON 和附件

下面以 [WeChatDataAnalysis](https://github.com/LifeArchiveProject/WeChatDataAnalysis) 为例。本项目附了它的 JSON 转换脚本。

1. 从该工具的 [Releases](https://github.com/LifeArchiveProject/WeChatDataAnalysis/releases/latest) 下载与系统匹配的版本，先查看它对微信版本、系统和芯片的要求。
2. 按工具说明连接自己的微信数据。数据库密钥是这一环节的条件；若工具读不到密钥，应先解决导出问题，Nature Love 本身不获取密钥。
3. 打开目标联系人的聊天，核对双方身份与最早、最晚日期。
4. 在导出设置中选择 **JSON、全部时间、全部消息类型**。需要保存照片、视频、表情和语音时，同时选择导出媒体附件；相关选项名称随版本变化。
5. 保存并解压导出包。保留整个目录，包括联系人目录里的 `messages.json`、媒体目录以及导出报告。可以另外导出一份 HTML，用来对照浏览。

建议按下面的方式存放，不改动原始导出：

```text
private/
├── original/             # 解压后的完整导出包
│   └── .../
│       └── messages.json # 目标联系人的原始 JSON
└── messages.json         # 稍后转换出的分析文件
```

**有消息条目，不代表附件原件一定还在。** 导出后要打开文件抽查：照片是不是原图，视频和语音能否播放，表情是否有实际图片。过期文件、缩略图和导出失败项要单独记下来。

如果只想整理某一小段，也可以用 Mac 微信的“合并转发 → 转发到其他应用”，通过 [WeChatBridge](https://github.com/freestylefly/WeChatBridge) 保存到文件夹。这条路需要手动分批选择，适合片段；导出的 TXT/ZIP 仍需整理成下方的输入格式。更多导出、附件和完整性核对方法见[获取记录说明](docs/GETTING_RECORDS.md)。

### 3. 转成分析文件

先完成下面的安装，再运行转换。把 `--input` 后面的路径改成目标联系人的实际文件路径：

```bash
python scripts/convert_wechatdataanalysis.py --input "private/original/目标联系人/messages.json" --output private/messages.json
```

脚本处理 WeChatDataAnalysis 的 `schemaVersion: 1` 聊天 JSON，默认 **A 是导出账号本人，B 是对方**。它会转换时间、消息类型、正文、表情标识，并把语音的毫秒时长换成秒。附件继续保留在原始导出目录。

这个导出格式通常没有稳定的通话会话标识。转换后可以统计通话提示条数，但不能据此补造去重后的语音/视频通话次数或完整通话总时长。若另有可靠元数据，可按[输入字段](docs/INPUT_SCHEMA.md)补充 `call_id`、`call_type` 和 `duration_seconds`。

使用其他工具导出时，按以下结构整理；CSV 也使用同名列。至少保留 `timestamp` 和 `sender`，正文放在 `text`，消息类型放在 `type`。不要只保留纯文字，否则媒体消息无法统计。

```json
[
  {"id":"m1","timestamp":"2024-01-01T12:00:00+08:00","sender":"A","type":"text","text":"你好"},
  {"id":"m2","timestamp":"2024-01-01T12:00:08+08:00","sender":"B","type":"text","text":"你好呀"}
]
```

## 安装

需要 [Python 3.10 或更新版本](https://www.python.org/downloads/)，首次使用可选 Python 3.12。下载本项目 ZIP 并解压，或用 Git：

```bash
git clone https://github.com/Charles-Xu0518/NatureLove-OpenSource.git
cd NatureLove-OpenSource
```

后面的命令都在含有 `pyproject.toml` 的项目目录执行。

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
```

**Windows 命令提示符（CMD）**

```bat
py -3 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install .
```

**Windows PowerShell**

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install .
```

PowerShell 用户在后续命令中用 `.\.venv\Scripts\python.exe` 替换 `python`，无需运行激活脚本。macOS / Linux 或 CMD 重新打开终端后，需要重新激活环境。

先跑一次演示：

```bash
python -m naturelove demo --output outputs/demo
```

完成后双击 `outputs/demo/report_zh.html`。能看到图表和文章，就可以换成自己的记录。

## 开始分析

生成配置文件：

```bash
python -m naturelove init-config config.local.json
```

打开 `config.local.json`，填写双方署名、纪念日和喜好。下面是一份最小配置，名字、日期和城市都是示例；未列出的设置沿用默认值。

```json
{
  "title": "Our Everyday Story",
  "timezone": "Asia/Shanghai",
  "relationship_date": "2024-01-21",
  "joint_first_authors": true,
  "participants": [
    {"id":"A","name":"Alex","hometown":"City A","likes":["摄影","散步"],"dislikes":[]},
    {"id":"B","name":"Jamie","hometown":"City B","likes":["阅读","甜点"],"dislikes":[]}
  ],
  "colors": ["#8E6A9D", "#CB4F86"]
}
```

`id` 必须与消息的 `sender` 对应，`name` 是文章里显示的名字。没有确定的纪念日就把 `relationship_date` 写成 `null`。

运行：

```bash
python -m naturelove run --input private/messages.json --config config.local.json --output outputs/my-report
```

CSV 输入只需将 `--input` 改成实际的 `.csv` 路径。结果在 `outputs/my-report/`：

| 文件 | 用来做什么 |
|---|---|
| `report_zh.html` / `report_en.html` | 先在浏览器里通读中英文初稿 |
| `summary.json` | 核对日期、消息数、各项统计和缺失值 |
| `run_config.json` | 保留这次分析使用的设置 |
| `figures/Figure1` 至 `Figure8` | 八组图，每组都有 PNG、PDF、SVG |
| `latex/report_zh.tex` / `report_en.tex` | 继续修改文章并排版 |

先核对总量和首尾日期，再挑几条语音、表情、通话对照原始记录。转换前后条数应一致；分析阶段若去除了相同 ID 的重复记录，数量会记在 `summary.json` 的 `quality` 中。短窗口或文字量不足时，部分指标会显示 `NA`。

## 图表怎么改

| 图 | 内容 | 写作时可以追问的问题 |
|---|---|---|
| Figure 1 | 聊天量、连续性与消息类型 | 不同阶段的交流强度怎样变化？ |
| Figure 2 | 星期、小时与双方发送时钟 | 聊天主要发生在一天中的什么时候？ |
| Figure 3 | 消息、字符、回合、对话起止和回复间隔 | 换一种计数方式，双方参与是否呈现不同样子？ |
| Figure 4 | 词语、短句与共用表情标识 | 哪些表达构成了你们的日常？ |
| Figure 5 | 通话提示、可识别会话和已知时长 | 这份记录保留了哪些文字之外的交流？ |
| Figure 6 | 自定义话题及词典覆盖率 | 常谈什么，词典又漏掉了什么？ |
| Figure 7 | 内容词重叠、等量抽样与虚词匹配 | 语言结果在控制消息量后是否相近？ |
| Figure 8 | 自填城市、喜好与插画 | 哪些个人细节值得留在文章里？ |

常用修改都在 `config.local.json`：

- `colors`：双方的颜色，顺序与 `participants` 一致。
- `phrases`、`topics`：想统计的称呼、短句和话题词。改完后要重新计算。
- `illustration`：自己的 PNG/JPEG 插画。例如图片放在 `assets/private/art.png`，配置写成 `"illustration": "assets/private/art.png"`。
- `conversation_gap_hours`：划分新对话的间隔，默认 3 小时。
- `day_boundary_hour`：计算聊天日末条消息时的日界，默认凌晨 5 点。

改配置后重新运行分析。PNG 适合预览和插入文档，PDF/SVG 适合继续排版。想改坐标名称、字号或图的布局，编辑 `src/naturelove/figures.py`，然后重新执行 `python -m pip install .` 并重跑。

## 文章怎么写

生成的文章已经填入统计和图注，接下来主要是补背景、组织结果和润色。建议先复制整个 `outputs/my-report/` 到 `private/manuscript/`，保留 `latex/` 与 `figures/` 的相对位置，再开始改稿。这样重新分析时不会覆盖手工修改。

1. **先写时间线。** 记录从哪天开始，哪些日期是双方确认的纪念日，是否有缺失月份。考试、工作、见面等背景由你们补充。
2. **每段围绕一个发现。** 把关键数字和图号放在一起，再解释它与生活经历有什么联系。消息数、字符数和回合数可以放在同一段比较。
3. **把个人细节写进来。** 选双方愿意留下的称呼、习惯和片段。喜好页使用自己填写的资料，文字引用回到原始记录核对。
4. **最后写讨论和摘要。** 讨论把几组结果连起来；摘要只留下全文最主要的发现。回复间隔描述聊天节奏，词汇重叠描述语言材料，解释时还需要当时的语境。

中文正文改 `private/manuscript/latex/report_zh.tex`，英文改 `report_en.tex`。如果只想先改文字，也可以编辑生成的 HTML。更具体的段落写法、图注和中英文核对步骤见[写作说明](docs/WRITING.md)。

### 排成 PDF

macOS 安装完整 [MacTeX](https://tug.org/mactex/)，Windows / Linux 安装 [TeX Live](https://tug.org/texlive/quickinstall.html)。安装后重新打开终端，确认 `xelatex --version` 可以运行。

在分析时加上 `--pdf`，会同时生成文章 PDF：

```bash
python -m naturelove run --input private/messages.json --config config.local.json --output outputs/my-report --pdf
```

手工改完稿件后，从项目目录进入稿件所在文件夹，编译两遍：

```bash
cd private/manuscript/latex
xelatex -no-shell-escape -interaction=nonstopmode -halt-on-error report_zh.tex
xelatex -no-shell-escape -interaction=nonstopmode -halt-on-error report_zh.tex
```

英文稿把文件名换成 `report_en.tex`。生成的 PDF 在当前 `latex/` 目录。字体和编译问题见 [PDF 说明](docs/PDF.md)。

## 常见问题

| 情况 | 处理 |
|---|---|
| 只有微信加密备份，电脑聊天里看不到旧消息 | 先完成可浏览的历史导入；备份文件不能直接交给分析程序 |
| 导出工具读不到数据库密钥 | 查该工具支持的系统与微信版本；记录尚未导出时，本项目无法接着分析 |
| 转换脚本提示格式不符 | 检查是不是目标联系人的 `messages.json`；其他工具的 JSON 不能仅靠改文件名兼容 |
| 转换输出文件已经存在 | 换一个新文件名，原始记录和上一次转换结果都会保留 |
| `No module named naturelove` | 确认使用虚拟环境，并在项目目录执行 `python -m pip install .` |
| 输出目录非空 | 换一个新目录；已由本工具生成的目录可以重跑，但会更新原结果 |
| 图中出现 `term N` | 绘图环境缺少中文字体；安装如 Noto CJK 的字体后重跑，原词保留在统计 JSON 中 |
| 通话时长或次数不全 | 查看导出是否含会话标识和时长；通话提示、独立会话和已知时长分别统计 |

原始聊天、附件、配置和稿件留在本地。只处理自己有权使用的记录，引用对话前与另一位参与者确认。

## 来源

分析思路受到 [momoPaper123 的 Nature Love](https://github.com/momoPaper123/-) 启发。本项目独立实现的代码和模板采用 [MIT](LICENSE) 许可，来源说明见 [NOTICE.md](NOTICE.md)。这是纪念文章项目，与 Nature Portfolio 无隶属关系。

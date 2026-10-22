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

完整流程是：**手机记录导入电脑微信 → 获取并校验密钥 → 导出 JSON 和附件 → 转换为分析文件**。Nature Love 从已导出的文件开始工作。

下面按 Mac 写。导出工具使用 [WeChatDataAnalysis](https://github.com/LifeArchiveProject/WeChatDataAnalysis)，按钮和选项按 **v2.10.0** 核对，核对日期为 2026-10-23。微信流（WeChatBridge）只适合手动选择的片段，不能代替这里的完整导出。

### 1. 把手机上的历史导入电脑微信

手机和 Mac 登录同一微信账号，连接同一网络。

1. 手机微信进入 **我 → 设置 → 聊天记录管理 → 导入与导出 → 导出到电脑**。
2. 选择目标联系人，时间选全部，在电脑微信确认接收。
3. 保持两端运行，等传输完成。在 Mac 上打开聊天，核对最早日期，再抽查旧照片、视频和语音。

有些版本把入口放在“聊天”或“通用”下，名称为“聊天记录迁移与备份”。需要的是**迁移后能在电脑微信里浏览的历史**；“备份到电脑”生成的恢复备份不能直接转换成 JSON。入口可参考[微信迁移说明](https://consumer.huawei.com/cn/support/content/zh-cn01118496/)。

### 2. 在 Mac 上准备导出工具

1. 在 **苹果菜单 → 关于本机** 查看芯片和系统版本。上游桌面包面向 **macOS 15+、Apple Silicon（M 系列）**；本教程不把 Intel Mac 视为已支持。
2. 打开 [Releases](https://github.com/LifeArchiveProject/WeChatDataAnalysis/releases/latest)，下载 `mac-arm64.dmg` 或对应 ZIP，把 `WeChatDataAnalysis.app` 放进“应用程序”。微信使用官方安装的 `/Applications/WeChat.app`。
3. 打开 **系统设置 → 隐私与安全性 → 完全磁盘访问权限**，添加并启用 WeChatDataAnalysis，完全退出后重新打开。不要只给浏览器授权；用源码运行时，权限应给实际启动服务的终端或应用。
4. 在工具中选择自己的微信账号，进入“数据库解密”。多账号时核对头像、名称和当前登录账号。
5. 检查“数据库存储路径”是否指向该账号当前的 `db_storage`。不要选手机备份、导出目录或旧账号副本。

若自动发现失败，在访达按 `⌘⇧G`，打开微信 4.x 常见的活动数据位置：

```text
~/Library/Containers/com.tencent.xinWeChat/Data/Documents/app_data/xwechat_files/
```

找到当前账号下的 `db_storage`，在访达选中后按 `⌥⌘C` 复制完整路径，填入工具。路径不存在时，以工具发现及微信实际使用的位置为准；具体定位方法见[Mac 数据目录说明](docs/GETTING_RECORDS.md#找到当前账号的数据目录)。

### 3. 获取并校验数据库密钥

**先用主程序的一键获取：**

1. 保持微信已登录，在“数据库解密”页点击 **一键获取数据库密钥**。
2. 页面开始等待后，按它的提示**完整退出微信程序**，再重新打开并登录同一账号。关闭聊天窗口不等于退出程序。
3. 手机有登录确认时由本人完成，保持导出工具和当前页面打开。
4. 成功后，“解密密钥”框会填入 **64 个十六进制字符**。已有经过验证的密钥，也可以直接填入这个框；它不是微信登录密码，也不是 AI API Key。
5. 点击 **开始解密**。等任务结束，核对成功与失败数量，再打开目标会话，确认能读到文字和历史日期。密钥长度正确本身不代表它适用于当前账号。

**如果主程序明确提供“实验性本机调试兜底”：**

这条路线需要管理员授权，会临时重签微信并在结束时恢复官方版本，可能触发安全提醒。先备份重要数据，只在已理解提示后继续。它不是每个版本、每台 Mac 都会出现的入口。

1. 确认使用 Apple Silicon 和默认位置的官方微信；提示缺少 LLDB 时，在终端运行 `xcode-select --install`，完成安装后再试。
2. 在工具的风险说明中选择继续，等待备份和临时微信准备完成。
3. **第一次登录临时微信，进入聊天页**，再点“已进入聊天，开始预检”。预检失败就停止并恢复。
4. 预检通过后，在微信菜单中**退出当前账号**，停在二维码页，先不要重新登录。
5. 回到导出工具，点“已看到二维码，开始监测”，完成管理员授权。等页面明确显示 **监测已就绪**，再扫码或在手机上确认同一账号登录。
6. 等工具完成捕获、数据库校验和官方微信恢复。看到密钥填回及恢复完成提示后，回到“开始解密”。窗口自行关闭不等于获取成功。

中途要结束，用 **停止并恢复**。主程序没有提供兜底、组件校验失败或恢复未完成时，先按[故障处理](docs/GETTING_RECORDS.md#获取失败和恢复)排查，不要反复重签。流程依据[上游 Mac 捕获说明](https://github.com/LifeArchiveProject/WeChatDataAnalysis/blob/v2.10.0/docs/MACOS_KEY_CAPTURE.md)。

### 4. 先确认照片和表情能读取

数据库密钥负责读取消息；部分图片还需要另一组**图片密钥**。

- 在“图片密钥”步骤检查自动回填结果。需要时用“扫描微信内存”，按该页提示打开微信图片，并仅在系统要求时给实际执行扫描的应用辅助功能权限。**不要把上面的 64 字符数据库密钥填进图片 XOR / AES 栏。**
- 回聊天页打开几张不同月份的旧图；要保留高清图，应先确认 Mac 微信里已下载原图。批量“图片解密”是可选的预处理，不能恢复源端已过期的照片。
- 要补存表情原文件，可在“批量下载表情包”页点“开始下载表情”，完成后再导出。这一步会联网，地址失效的表情仍可能缺失。
- 语音转文字可以先跳过；**保存语音附件不需要先做转写**。

图片步骤如提供云端解析，应先确认它会发送什么；这里只做本地处理时使用本地扫描。关于来源限制的系统提示，按 [Apple 的应用打开说明](https://support.apple.com/zh-cn/102445)处理。

### 5. 导出目标联系人的 JSON 和附件

在聊天页打开目标会话，点“导出聊天记录”，按下表设置：

如果面板提示“隐私模式已开启”，先用侧边栏的眼睛图标关闭它，再回到导出面板。

| 选项 | 选择 |
|---|---|
| 会话范围 | 当前会话，只勾选这一位联系人 |
| 文件格式 | **JSON**，不要保留默认的 HTML |
| 消息类型 | **保持全选**，包括媒体、系统、引用和通话；已显示“取消全选”时不再点击 |
| 开始时间 / 结束时间 | **都留空**表示全部时间；研究固定区间时再填写 |
| 输出方式 | 首次归档选 **ZIP 全量**；后续持续保存可选“增量目录” |
| 保存位置 | 点“选择目录”，使用自己新建的私人目录 |
| 语音转文字 | 首次归档可不选，不影响原始音频导出 |
| 隐私模式 | 本地原文分析时关闭；该模式会隐藏正文且不导出媒体 |

这一版界面会随选中的媒体消息类型一起打包可用资源，**没有独立的“导出全部附件”总开关**。只选文本就不会取得完整媒体归档。

点“开始导出”，等任务和文件保存都完成。ZIP 解压后应能找到类似结构；会话目录名会带标识，附件子目录随内容变化：

```text
private/original/
├── manifest.json
├── report.json
├── conversations/
│   └── 目标联系人_标识/
│       ├── messages.json
│       └── meta.json
└── media/
    └── ...
```

保留整个目录。另导出 HTML 时，保存在另一个目录，方便对照浏览；它不能代替分析用 JSON。增量模式还需保留根目录的 `.wechat-chat-export.json`，不要只拷贝某个会话文件。

### 6. 核对后转成分析文件

先检查最早与最晚日期、双方发送方向，并打开几张照片、一段视频、一条语音和一个表情。查看 `report.json` 中的附件缺失情况；只有消息记录或表情标识，不能证明文件已经保存。通话提示也不包含通话过程的录音录像。

完成下方[安装](#安装)后，在 Nature Love 项目根目录执行，替换成实际会话目录：

```bash
python scripts/convert_wechatdataanalysis.py --input "private/original/conversations/目标联系人_标识/messages.json" --output private/messages.json
```

转换处理 `schemaVersion: 1`：**A 是导出账号本人，B 是对方**。时间、正文、类型、表情标识和语音时长会转成分析字段；附件仍留在原始目录。成功后会显示转换条数，应与原文件的消息条数一致。

脚本不会覆盖已有输出；要重新转换，可另取文件名，如 `private/messages-v2.json`。这个常规 JSON 不一定有通话会话标识，不能直接把提示条数写成去重后的通话次数。字段、附件检查和片段导出另见[完整获取说明](docs/GETTING_RECORDS.md)。

使用其他导出工具时，按[标准输入](docs/INPUT_SCHEMA.md)整理。最小 JSON 如下，CSV 使用同名列：

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

## 作者与许可

Nature Love 由 Zhiheng Xu 创建和维护，代码与模板采用 [MIT](LICENSE) 许可。所用统计方法和依赖见 [NOTICE.md](NOTICE.md)。这是个人纪念文章项目，与 Nature Portfolio 无隶属关系。

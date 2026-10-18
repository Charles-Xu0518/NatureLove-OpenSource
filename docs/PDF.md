# PDF、字体与排版

HTML 无需 TeX，可直接用浏览器打开或打印。可编辑 LaTeX 总会写入输出的 `latex/` 子目录；PDF 是额外选项。

## 生成 PDF

安装含 XeLaTeX、xeCJK、Fandol 和 TeX Gyre 的 TeX Live / MacTeX，确认终端中 `xelatex --version` 可用，然后：

```bash
naturelove demo --output outputs/demo --pdf
```

或者在生成目录的 `latex/` 中，分别对 `report_zh.tex` 和 `report_en.tex` 编译两次。不要只复制一个 TeX 文件：它使用相邻 `../figures/` 中的图。

所需字体文件包括 `FandolSong-Regular.otf`、`FandolSong-Bold.otf`、`FandolHei-Regular.otf`、`texgyretermes-regular.otf` 和 `texgyreheros-regular.otf`。这些由 TeX 安装提供；仓库不复制任何系统字体。可用 `kpsewhich FandolSong-Regular.otf` 检查。

编译使用关闭 shell escape 的参数。用户提供的姓名、标题和正文统计文字都会进行 LaTeX 特殊字符转义。失败时保留编译日志与源文件，不删除结果。

## 图表中的中文

matplotlib 会尝试 Noto、系统中文字体等。没有中文字体时，图表中的中文词标签以 `term N` 显示，实际词语保留在 JSON 与 HTML 中，避免输出缺字方框。安装支持中文的字体后重跑即可。图中的英文轴名是通用模板的一部分。

人名、喜好等配置建议使用字体支持的普通文字；彩色 emoji 通常不适合 XeLaTeX 正文字体。自定义插画使用 PNG/JPEG，按配置中路径读取并嵌入个人画像图，原文件不会复制进源码仓库。

默认提供300 dpi PNG和矢量PDF/SVG。PNG中的文字取决于生成环境字体；PDF需要生成后检查页数、图注、字号与截断情况。本项目合成演示已在本地进行这样的检查，详见验证记录。

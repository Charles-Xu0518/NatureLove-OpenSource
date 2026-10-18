"""Deterministic bilingual writing components and portable report templates."""
from importlib.resources import files
from pathlib import Path
import json
import shutil
import subprocess
from jinja2 import Environment, FileSystemLoader, StrictUndefined


def fmt(value, digits=1):
    if value is None: return "NA"
    return f"{value:,.{digits}f}" if isinstance(value, float) else f"{value:,}" if isinstance(value, int) else str(value)


def percent(value):
    return fmt(value * 100) + "%" if value is not None else "NA"


def tex_escape(value):
    mapping = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
               "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(mapping.get(c, c) for c in str(value))


def sections(summary, config, language):
    s = summary; a, b = s["units"]; pa, pb = config["participants"]
    names = [pa["name"], pb["name"]]; zh = language == "zh"
    lexical = [r for r in s["language"]["months"] if r["cosine"] is not None]
    endpoints = (f"{lexical[0]['month']}: {fmt(lexical[0]['cosine'], 3)}; {lexical[-1]['month']}: {fmt(lexical[-1]['cosine'], 3)}"
                 if lexical else "NA")
    decomposition = s["decomposition"]
    identity = (f"{fmt(decomposition['message_ratio'], 3)} = {fmt(decomposition['turn_ratio'], 3)} x {fmt(decomposition['messages_per_turn_ratio'], 3)} (rounded)"
                if decomposition else "NA")
    if zh:
        titles = ["聊天量与连续性", "一天中的发送时刻", "换一个单位，重新理解参与", "词语与表达习惯",
                  "文字之外的渠道", "话题词典的覆盖边界", "词汇重叠与虚词匹配", "为各自的喜欢留位置"]
        bodies = [
            [f"归档窗口为 {s['first_date']} 至 {s['last_date']}，共 {fmt(s['records'])} 条记录，其中双方消息 {fmt(s['participant_messages'])} 条、系统提示 {fmt(s['system_records'])} 条。{s['calendar_dates']} 个自然日中，{s['active_dates']} 天留有记录。",
             f"单日峰值为 {s['peak']['date']} 的 {fmt(s['peak']['count'])} 条；最长连续区间为 {s['longest_run']['days']} 天。月度强度使用实际观察自然日作为分母，零记录日期保留在日历中。强度与连续性回答不同的问题。"],
            ["小时与星期分布描述发送时刻。星期热图按对应星期几的实际数量归一化，个人时钟按各自消息总数归一化；午夜后占比定义为 00:00-04:59。",
             "这些时刻不测量睡眠或持续在线。不同分母的图应分别解读，不能把较大的占比直接换成更多绝对条数。"],
            [f"{names[0]} 占消息的 {percent(a['message_share'])}、字符的 {percent(a['character_share'])}、发言回合的 {percent(a['turn_share'])}。双方回合数分别为 {fmt(a['turns'])} 与 {fmt(b['turns'])}。",
             f"计数分解为：消息数比 = 回合数比 x 平均每回合条数比；本档案为 {identity}。这是计数关系，不是付出或情绪劳动的因果模型。",
             f"双方相邻回复间隔中位数为 {fmt(a['reply_median_seconds'])} 秒与 {fmt(b['reply_median_seconds'])} 秒。间隔为发送者切换时的时间戳差，不是已读后响应时间。"],
            [f"文字正文共 {fmt(s['text_messages'])} 条、{fmt(s['characters'])} 字符。词语对比是语料内相对排名；短句计数按每条正文是否包含指定字符串计算。",
             f"已提供标识的表情共有 {s['stickers']['identified']} 种，其中 {s['stickers']['shared_identifiers']} 种由双方都发送过。没有表情标识时，不推定不同图片的身份。图中不展示原始附件。"],
            [f"{s['calls']['notices']} 条通话提示对应 {s['calls']['identifiable_sessions']} 次可识别独立通话；{s['calls']['unidentified_notices']} 条提示缺少有效会话标识。{s['calls']['known_duration_sessions']} 次保留一致时长，合计 {fmt(s['calls']['known_hours'], 2)} 小时。",
             f"语音消息共 {s['voice']['messages']} 条，已知源时长 {fmt(s['voice']['known_hours'], 2)} 小时。缺失时长保持缺失，冲突时长不任意选取；不同渠道的时长没有作时间重叠扣除。",
             "探索性情绪默认关闭。开启后，仅报告示例词典的覆盖与日期整组重抽样结果，不生成感情分数。"],
            [f"可配置话题词典至少命中一次的正文占 {percent(s['topic_coverage'])}。一条正文可以属于多个类别，因此图中不是完整、互斥的主题构成。",
             "食物或地点的提及，不直接换算为共同用餐、旅行或约定兑现。修改词典会改变覆盖与排名，应记录具体词表。"],
            [f"内容词余弦的首末可计算月份为 {endpoints}。固定词表包含 {s['language']['vocabulary_size']} 个词，每月每人等量抽取 {s['language']['sample_messages']} 条有内容词消息，共 {s['language']['sampling_draws']} 次。",
             "阴影是抽样敏感性范围，不是因果置信区间。样本不足时等量条数自动缩小，或保持不可计算；没有补造相似度。八类虚词匹配使用小型示例词典，未经量表验证，不能代替关系质量评价。"],
            ["本页使用配置中自述的家乡、喜欢与不喜欢，独立于统计证据。不同喜好可以共同保留，并不需要先由词频证明。",
             "默认插图为本项目绘制的抽象丝带。你可以在本地配置自己的插画；请自行确认素材使用权，并让私人素材留在忽略目录中。"],
        ]
    else:
        titles = ["Volume and continuity", "The sending clock", "The unit changes participation", "Words and expressive habits",
                  "Channels beyond text", "Topic coverage bounds interpretation", "Lexical overlap and function words", "Room for different favorites"]
        bodies = [
            [f"The archive spans {s['first_date']} to {s['last_date']}: {fmt(s['records'])} records, including {fmt(s['participant_messages'])} participant messages and {fmt(s['system_records'])} system notices. Records occur on {s['active_dates']} of {s['calendar_dates']} calendar dates.",
             f"The peak is {fmt(s['peak']['count'])} records on {s['peak']['date']}; the longest continuous run lasts {s['longest_run']['days']} dates. Monthly intensity uses observed calendar dates, including zero-record dates. Intensity and continuity answer different questions."],
            ["Hourly and weekday distributions describe sending times. The weekday heat map adjusts for calendar exposure; individual hourly profiles use each sender's own message total. The night window is 00:00-04:59.",
             "These distributions do not measure sleep or continuous availability. A higher share need not represent a larger absolute count."],
            [f"{names[0]} contributes {percent(a['message_share'])} of participant messages, {percent(a['character_share'])} of characters and {percent(a['turn_share'])} of turns. Turn counts are {fmt(a['turns'])} and {fmt(b['turns'])}.",
             f"Message-count ratio = turn-count ratio x mean-messages-per-turn ratio: {identity}. This is an accounting identity, not a causal model of effort or emotional work.",
             f"Median adjacent reply gaps are {fmt(a['reply_median_seconds'])} and {fmt(b['reply_median_seconds'])} seconds. They are timestamp differences at sender switches, not read-receipt latencies."],
            [f"There are {fmt(s['text_messages'])} text bodies and {fmt(s['characters'])} characters. Word contrasts are corpus-relative rankings. Phrase counts measure bodies containing a specified string.",
             f"Supplied sticker identifiers distinguish {s['stickers']['identified']} images; {s['stickers']['shared_identifiers']} identifiers are used by both. Image identities are not inferred when identifiers are absent. Raw attachments are not displayed."],
            [f"{s['calls']['notices']} call notices resolve to {s['calls']['identifiable_sessions']} identifiable sessions; {s['calls']['unidentified_notices']} notices lack usable identifiers. Duration is consistent and retained for {s['calls']['known_duration_sessions']} sessions, totaling {fmt(s['calls']['known_hours'], 2)} hours.",
             f"The {s['voice']['messages']} voice-note records contain {fmt(s['voice']['known_hours'], 2)} known source hours. Missing durations stay missing and conflicting durations are not arbitrarily selected. Channel durations are not corrected for overlap.",
             "Exploratory affect is disabled by default. If enabled, only example-lexicon coverage and date-cluster bootstrap results are reported; no affection score is produced."],
            [f"At least one configurable topic dictionary matches {percent(s['topic_coverage'])} of text bodies. Categories overlap; the figure is not an exhaustive, exclusive partition of the conversation.",
             "Mentions do not establish meals, journeys or fulfilled plans. Changing a dictionary changes coverage and rankings; retain the exact specification."],
            [f"The first and last eligible content-word cosines are {endpoints}. A fixed vocabulary has {s['language']['vocabulary_size']} word types. Equal samples use {s['language']['sample_messages']} eligible messages per person per month across {s['language']['sampling_draws']} draws.",
             "Shading describes sampling sensitivity, not causal confidence. Small pools reduce the common sample size; unavailable similarities stay unavailable. The eight-category function-word index is an unvalidated example, not a relationship-quality measure."],
            ["This page uses reported hometowns, likes and dislikes from configuration, separate from statistical evidence. Preferences can be preserved without first being inferred from word frequencies.",
             "The default artwork is an abstract ribbon drawn by this project. You may supply a private illustration locally; confirm its usage rights and keep it in an ignored directory."],
        ]
    return [{"number": i + 1, "title": title, "paragraphs": paragraphs} for i, (title, paragraphs) in enumerate(zip(titles, bodies))]


def write_reports(summary, config, output, pdf=False):
    output = Path(output); template_dir = str(files("naturelove").joinpath("templates"))
    html_env = Environment(loader=FileSystemLoader(template_dir), autoescape=True, undefined=StrictUndefined)
    tex_env = Environment(loader=FileSystemLoader(template_dir), autoescape=False, undefined=StrictUndefined)
    tex_env.filters["tex"] = tex_escape
    (output / "report.css").write_text(files("naturelove").joinpath("templates/report.css").read_text(), encoding="utf-8")
    tex_dir = output / "latex"; tex_dir.mkdir(exist_ok=True)
    for lang in ["zh", "en"]:
        context = {"s": summary, "config": config, "language": lang, "sections": sections(summary, config, lang),
                   "abstract": (f"本稿基于 {fmt(summary['records'])} 条归档记录，分别观察交流连续性、参与方式、渠道与语言重叠。所有数字由本次输入计算，未借用其他档案的结果。"
                                if lang == "zh" else f"This report describes continuity, participation, channels and lexical overlap in {fmt(summary['records'])} archive records. Every number is calculated from this input; no other archive's findings are substituted."),
                   "authors": " & ".join(p["name"] for p in config["participants"])}
        (output / f"report_{lang}.html").write_text(html_env.get_template("report.html.j2").render(**context), encoding="utf-8")
        (tex_dir / f"report_{lang}.tex").write_text(tex_env.get_template("report.tex.j2").render(**context), encoding="utf-8")
    if pdf:
        executable = shutil.which("xelatex")
        if not executable:
            raise ValueError("PDF needs XeLaTeX on PATH (TeX Live/MacTeX). HTML and editable TeX sources have already been saved.")
        for lang in ["zh", "en"]:
            for _ in range(2):
                run = subprocess.run([executable, "-no-shell-escape", "-interaction=nonstopmode", "-halt-on-error", f"report_{lang}.tex"],
                                     cwd=tex_dir, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
                (tex_dir / f"compile_{lang}.txt").write_text(run.stdout + run.stderr, encoding="utf-8")
                if run.returncode:
                    raise ValueError(f"XeLaTeX failed; see latex/compile_{lang}.txt. Saved sources are retained.")
            shutil.copyfile(tex_dir / f"report_{lang}.pdf", output / f"report_{lang}.pdf")

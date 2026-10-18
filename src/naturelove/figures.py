"""Seven analysis figures and a personal portrait, with no bundled character art."""
from collections import Counter
from pathlib import Path
import re
import textwrap
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, PathPatch
from matplotlib.path import Path as DrawingPath
import matplotlib.dates as mdates


def setup_fonts():
    cjk = False
    for name in ["Noto Sans CJK SC", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", "Songti SC", "SimHei"]:
        try:
            font_manager.findfont(name, fallback_to_default=False)
            plt.rcParams["font.family"] = ["DejaVu Sans", name]
            cjk = True
            break
        except ValueError:
            continue
    plt.rcParams.update({"font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8,
                         "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 6,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "pdf.fonttype": 3, "svg.fonttype": "none", "axes.unicode_minus": False})
    return cjk


def ecdf(ax, values, label, color):
    values = np.sort(np.array(values, dtype=float))
    if len(values): ax.step(values, np.arange(1, len(values) + 1) / len(values), where="post", label=label, color=color)


def empty(ax, text="No eligible observations"):
    ax.text(.5, .5, text, ha="center", va="center", transform=ax.transAxes, color="#786b76")
    ax.set_xticks([]); ax.set_yticks([])


def panels(axes, titles):
    for index, (ax, title) in enumerate(zip(np.ravel(axes), titles)):
        ax.set_title(chr(65 + index) + "  " + title, loc="left", pad=10)


def make_figures(summary, plot, config, output):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    cjk = setup_fonts(); ids = [p["id"] for p in config["participants"]]
    labels = {p["id"]: p["name"] for p in config["participants"]}
    colors = dict(zip(ids, config["colors"])); rose = config["colors"][1]
    def label(value, index=0):
        return value if cjk or not re.search(r"[\u4e00-\u9fff]", value) else f"term {index + 1}"
    names = {s: label(labels[s], i) for i, s in enumerate(ids)}
    def canvas(): return plt.subplots(2, 2, figsize=(7.1, 5.5), layout="constrained")
    def save(fig, number, title):
        fig.get_layout_engine().set(rect=(0, .045, 1, .92))
        heading = fig.suptitle(title, x=.03, ha="left", color=rose, fontsize=13, fontweight="bold")
        if summary["synthetic"]:
            fig.text(.99, .005, "SYNTHETIC DEMO", ha="right", color="#8e6a9d", fontsize=6)
        for extension in ["png", "svg"]:
            fig.savefig(output / f"Figure{number}.{extension}", dpi=300, bbox_inches="tight", pad_inches=.1)
        heading.remove()
        fig.get_layout_engine().set(rect=(0, .045, 1, .96))
        fig.savefig(output / f"Figure{number}.pdf", dpi=300, bbox_inches="tight", pad_inches=.1)
        plt.close(fig)
    daily = summary["daily"]; dates = [np.datetime64(d["date"]) for d in daily]
    months = summary["monthly"]; x = np.arange(len(months)); month_labels = [m["month"] for m in months]
    people = plot["people"]; units = summary["units"]

    fig, ax = canvas()
    ax[0, 0].plot(dates, np.cumsum([d["count"] for d in daily]), color=rose)
    ax[0, 0].set_ylabel("Archive records"); ax[0, 0].xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=5))
    if summary["relationship_window"]:
        ax[0, 0].axvline(np.datetime64(config["relationship_date"]), color=config["colors"][0], ls="--", lw=.8)
    ax[0, 1].bar(dates, [d["count"] for d in daily], color=rose, width=.8)
    ax[0, 1].xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=5))
    ax[1, 0].bar(x, [m["records_per_day"] for m in months], color=config["colors"][0]); ax[1, 0].set_xticks(x, month_labels, rotation=30)
    types = summary["types"]; ax[1, 1].barh(list(types), list(types.values()), color=rose)
    panels(ax, ["Cumulative record", "All calendar dates, including zeros", "Records / observed calendar day", "Participant message types"])
    save(fig, 1, "Volume and continuity")

    fig, ax = canvas(); exposure = Counter(np.datetime64(d["date"]).astype(object).weekday() for d in daily)
    heat = np.zeros((7, 24))
    for r in people: heat[r["weekday"], r["hour"]] += 1
    denominator = np.array([exposure[i] for i in range(7)])[:, None]
    heat = np.divide(heat, denominator, out=np.full_like(heat, np.nan), where=denominator != 0)
    im = ax[0, 0].imshow(heat, aspect="auto", cmap="PuRd"); fig.colorbar(im, ax=ax[0, 0], shrink=.75)
    ax[0, 0].set_yticks(range(7), ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
    for s in ids:
        sub = [r for r in people if r["sender"] == s]
        counts = Counter(r["hour"] for r in sub)
        if sub: ax[0, 1].plot(range(24), [100 * counts[h] / len(sub) for h in range(24)], label=names[s], color=colors[s])
    ax[0, 1].legend(frameon=False); ax[0, 1].set_ylabel("Own participant messages (%)")
    by_month = np.zeros((len(months), 24))
    for i, m in enumerate(months):
        sub = [r for r in people if r["month"] == m["month"]]
        if not sub: by_month[i, :] = np.nan
        for r in sub: by_month[i, r["hour"]] += 100 / len(sub)
    ax[1, 0].imshow(by_month, aspect="auto", cmap="PuRd"); ax[1, 0].set_yticks(x, month_labels)
    ax[1, 1].plot(x, [100 * m["night_share"] if m["night_share"] is not None else np.nan for m in months], "o-", color=rose)
    ax[1, 1].set_xticks(x, month_labels, rotation=30); ax[1, 1].set_ylabel("Participant messages (%)")
    panels(ax, ["Weekday / hour, exposure adjusted", "Each person's sending clock", "Within-month hourly distribution", "00:00-04:59 share"])
    save(fig, 2, "The sending clock")

    fig, ax = canvas(); left = np.zeros(3)
    for i, u in enumerate(units):
        shares = [100 * u[k] if u[k] is not None else 0 for k in ["message_share", "character_share", "turn_share"]]
        ax[0, 0].barh(range(3), shares, left=left, color=colors[u["sender"]], label=names[u["sender"]])
        for j, v in enumerate(shares):
            if v > 8: ax[0, 0].text(left[j] + v / 2, j, f"{v:.1f}%", color="white", ha="center", va="center", fontsize=7)
        left += shares
    ax[0, 0].set_yticks(range(3), ["Messages", "Text characters", "Turns"]); ax[0, 0].invert_yaxis(); ax[0, 0].set_xlim(0, 100)
    if not summary["characters"]:
        ax[0, 0].text(50, 1, "NA: no text characters", ha="center", va="center", fontsize=7)
    ax[0, 0].legend(frameon=False, fontsize=5.5, ncol=2, loc="upper center", bbox_to_anchor=(.5, -.15))
    for s in ids:
        ecdf(ax[0, 1], [t["messages"] for t in plot["turns"] if t["sender"] == s], names[s], colors[s])
        ecdf(ax[1, 1], plot["replies"][s], names[s], colors[s])
    ax[0, 1].set_xscale("log"); ax[0, 1].legend(frameon=False); ax[1, 1].set_xscale("symlog", linthresh=1); ax[1, 1].legend(frameon=False)
    ax[1, 1].set_xlabel("Timestamp gap in seconds")
    for i, u in enumerate(units):
        ax[1, 0].bar(np.array([0, 1]) + i * .34, [u["conversation_starts"], u["closing_messages"]], width=.32, label=names[u["sender"]], color=colors[u["sender"]])
    ax[1, 0].set_xticks([.17, 1.17], ["Starts", "Chat-day last messages"]); ax[1, 0].legend(frameon=False)
    panels(ax, ["Three units of participation", "Messages per turn: cumulative fraction", "Different positions in an exchange", "Adjacent reply gaps: cumulative fraction"])
    save(fig, 3, "Participation depends on the unit")

    fig, ax = canvas(); contrasts = summary["language"]["contrasts"]
    selected = (contrasts[:5] + contrasts[-5:]) if len(contrasts) > 10 else contrasts
    if selected:
        ax[0, 0].barh(range(len(selected)), [r["score"] for r in selected], color=[config["colors"][int(r["score"] > 0)] for r in selected])
        ax[0, 0].set_yticks(range(len(selected)), [label(r["word"], i) for i, r in enumerate(selected)])
    else: empty(ax[0, 0])
    phrases = summary["phrases"]
    if phrases:
        ax[0, 1].barh(range(len(phrases)), [p["messages"] for p in phrases], color=rose)
        ax[0, 1].set_yticks(range(len(phrases)), [label(p["phrase"], i) for i, p in enumerate(phrases)])
    else: empty(ax[0, 1])
    ax[1, 0].bar(["All identified", "Used by both"], [summary["stickers"]["identified"], summary["stickers"]["shared_identifiers"]], color=config["colors"])
    ax[1, 1].bar([names[s] for s in ids], [u["mean_characters_per_turn"] or 0 for u in units], color=config["colors"])
    panels(ax, ["Weighted word contrasts (relative ranking)", "Messages containing each phrase", "Sticker identifiers, where supplied", "Mean text characters per turn"])
    save(fig, 4, "Words and expressive habits")

    fig, ax = canvas(); calls = summary["calls"]
    ax[0, 0].bar(["Call notices", "Identified sessions", "No session id"], [calls["notices"], calls["identifiable_sessions"], calls["unidentified_notices"]], color=[rose, config["colors"][0], "#d8c9d2"])
    ax[0, 0].tick_params(axis="x", labelsize=6)
    ax[0, 1].bar(["Known calls", "Known voice notes"], [calls["known_hours"], summary["voice"]["known_hours"]], color=config["colors"]); ax[0, 1].set_ylabel("Source-reported hours")
    totals = [sum(c["month"] == m["month"] for c in calls["sessions"]) for m in months]
    ax[1, 0].bar(x, totals, color=rose); ax[1, 0].set_xticks(x, month_labels, rotation=30)
    if summary["affect"]["enabled"]:
        results = summary["affect"]["reply_context"]
        for i, s in enumerate(ids):
            r = results[s]
            if r["interval95"]:
                lo, hi = r["interval95"]; v = r["difference"]
                ax[1, 1].errorbar(v, i, xerr=[[max(0, v - lo)], [max(0, hi - v)]], fmt="o", color=colors[s], capsize=3)
        ax[1, 1].set_yticks(range(2), [names[s] for s in ids]); ax[1, 1].axvline(0, color="#bbb", lw=.7)
        ax[1, 1].set_xlabel("Negative-minus-other gap (seconds)")
    else: empty(ax[1, 1], "Exploratory affect is disabled\nEnable explicitly in configuration")
    panels(ax, ["Notices and sessions are different units", "Duration is summed once per session", "Identifiable call sessions by month", "Optional date-bootstrap reply context"])
    save(fig, 5, "Channels and measurement limits")

    fig, ax = canvas(); topics = summary["topics"]
    if topics:
        ax[0, 0].barh(range(len(topics)), [t["messages"] for t in topics], color=rose)
        ax[0, 0].set_yticks(range(len(topics)), [label(t["topic"], i) for i, t in enumerate(topics)])
        for i, s in enumerate(ids):
            denominator = sum(r["sender"] == s and r["type"] == "text" for r in people)
            values = [1000 * t["by_sender"].get(s, 0) / denominator if denominator else 0 for t in topics]
            ax[0, 1].barh(np.arange(len(topics)) + i * .35, values, height=.33, color=colors[s], label=names[s])
        ax[0, 1].set_yticks(np.arange(len(topics)) + .17, [label(t["topic"], i) for i, t in enumerate(topics)]); ax[0, 1].legend(frameon=False)
    else: empty(ax[0, 0]); empty(ax[0, 1])
    coverage = summary["topic_coverage"]
    if coverage is not None:
        ax[1, 0].barh([0], [coverage * 100], color=rose); ax[1, 0].set_xlim(0, 100); ax[1, 0].set_yticks([]); ax[1, 0].set_xlabel("At least one dictionary match (%)")
    else: empty(ax[1, 0], "No text bodies")
    empty(ax[1, 1], "A message may match several topics.\nMentions do not establish activities.\nDictionaries are configurable examples.")
    panels(ax, ["Dictionary-visible mentions", "Matches per 1,000 own text bodies", "Coverage of all text bodies", "Interpretation boundary"])
    save(fig, 6, "Everyday topics, bounded by coverage")

    fig, ax = plt.subplots(2, 1, figsize=(7.1, 5.5), layout="constrained"); series = summary["language"]["months"]
    if series:
        xx = range(len(series)); ax[0].plot(xx, [r["cosine"] for r in series], "o-", color=config["colors"][0], label="Observed")
        ax[0].plot(xx, [r["sample_median"] if r["sample_median"] is not None else np.nan for r in series], "s--", color=rose, label="Equal count, fixed vocabulary")
        ax[0].fill_between(xx, [r["sampling_range95"][0] if r["sampling_range95"] else np.nan for r in series],
                           [r["sampling_range95"][1] if r["sampling_range95"] else np.nan for r in series], color=rose, alpha=.15)
        ax[1].plot(xx, [r["style_matching"] if r["style_matching"] is not None else np.nan for r in series], "o-", color=rose)
        for a in ax: a.set_xticks(list(xx), [r["month"] for r in series]); a.set_ylim(0, 1.02)
        ax[0].legend(frameon=False)
    else:
        for a in ax: empty(a, "Need content words from both participants in the same month")
    panels(ax, ["Content-word cosine and sampling range", "Adapted function-word matching (unvalidated)"])
    save(fig, 7, "Lexical overlap and style are different measures")

    fig, ax = plt.subplots(figsize=(7.1, 4.2), layout="constrained"); ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    if config["illustration"]:
        art = plt.imread(config["illustration"]); ax.imshow(art, extent=(.02, .98, .58, .98), aspect="auto")
    else:
        path = DrawingPath([(.04, .78), (.3, .98), (.38, .55), (.5, .78), (.62, .98), (.7, .55), (.96, .78)],
                           [DrawingPath.MOVETO] + [DrawingPath.CURVE4] * 6)
        ax.add_patch(PathPatch(path, edgecolor=rose, facecolor="none", linewidth=2.5, alpha=.7))
        ax.text(.5, .91, "TWO VOICES / A SHARED EVERYDAY", ha="center", color=rose, fontsize=11)
        ax.text(.5, .66, "Personal background, supplied by the participants", ha="center", color="#786b76", fontsize=7)
    for i, p in enumerate(config["participants"]):
        left = .02 + i * .5
        ax.add_patch(FancyBboxPatch((left, .04), .44, .49, boxstyle="round,pad=.01", facecolor="#fbeff4", edgecolor=config["colors"][i], lw=.7))
        ax.text(left + .025, .45, names[p["id"]], color=config["colors"][i], fontsize=11, fontweight="bold")
        hometown = label(p["hometown"]) if p["hometown"] else "Hometown not supplied"
        ax.text(left + .025, .36, hometown, fontsize=8, color="#786b76")
        likes = "; ".join(p["likes"]) or "Preferences not supplied"
        lines = textwrap.wrap(label(likes), 34)[:3]
        if p["dislikes"]: lines.append("Dislikes: " + label("; ".join(p["dislikes"])))
        for j, line in enumerate(lines[:4]): ax.text(left + .025, .27 - j * .055, line, fontsize=7.5)
    save(fig, 8, "A personal portrait, separate from statistics")
    return [f"Figure{i}" for i in range(1, 9)]

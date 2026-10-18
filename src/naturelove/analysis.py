"""Descriptive summaries with explicit units, denominators and missingness."""
from collections import Counter, defaultdict
from datetime import date, timedelta
import logging
import math
import re
import numpy as np

# A small, independently assembled example vocabulary. It is deliberately configurable.
STOPWORDS = {"我们", "你们", "他们", "这个", "那个", "一个", "就是", "可以", "还是", "什么", "怎么", "没有", "自己", "现在", "已经", "the", "and", "that", "this"}
FUNCTION_WORDS = {
    "pronouns": {"我", "你", "他", "她", "我们", "你们"},
    "particles": {"啊", "呢", "吗", "吧", "呀"},
    "negators": {"不", "没", "没有", "别"},
    "conjunctions": {"和", "但是", "所以", "因为", "如果"},
    "degree": {"很", "太", "更", "最", "非常"},
    "questions": {"谁", "什么", "怎么", "为什么", "哪里"},
    "aspect": {"了", "过", "着", "正在"},
    "prepositions": {"在", "从", "向", "对", "给", "把"},
}


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def median(values):
    return float(np.median(values)) if values else None


def cosine(a, b):
    denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / denominator) if denominator else None


def combine(counters):
    result = Counter()
    for counter in counters:
        result.update(counter)
    return result


def tokenize(text):
    import jieba
    jieba.setLogLevel(logging.ERROR)
    text = re.sub(r"https?://\S+|\[[^\]\n]{1,30}\]", " ", text)
    return [w.lower().strip() for w in jieba.lcut(text) if re.search(r"[\u4e00-\u9fffA-Za-z]", w)]


def affect_score(text, lexicon):
    positive = sum(text.count(w) for w in lexicon["positive"] if w)
    negative = sum(text.count(w) for w in lexicon["negative"] if w)
    return ratio(positive - negative, positive + negative)


def bootstrap_reply(rows, seed, draws=1000):
    negative = [r["gap"] for r in rows if r["negative"]]
    other = [r["gap"] for r in rows if not r["negative"]]
    if not negative or not other:
        return {"negative_n": len(negative), "other_n": len(other), "difference": None, "interval95": None}
    dates = defaultdict(list)
    for row in rows:
        dates[row["date"]].append(row)
    if len(dates) < 2:
        return {"negative_n": len(negative), "other_n": len(other), "negative_median": median(negative),
                "other_median": median(other), "difference": median(negative) - median(other),
                "interval95": None, "bootstrap_draws": 0, "note": "At least two eligible dates are needed for date resampling."}
    groups = list(dates.values()); rng = np.random.default_rng(seed); differences = []
    for _ in range(draws):
        selected = [row for i in rng.integers(0, len(groups), len(groups)) for row in groups[i]]
        a = [r["gap"] for r in selected if r["negative"]]
        b = [r["gap"] for r in selected if not r["negative"]]
        if a and b:
            differences.append(median(a) - median(b))
    return {"negative_n": len(negative), "other_n": len(other), "negative_median": median(negative),
            "other_median": median(other), "difference": median(negative) - median(other),
            "interval95": [float(x) for x in np.quantile(differences, [.025, .975])] if differences else None,
            "bootstrap_draws": draws}


def language_summary(texts, ids, config):
    tokens = {r["id"] + ":" + str(r["source_order"]): tokenize(r["text"]) for r in texts}
    content = {}
    pooled = Counter(); per_sender = {s: Counter() for s in ids}
    monthly = defaultdict(lambda: {s: [] for s in ids})
    style = defaultdict(lambda: {s: Counter() for s in ids})
    total_tokens = defaultdict(lambda: Counter())
    for row in texts:
        key = row["id"] + ":" + str(row["source_order"]); all_words = tokens[key]
        words = Counter(w for w in all_words if len(w) >= 2 and w not in STOPWORDS)
        content[key] = words; pooled.update(words); per_sender[row["sender"]].update(words)
        if words:
            monthly[row["month"]][row["sender"]].append(words)
        for category, terms in FUNCTION_WORDS.items():
            style[row["month"]][row["sender"]][category] += sum(w in terms for w in all_words)
        total_tokens[row["month"]][row["sender"]] += len(all_words)
    vocabulary = sorted(w for w, count in pooled.items() if count >= config["vocabulary_min_count"])
    valid = {month: groups for month, groups in monthly.items() if all(groups[s] for s in ids)}
    common_sample = min([config["sample_messages"]] + [len(g[s]) for g in valid.values() for s in ids]) if valid else 0
    rng = np.random.default_rng(config["seed"]); series = []
    for month, groups in sorted(valid.items()):
        local = sorted(set().union(*(set(c) for s in ids for c in groups[s])))
        aggregates = [combine(groups[s]) for s in ids]
        observed = cosine(*[np.array([c[w] for w in local], dtype=float) for c in aggregates])
        fixed = cosine(*[np.array([c[w] for w in vocabulary], dtype=float) for c in aggregates]) if vocabulary else None
        sampled = []
        if vocabulary:
            for _ in range(config["sampling_draws"]):
                vectors = []
                for s in ids:
                    chosen = rng.choice(len(groups[s]), common_sample, replace=False)
                    counts = combine(groups[s][i] for i in chosen)
                    vectors.append(np.array([counts[w] for w in vocabulary], dtype=float))
                value = cosine(*vectors)
                if value is not None:
                    sampled.append(value)
        scores = []
        if all(total_tokens[month][s] for s in ids):
            for category in FUNCTION_WORDS:
                a, b = [style[month][s][category] / total_tokens[month][s] for s in ids]
                scores.append(1 - abs(a - b) / (a + b + .0001))
        series.append({"month": month, "cosine": observed, "fixed_vocabulary_cosine": fixed,
                       "sample_median": median(sampled),
                       "sampling_range95": [float(x) for x in np.quantile(sampled, [.025, .975])] if sampled else None,
                       "messages_per_person": common_sample, "available_messages": {s: len(groups[s]) for s in ids},
                       "successful_sampling_draws": len(sampled),
                       "style_matching": float(np.mean(scores)) if scores else None})
    # Informative-prior log odds: a corpus-relative ranking, not an independent significance test.
    contrasts = []; totals = [sum(per_sender[s].values()) for s in ids]; prior_total = .1 * sum(pooled.values())
    for word, count in pooled.items():
        if count < 5:
            continue
        prior = .1 * count; counts = [per_sender[s][word] for s in ids]
        denominators = [totals[i] + prior_total - counts[i] - prior for i in range(2)]
        if min(denominators) <= 0:
            continue
        delta = math.log((counts[1] + prior) / denominators[1]) - math.log((counts[0] + prior) / denominators[0])
        score = delta / math.sqrt(1 / (counts[0] + prior) + 1 / (counts[1] + prior))
        contrasts.append({"word": word, "score": score, "counts": dict(zip(ids, counts))})
    return {"months": series, "vocabulary_size": len(vocabulary), "sample_messages": common_sample,
            "sampling_draws": config["sampling_draws"], "vocabulary_min_count": config["vocabulary_min_count"],
            "top_words": {s: per_sender[s].most_common(12) for s in ids},
            "contrasts": sorted(contrasts, key=lambda x: x["score"]),
            "note": "Central sampling ranges are sensitivity summaries, not causal confidence intervals. Style dictionary is a small unvalidated example."}


def analyze(rows, config, quality):
    ids = [p["id"] for p in config["participants"]]
    people = [r.copy() for r in rows if r["type"] != "system"]
    first, last = [date.fromisoformat(rows[i]["date"]) for i in [0, -1]]
    calendar = [first + timedelta(days=i) for i in range((last - first).days + 1)]
    counts = Counter(r["date"] for r in rows); run = []; longest = []
    daily = []
    for day in calendar:
        key = day.isoformat(); n = counts[key]
        daily.append({"date": key, "count": n})
        if n:
            run.append(key)
            if len(run) > len(longest): longest = run.copy()
        else:
            run = []
    turns = []; conversations = 0; previous = None; replies = {s: [] for s in ids}; closing = {}
    for row in people:
        gap = row["timestamp"] - previous["timestamp"] if previous else None
        new = previous is None or gap > config["conversation_gap_hours"] * 3600
        if new: conversations += 1
        if new or row["sender"] != previous["sender"]:
            turns.append({"sender": row["sender"], "messages": 0, "characters": 0, "conversation": conversations,
                          "date": row["date"], "start": row["timestamp"], "end": row["timestamp"], "scores": []})
        turn = turns[-1]; turn["messages"] += 1; turn["characters"] += row["characters"]; turn["end"] = row["timestamp"]
        if config["exploratory_affect"] and row["type"] == "text":
            score = affect_score(row["text"], config["affect_lexicon"])
            if score is not None: turn["scores"].append(score)
        if not new and previous["sender"] != row["sender"]:
            replies[row["sender"]].append(gap)
        day = date.fromisoformat(row["date"])
        if row["hour"] < config["day_boundary_hour"]: day -= timedelta(days=1)
        closing[day.isoformat()] = row["sender"]
        previous = row
    starts = Counter()
    for i, turn in enumerate(turns):
        if i == 0 or turn["conversation"] != turns[i - 1]["conversation"]: starts[turn["sender"]] += 1
    text_rows = [r for r in people if r["type"] == "text"]
    total_chars = sum(r["characters"] for r in people); units = []
    for s in ids:
        messages = [r for r in people if r["sender"] == s]; ts = [t for t in turns if t["sender"] == s]
        units.append({"sender": s, "messages": len(messages), "message_share": ratio(len(messages), len(people)),
                      "characters": sum(r["characters"] for r in messages),
                      "character_share": ratio(sum(r["characters"] for r in messages), total_chars),
                      "turns": len(ts), "turn_share": ratio(len(ts), len(turns)),
                      "mean_messages_per_turn": ratio(len(messages), len(ts)), "median_messages_per_turn": median([t["messages"] for t in ts]),
                      "mean_characters_per_turn": ratio(sum(t["characters"] for t in ts), len(ts)),
                      "reply_median_seconds": median(replies[s]), "conversation_starts": starts[s],
                      "closing_messages": sum(v == s for v in closing.values())})
    monthly = []
    for month in sorted({r["month"] for r in rows}):
        sub = [r for r in rows if r["month"] == month]; ps = [r for r in sub if r["type"] != "system"]
        days = sum(day.strftime("%Y-%m") == month for day in calendar)
        monthly.append({"month": month, "records": len(sub), "observed_days": days,
                        "records_per_day": len(sub) / days, "participant_messages": len(ps),
                        "night_share": ratio(sum(r["hour"] < 5 for r in ps), len(ps)),
                        "types": dict(Counter(r["type"] for r in ps))})
    call_rows = [r for r in people if r["type"] == "call"]; grouped = defaultdict(list)
    for row in call_rows:
        if row["call_id"]: grouped[row["call_id"]].append(row)
    calls = []; conflicts = 0
    for group in grouped.values():
        values = {r["duration_seconds"] for r in group if r["duration_seconds"] is not None}
        if len(values) > 1: conflicts += 1
        kinds = {r["call_type"] for r in group} - {"unknown", ""}
        calls.append({"month": group[0]["month"], "type": next(iter(kinds)) if len(kinds) == 1 else "mixed" if kinds else "unknown",
                      "duration_seconds": next(iter(values)) if len(values) == 1 else None,
                      "source_notices": len(group)})
    voices = [r for r in people if r["type"] == "voice"]
    phrases = [{"phrase": word, "messages": sum(word in r["text"] for r in text_rows)} for word in config["phrases"]]
    topics = []; matched = 0
    for name, words in config["topics"].items():
        selected = [r for r in text_rows if any(w and w in r["text"] for w in words)]
        topics.append({"topic": name, "messages": len(selected), "by_sender": dict(Counter(r["sender"] for r in selected))})
    matched = sum(any(any(w and w in r["text"] for w in words) for words in config["topics"].values()) for r in text_rows)
    stickers = defaultdict(Counter)
    for row in people:
        if row["type"] == "sticker" and row["sticker_id"]: stickers[row["sticker_id"]][row["sender"]] += 1
    shared = [v for v in stickers.values() if all(v[s] for s in ids)]
    sensitivity = []
    for threshold in [1, 3, 6]:
        opened = Counter(r["sender"] for i, r in enumerate(people) if i == 0 or r["timestamp"] - people[i - 1]["timestamp"] > threshold * 3600)
        sensitivity.append({"gap_hours": threshold, "conversations": sum(opened.values()), "starts": {s: opened[s] for s in ids}})
    affect = {"enabled": bool(config["exploratory_affect"])}
    if affect["enabled"]:
        scored = [affect_score(r["text"], config["affect_lexicon"]) for r in text_rows]
        pairs = {s: [] for s in ids}
        for previous, current in zip(turns, turns[1:]):
            if previous["conversation"] == current["conversation"] and previous["scores"]:
                pairs[current["sender"]].append({"date": current["date"], "gap": current["start"] - previous["end"],
                                                  "negative": float(np.mean(previous["scores"])) < -.2})
        affect.update({"scored_messages": sum(v is not None for v in scored),
                       "coverage": ratio(sum(v is not None for v in scored), len(text_rows)),
                       "reply_context": {s: bootstrap_reply(pairs[s], config["seed"]) for s in ids},
                       "note": "Exploratory lexicon only; missing scores stay missing; no human validation or emotion/relationship quality score."})
    relationship = config["relationship_date"]
    relationship_window = None
    if relationship and first <= date.fromisoformat(relationship) <= last:
        dates = [d for d in daily if d["date"] >= relationship]
        relationship_window = {"calendar_dates": len(dates), "elapsed_days": len(dates) - 1,
                               "active_dates": sum(d["count"] > 0 for d in dates)}
    a, b = units
    decomposition = None
    if a["messages"] and b["messages"]:
        decomposition = {"message_ratio": a["messages"] / b["messages"], "turn_ratio": a["turns"] / b["turns"],
                         "messages_per_turn_ratio": a["mean_messages_per_turn"] / b["mean_messages_per_turn"]}
    summary = {"schema_version": 1, "synthetic": config["synthetic"], "quality": quality,
               "records": len(rows), "participant_messages": len(people), "system_records": len(rows) - len(people),
               "text_messages": len(text_rows), "characters": total_chars, "first_date": first.isoformat(), "last_date": last.isoformat(),
               "calendar_dates": len(calendar), "active_dates": sum(d["count"] > 0 for d in daily),
               "peak": max(daily, key=lambda d: d["count"]),
               "longest_run": {"days": len(longest), "start": longest[0], "end": longest[-1]},
               "relationship_window": relationship_window, "daily": daily, "monthly": monthly, "units": units,
               "decomposition": decomposition, "conversations": conversations, "conversation_sensitivity": sensitivity,
               "chat_days": len(closing), "types": dict(Counter(r["type"] for r in people)),
               "calls": {"notices": len(call_rows), "identifiable_sessions": len(calls),
                         "unidentified_notices": sum(not r["call_id"] for r in call_rows),
                         "known_duration_sessions": sum(c["duration_seconds"] is not None for c in calls),
                         "known_hours": sum(c["duration_seconds"] or 0 for c in calls) / 3600,
                         "duration_conflicts": conflicts, "sessions": calls},
               "voice": {"messages": len(voices), "known_duration_messages": sum(r["duration_seconds"] is not None for r in voices),
                         "known_hours": sum(r["duration_seconds"] or 0 for r in voices) / 3600},
               "stickers": {"identified": len(stickers), "shared_identifiers": len(shared),
                            "shared_references": sum(sum(v.values()) for v in shared)},
               "phrases": phrases, "topics": topics, "topic_coverage": ratio(matched, len(text_rows)),
               "language": language_summary(text_rows, ids, config), "affect": affect}
    plot_data = {"people": people, "turns": turns, "replies": replies}
    return summary, plot_data

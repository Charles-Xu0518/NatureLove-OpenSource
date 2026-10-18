"""Deterministic fictional messages; never reads an existing conversation."""
from copy import deepcopy
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import random
from .config import DEFAULT


def demo_config():
    config = deepcopy(DEFAULT)
    config.update({"synthetic": True, "relationship_date": "2024-01-21", "sampling_draws": 40})
    config["participants"][0].update({"hometown": "City A", "likes": ["Photography", "Walking", "Coffee"]})
    config["participants"][1].update({"hometown": "City B", "likes": ["Reading", "Music", "Dessert"], "dislikes": ["Very bitter food"]})
    return config


def generate_messages(config=None):
    config = config or demo_config(); rng = random.Random(config["seed"])
    ids = [p["id"] for p in config["participants"]]; rows = []
    start = datetime(2024, 1, 3, 18, 0, tzinfo=ZoneInfo(config["timezone"]))
    corpus = [["今天工作怎么样", "咖啡很好喝", "哈哈今天很开心", "下班一起散步", "论文还没有写完", "到家告诉我", "这个电影喜欢吗", "谢谢你呀"],
              ["今天上课很有意思", "晚饭想吃什么", "奶茶加冰可以吗", "我也喜欢这个音乐", "晚安明天见", "有点担心作业", "期待周末看书", "冰淇淋很好吃"]]
    def add(when, sender, kind="text", text="", **kwargs):
        rows.append({"id": f"demo-{len(rows) + 1:05d}", "timestamp": when.isoformat(), "sender": sender,
                     "type": kind, "text": text, **kwargs})
    for day in range(67):
        if day % 13 == 0: continue
        when = start + timedelta(days=day, hours=(day % 6) - 2)
        for turn in range(rng.randint(6, 12)):
            index = (turn + day) % 2; sender = ids[index]
            packets = rng.randint(1, 3) if index == 0 else 1
            for packet in range(packets):
                text = rng.choice(corpus[index] + corpus[1 - index][:min(4, day // 17)])
                kind = rng.choices(["text", "sticker", "image", "voice"], weights=[84, 7, 5, 4])[0]
                extra = {"sticker_id": "demo-sticker-" + str(rng.randrange(8))} if kind == "sticker" else {}
                if kind == "voice": extra["duration_seconds"] = rng.randint(2, 18)
                add(when + timedelta(seconds=packet), sender, kind, text if kind == "text" else "", **extra)
            when += timedelta(seconds=packets + rng.randint(3, 38))
        if day % 9 == 0:
            call_id = "demo-call-" + str(day)
            for offset, sender in [(0, ids[0]), (360, ids[1])]:
                add(when + timedelta(seconds=offset), sender, "call", call_id=call_id, call_type="video" if day % 2 else "audio", duration_seconds=360)
        if day % 17 == 0:
            add(when + timedelta(minutes=10), ids[1], "call")
        if day % 11 == 0: add(when + timedelta(minutes=11), "system", "system", "Synthetic system notice")
    return rows

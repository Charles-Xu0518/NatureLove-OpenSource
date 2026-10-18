"""Configuration has no machine-specific paths or personal defaults."""
from copy import deepcopy
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo
import json

DEFAULT = {
    "title": "Nature Love", "timezone": "Asia/Shanghai", "relationship_date": None, "joint_first_authors": False,
    "participants": [{"id": "A", "name": "Participant A", "hometown": "", "likes": [], "dislikes": []},
                     {"id": "B", "name": "Participant B", "hometown": "", "likes": [], "dislikes": []}],
    "conversation_gap_hours": 3, "day_boundary_hour": 5, "seed": 20261018,
    "sample_messages": 1000, "sampling_draws": 200, "vocabulary_min_count": 10,
    "phrases": ["早安", "晚安", "谢谢", "想你", "爱你", "哈哈"],
    "topics": {"日常": ["早饭", "午饭", "晚饭", "下班", "睡觉"],
               "饮食": ["咖啡", "奶茶", "冰淇淋", "吃饭", "火锅"],
               "工作学习": ["上课", "作业", "工作", "论文", "开会"],
               "出行": ["出发", "到家", "地铁", "车站", "机场"]},
    "exploratory_affect": False,
    "affect_lexicon": {"positive": ["开心", "喜欢", "谢谢", "爱你", "期待"],
                       "negative": ["难过", "讨厌", "生气", "失望", "担心"]},
    "colors": ["#8E6A9D", "#CB4F86"], "illustration": None,
    "synthetic": False,
}


def load_config(path=None):
    config = deepcopy(DEFAULT)
    if path:
        path = Path(path).expanduser().resolve()
        incoming = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(incoming, dict):
            raise ValueError("Configuration must be a JSON object.")
        unknown = set(incoming) - set(DEFAULT)
        if unknown:
            raise ValueError("Unknown configuration fields: " + ", ".join(sorted(unknown)))
        config.update(incoming)
        if config["illustration"]:
            art = Path(config["illustration"]).expanduser()
            config["illustration"] = str((path.parent / art).resolve() if not art.is_absolute() else art.resolve())
    ZoneInfo(config["timezone"])
    people = config["participants"]
    if len(people) != 2 or any(not p.get("id") or not p.get("name") for p in people):
        raise ValueError("Exactly two participants with non-empty id and name are required.")
    if len({str(p["id"]) for p in people}) != 2:
        raise ValueError("Participant identifiers must differ.")
    for p in people:
        p["id"] = str(p["id"])
        for key, default in [("hometown", ""), ("likes", []), ("dislikes", [])]:
            p.setdefault(key, default)
        if not isinstance(p["likes"], list) or not isinstance(p["dislikes"], list):
            raise ValueError("Participant likes and dislikes must be lists.")
    if config["relationship_date"]:
        date.fromisoformat(config["relationship_date"])
    if not 0 <= config["day_boundary_hour"] <= 23:
        raise ValueError("day_boundary_hour must be between 0 and 23.")
    if not 0 < config["conversation_gap_hours"] <= 168:
        raise ValueError("conversation_gap_hours must be in (0, 168].")
    for key in ["sample_messages", "sampling_draws", "vocabulary_min_count"]:
        if not isinstance(config[key], int) or not 1 <= config[key] <= 100000:
            raise ValueError(key + " must be a positive integer at most 100000.")
    if len(config["colors"]) != 2:
        raise ValueError("Exactly two participant colors are required.")
    return config

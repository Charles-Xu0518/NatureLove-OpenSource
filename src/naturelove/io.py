"""Normalize exported JSON/CSV. This module does not decrypt databases."""
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import csv
import hashlib
import json
import math

TYPES = {"emoji": "sticker", "voip": "call", "quote": "text", "picture": "image", "audio": "voice"}
SUPPORTED = {"text", "sticker", "image", "video", "voice", "call", "file", "link", "location", "system", "other"}


def value(row, *keys):
    return next((row[k] for k in keys if k in row and row[k] is not None and row[k] != ""), None)


def number(raw, field):
    if raw is None or raw == "":
        return None
    try:
        parsed = float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid {field}: a non-negative finite number is required.") from exc
    if not math.isfinite(parsed) or parsed < 0:
        raise ValueError(f"Invalid {field}: a non-negative finite number is required.")
    return parsed


def parse_time(raw, timezone):
    zone = ZoneInfo(timezone)
    if isinstance(raw, (int, float)) or (isinstance(raw, str) and raw.replace(".", "", 1).isdigit()):
        ts = float(raw)
        if abs(ts) >= 100000000000:
            ts /= 1000
        return datetime.fromtimestamp(ts, zone)
    if not isinstance(raw, str):
        raise ValueError("A timestamp or ISO datetime is required for every message.")
    parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    return (parsed.replace(tzinfo=zone) if parsed.tzinfo is None else parsed.astimezone(zone))


def load_messages(path, config):
    path = Path(path).expanduser().resolve()
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as stream:
            raw_rows = list(csv.DictReader(stream))
    elif path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        raw_rows = data.get("messages") if isinstance(data, dict) else data
        if not isinstance(raw_rows, list):
            raise ValueError("JSON must be a message list or an object with a messages list.")
    else:
        raise ValueError("Input must be a .json or .csv export.")
    if not raw_rows:
        raise ValueError("The input contains no messages.")
    ids = {p["id"] for p in config["participants"]}
    rows, seen, duplicate_count = [], {}, 0
    for index, row in enumerate(raw_rows, 1):
        if not isinstance(row, dict):
            raise ValueError(f"Message {index} is not an object.")
        try:
            kind = str(value(row, "render_type", "type") or "text")
            kind = TYPES.get(kind, kind)
            if kind not in SUPPORTED:
                kind = "other"
            sender = str(value(row, "sender", "sender_id") or "")
            if kind != "system" and sender not in ids:
                raise ValueError("Sender is not one of the two configured participant ids.")
            when = parse_time(value(row, "timestamp", "ts", "datetime", "time", "create_time"), config["timezone"])
            text = value(row, "text", "content") or ""
            if not isinstance(text, str):
                raise ValueError("Text/content must be a string, not a nested export object.")
            raw_id = value(row, "id", "source_message_id", "server_id")
            call_id = str(value(row, "call_id", "call_session_id", "room_id") or "")
            if call_id == "0":
                call_id = ""
            normalized = {
                "id": str(raw_id) if raw_id is not None else f"row-{index}",
                "timestamp": when.timestamp(), "datetime": when.isoformat(), "date": when.date().isoformat(),
                "month": when.strftime("%Y-%m"), "hour": when.hour, "weekday": when.weekday(),
                "sender": sender, "type": kind, "text": text,
                "characters": len(text) if kind == "text" else 0,
                "duration_seconds": number(value(row, "duration_seconds", "voice_sec" if kind == "voice" else "call_sec"), "duration_seconds"),
                "call_id": hashlib.sha256(call_id.encode()).hexdigest() if call_id else None,
                "call_type": str(value(row, "call_type") or "unknown"),
                "sticker_id": str(value(row, "sticker_id", "emoji_md5") or ""),
                "media_path": str(value(row, "media_path") or ""), "source_order": index,
            }
            if raw_id is not None and str(raw_id) not in {"", "0"}:
                if normalized["id"] in seen:
                    previous = {k: v for k, v in seen[normalized["id"]].items() if k != "source_order"}
                    current = {k: v for k, v in normalized.items() if k != "source_order"}
                    if previous != current:
                        raise ValueError("Conflicting records use the same message id.")
                    duplicate_count += 1
                    continue
                seen[normalized["id"]] = normalized
            rows.append(normalized)
        except (ValueError, TypeError, OverflowError) as exc:
            raise ValueError(f"Message {index}: {exc}") from exc
    rows.sort(key=lambda r: (r["timestamp"], r["source_order"]))
    if not any(r["type"] != "system" for r in rows):
        raise ValueError("At least one participant message is required.")
    quality = {"input_records": len(raw_rows), "retained_records": len(rows), "duplicate_records_removed": duplicate_count,
               "input_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "timezone": config["timezone"]}
    return rows, quality

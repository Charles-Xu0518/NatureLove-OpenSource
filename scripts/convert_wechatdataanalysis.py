"""Convert a single WeChatDataAnalysis schemaVersion 1 JSON export locally."""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys


TYPE_MAP = {"emoji": "sticker", "voip": "call", "quote": "text"}
TYPES = {"text", "image", "video", "voice", "sticker", "call", "file", "link", "location", "system", "other"}


def seconds(raw, divisor=1):
    if raw is None or raw == "":
        return None
    if isinstance(raw, bool):
        raise ValueError("Duration must be a number.")
    result = float(raw) / divisor
    if not math.isfinite(result) or result < 0:
        raise ValueError("Duration must be finite and non-negative.")
    return result


def convert_export(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("messages"), list):
        raise ValueError("Choose the conversation's messages.json from a WeChatDataAnalysis JSON export.")
    if payload.get("schemaVersion", 1) != 1:
        raise ValueError("Only schemaVersion 1 is supported.")
    conversation = payload.get("conversation") or {}
    if not isinstance(conversation, dict) or conversation.get("isGroup"):
        raise ValueError("Choose one private conversation, not a group export.")
    if not payload["messages"]:
        raise ValueError("The export contains no messages.")
    result, conversations = [], set()
    for index, row in enumerate(payload["messages"], 1):
        try:
            if not isinstance(row, dict) or not isinstance(row.get("renderType"), str):
                raise ValueError("Missing renderType; this is not the expected export format.")
            if row.get("isGroup"):
                raise ValueError("Group messages are not supported.")
            if row.get("conversationUsername"):
                conversations.add(str(row["conversationUsername"]))
            kind = TYPE_MAP.get(row["renderType"], row["renderType"])
            kind = kind if kind in TYPES else "other"
            sent = row.get("isSent")
            if kind != "system" and not isinstance(sent, bool):
                raise ValueError("isSent must be true or false; sender direction was not guessed.")
            timestamp = row.get("createTime")
            if isinstance(timestamp, bool) or timestamp is None or timestamp == "":
                raise ValueError("Missing createTime.")
            timestamp = float(timestamp)
            if not math.isfinite(timestamp):
                raise ValueError("createTime must contain finite Unix seconds.")
            datetime.fromtimestamp(timestamp, timezone.utc)
            text = row.get("content", "")
            if text is None:
                text = ""
            if not isinstance(text, str):
                raise ValueError("content must be a string.")
            message = {"timestamp": timestamp, "sender": "system" if kind == "system" else "A" if sent else "B",
                       "type": kind, "text": text}
            identifier = row.get("id")
            if identifier is None or identifier == "":
                identifier = row.get("serverId")
            if isinstance(identifier, (dict, list, bool, float)):
                raise ValueError("Message ids must be strings or integers.")
            if identifier is not None and str(identifier) not in {"", "0"}:
                message["id"] = str(identifier)
            if kind == "voice":
                duration = seconds(row.get("voiceLength"), 1000)
                message["duration_seconds"] = duration if duration else None
            elif kind == "call":
                message["call_type"] = row.get("voipType") or "unknown"
                if row.get("call_id"):
                    message["call_id"] = str(row["call_id"])
                message["duration_seconds"] = seconds(row.get("duration_seconds"))
            if kind == "sticker":
                message["sticker_id"] = str(row.get("emojiMd5") or "")
            result.append(message)
        except (ValueError, TypeError, OverflowError) as exc:
            raise ValueError(f"Message {index}: {exc}") from exc
    if len(conversations) > 1:
        raise ValueError("The file contains more than one conversation.")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        source = Path(args.input).expanduser().resolve()
        target = Path(args.output).expanduser().resolve()
        if source == target:
            raise ValueError("Use a separate output file; the original export must be retained.")
        payload = json.loads(source.read_text(encoding="utf-8-sig"))
        records = convert_export(payload)
        encoded = json.dumps(records, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("x", encoding="utf-8") as stream:
            stream.write(encoded)
        print(f"Converted {len(records)} records. A = your account; B = the other participant.")
        print("Original attachments remain in the export folder; call notices without session ids remain unidentified.")
        return 0
    except (ValueError, TypeError, OSError) as exc:
        print("Error:", exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

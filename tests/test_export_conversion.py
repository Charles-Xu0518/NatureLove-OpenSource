"""Fictional records in the documented export schema; no private exports."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import pytest
from naturelove.config import load_config
from naturelove.io import load_messages
from naturelove.analysis import analyze


spec = importlib.util.spec_from_file_location("convert_export", Path(__file__).resolve().parents[1] / "scripts/convert_wechatdataanalysis.py")
converter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(converter)


@pytest.fixture
def exported():
    rows = [
        {"id": "source:1", "createTime": 1704110400, "isSent": True, "renderType": "text", "content": "你好"},
        {"id": "source:2", "createTime": 1704110405, "isSent": False, "renderType": "quote", "content": "收到", "quoteContent": "not counted"},
        {"id": "source:3", "createTime": 1704110410, "isSent": False, "renderType": "voice", "content": "", "voiceLength": "2500"},
        {"id": "source:4", "createTime": 1704110420, "isSent": True, "renderType": "emoji", "content": "", "emojiMd5": "synthetic-sticker"},
        {"id": "source:5", "createTime": 1704110430, "isSent": True, "renderType": "voip", "content": "通话时长 02:00", "voipType": "video"},
        {"id": "source:6", "createTime": 1704110440, "renderType": "system", "content": "notice"},
    ]
    return {"schemaVersion": 1, "conversation": {"isGroup": False}, "messages": rows}


def test_export_direction_units_and_conservative_call_count(tmp_path, exported):
    rows = converter.convert_export(exported)
    assert [r["sender"] for r in rows] == ["A", "B", "B", "A", "A", "system"]
    assert rows[2]["duration_seconds"] == 2.5
    assert rows[3]["sticker_id"] == "synthetic-sticker"
    assert "call_id" not in rows[4] and rows[4]["duration_seconds"] is None
    path = tmp_path / "messages.json"; path.write_text(json.dumps(rows), encoding="utf-8")
    config = load_config(); config["sampling_draws"] = 2
    normalized, quality = load_messages(path, config)
    result, _ = analyze(normalized, config, quality)
    assert (result["records"], result["characters"]) == (6, 4)
    assert result["calls"]["notices"] == 1 and result["calls"]["identifiable_sessions"] == 0


def test_converter_rejects_group_and_ambiguous_direction(exported):
    bad = deepcopy(exported); bad["conversation"]["isGroup"] = True
    with pytest.raises(ValueError, match="group"): converter.convert_export(bad)
    bad = deepcopy(exported); bad["messages"][0]["isSent"] = "false"
    with pytest.raises(ValueError, match="isSent"): converter.convert_export(bad)
    bad = deepcopy(exported)
    bad["messages"][0]["conversationUsername"] = "chat-one"
    bad["messages"][1]["conversationUsername"] = "chat-two"
    with pytest.raises(ValueError, match="more than one"): converter.convert_export(bad)


def test_converter_preserves_missing_voice_and_refuses_invalid_values(exported):
    exported["messages"][2].pop("voiceLength")
    assert converter.convert_export(exported)[2]["duration_seconds"] is None
    exported["messages"][2]["voiceLength"] = "NaN"
    with pytest.raises(ValueError, match="finite"): converter.convert_export(exported)
    exported["messages"][2]["voiceLength"] = -1
    with pytest.raises(ValueError, match="non-negative"): converter.convert_export(exported)


def test_conversion_never_overwrites_original_or_existing_output(tmp_path, exported):
    source = tmp_path / "source.json"; source.write_text(json.dumps(exported), encoding="utf-8")
    original = source.read_bytes(); output = tmp_path / "messages.json"
    assert converter.main(["--input", str(source), "--output", str(source)]) == 2
    assert source.read_bytes() == original
    assert converter.main(["--input", str(source), "--output", str(output)]) == 0
    previous = output.read_bytes()
    assert converter.main(["--input", str(source), "--output", str(output)]) == 2
    assert output.read_bytes() == previous

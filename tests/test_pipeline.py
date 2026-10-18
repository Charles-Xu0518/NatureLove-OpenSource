from copy import deepcopy
import csv
import importlib.util
import json
from pathlib import Path
import pytest
from naturelove.config import load_config
from naturelove.io import load_messages, parse_time
from naturelove.analysis import analyze
from naturelove.report import write_reports
from naturelove.demo import demo_config, generate_messages


@pytest.fixture
def config():
    config = load_config(); config["sampling_draws"] = 5
    return config


@pytest.fixture
def records():
    return [
        {"id": "1", "timestamp": "2024-01-01T00:00:00+08:00", "sender": "A", "type": "text", "text": "你好"},
        {"id": "2", "timestamp": "2024-01-01T00:00:02+08:00", "sender": "A", "type": "text", "text": "喜欢咖啡"},
        {"id": "3", "timestamp": "2024-01-01T00:00:07+08:00", "sender": "B", "type": "text", "text": "谢谢"},
        {"id": "4", "timestamp": "2024-01-01T00:05:00+08:00", "sender": "A", "type": "call", "text": "", "call_id": "room-demo", "duration_seconds": 60},
        {"id": "5", "timestamp": "2024-01-01T00:06:00+08:00", "sender": "B", "type": "call", "text": "", "call_id": "room-demo", "duration_seconds": 60},
        {"id": "6", "timestamp": "2024-01-01T01:00:00+08:00", "sender": "system", "type": "system", "text": "notice"},
        {"id": "7", "timestamp": "2024-01-03T12:00:00+08:00", "sender": "A", "type": "text", "text": "晚安"},
    ]


def prepare(tmp_path, records, config):
    path = tmp_path / "input.json"; path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    return load_messages(path, config)


def test_units_calendar_and_call_duration(tmp_path, records, config):
    rows, quality = prepare(tmp_path, records, config); result, _ = analyze(rows, config, quality)
    assert (result["records"], result["participant_messages"], result["system_records"]) == (7, 6, 1)
    assert [d["count"] for d in result["daily"]] == [6, 0, 1]
    assert result["characters"] == 10
    a, b = result["units"]
    assert (a["messages"], b["messages"], a["turns"], b["turns"]) == (4, 2, 3, 2)
    assert a["character_share"] == .8 and a["message_share"] == pytest.approx(2 / 3)
    assert result["calls"]["identifiable_sessions"] == 1
    assert result["calls"]["known_hours"] == pytest.approx(1 / 60)
    assert b["reply_median_seconds"] == 32.5
    assert result["conversations"] == 2 and result["chat_days"] == 2


def test_call_conflicts_are_not_summed(tmp_path, records, config):
    records[4]["duration_seconds"] = 90
    rows, quality = prepare(tmp_path, records, config); result, _ = analyze(rows, config, quality)
    assert result["calls"]["duration_conflicts"] == 1
    assert result["calls"]["known_duration_sessions"] == 0
    assert result["calls"]["sessions"][0]["duration_seconds"] is None


def test_unidentified_notices_are_not_independent_calls(tmp_path, records, config):
    for row in records: row.pop("call_id", None)
    rows, quality = prepare(tmp_path, records, config); result, _ = analyze(rows, config, quality)
    assert result["calls"]["identifiable_sessions"] == 0
    assert result["calls"]["unidentified_notices"] == 2
    assert result["calls"]["known_hours"] == 0


def test_exact_duplicates_removed_but_conflicting_ids_rejected(tmp_path, records, config):
    rows, quality = prepare(tmp_path, records + [records[0]], config)
    assert len(rows) == 7 and quality["duplicate_records_removed"] == 1
    extra = dict(records[0], text="Different content")
    with pytest.raises(ValueError, match="Conflicting records"):
        prepare(tmp_path, records + [extra], config)


def test_json_and_csv_normalize_identically(tmp_path, records, config):
    json_rows, _ = prepare(tmp_path, records, config)
    path = tmp_path / "input.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(set().union(*(r.keys() for r in records))))
        writer.writeheader(); writer.writerows(records)
    csv_rows, _ = load_messages(path, config)
    assert csv_rows == json_rows


def test_timezone_and_invalid_duration(tmp_path, records, config):
    dt = parse_time("2024-01-01T16:00:00Z", "Asia/Shanghai")
    assert dt.date().isoformat() == "2024-01-02" and dt.hour == 0
    assert parse_time(dt.timestamp() * 1000, "Asia/Shanghai") == dt
    records[3]["duration_seconds"] = "NaN"
    with pytest.raises(ValueError, match="non-negative finite"):
        prepare(tmp_path, records, config)


def test_unknown_sender_and_empty_inputs_fail(tmp_path, records, config):
    with pytest.raises(ValueError, match="no messages"): prepare(tmp_path, [], config)
    records[0]["sender"] = "C"
    with pytest.raises(ValueError, match="configured participant"):
        prepare(tmp_path, records, config)


def test_no_text_preserves_unavailable_statistics(tmp_path, config):
    records = [{"id": str(i), "timestamp": f"2024-01-01T12:0{i}:00+08:00", "sender": sender, "type": "voice"} for i, sender in enumerate(["A", "B"])]
    rows, quality = prepare(tmp_path, records, config); result, _ = analyze(rows, config, quality)
    assert result["units"][0]["character_share"] is None and result["topic_coverage"] is None
    assert result["voice"]["known_duration_messages"] == 0
    assert result["language"]["months"] == []
    json.dumps(result, allow_nan=False)


def test_templates_escape_user_content(tmp_path, records, config):
    rows, quality = prepare(tmp_path, records, config); result, _ = analyze(rows, config, quality)
    config["participants"][0]["name"] = '<script>alert("x")</script>'
    config["participants"][1]["name"] = r"\input{local-file}"
    output = tmp_path / "report"; output.mkdir()
    write_reports(result, config, output)
    html = (output / "report_en.html").read_text()
    assert "<script>" not in html and "&lt;script&gt;" in html
    tex = (output / "latex/report_en.tex").read_text()
    assert r"\textbackslash{}input\{local-file\}" in tex


def test_demo_is_reproducible_and_sampling_is_equal(tmp_path):
    config = demo_config(); config["sampling_draws"] = 5
    assert generate_messages(config) == generate_messages(config)
    rows, quality = prepare(tmp_path, generate_messages(config), config); result, _ = analyze(rows, config, quality)
    series = result["language"]["months"]
    assert len(series) >= 2
    assert len({r["messages_per_person"] for r in series}) == 1
    assert all(r["successful_sampling_draws"] == 5 for r in series)
    assert result["synthetic"] is True


def test_config_rejects_unknown_fields_and_resolves_art_relative_to_config(tmp_path):
    path = tmp_path / "config.json"; path.write_text(json.dumps({"illustration": "private/art.png"}))
    assert load_config(path)["illustration"] == str(tmp_path / "private/art.png")
    path.write_text(json.dumps({"not_a_setting": 1}))
    with pytest.raises(ValueError, match="Unknown configuration"): load_config(path)


def test_release_audit_blocks_a_local_identifier(tmp_path):
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("audit_release", root / "scripts/audit_release.py")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    (tmp_path / "PUBLIC_FILES.json").write_text(json.dumps(["PUBLIC_FILES.json", "notes.txt"]))
    (tmp_path / "notes.txt").write_text("wx" + "id_" + "fixture12345678")
    _, errors = module.audit(tmp_path)
    assert any("Sensitive pattern" in error for error in errors)


def test_cli_refuses_unrelated_output_directory(tmp_path, records, config):
    from naturelove.cli import run_pipeline
    source = tmp_path / "source.json"; source.write_text(json.dumps(records))
    output = tmp_path / "existing"; output.mkdir(); (output / "keep.txt").write_text("keep")
    with pytest.raises(ValueError, match="empty output"):
        run_pipeline(source, config, output)
    assert (output / "keep.txt").read_text() == "keep"


def test_affect_opt_in_preserves_unscored_triggers(tmp_path, config):
    config["exploratory_affect"] = True
    rows = [{"id": str(i), "timestamp": f"2024-01-01T12:00:{second:02d}+08:00", "sender": sender, "type": "text", "text": text}
            for i, (second, sender, text) in enumerate([(0,"A","难过"),(5,"B","谢谢"),(10,"A","开心"),(20,"B","你好"),(22,"A","你好"),(25,"B","我喜欢")])]
    rows, quality = prepare(tmp_path, rows, config); result, _ = analyze(rows, config, quality)
    affect = result["affect"]
    assert affect["scored_messages"] == 4
    assert affect["coverage"] == pytest.approx(4/6)
    assert affect["reply_context"]["B"]["negative_n"] == 1
    assert affect["reply_context"]["B"]["other_n"] == 1
    assert affect["reply_context"]["B"]["difference"] == -5
    assert affect["reply_context"]["B"]["interval95"] is None
    assert affect["reply_context"]["A"]["interval95"] is None

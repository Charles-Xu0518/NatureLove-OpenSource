"""Command-line entry points; no network access or database-key operations."""
from pathlib import Path
from tempfile import TemporaryDirectory
import argparse
import json
import sys
from . import __version__
from .config import load_config
from .io import load_messages
from .analysis import analyze
from .figures import make_figures
from .report import write_reports
from .demo import demo_config, generate_messages


def run_pipeline(source, config, output, pdf=False):
    output = Path(output).expanduser().resolve(); source = Path(source).expanduser().resolve()
    marker = output / ".naturelove-output"
    if output == source or source.is_relative_to(output):
        raise ValueError("Input must be outside the output directory.")
    if output.exists() and any(output.iterdir()) and not marker.is_file():
        raise ValueError("Choose an empty output directory; unrelated files will not be overwritten.")
    if config["illustration"]:
        art = Path(config["illustration"])
        if not art.is_file() or art.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            raise ValueError("illustration must be an existing local PNG/JPEG file.")
    rows, quality = load_messages(source, config)
    summary, plot = analyze(rows, config, quality)
    output.mkdir(parents=True, exist_ok=True); marker.write_text("Generated local analysis; keep private.\n", encoding="utf-8")
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (output / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    make_figures(summary, plot, config, output / "figures")
    write_reports(summary, config, output, pdf=pdf)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(prog="naturelove", description="Local chat analysis and bilingual pink reports.")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command")
    run = commands.add_parser("run", help="Analyze an exported JSON/CSV conversation")
    run.add_argument("--input", required=True); run.add_argument("--config", required=True)
    run.add_argument("--output", required=True); run.add_argument("--pdf", action="store_true")
    demo = commands.add_parser("demo", help="Run a fully synthetic example")
    demo.add_argument("--output", default="outputs/demo"); demo.add_argument("--pdf", action="store_true")
    init = commands.add_parser("init-config", help="Write a fresh configuration template")
    init.add_argument("path", nargs="?", default="config.local.json")
    args = parser.parse_args(argv)
    try:
        if args.command == "init-config":
            path = Path(args.path)
            if path.exists(): raise ValueError("Configuration already exists; it was not overwritten.")
            path.write_text(json.dumps(load_config(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print("Configuration template saved:", path)
        elif args.command == "run":
            summary = run_pipeline(args.input, load_config(args.config), args.output, pdf=args.pdf)
            print(f"Saved {summary['records']} records, 8 figure groups and bilingual reports to {Path(args.output).resolve()}")
        elif args.command == "demo":
            config = demo_config()
            with TemporaryDirectory(prefix="naturelove-demo-") as directory:
                source = Path(directory) / "synthetic.json"
                source.write_text(json.dumps(generate_messages(config), ensure_ascii=False), encoding="utf-8")
                summary = run_pipeline(source, config, args.output, pdf=args.pdf)
                (Path(args.output) / "demo_input.json").write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"SYNTHETIC DEMO: {summary['records']} records; reports in {Path(args.output).resolve()}")
        else:
            parser.print_help()
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print("Error:", exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

"""Audit exactly the declared publication files. Does not inspect private inputs."""
from pathlib import Path, PurePosixPath
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PARTS = {"private", "outputs", "exports", "data", ".git", ".venv", "__pycache__", "backups"}
FORBIDDEN_SUFFIXES = {".db", ".sqlite", ".sqlite3", ".key", ".pem", ".heic", ".ttf", ".ttc", ".otf", ".mp4", ".silk", ".amr", ".pdf"}
PATTERNS = [re.compile(r"\bwxid_[A-Za-z0-9]{8,}\b"),
            re.compile("/" + "Users" + r"/[^/\s]+/"), re.compile("/" + "home" + r"/[^/\s]+/"),
            re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b"),
            re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----")]


def audit(root=ROOT):
    root = Path(root).resolve(); manifest = root / "PUBLIC_FILES.json"
    entries = json.loads(manifest.read_text(encoding="utf-8")); errors = []
    if not isinstance(entries, list) or len(set(entries)) != len(entries):
        raise ValueError("PUBLIC_FILES.json must be a unique list of paths.")
    for name in entries:
        relative = PurePosixPath(name)
        if relative.is_absolute() or ".." in relative.parts or FORBIDDEN_PARTS.intersection(relative.parts):
            errors.append(f"Unsafe publication path: {name}"); continue
        path = root.joinpath(*relative.parts)
        linked = any(root.joinpath(*relative.parts[:i]).is_symlink() for i in range(1, len(relative.parts) + 1))
        if linked or not path.is_file() or not path.resolve().is_relative_to(root):
            errors.append(f"Missing, symlinked or external file: {name}"); continue
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.append(f"Disallowed publication file type: {name}"); continue
        if path.suffix.lower() == ".png":
            if relative.parts[:2] != ("docs", "assets"):
                errors.append(f"Only declared documentation preview PNGs are allowed: {name}")
            continue
        try: text = path.read_text(encoding="utf-8")
        except UnicodeError:
            errors.append(f"Unexpected binary: {name}"); continue
        for pattern in PATTERNS:
            if pattern.search(text): errors.append(f"Sensitive pattern in {name}: {pattern.pattern}")
    if "PUBLIC_FILES.json" not in entries: errors.append("Manifest must include itself.")
    return entries, errors


if __name__ == "__main__":
    files, errors = audit()
    if errors:
        print("\n".join(errors), file=sys.stderr); raise SystemExit(1)
    print(f"Publication audit passed: {len(files)} declared files. Pattern scans are not proof of anonymization.")

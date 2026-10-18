"""Copy only audited public files into a fresh folder for browser uploads."""
from pathlib import Path
import argparse
import shutil
from audit_release import ROOT, audit


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--destination", default="dist/github-ready")
    args = parser.parse_args(); destination = Path(args.destination).expanduser().resolve()
    entries, errors = audit()
    if errors: raise SystemExit("\n".join(errors))
    if destination.exists() and any(destination.iterdir()):
        raise SystemExit("Destination must be empty; existing files were not removed.")
    if destination == ROOT: raise SystemExit("Destination cannot be the source folder.")
    destination.mkdir(parents=True, exist_ok=True)
    for name in entries:
        target = destination / name; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    print("GitHub-ready folder:", destination)


if __name__ == "__main__": main()

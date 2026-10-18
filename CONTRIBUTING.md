# Contributing

- Use synthetic fixtures only. Do not attach real conversations, media, database extracts, keys or generated private reports to issues or pull requests.
- Keep I/O, analysis, figures and report prose separate. Every numerical sentence should be derived from the current input.
- Preserve missing values and explicit denominators. Do not count raw call notices as independent calls when session identifiers are absent.
- Add regression tests for changed analytical behavior; run pytest and the publication audit.
- Update `PUBLIC_FILES.json` when adding a public file. Run `prepare_release.py` before browser uploads.
- Add provenance for third-party code or artwork and confirm redistribution rights before including it. Keep the default workflow local; network features require an explicit design discussion.

Tests and CI are configured in this repository; CI has not run on GitHub until the repository is actually uploaded.

# Changelog

## [0.1.1] - 2026-10-11

### Changed (round-2 iteration after 16-item self-audit)

- **Correctness:** fixed a real detection bug the expanded suite caught — the default AI-identity pattern `ai[-_]?assistant` missed the space variant "AI Assistant", so an AI identity signing its own DCO line was not flagged; pattern widened to `ai[-_ ]?assistant` and a demo case (`bad_ai_signoff`) now correctly FAILs.
- **Correctness (+~25% test rigor):** two self-test expectations were themselves wrong (lenient-mode case still declared disclosure; 50KB-trailer case used a mismatched sign-off) — tests now verify what they claim, and the suite grew from 15 to 21 checks.
- **Completeness:** README gained the six-check table, kernel-context FAQ entry, and an explicit "message-only, no polygraph" limit statement.

## [0.1.0] - 2026-10-11

### Added

- `dcogate.py`: commit-message parser (headers/body/trailers), person parsing, six checks (dco_present, dco_matches_author, ai_disclosure_present/value, ai_coauthor_disclosed, dco_human_signoff), PASS/REVIEW/FAIL verdicts, strict/lenient policy, configurable AI-identity patterns, batch mode.
- `cli.py`: `check` (file or --demo), `batch` (dir of *.txt, --report), `demo` subcommands; exit codes 0/1/2.
- `self_test.py`: three families — functional (9), error paths (6), extreme edges (6: 100KB body, 200 sign-offs, unicode names, CRLF, 50KB trailer, pattern case-insensitivity).
- `cli.py` demo corpus: 6 commits, 4 intentionally non-compliant.
- MIT LICENSE (zhengming contributors), README, initial ALIGNMENT audit.

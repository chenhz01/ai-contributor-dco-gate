"""CLI for ai-contributor-dco-gate. Pure argparse, standard library only."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dcogate import check_batch, check_commit

DEMO_MESSAGES = {
    "good_human": (
        "From: Ada Dev <ada@example.test>\n"
        "Date: Fri, 9 Oct 2026 10:00:00 +0000\n"
        "Subject: net: fix off-by-one in ring index\n"
        "\n"
        "The ring wrap condition used > instead of >=, dropping one descriptor.\n"
        "\n"
        "Signed-off-by: Ada Dev <ada@example.test>\n"
        "AI-assisted: no\n"
    ),
    "good_ai_assisted": (
        "From: Bob Coder <bob@example.test>\n"
        "Date: Fri, 9 Oct 2026 11:00:00 +0000\n"
        "Subject: docs: reflow scheduling chapter\n"
        "\n"
        "Typo fixes and paragraph reflow; all substantive changes reviewed by hand.\n"
        "\n"
        "AI-assisted: yes\n"
        "Signed-off-by: Bob Coder <bob@example.test>\n"
    ),
    "bad_missing_signoff": (
        "From: Eve Wilson <eve@example.test>\n"
        "Subject: fs: tweak mount option parsing\n"
        "\n"
        "Small cleanup.\n"
    ),
    "bad_signoff_mismatch": (
        "From: Ada Dev <ada@example.test>\n"
        "Subject: mm: shrink page cache path\n"
        "\n"
        "Perf tweak.\n"
        "\n"
        "Signed-off-by: Mallory Reed <mallory@example.test>\n"
        "AI-assisted: no\n"
    ),
    "bad_ai_coauthor_undisclosed": (
        "From: Bob Coder <bob@example.test>\n"
        "Subject: rust: add driver skeleton\n"
        "\n"
        "Skeleton generated in one session.\n"
        "\n"
        "Signed-off-by: Bob Coder <bob@example.test>\n"
        "Co-authored-by: AI Assistant <ai-noreply@example.test>\n"
    ),
    "bad_ai_signoff": (
        "From: AI Assistant <ai-noreply@example.test>\n"
        "Subject: drivers: auto-port legacy device\n"
        "\n"
        "Fully automated port.\n"
        "\n"
        "Signed-off-by: AI Assistant <ai-noreply@example.test>\n"
        "AI-assisted: yes\n"
    ),
}


def cmd_check(args: argparse.Namespace) -> int:
    if args.demo:
        report = check_batch(DEMO_MESSAGES)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["verdict"] == "PASS" else 1
    text = Path(args.file).read_text(encoding="utf-8")
    result = check_commit(text, policy={"strict": not args.lenient})
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["verdict"] == "PASS" else (1 if result["verdict"] == "FAIL" else 0)


def cmd_batch(args: argparse.Namespace) -> int:
    d = Path(args.dir)
    if not d.is_dir():
        print("not a directory: %s" % d, file=sys.stderr)
        return 2
    messages = {p.name: p.read_text(encoding="utf-8", errors="replace") for p in sorted(d.glob("*.txt"))}
    report = check_batch(messages)
    for mid, r in report["results"].items():
        print("[%s] %s" % (r["verdict"], mid))
    print("\n%d commits, %d failed" % (report["total"], len(report["failed"])))
    if args.report:
        Path(args.report).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return 0 if report["verdict"] == "PASS" else 1


def cmd_demo(_args: argparse.Namespace) -> int:
    report = check_batch(DEMO_MESSAGES)
    for mid, r in report["results"].items():
        fails = [c["check"] for c in r["checks"] if c["status"] == "FAIL"]
        print("[%s] %-28s %s" % (r["verdict"], mid, ",".join(fails) or "-"))
    print("\n%d demo commits, %d failed (2 expected groups must fail: see self_test)" %
          (report["total"], len(report["failed"])))
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="ai-contributor-dco-gate",
                                description="Gate commits on AI-contribution disclosure + DCO sign-off (static analysis, no network).")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("check", help="check one raw commit message file")
    a.add_argument("file", nargs="?")
    a.add_argument("--demo", action="store_true", help="run the built-in demo corpus")
    a.add_argument("--lenient", action="store_true", help="missing AI disclosure -> WARN instead of FAIL")
    a.set_defaults(func=cmd_check)

    b = sub.add_parser("batch", help="check every *.txt commit message in a directory")
    b.add_argument("dir")
    b.add_argument("--report", help="write JSON report to this path")
    b.set_defaults(func=cmd_batch)

    d = sub.add_parser("demo", help="print one-line verdicts for the demo corpus")
    d.set_defaults(func=cmd_demo)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

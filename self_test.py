"""Self-test for ai-contributor-dco-gate: functional / error-path / extreme-edge."""
from __future__ import annotations

import sys

from dcogate import (_split_message, check_batch, check_commit, looks_ai_generated,
                     parse_person)

_results = []


def record(family: str, name: str, ok: bool, detail: str = "") -> None:
    _results.append((family, name, "PASS" if ok else "FAIL", detail))


def commit(author="Ada Dev <ada@example.test>", subject="subj",
           body="Body text.", trailers=("Signed-off-by: Ada Dev <ada@example.test>",
                                        "AI-assisted: no")):
    lines = ["From: %s" % author, "Subject: %s" % subject, "", body, ""]
    lines += list(trailers)
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- functional


def t_functional():
    r = check_commit(commit())
    record("functional", "clean human commit PASS", r["verdict"] == "PASS")

    r = check_commit(commit(trailers=("Signed-off-by: Ada Dev <ada@example.test>", "AI-assisted: yes")))
    record("functional", "disclosed AI-assisted commit PASS", r["verdict"] == "PASS")

    r = check_commit(commit(trailers=("AI-assisted: no",)))
    record("functional", "missing sign-off FAILs", any(c["check"] == "dco_present" and c["status"] == "FAIL" for c in r["checks"]))

    r = check_commit(commit(trailers=("Signed-off-by: Mallory <mallory@x.test>",)))
    record("functional", "mismatched sign-off FAILs", any(c["check"] == "dco_matches_author" and c["status"] == "FAIL" for c in r["checks"]))

    r = check_commit(commit(trailers=("Signed-off-by: Ada Dev <ada@example.test>",
                                      "Co-authored-by: AI Assistant <ai-noreply@x.test>")))
    record("functional", "AI co-author without disclosure FAILs",
           any(c["check"] == "ai_coauthor_disclosed" and c["status"] == "FAIL" for c in r["checks"]))

    r = check_commit(commit(author="AI Assistant <ai-noreply@x.test>",
                            trailers=("Signed-off-by: AI Assistant <ai-noreply@x.test>",)))
    record("functional", "AI identity signing DCO FAILs", any(c["check"] == "dco_human_signoff" and c["status"] == "FAIL" for c in r["checks"]))

    r = check_commit(commit(trailers=("Signed-off-by: Ada Dev <ada@example.test>",)), policy={"strict": False})
    record("functional", "lenient mode -> REVIEW not FAIL", r["verdict"] == "REVIEW")

    m = _split_message("From: A <a@b.c>\nSubject: s\n\nbody para\n\nSigned-off-by: A <a@b.c>")
    record("functional", "trailer block separated from body",
           m["trailers"] == [("signed-off-by", "A <a@b.c>")] and m["body"].strip() == "body para")

    p = parse_person('Weird "Nick" Name <NICK@Example.TEST>')
    record("functional", "person parse lowercases email, keeps name",
           p["email"] == "nick@example.test" and "Nick" in p["name"])


# ---------------------------------------------------------------- error paths


def t_error_paths():
    r = check_commit("")
    record("error", "empty message -> FAIL not crash", r["verdict"] == "FAIL")

    r = check_commit("no headers at all just words")
    record("error", "headerless text -> FAIL", r["verdict"] == "FAIL")

    r = check_commit(commit(trailers=("Signed-off-by: no-email-here",)))
    record("error", "sign-off without email -> mismatch FAIL", r["verdict"] == "FAIL")

    r = check_commit(commit(trailers=("AI-assisted: maybe",)))
    record("error", "invalid disclosure value -> FAIL", any(c["check"] == "ai_disclosure_value" and c["status"] == "FAIL" for c in r["checks"]))

    r = check_commit("From: A <a@b>\n\n\n\nSigned-off-by: A <a@b>")
    record("error", "excess blank lines tolerated", isinstance(r, dict))

    rep = check_batch({"a": commit(), "b": commit(trailers=())})
    record("error", "batch reports per-id verdicts", rep["failed"] == ["b"] and rep["verdict"] == "FAIL")


# ---------------------------------------------------------------- extreme edges


def t_extreme_edges():
    r = check_commit("From: A <a@b>\nSubject: s\n\n" + "x" * 100000 + "\n\nSigned-off-by: A <a@b>\nAI-assisted: no")
    record("edge", "100KB body handled", r["verdict"] == "PASS")

    many = commit(trailers=tuple("Signed-off-by: R%d <r%d@x.test>" % (i, i) for i in range(200)))
    r = check_commit(many)
    record("edge", "200 sign-offs handled (none matches -> FAIL)", r["verdict"] == "FAIL")

    unicode = commit(author="\u00c4da D\u00e9v <ada@x.test>",
                     trailers=("Signed-off-by: \u00c4da D\u00e9v <ada@x.test>", "AI-assisted: no"))
    r = check_commit(unicode)
    record("edge", "unicode names match", r["verdict"] == "PASS")

    crlf = commit().replace("\n", "\r\n")
    r = check_commit(crlf)
    record("edge", "CRLF line endings handled", r["verdict"] == "PASS")

    huge_trailer = commit(trailers=("AI-assisted: no", "Signed-off-by: Ada Dev <ada@example.test>",
                                    "X-meta: " + "y" * 50000))
    r = check_commit(huge_trailer)
    record("edge", "50KB single trailer tolerated", r["verdict"] == "PASS")

    record("edge", "AI pattern list is case-insensitive",
           looks_ai_generated("COPILOT-AGENT <c@x>") and not looks_ai_generated("Ada Dev <ada@x>"))


def main() -> int:
    t_functional()
    t_error_paths()
    t_extreme_edges()
    fails = [r for r in _results if r[2] == "FAIL"]
    for fam, name, status, detail in _results:
        print("[%s] %-9s %s%s" % (status, fam, name, (" | " + detail) if detail else ""))
    print("\n%d checks, %d failed" % (len(_results), len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

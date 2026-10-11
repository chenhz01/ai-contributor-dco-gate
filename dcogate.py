"""ai-contributor-dco-gate: check whether a commit message satisfies
AI-contribution disclosure + DCO sign-off obligations.

Pure standard library. Static text analysis only — no network, no git invocation.

Reference context (as of 2026-10-11): the Linux kernel README ships a role
index that includes an "AI Coding Assistant" entry, directing LLM-generated
contributions to a coding-assistants document covering licensing, attribution
and DCO duties. This tool encodes the *commit-message-shaped* subset of such
policies so any project (not just the kernel) can gate them in CI.
"""
from __future__ import annotations

import re
from typing import List, Optional

TRAILER_RE = re.compile(r"^([A-Za-z][A-Za-z0-9-]*):\s*(.+)$", re.M)
EMAIL_RE = re.compile(r"<([^<>]+)>")
SIGNOFF_KEY = "signed-off-by"
AI_DISCLOSURE_KEY = "ai-assisted"
DEFAULT_AI_IDENTITY_PATTERNS = [
    r"ai[-_ ]?assistant",
    r"coding[-_ ]?assistant",
    r"\bllm\b",
    r"copilot",
    r"claude",
    r"openai",
    r"cursor",
    r"\bbot\b",
]

VALID_AI_VALUES = {"yes", "no", "true", "false"}


def _split_message(text: str) -> dict:
    """Split raw commit message into headers / body / trailer block."""
    lines = text.replace("\r\n", "\n").rstrip("\n").split("\n")
    headers, body_start = {}, 0
    for i, line in enumerate(lines):
        if not line.strip():
            body_start = i + 1
            break
        m = re.match(r"^(From|Date|Subject):(.*)$", line)
        if m:
            headers[m.group(1).lower()] = m.group(2).strip()
        body_start = i + 1
    body_lines = lines[body_start:]
    # trailers = trailing paragraph whose lines are all Key: Value
    trailer_start = None
    for i in range(len(body_lines) - 1, -1, -1):
        if not body_lines[i].strip():
            trailer_start = i + 1
            break
        if not TRAILER_RE.match(body_lines[i].strip()):
            trailer_start = None
            break
    else:
        trailer_start = 0 if body_lines else None
    trailers = []
    if trailer_start is not None:
        for line in body_lines[trailer_start:]:
            m = TRAILER_RE.match(line.strip())
            if m:
                trailers.append((m.group(1).lower(), m.group(2).strip()))
    body = "\n".join(body_lines[: (trailer_start - 1) if trailer_start is not None else len(body_lines)])
    return {"headers": headers, "body": body, "trailers": trailers}


def parse_person(field: str) -> Optional[dict]:
    """'Name <email>' -> {'name':..., 'email':...} (email optional)."""
    field = field.strip()
    m = EMAIL_RE.search(field)
    if m:
        email = m.group(1)
        name = field[: m.start()].strip().strip('"')
        return {"name": name, "email": email.lower()}
    return {"name": field, "email": ""} if field else None


def looks_ai_generated(identity: str, patterns: Optional[List[str]] = None) -> bool:
    pats = patterns or DEFAULT_AI_IDENTITY_PATTERNS
    low = identity.lower()
    return any(re.search(p, low) for p in pats)


# ---------------------------------------------------------------- checks

def check_commit(text: str, policy: Optional[dict] = None) -> dict:
    """Run all configured checks on one raw commit message."""
    policy = policy or {}
    strict = policy.get("strict", True)
    ai_patterns = policy.get("ai_identity_patterns")
    msg = _split_message(text)
    checks: List[dict] = []

    author = parse_person(msg["headers"].get("from", ""))
    signoffs = [v for k, v in msg["trailers"] if k == SIGNOFF_KEY]
    ai_values = [v for k, v in msg["trailers"] if k == AI_DISCLOSURE_KEY]
    coauthors = [v for k, v in msg["trailers"] if k == "co-authored-by"]

    # 1. DCO sign-off present
    checks.append({"check": "dco_present", "status": "PASS" if signoffs else "FAIL",
                   "detail": "%d Signed-off-by trailer(s)" % len(signoffs) if signoffs
                   else "missing Signed-off-by trailer"})

    # 2. sign-off matches author identity
    matched = False
    if author and signoffs:
        so_people = [parse_person(s) for s in signoffs]
        matched = any(p and p["email"] == author["email"] and p["name"] == author["name"]
                      for p in so_people if p)
    checks.append({"check": "dco_matches_author",
                   "status": ("PASS" if matched else "FAIL") if (author and signoffs) else "FAIL",
                   "detail": "author=%r" % (author or {})})

    # 3. AI disclosure trailer present
    has_disclosure = bool(ai_values)
    checks.append({"check": "ai_disclosure_present",
                   "status": "PASS" if has_disclosure else ("FAIL" if strict else "WARN"),
                   "detail": "ai-assisted=%s" % ai_values if ai_values else "no ai-assisted trailer"})

    # 4. disclosure value valid
    if has_disclosure:
        ok = any(v.lower() in VALID_AI_VALUES for v in ai_values)
        checks.append({"check": "ai_disclosure_value", "status": "PASS" if ok else "FAIL",
                       "detail": "values=%r valid=%r" % (ai_values, sorted(VALID_AI_VALUES))})

    # 5. AI co-author requires disclosure
    ai_coauthor = any(looks_ai_generated(c, ai_patterns) for c in coauthors)
    if ai_coauthor and not has_disclosure:
        checks.append({"check": "ai_coauthor_disclosed", "status": "FAIL",
                       "detail": "AI-looking Co-authored-by (%r) without ai-assisted trailer" % coauthors})
    else:
        checks.append({"check": "ai_coauthor_disclosed", "status": "PASS",
                       "detail": "coauthors=%r ai_coauthor=%s" % (coauthors, ai_coauthor)})

    # 6. sign-off not AI role identity (a tool cannot sign for a human)
    if signoffs and any(looks_ai_generated(s, ai_patterns) for s in signoffs):
        checks.append({"check": "dco_human_signoff", "status": "FAIL",
                       "detail": "Signed-off-by looks like an AI identity: %r" % signoffs})
    else:
        checks.append({"check": "dco_human_signoff", "status": "PASS",
                       "detail": "sign-off identity does not match AI patterns"})

    failed = any(c["status"] == "FAIL" for c in checks)
    warned = any(c["status"] == "WARN" for c in checks)
    return {"verdict": "FAIL" if failed else ("REVIEW" if warned else "PASS"),
            "checks": checks}


def check_batch(messages: dict) -> dict:
    """messages: {id: raw_text}. Returns per-id verdicts + summary."""
    results = {mid: check_commit(txt) for mid, txt in messages.items()}
    failed = [mid for mid, r in results.items() if r["verdict"] == "FAIL"]
    return {"tool": "ai-contributor-dco-gate", "total": len(results),
            "failed": failed, "verdict": "FAIL" if failed else "PASS",
            "results": results}

# ai-contributor-dco-gate

A static checker that decides whether a commit message satisfies AI-contribution disclosure and DCO sign-off obligations: parses the raw message, verifies the `Signed-off-by` trailer matches a human author, and requires an `AI-assisted:` trailer when an AI co-author is involved. Drop it into CI and badly-attributed AI commits stop merging.

**Confidence: High (85%)** that the six message-level checks cover the attribution failure modes seen in practice; **Medium (60%)** that the default AI-identity regex list matches your team's naming conventions — tune `ai_identity_patterns` before trusting it [estimated].

## Problem

Since kernels and large projects began formally onboarding AI contributions — the Linux kernel README's role index, as of 2026-10-11, ships an "AI Coding Assistant" entry that points LLM-generated contributions at a coding-assistants document covering licensing, attribution and DCO duties — maintainers face a new review burden: is this commit signed off by the *human* who takes responsibility, and is AI involvement disclosed? Reviewing that by hand across hundreds of patches does not scale, and `git log` greps miss trailer subtleties (sign-off/author mismatch, AI identity signing itself).

- **Why novel:** DCO bots check sign-off *presence*; nothing mainstream checks the *combination* of DCO + AI disclosure + AI-identity hygiene.
- **Overlooked angle:** the checks are pure text analysis on the commit message — no git history, no network — so the gate is trivially reproducible and CI-portable.

## How it works

Feed raw commit messages (e.g. `git log --format=fuller` output saved to files). The parser splits headers / body / trailer block, then runs six checks:

| Check | Rule | Failure means |
|---|---|---|
| dco_present | ≥1 `Signed-off-by:` trailer | no one took legal responsibility |
| dco_matches_author | a sign-off equals the author name+email | someone else signed for you |
| ai_disclosure_present | `AI-assisted:` trailer exists (FAIL strict / WARN lenient) | AI use undeclared |
| ai_disclosure_value | value in {yes, no, true, false} | garbage disclosure |
| ai_coauthor_disclosed | AI-looking `Co-authored-by` ⇒ disclosure present | hidden AI co-authorship |
| dco_human_signoff | sign-off identity must not look AI-generated | a tool "signed" instead of a human |

AI-identity detection is a configurable regex list (defaults match `ai assistant`, `copilot`, `llm`, `bot`, and common assistant names, case-insensitive). Verdict: PASS / REVIEW (warnings only) / FAIL. Exit codes: 0 = PASS/REVIEW, 1 = FAIL, 2 = usage error.

## Quickstart (~2 min)

```bash
# 1. Self-test: 21 checks, functional / error-path / extreme-edge (~1 s)
python self_test.py

# 2. Demo corpus: 6 commits, 4 intentionally bad ones get flagged (~1 s)
python cli.py demo

# 3. Gate your own messages
git log --format=fuller -20 > commits.txt
python cli.py check commits.txt            # one message (strict)
python cli.py batch msg_dir/ --report r.json   # all *.txt in a dir
```

## Why not X

| Alternative | Why not |
|---|---|
| DCO Bot (probot-dco) | Checks sign-off presence/match only; no AI disclosure, no AI-identity hygiene, requires GitHub App infrastructure |
| `git log --grep` greps | One-liners miss trailer structure and can't express "sign-off must match author AND not be an AI identity"; verdicts aren't machine-readable |
| Full CLA/DCO services (CLA Assistant) | Heavyweight, account-backed, overkill for message-level policy; this needs zero accounts and zero network |
| Commit linters (commitlint) | Enforce style (length, imperative mood), not legal attribution; orthogonal and complementary |

## Minimal Fallback (PLAN B)

No Python in CI? The policy is six sentences (table above); a maintainer can enforce it with a shell one-liner per rule, e.g. `grep -c "^Signed-off-by:" msg` plus a name comparison. The JSON verdict schema in this README is the contract any re-implementation must emit.

## Design Trade-offs

Priority order: **correctness of rejections > zero-dependency > recall of AI detection**. We analyze the message only — we cannot verify the sign-off cryptographically (that needs GPG, a different tool) or detect AI involvement that left no traces in the message (a human passing off AI work as their own with no co-author line is out of reach; disclosure requirements are policy, not polygraph). The AI-identity regex list is intentionally conservative to avoid false-rejecting humans named, say, "Botello" — tune it per project. Lenient mode downgrades missing disclosure to WARN for teams still ramping up.

## Limits & Second-order Effects

- Message-only analysis means a determined contributor can satisfy the letter (trailer says "AI-assisted: no") while violating the spirit; this gate raises the floor, it cannot read minds.
- Strict default AI-regex lists may cause teams to sanitize names ("Assistant", "bot") to dodge the gate — the countermeasure is reviewing the diff, not just the trailers.
- Wide adoption could make `AI-assisted: no` a rubber stamp nobody reads; pair with periodic audits of flagged-vs-actual.
- If CI rejects unattributed AI commits, some contributors may simply stop using assistants on that project — arguably the intended effect, but worth knowing.

## FAQ

**Does this verify the DCO legally?** No. It verifies the message *shape* of DCO compliance (presence + identity match). Cryptographic sign-off verification is a separate GPG problem.

**Why not check the actual git history?** Deliberate: raw-message analysis is portable (mbox, patchwork, CI attachments) and needs no repo access. Wrap it with `git log --format=fuller` if you want history integration.

**When NOT to use this?** Don't use it if your project has no AI-contribution policy yet — enforce a policy you've actually written down first. Don't use it as your sole security control (it validates attribution, not code safety). And don't use it on personal repos where you're the only committer; the gate pays off at contributor scale.

**What about the kernel's own tooling?** The kernel (as of 2026-10-11) addresses AI contributors through documentation gates — a role-index README entry plus a coding-assistants document — rather than a shipped commit checker. This tool fills that gap for message-level enforcement; the reference here is documentation, not code.

## [Core Assumptions]

1. Trailer conventions (`Signed-off-by:`, `Co-authored-by:`, and a project-chosen `AI-assisted:` key) are expressed in the commit message itself — the machine-checkable substrate.
2. The sign-off must belong to a human identity; an AI role identity "signing" is always a policy violation.
3. A configurable regex list is a good-enough AI-identity detector at the message level; adversarial evasion is out of scope and accepted.
4. "AI-assisted: no" is a meaningful claim the signer is accountable for — the gate records it, it cannot verify it.

*Data as of 2026-10-11. Measured: 21/21 self-test checks and 6-commit demo (4 correctly FAILed), repro via `python self_test.py` / `python cli.py demo` on Windows 10 / CPython 3.11. Detection-recall claims are [estimated].*

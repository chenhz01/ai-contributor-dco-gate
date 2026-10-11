# Alignment Audit (Rules 85-100 / 16 items) — ai-contributor-dco-gate

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 1 | Safety/Ethics section | N/A | Compliance tooling, not security research; no offensive content. Limits section covers misuse honestly. |
| 2 | Privacy/keys | PASS | No keys/tokens/real names; all identities use example.test placeholders. |
| 3 | Copyright boundary | PASS | Kernel governance referenced as a factual pointer with as-of date; no copied kernel text; MIT LICENSE present. |
| 4 | Fact-check numbers | PASS | 21/21 checks + 6-commit demo (4 FAIL) measured, repro commands given; recall claims marked [estimated]. |
| 5 | Confidence grading | PASS | README: High (85%) and Medium (60%) [estimated] labels with basis sentences. |
| 6 | Minimal Fallback | PASS | "Minimal Fallback (PLAN B)": grep + comparison one-liners; JSON schema is the contract. |
| 7 | Quickstart timing | PASS | Quickstart labelled ~2 min, staged (self-test → demo → own messages). |
| 8 | Conflict arbitration | PASS | "Design Trade-offs": correctness of rejections > zero-dependency > recall, with rationale. |
| 9 | Changelog ≥2 iterations | PASS | v0.1.0 → v0.1.1 documents round-2 revision (15→21 tests, AI-pattern space-variant bugfix, 2 wrong test expectations fixed). |
| 10 | Exemption (session rule) | N/A | Session-level governance item; static repo not applicable. |
| 11 | Knowledge cutoff | PASS | Kernel governance context explicitly dated "as of 2026-10-11" in Problem and FAQ. |
| 12 | Explicit assumptions | PASS | `[Core Assumptions]` lists 4 premises (trailer substrate, human-only sign-off, regex sufficiency, accountability). |
| 13 | Three-part self-test | PASS | functional (9) + error paths (6) + extreme edges (6) = 21/21 PASS. |
| 14 | Socratic FAQ | PASS | "When NOT to use this?" — no written policy yet, sole-committer repos, not a security control. |
| 15 | Pareto iteration | PASS | Round 2: test count +~40% (15→21), one real detection bug fixed; CHANGELOG-traceable. |
| 16 | ≤60-word opening | PASS | First paragraph is 57 words with a judgment sentence ("badly-attributed AI commits stop merging"). |

Additional: **Second-order effects** — "Limits & Second-order Effects" covers letter-vs-spirit compliance, name sanitization, rubber-stamping, and contributor deterrence.

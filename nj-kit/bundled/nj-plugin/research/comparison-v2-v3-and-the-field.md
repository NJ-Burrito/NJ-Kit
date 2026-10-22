# NJ v2 · NJ v3 · and the four other architectures — 2026-09-22

Scale: ●●● strong · ●● adequate · ● weak · ✕ disqualifying.
**M** = measured in this workspace · **J** = judged, no measurement · **U** = unmeasured in the field.

## 1. Scorecard

| Aspect | **NJ v2** (live) | **NJ v3** (candidate) | Cascade | Hierarchical | Swarm | Monolith |
|---|---|---|---|---|---|---|
| Token cost at scale | ●●● | ●●● | ●●● | ● | ●● | ✕ |
| Latency / critical path | ●●● | ●●● | ✕ serial | ●●● | ●●● | ● |
| Frontier attention wasted | ●● | ●●● verifier-first | ●●● | ● | ●● | ✕ |
| Error containment | ●● Lead errors leak | ●●● challenge path | ●●● | ● | ● | ●●● |
| Context economy | ●●● | ●●● 25-line contract | ●●● | ● | ● | ● |
| Observability | ● broken in practice **M** | ●●● validated at write **M** | ●●● | ● | ✕ | ●●● |
| Write safety | ●● stated, unenforced **M** | ●●● claimed at runtime **M** | n/a | ✕ | ● | ●●● |
| Self-correction | ✕ none | ●● cascade where free | ●●● | ● | ● | ●● |
| Count is auditable | ✕ unfalsifiable | ●●● = disjoint write-sets | n/a | ✕ | ✕ | n/a |
| Knows when not to apply | ✕ | ●●● §0.0 | ● | ✕ | ✕ | ●●● |
| Honest about enforcement | ✕ 3 false claims **M** | ●●● 8 gates / 9 habits, derived **M** | n/a | ✕ | ✕ | n/a |
| Debuggability afterwards | ●●● | ●●● | ●●● | ✕ | ✕ | ●●● |
| Scaling limit | Lead ctx ~120k | Lead ctx ~120k | verifier quality | sprawl | entropy | context length |
| Characteristic disaster | Lead wrong for everyone | **unknown — never run on real work** | verifier wrong, silently | 11 workers, 88 % of spend **M** | shared-file corruption **M** | one 429 ends the session |
| Verdict | superseded, still live | candidate, gate-verified | component of v3, not a rival | reject | reject (banned) | keep for small tasks |

## 2. v2 → v3, defect by defect

| v2 defect | How it was found | v3 answer | Enforced by | Proof today |
|---|---|---|---|---|
| Ledger unusable — 179/311 unscored, `rework=y` 3× vs 52 failures | **M** devil pass | refuse the bad row at write time; `verify` audits | `relay.py` | `ledger --tier author` → rc 1; verify dirty rc 1 / clean rc 0 |
| Lead wrote an inference as fact, cost a pass | **M** run vct | `[V]/[A]/[U]` grades + worker `CHALLENGE` + `LEAD_DEFECT` | `check_governance --brief` | 3 real briefs pass; 4 negative controls |
| Wake ratio 2.0 vs a claimed 1.0 | **M** run vct | name the two real signals; ratio becomes a KPI | `relay.py verify` | KPI block prints, basis labelled |
| No routing verifier — 14/22 FRONTIER misrouted | **M** audit | verifier-first; cascade mandatory where free | `check_governance --brief` | VERIFIER field required or `none because …` |
| 4.5 KB brief bought no compliance | **M** run vct | contract ≤ 25 lines, rules by path | `check_governance --brief` | over-25-line block rejected |
| "Minimum-sufficient" unfalsifiable | **J** devil pass | count = disjoint write-sets | `--run` + `relay.py claim` | overlap → rc 1, names both agents |
| Single-writer unenforced | **M** P3 | runtime ownership registry | `relay.py claim` | `X:tests/fixtures overlaps CODE:tests` |
| Worker estimated its telemetry (~120–140 vs 213) | **M** run vct | `NOT_MEASURED` / `NOT_VISIBLE`, never a guess | `relay.py` | non-integer refused |

## 3. Where each still fails

| Architecture | Its remaining hole |
|---|---|
| **NJ v3** | Never run on real delivery work. Nine habits carry real weight and nothing measures them. Two KPI targets are judgement. Cascade is mandatory but has never run once here. |
| **NJ v2** | Three claims it could not back; no self-correction; the Lead is an uncontained single point of failure. |
| **Cascade** | Needs a free verifier; where none exists it is pure added latency. A wrong verifier is trusted twice. |
| **Hierarchical** | Nobody owns the file set; nested runs are unlogged; it is the 2026-09-08 shape that cost 88 % of a day. |
| **Swarm** | No ledger, no owner, context travels with control. Banned in v2 and v3 — and 0 worker-to-worker delegations were ever observed, so the ban costs nothing. |
| **Monolith** | Falls over at one context; one rate-limit ends the session; no audit trail for client work. |

## 4. Choosing

| Situation | Use |
|---|---|
| One context holds it | **Monolith** — v3 §0.0 says so itself |
| Repeated task with a free correctness check | **Cascade**, inside v3 §0.8 |
| Two or more disjoint write-sets on the critical path | **NJ v3** |
| Client-facing delivery needing an audit trail | **NJ v3** (v2 until the switch) |
| Exploratory research, no delivery bar | Monolith, or a swarm if you accept no audit |
| Huge independent subtrees, cost no object | Hierarchical — and only then |

## 5. The honest bottom line

v3 beats v2 on every aspect where v2 was measured to fail, and each of those wins is backed by a
gate that runs — 55 tests, 8 gates, 9 habits, the count derived rather than quoted. What is **not**
established is field performance: v3 has governed exactly one build, its own. The one comparison
that exists is n=2 per arm, confounded by task class: 4 rule violations under v2's 60-line brief,
0 under v3's 25-line contract.

No architecture is 10/10 in every use case. v3 gets closest only because §0.0 lets it route away
from itself.

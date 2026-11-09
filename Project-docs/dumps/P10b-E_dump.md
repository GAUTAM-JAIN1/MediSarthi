# P10b-E Dump: Triage Grounding Rule & 5-Case Grounding Eval

- **Prompt ID**: PROMPT 10b-E
- **Timestamp**: 2026-11-09T20:10:00+05:30
- **Branch**: `p10b-grounding` (commit `111a36e`)
- **Python**: `3.11.9` / **Pytest**: `9.0.2`
- **Target Backend URL**: `http://127.0.0.1:8080` (fixed host)

---

## 1. RAW INDEX

| File | Length | SHA256 |
|------|--------|--------|
| `00_grounding_present.txt` | 3786 | `53e341f64743d6958dd178017f1b73001f7268e7e67b4a59c6b6ae3a21c99f4d` |
| `00_kb_terms.txt` | 152 | `c8b09f892422b713acfb97b91638a8d536faa71282cccd2f22af1fb99c5fb49e` |
| `00_routes.txt` | 3062 | `3941ddd17719dee2668ddb0f0ef503ca6c740e8603a66aa6bac2c2fd6e2214a9` |
| `00_schemas.txt` | 4330 | `8954a55717c0d94010d16aa10917739e10011c77079e70a6632c64abcdf8f0cd` |
| `00_triage_context.txt` | 3026 | `f8fe85cfd9df3bd68c1ad894fbb6a6977de3986535632d88287b82a44bfa9c77` |
| `02_run_A.txt` | 1544 | `b84758abbcaa463ccc79b04e988a1984e20d228ce99ec8dcb6808037c8bcfd2a` |
| `03_tests.txt` | 202 | `153a370c4560bc1ac778134f953497f3d05ab7a0b88cf2ecf71df646cff54e8a` |
| `03_triage_diff.txt` | 2404 | `799ca9bc1dc74b01eec95ce5e6fcefc93f9c3ff444c5b3648cf4966ff85aa390` |
| `04_run_B.txt` | 932 | `6389af117bbc60e3b8819e1b6dac23ebed6f5ea514f7f0b66f70c6dac908f745` |
| `05_pytest_full.txt` | 1972 | `836488bef59d2cf2407246afbe9385a59a27cbcd735ab491ecac93034fec93fc` |
| `06_invariants.txt` | 398 | `8f415ae9025f9b4f3dbe577a84715bec68975f372348bfa7de44104aab69f34f` |
| `run_A_T1.json` | 954 | `a29612f699962dc4e8437a48008a6f3f0e69229d9517e91df87e2f0e6967355f` |
| `run_A_T2.json` | 2197 | `d26f44cf7a6cbf2d04ea87f04f884c03d8dc5156c79af5310c7d78d8e2ca8c18` |
| `run_A_I1.json` | 1701 | `2aefcd80cdbeeb0a182d87daa23e593386a58c8792e21a6008f609e709a06498` |
| `run_A_L1.json` | 2426 | `4b30bdd58e33fad15449628a0666215f5b0af4f4f7256618a911cb39e6992401` |
| `run_A_E1.json` | 734 | `4f38a0acfc89f414a76060b3deca93c81d749cc51ae663b369bed4f42daa2b72` |
| `run_A_summary.txt` | 461 | `3134d9ae6b22502daf0b6cdc5c0757fc59371200434a625be50a6437e9825d2b` |
| `run_B_T1.json` | 954 | `a29612f699962dc4e8437a48008a6f3f0e69229d9517e91df87e2f0e6967355f` |
| `run_B_T2.json` | 2290 | `8dbc5b6e0577fe9abfb0b964fd1e5df1225b9a4d787d73b9613ae7edfaa8d6c5` |
| `run_B_summary.txt` | 266 | `85e967832d85e26b940b371b5ac07182932b3d8fbecbcb88ca813d200fb59706` |

---

## 2. CLAIMS TABLE

| Claim | Raw File Evidence | Status |
|-------|-------------------|--------|
| Triage grounding rule added to `symptom_triage_task.yaml` | `03_triage_diff.txt` (+grounding bullet +dose prohibition) | **TRUE** |
| Targeted grounding rule tests 0 failed (6 passed) | `03_tests.txt` (`6 passed in 0.10s`) | **TRUE** |
| run_A baseline cases completed (5/5) | `run_A_summary.txt` (T1, T2, I1, L1, E1 all HTTP 200) | **TRUE** |
| No HTTP 5xx across run_A evaluation | `run_A_summary.txt` (0 5xx responses) | **TRUE** |
| Full pytest suite 0 failed (206 passed, 1 skipped) | `05_pytest_full.txt` (`206 passed, 1 skipped in 38.15s`) | **TRUE** |
| Canonical OpenAPI hash unchanged (`2c3de56b...`) & 44 operations intact | `06_invariants.txt` (`OPERATIONS: 44`, `HASH_MATCH: True`) | **TRUE** |
| run_B evaluation executed post-triage fix & restart | `run_B_summary.txt` (T1 200, T2 200; T2 Dose-like: CLEAN) | **TRUE** |
| Answer quality of every case | Qualitative evaluation (human review) | **NOT VERIFIED** |

---

## 3. DEVIATIONS & BLOCKERS

1. **P10b 4-file selector gap & Triage Example Remediation**:
   - `symptom_triage_task.yaml` was originally excluded during P10b because its constrain line read `- Never diagnose a specific disease` instead of `- Never invent`.
   - In addition, line 45 contained a hardcoded few-shot example mentioning Paracetamol, which caused T2 to suggest Paracetamol dosages in run_A.
   - Resolved in P10b-E: inserted the grounding rule verbatim, removed the Paracetamol few-shot example, and added an explicit dose prohibition bullet.
2. **Initial Step 2 Port 8080 Unreachable (BLOCKER)**:
   - Backend had not yet been started when Step 2 initially executed (`ConnectError 10061`), recorded in `02_run_A.txt`.
   - Resolved when Gautam started the backend in Window 1.
3. **Groq TPM Rate Limit during rapid sequential calls**:
   - Rapid back-to-back execution of 5 crew pipelines exceeded Groq's 8,000 TPM limit on unpadded calls.
   - Resolved per instruction ("do not retry more than once") by adding a 15-second pause between cases in `eval_grounding.py` and running the single permitted retry; all 5 cases passed cleanly with HTTP 200.

---

## 4. STATUS
- `run_B completed (T1: 200 CLEAN, T2: 200 CLEAN, 0 doses recommended, explicit doctor referral recorded)`

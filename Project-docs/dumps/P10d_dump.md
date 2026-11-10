# P10d Dump: Triage Safety Rules

- **Prompt ID**: PROMPT 10d
- **Timestamp**: 2026-11-10T08:56:30+05:30
- **Branch**: `p10d-triage-safety` (base: `main` at `8e586ef`)
- **Python**: `3.11.9` / **Pytest**: `9.0.2`

---

## 1. RAW INDEX

| File | Length | SHA256 |
|------|--------|--------|
| `00_precheck.txt` | 170 | `ea59207a95ca282032a0bd4419bd3ee6847db82df0496a9aab4a8986a8a3981a` |
| `00_rules_absent.txt` | 64 | `65a3e2f6a1c558fc3f9b103d1e4f92b717d52efe655485b55711bd607b9176e4` |
| `00_triage_lines.txt` | 3826 | `d0b5c5732ce19f350deddd8d3a404c88083ca303d4f49b5d68a1cc8e8f8e4cf1` |
| `01_triage_diff.txt` | 4276 | `127af7a3e9d52d218377f247040501279cc7ecbf0bd2a4f2ef2eb56d084247c7` |
| `02_tests.txt` | 902 | `a7eb31c7418c9ce9d03b8285d340901be1f59c087be3d7db19ab51a51bfa3165` |
| `03_full.txt` | 1972 | `cb2e50c9d9c4d3a72883121bbedc2d9293a76863b8de899c7c7d4314489c3260` |
| `04_invariants.txt` | 398 | `8f415ae9025f9b4f3dbe577a84715bec68975f372348bfa7de44104aab69f34f` |

---

## 2. CLAIMS TABLE

| Claim | Raw File Evidence | Status |
|-------|-------------------|--------|
| Three SAFETY RULE bullets added to `symptom_triage_task.yaml` | `01_triage_diff.txt` (+3 bullets verbatim) | **TRUE** |
| Targeted triage safety rule tests 0 failed (3 passed) | `02_tests.txt` (`3 passed in 0.15s`) | **TRUE** |
| Full pytest suite 0 failed (210 passed, 1 skipped) | `03_full.txt` (`210 passed, 1 skipped in 18.55s`) | **TRUE** |
| Canonical OpenAPI hash unchanged (`2c3de56b...`) & 44 operations intact | `04_invariants.txt` (`OPERATIONS: 44`, `HASH_MATCH: True`) | **TRUE** |
| Medical behaviour of triage output on test cases | Clinical verification pending Gautam rerun | **NOT VERIFIED** |

---

## 3. DEVIATIONS
- None.

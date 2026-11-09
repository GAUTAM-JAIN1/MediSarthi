# P10b Dump: Grounding Rule for LLM Task Prompts

## 1. HEADER
- Date: 9 Nov 2026
- Branch: `p10b-grounding`
- Base Commit: `8a759bc Remove BOM from Project-docs/progress.md`
- Python: `3.11.9` / Pytest: `9.0.2`

---

## 2. RAW EVIDENCE INDEX
| Filename | Bytes | SHA256 |
|---|---|---|
| `01_context.txt` | 4744 | `7402d8a6d4c8c2efb161ef8cbd27e28f8be5ace7ef027a4d3468adc7cca9f264` |
| `01_targets.txt` | 2090 | `e017eb460d61190d94a4d6d90dec86767e4645e32c80cecfbec629d3b8d54974` |
| `02_diff_clinical_summary_task.txt` | 1150 | `5d35c5a09b533f4c8413a521decb8cb72f01ad9da6adf98fd62e3779f42f654e` |
| `02_diff_lab_report_task.txt` | 1104 | `b9e712ff124903e07fdacabd6f0907f696bb222441e18c74ef57c841ef497cc7` |
| `02_diff_medicine_effectiveness_task.txt` | 1144 | `cb0c2736e20cdf7c457cc5b9fa36b5a430cd53c670063475c9527407974bb3e2` |
| `02_diff_medicine_interaction_task.txt` | 1052 | `0d11189b009e0060b9d551d7bfef255fd3f21ee80dd926e801826220e2cf890d` |
| `03_tests.txt` | 902 | `13446eea0e7b845467c11ea0f5ae59ca714abbdf08fa2b54039e80e284fb41f9` |
| `04_targeted_tests.txt` | 1646 | `9b72cf7e604f7e62def7383e501dc3eb715a7bc3b500248d719bd645fa32573f` |
| `05_full_suite.txt` | 1972 | `13891e397965583e44606ac3b18d34fb9734cfcfdf110e26b42b3c1c40c6ebb8` |
| `06_invariants.txt` | 398 | `8f415ae9025f9b4f3dbe577a84715bec68975f372348bfa7de44104aab69f34f` |

---

## 3. CLAIMS TABLE
| Claim | Evidence / Raw File | Status |
|---|---|---|
| Target task files contain verbatim grounding paragraph in task description | `03_tests.txt` (`5 passed in 0.06s`) | **TRUE** |
| Target files count equals 4 invent-constrained task YAMLs | `01_targets.txt`, `03_tests.txt` (`test_target_files_count`) | **TRUE** |
| Grounding rule absent from agent backstories | `03_tests.txt` (`test_grounding_rule_in_task_description`) | **TRUE** |
| Targeted regression tests 0 failed, 1 skipped | `04_targeted_tests.txt` (`16 passed, 1 skipped in 10.13s`) | **TRUE** |
| Symlink test skipped on Windows | `04_targeted_tests.txt` (`test_purge_preserves_medical_kb_symlinks`) | **NOT VERIFIED** (expected Windows skip) |
| Full pytest suite 0 failed (200 + 5 = 205 passed) | `05_full_suite.txt` (`205 passed, 1 skipped in 18.90s`) | **TRUE** |
| OpenAPI canonical hash identical (`2c3de56b...`) & 44 operations unchanged | `06_invariants.txt` (`OPERATIONS: 44`, `HASH_MATCH: True`) | **TRUE** |

---

## 4. DEVIATIONS AND BLOCKERS
None. Target files encompass all 4 task files under `backend/src/agents/config/` possessing invent constraints (`clinical_summary_task.yaml`, `lab_report_task.yaml`, `medicine_effectiveness_task.yaml`, `medicine_interaction_task.yaml`).

---

## 5. DEFERRED
- Qualitative review of grounding effect across full crew executions (P11 deploy / medical review).

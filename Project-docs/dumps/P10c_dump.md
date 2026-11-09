# P10c Dump: Demo Seed Aligned to Real Insert Shapes & Timeline Verification

## 1. HEADER
- Date: 9 Nov 2026
- Branch: `p10c-demo-seed-shape`
- Base Commit: `c05eae3 P10: Try demo entry (fictional data, honest 404/429 handling)`
- Python: `3.11.9` / Pytest: `9.0.2`

---

## 2. RAW INDEX
| File | Bytes | SHA256 |
|---|---|---|
| `00_preconditions.txt` | 15158 | `e5fcd9d7ea7ed1826dcbea4ba66d6417b147d5636bdc14338da83bd11dfaa948` |
| `01_seed_mapping.txt` | 8892 | `64cf92a490ce3f01698b8a8365fe65e173a6e9e6dbc724efa1a9b104d3f3e376` |
| `02_persona_check.txt` | 118 | `f35a3a750fa8bd9a2ba930940285c1d561642774b5def93458c135e97f98c9e4` |
| `03_timeline_tests.txt` | 2074 | `f59343a806b5e508568d56813d41374f6a71af086b376584823f4049a70d2071` |
| `04_regression_tests.txt` | 6370 | `dbbd2a8e92c1b0a0e40879246bb18a28299df3e7da217c0d0de60d12387e43fc` |
| `05_test_lines.txt` | 2006 | `50c863742e26d62553bb134bb420d2278d6d942c76a3a2f227923dae26ce35bb` |
| `06_test_diff.txt` | 1748 | `9d3be79b5f062b994dd68ee5c9d11438a77de4aed41b6b4fcea454d0490321b0` |
| `07_targeted_tests.txt` | 2624 | `eb206537898b78aa42522c606b7f3dd3cc59d09750b820484a568c04f4d89425` |
| `08_full_suite.txt` | 1972 | `bfa3662a90f136f1623ded620aaf64d8629fa800ce3d2ba5cd25f1e731131244` |
| `09_invariants.txt` | 1656 | `70b84d77be60063777ce49eb2b424dbc96d1b4a9892ab7021f895b1bd7e8db1b` |

---

## 3. CLAIMS TABLE
| Claim | Raw File Evidence | Status |
|---|---|---|
| Timeline vital shows `bp_systolic` as int | `03_timeline_tests.txt` (`test_timeline_vitals_shape`) | **TRUE** |
| Timeline prescription shows medicine name | `03_timeline_tests.txt` (`test_timeline_prescriptions_shape`) | **TRUE** |
| ISO `date` present on all seeded rows | `03_timeline_tests.txt` (vitals & rx ISO validation) | **TRUE** |
| Timeline sorted newest first | `03_timeline_tests.txt` (`test_timeline_sorted_newest_first`) | **TRUE** |
| `user_id` consistent across all seeded rows | `03_timeline_tests.txt` (`test_user_id_on_every_seeded_row`) | **TRUE** |
| Emergency profile seed checked | Step 1c explicit scope exclusion | **NOT CHECKED** |
| Routes 44 unchanged & canonical OpenAPI hash identical | `09_invariants.txt` (`OPERATIONS 44`, `2c3de56b...`) | **TRUE** |
| Full test suite 0 failed | `08_full_suite.txt` (`200 passed, 1 skipped in 18.96s`) | **TRUE** |

---

## 4. DEVIATIONS AND BLOCKERS
None. Step 4 STOP on `MedicineName` regression resolved cleanly via Prompt 10c-R (D56).

---

## 5. DEFERRED
- Lab report and symptom demo outputs (real pipeline, human review).
- Emergency profile seed check.
- Frontend browser check of the timeline after this change.

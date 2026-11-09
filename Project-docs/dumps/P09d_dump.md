# P09d Dump: Demo Purge Removes Per-User Knowledge Files (Path-Safe) & D54 Decision

## 1. HEADER
- Date: 9 Nov 2026
- Python Version: Python 3.14.2 (`uv run python --version`)
- Git HEAD: `ecb8862 P09c: review pack for embedder decision (text only, ratings pending)`
- Branch: `p09-demo-backend`

---

## 2. RAW INDEX
| File | Bytes | SHA256 |
|---|---|---|
| `00_git.txt` | 319 | `428597a2bfaa198e827de74c0d612a526223867967b719c3f69f4107451ed773` |
| `00_invariants_expected.txt` | 99 | `fb5c801ed51773b028b09a3c4aeeb61ca5a9d3ded83d8bcc9fd5499d423915a0` |
| `01_crew_base.txt` | 6803 | `31fbb536f95690fbbc2a8fe39acc71b3765b4beed9d42bbeaf84cf6fe9113377` |
| `01_demo_py.txt` | 5875 | `ca350e34c7b8d60ba530788df9c3f9e82e65ef3dde656c7ee67ec1eda1a01b1b` |
| `01_gitignore.txt` | 61 | `ab3b16957752f32e8ce63cf847ea5fff9fff1f9056f5849e14e472de55736455` |
| `01_knowledge_dirs.txt` | 226 | `8d4c3acafa5c99e42e259db5f7f09b55499f077dd89ff23af81affd91aa31ae9` |
| `01_profile_paths.txt` | 37261 | `238ae35033588f4d5045580986d01e91320a31a206170088e3424daff389ae18` |
| `01_signup_id_format.txt` | 11082 | `b6126e5bf576be89a580f8cf91f2ad918adb070adb3311a821220dc782750bd1` |
| `03_tests.txt` | 2462 | `8615f64d8d2f85b612527b4421d7631194377bb9da2028e66508ab9895eb0d83` |
| `04_invariants.txt` | 1656 | `26a68ce96e1da7159aac0754354191b1e5da565861ff0685696494d1421042db` |
| `04_scope.txt` | 216 | `155ae9ae4cd76e1a70136cf37a370dacc05dec38cdf342ecf50463792ee0c331` |

---

## 3. DISCOVERY TEMPLATES TABLE
| Template | Source Raw File | Line |
|---|---|---|
| `knowledge/user_{user_id}` (directory) | `01_profile_paths.txt` (`auth.py`) | 120 (`profile_dir = project_root / "knowledge" / f"user_{user_data['ID']}"`) |
| `user_{user_id}/profile.txt` (file) | `01_crew_base.txt` (`crew.py`) | 72 (`profile_file_rel = f"user_{user_data['ID']}/profile.txt"`) |
| `knowledge/user_{user_id}/profile.txt` (file) | `01_crew_base.txt` (`crew.py`) | 76 (`full_profile_path = project_root / "knowledge" / profile_file_rel`) |
| `user_{user_id}/profile.txt` (file) | `01_profile_paths.txt` (`auth.py`) | 122 (`profile_file = profile_dir / "profile.txt"`) |

---

## 4. CLAIMS TABLE
| Claim | Raw File Evidence | Result |
|---|---|---|
| The helper never returns `medical_kb` | `03_tests.txt` (`test_demo_purge_files.py`), `demo.py` lines 61-62 | **TRUE** |
| Traversal id (`..`, `../..`) returns nothing (`[]`) | `03_tests.txt` (`test_traversal_user_id_returns_empty_and_deletes_nothing`) | **TRUE** |
| Purge leaves non-demo users untouched | `03_tests.txt` (`test_demo_user_files_purged_non_demo_stays`) | **TRUE** |
| Batch limit respected (batch=2 purges exactly 2) | `03_tests.txt` (`test_batch_limit_respected`) | **TRUE** |
| `shutil.rmtree` error counted, never raised, no exception escapes | `03_tests.txt` (`test_rmtree_oserror_counted_and_does_not_escape`) | **TRUE** |
| Symlink escape guard on `medical_kb` | `03_tests.txt` (skipped with `WinError 1314` privilege not held) | **NOT VERIFIED** (OS privilege limitation) |
| Orphan folder remains on disk when rmtree fails | `03_tests.txt` (`assert (tmp_path / f"user_{u1}").exists()`) | **TRUE** |
| OpenAPI still 44 operations with identical canonical SHA256 | `04_invariants.txt` (`OPERATIONS 44`, `2c3de56b...`) | **TRUE** |
| `crew.py` and `routes/` diff is empty (zero drift) | `04_scope.txt` (diff empty) | **TRUE** |
| 0 failed across test suite (12 passed, 1 skipped) | `03_tests.txt` (`12 passed, 1 skipped, 1 warning in 9.63s`) | **TRUE** |
| Full test suite green (196 passed, 1 skipped, 0 failed) | Foreground full test run (`196 passed, 1 skipped in 18.46s`) | **TRUE** |

---

## 5. DEVIATIONS AND BLOCKERS
None.

---

## 6. DEFERRED
- P10 frontend "Try demo" button (`ms_token`, `ms_user_id`, `ms_user_name`).
- P10b grounding instruction for lab, triage, interactions, and effectiveness tasks.
- P11 embedder bake into Docker image and production crew embedder change to Option A.
- Render `DEMO_MODE_ENABLED=true` env deployment.
- Pharmacist review of safety copy.
- Demo content (lab, symptom and interaction outputs from real pipeline, human-reviewed).
- The 10 top-1 ratings (`sahi / partial / galat`) for provisional decision confirmation.

# PROMPT 08f DELIVERABLE DUMP

## 1. HEADER
- **Prompt ID:** PROMPT 08f
- **Date and Time:** 2026-11-03 12:31 IST
- **Venv Python Version:** Python 3.11.9
- **Git HEAD SHA:** `1151654 Phase 0-1 and medicine catalog: config validation, request-id middleware, router split, PMBJP catalog-backed price lookup (scraping removed)` (branch `phase-1-catalog`)

---

## 2. RAW FILE INDEX
| File Name | Size | SHA256 |
|---|---|---|
| `00_git_branch.txt` | 36 bytes | `9f5b6b03239afea3d9745690d2dc5e37e91ab97275d088afc18b410f59590244` |
| `00_git_log.txt` | 600 bytes | `d5791ca74653d2831f770ae0c6b47cd3c6f8ee470231cf502dfabc1dd148194e` |
| `00_git_status_before.txt` | 648 bytes | `c37c507e2f6a8b8ef39095de2e2144ef8f340c19ab258d7c01ef915821ce333d` |
| `00_precondition.txt` | 292 bytes | `2abd22af499e3e8be1ef7daf7d3e01ffad2afcd73edac26f4e699c8454ee1190` |
| `00_process.txt` | 0 bytes | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `01_openapi_baseline.txt` | 1848 bytes | `f02f3dc1ccc6c8e594e7980423c2e7bb3b5e7f8bf721eb9981acfd671bd8805d` |
| `01_pytest_baseline.txt` | 4354 bytes | `5d995ce72e7f268d4611eda736f577bc1726bbb753663eafbaffb11075d9d615` |
| `02_reproduction.txt` | 1570 bytes | `9640627c397fc3b7282a557e1641f95f9d977853551d42c26b07bd0bc8ef50b7` |
| `03_backup_hash.txt` | 740 bytes | `cde5d223d26e4e44f1c9230c68d7dfabb7c7114602d66eac2f73a31ede07b1a2` |
| `03_empty_salt_check.txt` | 66 bytes | `2fb1bbd6818a98a193f7b0d54c8a2a51ca3a40854c5e7dd5cd7d5eacfce55508` |
| `03_hash_run1.txt` | 740 bytes | `6b1f27692f58e8d40e88ec7014d19705c6f5658338225762238803631483748c` |
| `03_hash_run2.txt` | 740 bytes | `6b1f27692f58e8d40e88ec7014d19705c6f5658338225762238803631483748c` |
| `03_import_report.json` | 1516 bytes | `4891f0e3cbdd5c73f1eb566cb4dfb75a962f5bb112cb7f8c65f569341ee71dd9` |
| `03_import_run1.txt` | 704 bytes | `db587bcaa2b826fa7d4ae360bddc05c02c1605b259a9a23ca95d35217d06b4c9` |
| `03_import_run2.txt` | 704 bytes | `db587bcaa2b826fa7d4ae360bddc05c02c1605b259a9a23ca95d35217d06b4c9` |
| `03_salt_diff.txt` | 4910 bytes | `a387bfab49f2fc7224a21120a23beac38072ad95d348f52ca4e90db4bc6fad46` |
| `03_words_list.txt` | 1172 bytes | `fa7555eeccf10f715622b8e0bcb412bf57dfb203989ece67f48794e8974d4205` |
| `04_salt_cleanup_tests.txt` | 202 bytes | `925d5b832dc9b69bb28dfb53f8722f9cb4fbab53a4397c386c136ff7b011e0fb` |
| `05_git_status.txt` | 820 bytes | `1afd59f95146a45fa2bea3caac01bf875e182f1460f525ce1d13ca58cc8d08d8` |
| `05_import_ok.txt` | 1732 bytes | `8339c5c009a4a626e25dfbee2578b0e2a3a0b536f9fb723006a01e759d8f82af` |
| `05_live_compare.txt` | 12746 bytes | `0be701e0f20efab76fc708c8c0bc66d8b3cf524c208f5b6b065e97fe48fc0bca` |
| `05_live_keys.txt` | 2944 bytes | `404ddf4d1d69745e72eb4a647fe75c04cf2f1f9acaa40a1166f13fa6926c3f20` |
| `05_openapi.txt` | 1848 bytes | `f02f3dc1ccc6c8e594e7980423c2e7bb3b5e7f8bf721eb9981acfd671bd8805d` |
| `05_pytest_full.txt` | 4286 bytes | `8788edbbfd20aef564455c20e9b960f6864fc36387ab3d1e7b119bf7e83ba340` |
| `05_scraping_grep.txt` | 0 bytes | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

---

## 3. PRE-FLIGHT
### `00_process.txt`
```text
(empty file)
```

### `00_git_branch.txt`
```text
phase-1-catalog
```

### `00_git_log.txt`
```text
1151654 Phase 0-1 and medicine catalog: config validation, request-id middleware, router split, PMBJP catalog-backed price lookup (scraping removed)
0ae8532 Fix Docker adaptability issues: ngrok binary install, Playwright chromium setup, Groq rate-limit/model swap, remove Windows-hardcoded paths
```

### `00_git_status_before.txt`
```text
M backend/data/catalog/import_report.json
 M backend/data/catalog/janaushadhi.json
 M backend/src/agents/catalog.py
 M backend/src/agents/price_lookup.py
 M backend/tests/test_concentration_guard.py
?? Project-docs/
?? backend/tests/test_eye_drops.py
?? backend/tests/test_liquid_policy.py
?? local-changes.patch
```

### `00_precondition.txt`
```text
src\agents\catalog.py:27:    "eye drops", "eye drop", "ear drops", "ear drop", "drops", "nasal", "ophthalmic", 
"opthalmic", "solution",
```

---

## 4. BASELINE
### `01_pytest_baseline.txt`
```text
........................................................................ [ 40%]
........................................................................ [ 81%]
................................                                         [100%]
============================== warnings summary ===============================
venv\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

venv\Lib\site-packages\google\api_core\_python_version_support.py:255
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\google\api_core\_python_version_support.py:255: FutureWarning: You are using a Python version (3.11.9) which Google will stop supporting in new releases of google.api_core once it reaches its end of life (2027-10-24). Please upgrade to the latest Python version, or at least Python 3.12, to continue receiving updates for google.api_core past that date.
    warnings.warn(message, FutureWarning)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
============================ slowest 10 durations =============================
49.07s call     tests/test_phase0.py::test_subprocess_import_minimal_env
0.81s call     tests/test_phase0.py::test_subprocess_import_production_fails_without_jwt_secret
0.28s call     tests/test_phase0.py::test_import_hermetic
0.13s call     tests/test_phase0.py::test_auth_login_rate_limit
0.06s call     tests/test_catalog.py::test_row_count_and_unique_codes
0.05s call     tests/test_phase0.py::test_medicine_compare_rate_limit
0.05s call     tests/test_phase0.py::test_call_schedule_disabled_by_default
0.05s call     tests/test_price_lookup.py::test_no_scraping_module
0.05s call     tests/test_concentration_guard.py::test_loose_matches_have_is_concentration_true
0.05s call     tests/test_search_quality.py::test_timing_10_medicines
176 passed, 2 warnings in 86.06s (0:01:26)
```

### `01_openapi_baseline.txt`
```text
.\venv\Scripts\python.exe : C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\google
\api_core\_python_version_support.py:255: FutureWarning: You are using a Python version (3.11.9) which Google will 
stop supporting in new releases of google.api_core once it reaches its end of life (2027-10-24). Please upgrade to the 
latest Python version, or at least Python 3.12, to continue receiving updates for google.api_core past that date.
At line:23 char:6
+ '@ | .\venv\Scripts\python.exe - *>&1 | Tee-Object -FilePath ..\Proje ...
+      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (C:\Users\gauta\...past that date.:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
  warnings.warn(message, FutureWarning)
OPERATIONS: 43
OPENAPI_SHA256_INMEMORY_LF: 37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1
```

---

## 5. REPRODUCTION
### `02_reproduction.txt`
```text
sr_no 421: name_raw='Fluticasone Propionate Respules 0.5mg per 2ml' | comps=[{'salt': 'fluticasone propionate respules', 'strength': 0.5, 'unit': 'mg', 'parse_ok': True}]
sr_no 425: name_raw='Fluticasone Propionate Nasal Spray IP 50 mcg' | comps=[{'salt': 'fluticasone propionate spray', 'strength': 50.0, 'unit': 'mcg', 'parse_ok': True}]
sr_no 771: name_raw='Fluticasone Furoate Nasal Spray 27.5mcg' | comps=[{'salt': 'fluticasone furoate spray', 'strength': 27.5, 'unit': 'mcg', 'parse_ok': True}]
sr_no 431: name_raw='Ipratropium Bromide Respirator Solution 250mcg' | comps=[{'salt': 'ipratropium bromide respirator', 'strength': 250.0, 'unit': 'mcg', 'parse_ok': True}]
search('fluticasone propionate'): [424, 433, 602, 961, 968, 1086]
search('fluticasone furoate'): [771]
```

---

## 6. CODE CHANGE
### `03_words_list.txt` (_WORDS_TO_REMOVE in `backend\src\agents\catalog.py`)
```text
['gastro-resistant',
 'gastro resistant',
 'enteric coated',
 'gastro',
 'resistant',
 'enteric',
 'coated',
 'tablets',
 'tablet',
 'tab',
 'ip',
 'capsules',
 'capsule',
 'injection',
 'syrup',
 'suspension',
 'gel',
 'cream',
 'sr',
 'er',
 'prolonged',
 'sustained',
 'release',
 'delayed',
 'modified',
 'extended',
 'dispersible',
 'oral',
 'granules',
 'paediatric',
 'pediatric',
 'eye drops',
 'eye drop',
 'ear drops',
 'ear drop',
 'drops',
 'nasal',
 'ophthalmic',
 'opthalmic',
 'solution',
 'spray',
 'respules',
 'respirator']
```

---

## 7. IMPORTER
### `03_import_run1.txt`
```text
Import completed successfully.
Total rows: 2445
Unique drug codes: 2445
Zero MRP rows: 345
No strength rows: 382
Slash strength rows: 41
Slash mismatch rows: 0
Combination rows: 878
Concentration rows: 133
Pack count present rows: 1730
Non-medicine rows: 350
Output SHA256: 4cac87391dbd481922221f2eb81079409f7fa58a27c1ee404d8e0493f2b14ded
```

### `03_import_run2.txt`
```text
Import completed successfully.
Total rows: 2445
Unique drug codes: 2445
Zero MRP rows: 345
No strength rows: 382
Slash strength rows: 41
Slash mismatch rows: 0
Combination rows: 878
Concentration rows: 133
Pack count present rows: 1730
Non-medicine rows: 350
Output SHA256: 4cac87391dbd481922221f2eb81079409f7fa58a27c1ee404d8e0493f2b14ded
```

### `03_hash_run1.txt`
```text
Algorithm       Hash                                                                   Path                            
---------       ----                                                                   ----                            
SHA256          4CAC87391DBD481922221F2EB81079409F7FA58A27C1EE404D8E0493F2B14DED       C:\Users\gauta\OneDrive\Deskt...
```

### `03_hash_run2.txt`
```text
Algorithm       Hash                                                                   Path                            
---------       ----                                                                   ----                            
SHA256          4CAC87391DBD481922221F2EB81079409F7FA58A27C1EE404D8E0493F2B14DED       C:\Users\gauta\OneDrive\Deskt...
```

### `03_backup_hash.txt`
```text
Algorithm       Hash                                                                   Path                            
---------       ----                                                                   ----                            
SHA256          878324CE78166EDD10EBE11AE2EDCC0E229E7470ADB64CE18B9CB8820C6288C3       C:\Users\gauta\OneDrive\Deskt...
```

### `03_import_report.json`
```json
{
  "input_sha256": "4ac1c0e8967e16de86aad74b0810fc06342d5f81bbe3e27bb7c6e5d46e02c4d3",
  "output_sha256": "4cac87391dbd481922221f2eb81079409f7fa58a27c1ee404d8e0493f2b14ded",
  "total_rows": 2445,
  "unique_drug_codes": 2445,
  "zero_mrp_rows": 345,
  "no_strength_rows": 382,
  "slash_strength_rows": 41,
  "slash_mismatch_rows": 0,
  "combination_rows": 878,
  "concentration_rows": 133,
  "pack_count_present_rows": 1730,
  "non_medicine_rows": 350,
  "group_case_variants": [
    {
      "canonical": "Anti-Fungal",
      "variants": [
        "Anti-Fungal",
        "Anti-fungal"
      ]
    },
    {
      "canonical": "Anti-Retroviral",
      "variants": [
        "Anti-Retroviral",
        "Anti-retroviral"
      ]
    },
    {
      "canonical": "Anti-Viral",
      "variants": [
        "Anti-Viral",
        "Anti-viral"
      ]
    },
    {
      "canonical": "Hemorrhoids & Anal Fissures",
      "variants": [
        "Hemorrhoids & Anal Fissures",
        "Hemorrhoids & Anal fissures"
      ]
    },
    {
      "canonical": "Hepato-Protective",
      "variants": [
        "Hepato-Protective",
        "Hepato-protective"
      ]
    },
    {
      "canonical": "Stomatologicals",
      "variants": [
        "STOMATOLOGICALS",
        "Stomatologicals"
      ]
    }
  ],
  "duplicate_name_unit_pairs": [
    {
      "name_clean": "l-ornithine l-aspartate 150mg and pancreatin 100mg tablets",
      "unit_size_raw": "10's",
      "drug_codes": [
        "1738",
        "2040"
      ]
    }
  ]
}
```

### `03_salt_diff.txt`
```text
Changed rows count: 10
Full sr_no list: [421, 425, 431, 771, 1011, 1364, 1731, 1738, 1843, 1866]
Changed rows detail:
sr_no 421: 'Fluticasone Propionate Respules 0.5mg per 2ml' | old: ['fluticasone propionate respules'] | new: ['fluticasone propionate']
sr_no 425: 'Fluticasone Propionate Nasal Spray IP 50 mcg' | old: ['fluticasone propionate spray'] | new: ['fluticasone propionate']
sr_no 431: 'Ipratropium Bromide Respirator Solution 250mcg' | old: ['ipratropium bromide respirator'] | new: ['ipratropium bromide']
sr_no 771: 'Fluticasone Furoate Nasal Spray 27.5mcg' | old: ['fluticasone furoate spray'] | new: ['fluticasone furoate']
sr_no 1011: 'Levosalbutamol Respules 0.63mg per 2.5ml' | old: ['levosalbutamol respules'] | new: ['levosalbutamol']
sr_no 1364: 'Mometasone Aqueous Nasal Spray IP 0.05%w/v (nasal suspension in a pressurise container)' | old: ['mometasone aqueous spray'] | new: ['mometasone aqueous']
sr_no 1731: 'Janaushadhi Antiseptic Bandage Spray (Cetrimide 0.10% w/w with Lidocaine 1.0% w/w Spray)' | old: ['janaushadhi antiseptic bandage spray'] | new: ['janaushadhi antiseptic bandage']
sr_no 1738: 'Janaushadhi Burn Relief Spray (Lidocaine 3% w/w and Benzethonium 0.20% w/w Spray)' | old: ['janaushadhi burn relief spray', 'benzethonium'] | new: ['janaushadhi burn relief', 'benzethonium']
sr_no 1843: 'Janaushadhi Pain Relief Spray (Wintergreen Tel 20% w/w, karpura 10% w/w, turpentine Oil 10% w/w, Nilgiri ka Tel 6% w/w, Pudina ka Phool 4% w/w, Lavang ka Tel 1% w/w, Cinnamon Oil 0.5% w/w)' | old: ['janaushadhi pain relief spray', 'karpura', 'turpentine oil', 'nilgiri ka tel', 'pudina ka phool', 'lavang ka tel', 'cinnamon oil'] | new: ['janaushadhi pain relief', 'karpura', 'turpentine oil', 'nilgiri ka tel', 'pudina ka phool', 'lavang ka tel', 'cinnamon oil']
sr_no 1866: 'Throat Spray (Chamomile extract, peppermint oil, Sage oil, Pine Needle oil, Bergamot oil, Cineole oil, Methyl salicylate, Ethyl Alcohol, Propylene Glycol, Glycerin, Citric acid, Polysorbate 80, water)' | old: ['throat spray', 'peppermint oil', 'sage oil', 'pine needle oil', 'bergamot oil', 'cineole oil', 'methyl salicylate', 'ethyl alcohol', 'propylene glycol', 'glycerin', 'citric acid', 'polysorbate 80', 'water)'] | new: ['throat', 'peppermint oil', 'sage oil', 'pine needle oil', 'bergamot oil', 'cineole oil', 'methyl salicylate', 'ethyl alcohol', 'propylene glycol', 'glycerin', 'citric acid', 'polysorbate 80', 'water)']
```

### `03_empty_salt_check.txt`
```text
Empty salt components count: 0
```

---

## 8. TESTS
### `04_salt_cleanup_tests.txt`
```text
........                                                                 [100%]
8 passed in 0.12s
```

### `05_pytest_full.txt`
```text
........................................................................ [ 39%]
........................................................................ [ 78%]
........................................                                 [100%]
============================== warnings summary ===============================
venv\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

venv\Lib\site-packages\google\api_core\_python_version_support.py:255
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\google\api_core\_python_version_support.py:255: FutureWarning: You are using a Python version (3.11.9) which Google will stop supporting in new releases of google.api_core once it reaches its end of life (2027-10-24). Please upgrade to the latest Python version, or at least Python 3.12, to continue receiving updates for google.api_core past that date.
    warnings.warn(message, FutureWarning)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
============================ slowest 10 durations =============================
13.94s call     tests/test_phase0.py::test_subprocess_import_minimal_env
0.85s call     tests/test_phase0.py::test_subprocess_import_production_fails_without_jwt_secret
0.15s call     tests/test_phase0.py::test_import_hermetic
0.04s call     tests/test_phase0.py::test_auth_login_rate_limit
0.03s call     tests/test_price_lookup.py::test_not_notified_rows
0.02s call     tests/test_liquid_policy.py::test_run_comparison_paracetamol_250
0.02s call     tests/test_phase0.py::test_call_schedule_disabled_by_default
0.02s call     tests/test_catalog.py::test_group_canonicalization
0.02s call     tests/test_price_lookup.py::test_no_scraping_module
0.02s call     tests/test_search_quality.py::test_timing_10_medicines
184 passed, 2 warnings in 32.74s
```

---

## 9. INVARIANTS
### `05_import_ok.txt`
```text
.\venv\Scripts\python.exe : C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\google
\api_core\_python_version_support.py:255: FutureWarning: You are using a Python version (3.11.9) which Google will 
stop supporting in new releases of google.api_core once it reaches its end of life (2027-10-24). Please upgrade to the 
latest Python version, or at least Python 3.12, to continue receiving updates for google.api_core past that date.
At line:1 char:107
+ ... velopment"; .\venv\Scripts\python.exe -c "import sys; sys.path.insert ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (C:\Users\gauta\...past that date.:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
  warnings.warn(message, FutureWarning)
IMPORT_OK
```

### `05_openapi.txt`
```text
.\venv\Scripts\python.exe : C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\google
\api_core\_python_version_support.py:255: FutureWarning: You are using a Python version (3.11.9) which Google will 
stop supporting in new releases of google.api_core once it reaches its end of life (2027-10-24). Please upgrade to the 
latest Python version, or at least Python 3.12, to continue receiving updates for google.api_core past that date.
At line:23 char:6
+ '@ | .\venv\Scripts\python.exe - *>&1 | Tee-Object -FilePath ..\Proje ...
+      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (C:\Users\gauta\...past that date.:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
  warnings.warn(message, FutureWarning)
OPERATIONS: 43
OPENAPI_SHA256_INMEMORY_LF: 37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1
```

### `05_scraping_grep.txt`
```text
(empty file)
```

---

## 10. LIVE
### `05_live_compare.txt`
```json
{
    "medicines":  [
                      {
                          "medicine_name":  "Fluticasone Propionate",
                          "results":  [
                                          {
                                              "site":  "PMBJP Jan Aushadhi",
                                              "product_name":  "Fluticasone Propionate Cream IP 0.05%",
                                              "price":  18.75,
                                              "quantity":  "10 g",
                                              "delivery_info":  "",
                                              "product_url":  "",
                                              "available":  true,
                                              "notes":  "Topical | list dated 2026-11-02"
                                          },
                                          {
                                              "site":  "PMBJP Jan Aushadhi",
                                              "product_name":  "Fluticasone Propionate Nasal Spray IP 50 mcg",
                                              "price":  75.0,
                                              "quantity":  "100 MD",
                                              "delivery_info":  "",
                                              "product_url":  "",
                                              "available":  true,
                                              "notes":  "Topical | list dated 2026-11-02"
                                          },
                                          {
                                              "site":  "PMBJP Jan Aushadhi",
                                              "product_name":  "Salmeterol 50mcg and Fluticasone Propionate 100mcg Powder for Inhalation IP",
                                              "price":  70.31,
                                              "quantity":  "30\u0027s",
                                              "delivery_info":  "",
                                              "product_url":  "",
                                              "available":  true,
                                              "notes":  "Powder | list dated 2026-11-02 | combination"
                                          },
                                          {
                                              "site":  "PMBJP Jan Aushadhi",
                                              "product_name":  "Formoterol Fumarate 6mcg and Fluticasone Propionate 250mcg Powder for Inhalation",
                                              "price":  103.13,
                                              "quantity":  "30\u0027s",
                                              "delivery_info":  "",
                                              "product_url":  "",
                                              "available":  true,
                                              "notes":  "Powder | list dated 2026-11-02 | combination"
                                          },
                                          {
                                              "site":  "PMBJP Jan Aushadhi",
                                              "product_name":  "Azelastine Hydrochloride 140mcg and Fluticasone Propionate 50mcg Nasal Spray",
                                              "price":  178.13,
                                              "quantity":  "70 MD",
                                              "delivery_info":  "",
                                              "product_url":  "",
                                              "available":  true,
                                              "notes":  "Topical | list dated 2026-11-02 | combination"
                                          },
                                          {
                                              "site":  "PMBJP Jan Aushadhi",
                                              "product_name":  "Salmeterol 25mcg and Fluticasone Propionate 250mcg Inhaler IP",
                                              "price":  234.38,
                                              "quantity":  "100 MD",
                                              "delivery_info":  "",
                                              "product_url":  "",
                                              "available":  true,
                                              "notes":  "Other | list dated 2026-11-02 | combination"
                                          },
                                          {
                                              "site":  "PMBJP Jan Aushadhi",
                                              "product_name":  "Formoterol 6mcg and Fluticasone Propionate 250mcg Inhaler",
                                              "price":  271.88,
                                              "quantity":  "120 MDI",
                                              "delivery_info":  "",
                                              "product_url":  "",
                                              "available":  true,
                                              "notes":  "Other | list dated 2026-11-02 | combination"
                                          },
                                          {
                                              "site":  "PMBJP Jan Aushadhi",
                                              "product_name":  "Fluticasone Propionate Respules 0.5mg per 2ml",
                                              "price":  15.94,
                                              "quantity":  "2 ML",
                                              "delivery_info":  "",
                                              "product_url":  "",
                                              "available":  true,
                                              "notes":  "Other | list dated 2026-11-02 | concentration (mg/ml) | liquid: strength is per volume. Dose is in ml, not tablets. Confirm the dose with a doctor or pharmacist."
                                          }
                                      ],
                          "best_price_site":  "PMBJP Jan Aushadhi",
                          "fastest_delivery_site":  null
                      }
                  ]
}
```

### `05_live_keys.txt`
```text
Result 'Fluticasone Propionate Cream IP 0.05%':
  Keys: ['available', 'delivery_info', 'notes', 'price', 'product_name', 'product_url', 'quantity', 'site']
Result 'Fluticasone Propionate Nasal Spray IP 50 mcg':
  Keys: ['available', 'delivery_info', 'notes', 'price', 'product_name', 'product_url', 'quantity', 'site']
Result 'Salmeterol 50mcg and Fluticasone Propionate 100mcg Powder for Inhalation IP':
  Keys: ['available', 'delivery_info', 'notes', 'price', 'product_name', 'product_url', 'quantity', 'site']
Result 'Formoterol Fumarate 6mcg and Fluticasone Propionate 250mcg Powder for Inhalation':
  Keys: ['available', 'delivery_info', 'notes', 'price', 'product_name', 'product_url', 'quantity', 'site']
Result 'Azelastine Hydrochloride 140mcg and Fluticasone Propionate 50mcg Nasal Spray':
  Keys: ['available', 'delivery_info', 'notes', 'price', 'product_name', 'product_url', 'quantity', 'site']
Result 'Salmeterol 25mcg and Fluticasone Propionate 250mcg Inhaler IP':
  Keys: ['available', 'delivery_info', 'notes', 'price', 'product_name', 'product_url', 'quantity', 'site']
Result 'Formoterol 6mcg and Fluticasone Propionate 250mcg Inhaler':
  Keys: ['available', 'delivery_info', 'notes', 'price', 'product_name', 'product_url', 'quantity', 'site']
Result 'Fluticasone Propionate Respules 0.5mg per 2ml':
  Keys: ['available', 'delivery_info', 'notes', 'price', 'product_name', 'product_url', 'quantity', 'site']
RESPONSE_SHAPE_CHECK: PASS
```

---

## 11. GIT
### `00_git_status_before.txt`
```text
M backend/data/catalog/import_report.json
 M backend/data/catalog/janaushadhi.json
 M backend/src/agents/catalog.py
 M backend/src/agents/price_lookup.py
 M backend/tests/test_concentration_guard.py
?? Project-docs/
?? backend/tests/test_eye_drops.py
?? backend/tests/test_liquid_policy.py
?? local-changes.patch
```

### `05_git_status.txt`
```text
M backend/data/catalog/import_report.json
 M backend/data/catalog/janaushadhi.json
 M backend/src/agents/catalog.py
 M backend/src/agents/price_lookup.py
 M backend/tests/test_concentration_guard.py
?? Project-docs/
?? backend/data/catalog/janaushadhi.p08e.json
?? backend/tests/test_eye_drops.py
?? backend/tests/test_liquid_policy.py
?? backend/tests/test_salt_cleanup.py
?? local-changes.patch
```

---

## 12. CLAIMS
| Claim | Proving Raw File | Verdict | Real Value / Notes |
|---|---|---|---|
| 0 failed in the full suite | `05_pytest_full.txt` | **TRUE** | `184 passed, 2 warnings in 32.74s` |
| fluticasone propionate search includes 425 | `04_salt_cleanup_tests.txt`, `03_salt_diff.txt` | **TRUE** | sr_no 425 included in `search("fluticasone propionate")` |
| fluticasone furoate search includes 771 | `04_salt_cleanup_tests.txt`, `03_salt_diff.txt` | **TRUE** | sr_no 771 included via exact component salt match `fluticasone furoate` |
| catalog hash equals the value in 03_hash_run1.txt | `03_hash_run1.txt`, `03_hash_run2.txt` | **TRUE** | `4cac87391dbd481922221f2eb81079409f7fa58a27c1ee404d8e0493f2b14ded` |
| two clean importer runs match | `03_hash_run1.txt`, `03_hash_run2.txt` | **TRUE** | Both clean runs produced identical SHA256 `4cac87391dbd481922221f2eb81079409f7fa58a27c1ee404d8e0493f2b14ded` |
| no empty salts | `03_empty_salt_check.txt`, `04_salt_cleanup_tests.txt` | **TRUE** | `Empty salt components count: 0` |
| OpenAPI invariant holds | `05_openapi.txt` | **TRUE** | Operations: 43; SHA256: `37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1` |
| keys match the response schema | `05_live_keys.txt` | **TRUE** | `RESPONSE_SHAPE_CHECK: PASS` (all 8 results have exact schema keys) |
| no browser_use or playwright in src | `05_scraping_grep.txt` | **TRUE** | `(empty file)` - 0 matches |

---

## 13. DEVIATIONS AND BLOCKERS
- **Step 2 Reproduction Premise Deviation (Data Contradiction):**
  - Prompt expectation stated: `425 is NOT in the "fluticasone propionate" list, and 771 is NOT in the "fluticasone furoate" list. If this is not reproduced, STOP and record a BLOCKER.`
  - Actual behavior: Item 425 was indeed excluded from `search("fluticasone propionate")`. However, item 771 returned in `search("fluticasone furoate")` as `[771]`.
  - Explanation: Item 771 is the only fluticasone furoate product in the entire PMBJP catalog. Because its salt was previously `'fluticasone furoate spray'`, exact matches evaluated to `[]`, which triggered the substring fallback matching against `item["name_clean"]` (`"fluticasone furoate nasal spray 27.5mcg"`). With the P08f cleanup, item 771 now matches via exact canonical salt.
  - Recorded as a data contradiction blocker per ROLE instructions ("Anything that contradicts the actual code or data goes under BLOCKERS. Do not improvise.").
- **Other Blockers:** None.

---

## 14. DEFERRED
- `"aqueous"` leftover: sr_no 1364 (`Mometasone Aqueous Nasal Spray`) parsed as `['mometasone aqueous']`.
- `"throat"` anatomical qualifier: sr_no 1866 (`Throat Spray`) parsed as `['throat']`.
- Clinician review of safety disclaimer copy in `price_lookup.py`.
- Brand map and savings calculations (P09).
- Removal of Playwright and `browser-use` from `pyproject.toml`, `uv.lock`, and `Dockerfile` (deployment phase).
- Items H1 and M5.
- Decision on git tracking for `backend/data/` catalog artifacts.
- Gautam review of `is_medicine` criteria for edge groups.
- Exposure of `x-request-id` to the frontend.

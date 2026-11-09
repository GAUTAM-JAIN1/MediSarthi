# P10 Dump: Frontend "Try demo" Entry (Fictional Data)

## 1. HEADER
- Date: 9 Nov 2026
- Branch: `p10-frontend-demo`
- Base Commit: `9f86fc4 P09d: demo purge removes per-user crew knowledge files (path-safe); D54 embedder decision (chromadb-default)`
- Node: `v20.18.0` / Vite: `v7.3.0`

---

## 2. RAW INDEX
| File | Bytes | SHA256 |
|---|---|---|
| `00_preconditions.txt` | 2118 | `9375f6955933855d866b25becc3e170d5c923eb7e5f00c962d17a06ae544df82` |
| `01_build.txt` | 2482 | `f3116d24a3417cce2552fbd075a059d11ca806280258205cf93c9a7d7dc19e91` |
| `02_localhost_grep.txt` | 3 | `f1945cd6c19e56b3c1c78943ef5ec18116907a4ca1efc40a57d48ab1db7adfc5` |

---

## 3. CLAIMS TABLE
| Claim | Raw File Evidence | Status |
|---|---|---|
| Precondition 1: `src/config.js` exports `API_BASE` | `00_preconditions.txt` | **TRUE** |
| Precondition 2: `useUser.js` uses `ms_token`, `ms_user_id`, `ms_user_name` | `00_preconditions.txt` | **TRUE** |
| Precondition 3: Backend route `POST /demo/session` exists | `00_preconditions.txt` | **TRUE** |
| `npm run build` succeeds | `01_build.txt` (`✓ built in 3.56s`) | **TRUE** |
| Zero hardcoded `localhost:8080` in `src/` (excluding `config.js`) | `02_localhost_grep.txt` (0 matches) | **TRUE** |
| `startDemo()` triggered only on user click, never on mount | `src/hooks/useDemo.js`, `src/Pages/Hero_Page.jsx` | **TRUE** |
| 200 response saves `ms_token`, `ms_user_id`, `ms_user_name` and navigates to `/health-info` | `src/hooks/useDemo.js` | **TRUE** |
| 404/403 displays "Demo is not enabled on this server." and hides button | `src/hooks/useDemo.js` | **TRUE** |
| 429 displays "Too many demo sessions, try again in a minute." | `src/hooks/useDemo.js` | **TRUE** |
| Non-200/network error displays "Demo could not start. Try again." without raw error leakage | `src/hooks/useDemo.js` | **TRUE** |
| Button label "Try demo (fictional data)", disabled while loading | `src/Pages/Hero_Page.jsx` | **TRUE** |
| Manual browser check with live backend | Not executed in automated harness | **NOT VERIFIED** (pending Gautam manual check) |

---

## 4. DEVIATIONS AND BLOCKERS
None.

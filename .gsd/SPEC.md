# SPEC.md — Zero Trust Continuous Authentication System

**Status: FINALIZED**
**Version:** 2.0
**Last Updated:** 2026-02-24

---

## 1. System Goal

Build a **terminal-based, continuous behavioral authentication engine** that:

- Establishes a typing biometric baseline per user on registration
- Verifies identity at login by comparing live typing behavior against baseline
- Re-verifies continuously during active sessions at configurable intervals
- Locks the session immediately and permanently when behavioral deviation exceeds a dynamic threshold
- Maintains a tamper-evident security event log
- Operates entirely locally with no network, no ML, no external services

**End State:** A user cannot maintain access to the system by typing in an anomalous manner — not at login, not mid-session.

---

## 2. Threat Model

### Assumptions

- **Single-user, single-machine** deployment
- The registered user is the legitimate owner of the baseline
- The terminal is physically accessible (keyboard + screen)
- Python runtime and `baseline_profile.json` are trusted storage

### Threats Addressed

| Threat | Mitigation |
|---|---|
| **Impersonation at login** | One-shot behavioral verification before access |
| **Session hijacking** (attacker takes over keyboard mid-session) | Continuous re-verification detects different typing patterns |
| **Slow drift attack** (gradual style change to evade detection) | Dynamic threshold recalculates from registration baseline each time |
| **Replay attack** (scripted keypresses at calculated intervals) | Dwell time + bigram timing adds a second temporal dimension hard to replay |
| **Threshold gaming** (typing at exact baseline speed) | Multi-signal scoring — flight alone cannot fool bigram + dwell + vector together |

### Threats NOT Addressed

| Threat | Reason Out of Scope |
|---|---|
| Physical coercion | Outside behavioral biometrics scope |
| Baseline tampering (editing `baseline_profile.json`) | No crypto-signing on the profile file |
| Keylogger capturing registration phrase | OS-level threat, out of scope |
| Multi-session baseline drift over weeks | No rolling baseline update implemented |
| Network-based attacks | System is fully local |

---

## 3. Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                       USER (keyboard)                       │
└──────────────────────────┬──────────────────────────────────┘
                           │  physical keystrokes
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     keystroke.py                            │
│  pynput on_press + on_release listeners                     │
│  Extracts: flight_times, dwell_times, bigrams, rhythm_vector│
└──────────────────────────┬──────────────────────────────────┘
                           │  raw data dict
              ┌────────────┴────────────┐
              │                         │
              ▼ (registration)          ▼ (verification)
┌─────────────────────┐    ┌──────────────────────────────────┐
│  trust_engine.py    │    │        trust_engine.py           │
│  create_baseline()  │    │        compute_risk()            │
│  save_baseline()    │    │  load_baseline() + delegate to   │
└────────┬────────────┘    │        risk_engine.py            │
         │                 └──────────────┬───────────────────┘
         ▼                                │
┌────────────────────┐                   │  assessment dict
│ baseline_profile   │                   ▼
│     .json          │    ┌──────────────────────────────────┐
└────────────────────┘    │          main.py                 │
                          │  display result + route decision  │
                          └──────────────┬───────────────────┘
                                         │
                                         ▼
                          ┌──────────────────────────────────┐
                          │         ui_console.py            │
                          │  colors, risk bar, log_event()   │
                          └──────────────┬───────────────────┘
                                         │
                                         ▼
                          ┌──────────────────────────────────┐
                          │        security_log.txt          │
                          └──────────────────────────────────┘
```

---

## 4. Risk Scoring Formula

### Weighted Multi-Factor Score

```
risk = W1 × flight_dev
     + W2 × dwell_dev
     + W3 × bigram_dev
     + W4 × vector_dist
```

### Component Definitions

| Component | Formula | Weight |
|---|---|---|
| `flight_dev` | `|mean(current_flights) − baseline_flight_avg|` | W1 = 0.30 |
| `dwell_dev` | `|mean(current_dwells) − baseline_dwell_avg|` | W2 = 0.20 |
| `bigram_dev` | `mean( |baseline_avg[b] − mean(current[b])| )` for shared bigrams | W3 = 0.30 |
| `vector_dist` | `euclidean(v_baseline, v_current) / sqrt(len)` | W4 = 0.20 |

> Weights must always sum to 1.0. Tune via constants in `risk_engine.py`.

### Dynamic Threshold

```
threshold = max(flight_std, 0.02) × THRESHOLD_K
```

Where `THRESHOLD_K = 2.5`. Floor of `0.02` prevents zero-threshold edge cases.

### Decision

```
status = "TRUSTED"     if risk < threshold
         "SUSPICIOUS"  otherwise
```

### Informational Metric (not in score)

```
cosine_sim = dot(v1, v2) / (‖v1‖ × ‖v2‖)    ∈ [−1, 1]
```

Used for diagnostics display only.

---

## 5. Trust State Transitions

```
         ┌─────────────────────────────────────────────┐
         │                  IDLE                        │
         │   (system started, no session active)        │
         └───────────────────┬─────────────────────────┘
                             │ user selects Option 2 or 3
                             ▼
         ┌─────────────────────────────────────────────┐
         │              VERIFYING                       │
         │   (keystroke capture in progress)            │
         └────────────┬────────────────────────────────┘
                      │
          ┌───────────┴────────────┐
          │ risk < threshold       │ risk >= threshold
          ▼                        ▼
┌──────────────────┐    ┌──────────────────────────────┐
│    TRUSTED       │    │        SUSPICIOUS             │
│  Access granted  │    │  Access denied, no session    │
│  (Option 2 ends) │    │  Log: ALERT                   │
└────────┬─────────┘    └──────────────────────────────┘
         │ Option 3 only
         ▼
┌──────────────────────────────────────────────────────┐
│                SESSION ACTIVE                         │
│  Timer running (RE_VERIFY_INTERVAL seconds)          │
└──────────────┬───────────────────────────────────────┘
               │ timer fires → capture REVERIFICATION_TEXT
               ▼
┌──────────────────────────────────────────────────────┐
│                RE-VERIFYING                           │
└──────────────┬───────────────────────────────────────┘
               │
   ┌───────────┴──────────────┐
   │ risk < threshold         │ risk >= threshold OR no data
   ▼                          ▼
┌──────────────┐    ┌──────────────────────────────────┐
│ SESSION      │    │         LOCKED                    │
│ ACTIVE       │    │  Session terminated immediately   │
│ (continue)   │    │  Log: ALERT + LOCK                │
└──────────────┘    └──────────────────────────────────┘
```

**Terminal states:** `SUSPICIOUS` (never entered session), `LOCKED` (session terminated).
Both log to `security_log.txt` and require re-registration or re-login to recover.

---

## 6. Module Boundaries and Interfaces

### Internal Interface Contracts

```
keystroke.py  →  returns dict (never raises on capture errors, returns empty dict)
trust_engine.py →  calls risk_engine.compute_multifactor_risk(), never calls ui_console
risk_engine.py  →  pure functions, no I/O, no imports from other project modules
ui_console.py   →  reads from trust_engine (diagnostics), no writes to auth state
main.py         →  orchestrates all modules, owns session state flag
```

### Coupling Rules (enforced by contract, not code)

| From | To | Allowed | Notes |
|---|---|---|---|
| `main.py` | any module | Yes | Orchestrator |
| `trust_engine` | `risk_engine` | Yes | Math delegation only |
| `trust_engine` | `ui_console` | **NO** | No presentation in auth layer |
| `risk_engine` | any project module | **NO** | Pure math only |
| `keystroke` | any project module | **NO** | Pure capture only |
| `ui_console` | `trust_engine` | Read-only | Only for diagnostics display |
| `ui_console` | `risk_engine` | Read-only | Only for threshold display |

---

## 7. Baseline JSON Schema (v2)

```json
{
  "flight_avg":    0.18,
  "flight_std":    0.04,
  "dwell_avg":     0.09,
  "dwell_std":     0.03,
  "bigram_avg":    { "co": 0.19, "nt": 0.21 },
  "rhythm_vector": [0.15, 0.20, 0.18, 0.16, 0.19]
}
```

---

## 8. Configuration Parameters

| Constant | File | Default | Description |
|---|---|---|---|
| `W1` | `risk_engine.py` | `0.30` | Flight time weight |
| `W2` | `risk_engine.py` | `0.20` | Dwell time weight |
| `W3` | `risk_engine.py` | `0.30` | Bigram deviation weight |
| `W4` | `risk_engine.py` | `0.20` | Rhythm vector weight |
| `THRESHOLD_K` | `risk_engine.py` | `2.5` | Adaptive threshold multiplier |
| `MIN_SAMPLES` | `risk_engine.py` | `3` | Min samples for reliable scoring |
| `REGISTRATION_TEXT` | `main.py` | see code | Registration phrase |
| `VERIFICATION_TEXT` | `main.py` | see code | Login verification phrase |
| `REVERIFICATION_TEXT` | `main.py` | see code | Session re-check phrase |
| `RE_VERIFY_INTERVAL` | `main.py` | `30` | Seconds between re-verification |
| `max_interval` | `keystroke.py` | `3.0` | Pause filter cutoff (seconds) |

> **Problem:** Configuration is scattered across 3 files. This is a target for Phase 0.

---

## 9. Failure Modes

| Failure | Trigger | System Behaviour | Recovery |
|---|---|---|---|
| No baseline on login | `baseline_profile.json` absent | Error message, return to menu | Register baseline (Option 1) |
| No keystroke data captured | Listener error or timeout | Error message, abort, log WARN | Retry; check pynput permissions |
| Registration with too few keystrokes | `flight_times` is empty | `ValueError` caught, user prompted | Retype the phrase fully |
| Session re-check with no data | Listener silent during re-verify | Session LOCKED for safety | Re-register |
| `colorama` not installed | Import error | Stub fallback, no colors, no crash | `pip install colorama` |
| `baseline_profile.json` corrupted | `json.JSONDecodeError` | `Exception` caught, error message | Delete file and re-register |
| Malformed baseline (missing keys) | Missing field in dict | `dict.get()` returns safe default | Re-register to overwrite |
| Keyboard listener fails to start | pynput OS permission error | Exception caught, returns empty | Check OS accessibility permissions |
| Log file write fails | Disk full or permission denied | Silently ignored (`except OSError`) | Non-fatal; auth continues |
| Ctrl+C during session | `KeyboardInterrupt` | Session ends cleanly, logs EXIT | N/A |

---

## 10. Constraints

- **Terminal-only.** No GUI, no web interface.
- **No ML.** All scoring is purely statistical.
- **No network.** Fully local — no telemetry, no remote baseline sync.
- **Single-user.** One `baseline_profile.json` per installation.
- **Python 3.10+** required (union type hints: `dict | None`).
- **No dynamic baseline updates.** Registration is the sole truth; mid-session risk does not update the profile.

---

## 11. Non-Goals

- Multi-user authentication or user switching
- Remote / networked authentication
- Password, PIN, or token-based authentication
- Cryptographic signing of the baseline profile
- Integration with OS-level PAM or access control
- Mobile or embedded deployment

---

## 12. Acceptance Criteria

| Scenario | Expected Outcome |
|---|---|
| Register — sufficient data typed | `baseline_profile.json` written, all 6 fields present |
| Register — nothing typed | Error displayed, no file written |
| Login — typing matches baseline | `TRUSTED`, access granted, log INFO |
| Login — typing strongly deviates | `SUSPICIOUS`, access denied, log ALERT |
| Session Monitor — normal re-checks | Session continues, each check logged |
| Session Monitor — deviated re-check | Session LOCKED immediately, log ALERT + LOCK |
| Session Monitor — no data at re-check | Session LOCKED for safety |
| Option 4 — log file absent | Warning shown, no crash |
| Option 5 — no baseline | Warning shown, no crash |
| `colorama` absent | Monochrome output, system fully functional |
| Corrupt `baseline_profile.json` | Error caught, user prompted to re-register |

---

## 13. Phase Roadmap

| Phase | Name | Goal | Status |
|---|---|---|---|
| **Phase 0** | Architecture Hardening | Module boundaries, config centralisation, input validation, coupling removal | **NEXT** |
| **Phase 1** | Multi-baseline Support | Per-user profile storage, username selection at login | Planned |
| **Phase 2** | Adaptive Baseline | Rolling baseline update with configurable decay | Planned |
| **Phase 3** | Challenge Phrases | Configurable registration/verification phrases | Planned |
| **Phase 4** | Export & Reporting | PDF/CSV security report generation | Planned |

---

*Status: FINALIZED — implementation of Phase 0 may proceed.*

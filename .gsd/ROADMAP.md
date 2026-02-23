# ROADMAP.md — Zero Trust Continuous Authentication System

**Reference:** `.gsd/SPEC.md`
**Methodology:** SPEC → PLAN → EXECUTE → VERIFY → COMMIT

---

## Phase 0 — Architecture Hardening ✅ IN PROGRESS

> **Goal:** Stabilise module boundaries, centralise configuration, add input validation, and remove hidden coupling. No feature additions.

### Problems Identified

| # | Problem | Location | Impact |
|---|---|---|---|
| P1 | Config scattered across 3 files | `main.py`, `risk_engine.py`, `keystroke.py` | Hard to tune without hunting |
| P2 | `ui_console.py` imports `risk_engine` for threshold calc | `ui_console.py:298` | Presentation layer depends on math layer — violates boundary |
| P3 | `main.py._lock_session()` imports `colorama` directly | `main.py:266` | Bypasses `ui_console` abstraction |
| P4 | No input validation on baseline data | `trust_engine.py` | Corrupt JSON loads silently with wrong defaults |
| P5 | No minimum keystroke count enforced | `keystroke.py` / `trust_engine.py` | Baseline built on 2 keystrokes is unreliable |
| P6 | `threading.Lock` in main.py unused | `main.py` | Dead code / misleading |
| P7 | Log level strings include trailing spaces for alignment | `ui_console.py` | Inconsistent, fragile alignment |

### Tasks

#### Wave 1 — Foundation (no dependencies)

- [x] P0-T1: Create `config.py` — centralise all constants
- [x] P0-T2: Fix `_lock_session()` — remove bare `colorama` import, use `ui_console`
- [x] P0-T3: Fix `ui_console.view_trust_diagnostics()` — remove `risk_engine` import, accept `threshold` as argument from caller

#### Wave 2 — Validation (depends on Wave 1)

- [ ] P0-T4: Add `validate_baseline()` to `trust_engine.py` — verify required keys + types on load
- [ ] P0-T5: Enforce minimum keystroke count (`MIN_SAMPLES`) in `trust_engine.create_baseline()`
- [ ] P0-T6: Remove unused `threading.Lock` from `main.py`

#### Wave 3 — Cleanup (depends on Wave 2)

- [ ] P0-T7: Update all modules to import constants from `config.py`
- [ ] P0-T8: Normalise log level strings (remove trailing spaces, use fixed format)
- [ ] P0-T9: Full regression — `py_compile` all modules, run logic unit tests

---

## Phase 1 — Multi-Baseline Support (Planned)

> Per-user profile storage. Username selected at login. Profiles stored as `profiles/<username>.json`.

---

## Phase 2 — Adaptive Baseline (Planned)

> Rolling baseline updates with configurable decay factor after each successful TRUSTED session.

---

## Phase 3 — Configurable Challenge Phrases (Planned)

> Registration/verification phrases loaded from config file; custom phrases per deployment.

---

## Phase 4 — Export and Reporting (Planned)

> Security log export to CSV. Session summary report generation.

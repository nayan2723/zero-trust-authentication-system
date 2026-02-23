"""
config.py - Centralised Configuration
======================================
Single source of truth for all tunable constants.
Import from here in every module — never define magic numbers inline.

Weights must sum to 1.0. Dynamic threshold = flight_std * THRESHOLD_K.
"""

# ---------------------------------------------------------------------------
# Risk Engine Weights  (must sum to 1.0)
# ---------------------------------------------------------------------------
W1 = 0.30   # Flight time deviation weight
W2 = 0.20   # Dwell time deviation weight
W3 = 0.30   # Bigram timing deviation weight
W4 = 0.20   # Rhythm vector distance weight

assert abs(W1 + W2 + W3 + W4 - 1.0) < 1e-9, \
    f"Risk weights must sum to 1.0, got {W1 + W2 + W3 + W4}"

# ---------------------------------------------------------------------------
# Dynamic Threshold
# ---------------------------------------------------------------------------
THRESHOLD_K  = 2.5    # threshold = max(flight_std, FLOOR_STD) * THRESHOLD_K
FLOOR_STD    = 0.02   # minimum std to prevent zero threshold

# ---------------------------------------------------------------------------
# Keystroke Capture
# ---------------------------------------------------------------------------
MAX_INTERVAL  = 3.0   # discard any interval / dwell longer than this (seconds)
MIN_SAMPLES   = 5     # minimum flight-time samples for a valid baseline / check

# ---------------------------------------------------------------------------
# Session Monitor
# ---------------------------------------------------------------------------
RE_VERIFY_INTERVAL = 30   # seconds between continuous re-verification prompts

# ---------------------------------------------------------------------------
# Authentication Phrases
# ---------------------------------------------------------------------------
REGISTRATION_TEXT   = "zero trust systems rely on continuous verification"
VERIFICATION_TEXT   = "continuous authentication enhances security posture"
REVERIFICATION_TEXT = "trust no one verify always"

# ---------------------------------------------------------------------------
# Baseline Storage
# ---------------------------------------------------------------------------
BASELINE_FILE = "baseline_profile.json"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_FILE      = "security_log.txt"
LOG_MAX_LINES = 50   # max lines shown in Option 4 log viewer

# ---------------------------------------------------------------------------
# Risk Bar Display
# ---------------------------------------------------------------------------
BAR_WIDTH   = 30          # total blocks in the risk bar
FILLED_CHAR = "\u2588"    # █
EMPTY_CHAR  = "\u2591"    # ░
UI_WIDTH    = 62          # console inner width

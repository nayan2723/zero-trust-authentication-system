"""
risk_engine.py - Multi-Factor Risk Scoring Engine
==================================================
Contains all statistical math for behavioral biometric analysis:

  1. Euclidean distance  – overall rhythm vector deviation
  2. Cosine similarity   – directional rhythm pattern match
  3. Bigram deviation    – per-bigram average timing shift
  4. Multi-factor risk   – weighted combination of all signals
  5. Dynamic threshold   – adapts to user typing consistency

Weights are module-level constants and can be tuned freely.
"""

import math
import statistics

import config


# ---------------------------------------------------------------------------
# Weights and thresholds — sourced from config.py (single source of truth)
# Exposed as module-level names for backward compatibility.
# ---------------------------------------------------------------------------
W1          = config.W1
W2          = config.W2
W3          = config.W3
W4          = config.W4
THRESHOLD_K = config.THRESHOLD_K
MIN_SAMPLES = config.MIN_SAMPLES
_FLOOR_STD  = config.FLOOR_STD


# ---------------------------------------------------------------------------
# Vector math utilities
# ---------------------------------------------------------------------------

def _align_vectors(v1: list, v2: list) -> tuple:
    """
    Align two vectors to the same length by truncating the longer one.
    Returns (v1_aligned, v2_aligned).
    """
    min_len = min(len(v1), len(v2))
    return v1[:min_len], v2[:min_len]


def euclidean_distance(v1: list, v2: list) -> float:
    """
    Compute Euclidean distance between two timing vectors.

    distance = sqrt( sum( (v1_i - v2_i)^2 ) )

    Args:
        v1: Baseline rhythm vector
        v2: Current session rhythm vector

    Returns:
        Euclidean distance (0 = identical, higher = more deviant)
    """
    if not v1 or not v2:
        return 0.0

    a, b = _align_vectors(v1, v2)
    if not a:
        return 0.0

    sq_sum = sum((x - y) ** 2 for x, y in zip(a, b))
    return math.sqrt(sq_sum)


def cosine_similarity(v1: list, v2: list) -> float:
    """
    Compute cosine similarity between two timing vectors.

    similarity = dot(v1, v2) / (||v1|| * ||v2||)

    Args:
        v1: Baseline rhythm vector
        v2: Current session rhythm vector

    Returns:
        Similarity in [-1, 1]; 1 = perfectly aligned patterns
    """
    if not v1 or not v2:
        return 1.0

    a, b = _align_vectors(v1, v2)
    if not a:
        return 1.0

    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x ** 2 for x in a))
    norm_b = math.sqrt(sum(y ** 2 for y in b))

    if norm_a == 0 or norm_b == 0:
        return 1.0 if norm_a == norm_b else 0.0

    return dot / (norm_a * norm_b)


# ---------------------------------------------------------------------------
# Individual signal deviation functions
# ---------------------------------------------------------------------------

def flight_deviation(baseline_avg: float, current_times: list) -> float:
    """
    Absolute difference between baseline and current average flight time.

    Args:
        baseline_avg: Mean flight time from registration
        current_times: List of flight times in current session

    Returns:
        Absolute deviation (seconds)
    """
    if not current_times:
        return 0.0
    current_avg = statistics.mean(current_times)
    return abs(current_avg - baseline_avg)


def dwell_deviation(baseline_avg: float, current_times: list) -> float:
    """
    Absolute difference between baseline and current average dwell time.

    Args:
        baseline_avg: Mean dwell time from registration
        current_times: List of dwell times in current session

    Returns:
        Absolute deviation (seconds)
    """
    if not current_times or baseline_avg == 0.0:
        return 0.0
    current_avg = statistics.mean(current_times)
    return abs(current_avg - baseline_avg)


def bigram_deviation(baseline_bigrams: dict, current_bigrams: dict) -> float:
    """
    Mean absolute deviation in timing across shared bigrams.

    For each bigram present in both profiles, compute:
        |mean(baseline_times) - mean(current_times)|
    
    Then return the mean of all such deviations.

    Args:
        baseline_bigrams: {"co": 0.19, ...}  (averaged values from registration)
        current_bigrams:  {"co": [0.18, 0.21], ...}  (raw lists from current session)

    Returns:
        Mean bigram deviation (seconds); 0 if no shared bigrams
    """
    shared = set(baseline_bigrams.keys()) & set(current_bigrams.keys())
    if not shared:
        return 0.0

    deviations = []
    for bigram in shared:
        b_avg = baseline_bigrams[bigram]  # scalar saved during registration
        c_times = current_bigrams[bigram]
        if not c_times:
            continue
        c_avg = statistics.mean(c_times)
        deviations.append(abs(b_avg - c_avg))

    return statistics.mean(deviations) if deviations else 0.0


def rhythm_vector_distance(baseline_vector: list, current_vector: list) -> float:
    """
    Normalised Euclidean distance between rhythm vectors.

    Normalised by the number of aligned samples so scores are
    comparable regardless of phrase length.

    Args:
        baseline_vector: Ordered flight times from registration
        current_vector:  Ordered flight times from current session

    Returns:
        Normalised distance (0 = identical, higher = more deviant)
    """
    if not baseline_vector or not current_vector:
        return 0.0

    a, b = _align_vectors(baseline_vector, current_vector)
    if not a:
        return 0.0

    raw_dist = euclidean_distance(a, b)
    return raw_dist / math.sqrt(len(a))   # normalise by vector length


# ---------------------------------------------------------------------------
# Multi-factor risk scorer
# ---------------------------------------------------------------------------

def compute_multifactor_risk(
    baseline: dict,
    current_data: dict,
) -> dict:
    """
    Compute the weighted multi-factor risk score.

    Formula:
        risk = w1*flight_dev + w2*dwell_dev + w3*bigram_dev + w4*vector_dist

    Args:
        baseline    : Profile dict loaded from baseline_profile.json
        current_data: Dict returned by keystroke.capture_keystrokes()

    Returns:
        dict with individual component scores and total risk:
        {
            "flight_dev":    float,
            "dwell_dev":     float,
            "bigram_dev":    float,
            "vector_dist":   float,
            "cosine_sim":    float,
            "risk_score":    float,   # weighted total
            "threshold":     float,
            "status":        str,     # "TRUSTED" | "SUSPICIOUS"
        }
    """
    # ---- Extract baseline values ----
    b_flight_avg  = baseline.get("flight_avg", 0.0)
    b_flight_std  = baseline.get("flight_std", 0.05)
    b_dwell_avg   = baseline.get("dwell_avg",  0.0)
    b_bigrams     = baseline.get("bigram_avg", {})
    b_vector      = baseline.get("rhythm_vector", [])

    # ---- Extract current session values ----
    c_flights  = current_data.get("flight_times", [])
    c_dwells   = current_data.get("dwell_times",  [])
    c_bigrams  = current_data.get("bigrams", {})
    c_vector   = current_data.get("rhythm_vector", [])

    # ---- Compute each component ----
    f_dev  = flight_deviation(b_flight_avg, c_flights)
    d_dev  = dwell_deviation(b_dwell_avg,  c_dwells)
    bg_dev = bigram_deviation(b_bigrams,   c_bigrams)
    v_dist = rhythm_vector_distance(b_vector, c_vector)
    cos_sim = cosine_similarity(b_vector, c_vector)

    # ---- Weighted total ----
    risk = (
        W1 * f_dev   +
        W2 * d_dev   +
        W3 * bg_dev  +
        W4 * v_dist
    )

    # ---- Dynamic threshold ----
    threshold = dynamic_threshold(b_flight_std)

    # ---- Decision ----
    status = "TRUSTED" if risk < threshold else "SUSPICIOUS"

    return {
        "flight_dev":  round(f_dev,   4),
        "dwell_dev":   round(d_dev,   4),
        "bigram_dev":  round(bg_dev,  4),
        "vector_dist": round(v_dist,  4),
        "cosine_sim":  round(cos_sim, 4),
        "risk_score":  round(risk,    4),
        "threshold":   round(threshold, 4),
        "status":      status,
    }


# ---------------------------------------------------------------------------
# Dynamic threshold
# ---------------------------------------------------------------------------

def dynamic_threshold(flight_std: float, k: float = THRESHOLD_K) -> float:
    """
    Compute an adaptive authentication threshold.

    threshold = max(flight_std, FLOOR_STD) * k

    A tighter typist (low std) gets a tighter threshold.
    A loose typist (high std) gets more slack.

    Args:
        flight_std: Standard deviation of baseline flight times
        k:          Multiplier (default from config.THRESHOLD_K = 2.5)

    Returns:
        Threshold value (seconds)
    """
    std = max(flight_std, _FLOOR_STD)
    return round(std * k, 4)

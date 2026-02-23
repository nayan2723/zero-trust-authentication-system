"""
trust_engine.py - Behavioral Profile Manager & Trust Decision Layer
====================================================================
Responsibilities:
  - Build and save baseline profiles from raw keystroke data
  - Load profiles from disk
  - Delegate risk computation to risk_engine
  - Expose a clean verify_user() API to main.py

Baseline JSON schema (v2 – multi-metric):
{
  "flight_avg":    0.18,
  "flight_std":    0.04,
  "dwell_avg":     0.09,
  "dwell_std":     0.03,
  "bigram_avg":    { "co": 0.19, "nt": 0.21 },
  "rhythm_vector": [0.15, 0.20, 0.18, ...]
}
"""

import json
import statistics
import os

import risk_engine


class TrustEngine:
    """
    Manages the user's behavioral biometric baseline and trust decisions.
    """

    def __init__(self, baseline_file: str = "baseline_profile.json"):
        self.baseline_file = baseline_file
        # No static threshold – dynamic_threshold() in risk_engine is used instead.

    # ------------------------------------------------------------------
    # Baseline creation
    # ------------------------------------------------------------------

    def create_baseline(self, data: dict) -> dict:
        """
        Build a multi-metric baseline profile from raw keystroke capture data.

        Args:
            data: Dict returned by keystroke.capture_keystrokes()
                  Keys: flight_times, dwell_times, bigrams, rhythm_vector

        Returns:
            Baseline profile dict ready for save_baseline()

        Raises:
            ValueError: If insufficient data was collected
        """
        flight_times  = data.get("flight_times",  [])
        dwell_times   = data.get("dwell_times",   [])
        bigrams       = data.get("bigrams",        {})
        rhythm_vector = data.get("rhythm_vector",  [])

        if not flight_times:
            raise ValueError(
                "No flight time data captured. "
                "Please type more characters for the baseline."
            )

        # ---- Flight time statistics ----
        flight_avg = statistics.mean(flight_times)
        flight_std = (
            statistics.stdev(flight_times) if len(flight_times) > 1 else 0.05
        )

        # ---- Dwell time statistics ----
        if dwell_times:
            dwell_avg = statistics.mean(dwell_times)
            dwell_std = (
                statistics.stdev(dwell_times) if len(dwell_times) > 1 else 0.02
            )
        else:
            dwell_avg, dwell_std = 0.0, 0.02

        # ---- Bigram averages (scalar per bigram for compact storage) ----
        bigram_avg = {}
        for bigram_key, times in bigrams.items():
            if times:
                bigram_avg[bigram_key] = round(statistics.mean(times), 4)

        # ---- Build profile ----
        baseline = {
            "flight_avg":    round(flight_avg, 4),
            "flight_std":    round(flight_std, 4),
            "dwell_avg":     round(dwell_avg,  4),
            "dwell_std":     round(dwell_std,  4),
            "bigram_avg":    bigram_avg,
            "rhythm_vector": [round(t, 4) for t in rhythm_vector],
        }

        return baseline

    # ------------------------------------------------------------------
    # Persist / load
    # ------------------------------------------------------------------

    def save_baseline(self, profile: dict) -> None:
        """
        Persist baseline profile to JSON.

        Args:
            profile: Dict from create_baseline()
        """
        with open(self.baseline_file, "w") as f:
            json.dump(profile, f, indent=2)
        print(f"\n  Baseline profile saved -> {self.baseline_file}")

    def load_baseline(self) -> dict:
        """
        Load baseline profile from JSON.

        Returns:
            Baseline profile dict

        Raises:
            FileNotFoundError: If no baseline exists yet
        """
        if not os.path.exists(self.baseline_file):
            raise FileNotFoundError(
                f"Baseline file '{self.baseline_file}' not found. "
                "Please register a baseline first (Option 1)."
            )
        with open(self.baseline_file, "r") as f:
            return json.load(f)

    # ------------------------------------------------------------------
    # Risk computation
    # ------------------------------------------------------------------

    def compute_risk(self, current_data: dict, baseline: dict) -> dict:
        """
        Compute multi-factor risk score for a typing session.

        Args:
            current_data: Dict from keystroke.capture_keystrokes()
            baseline:     Dict from load_baseline()

        Returns:
            Risk assessment dict from risk_engine.compute_multifactor_risk():
            {
                flight_dev, dwell_dev, bigram_dev, vector_dist,
                cosine_sim, risk_score, threshold, status
            }

        Raises:
            ValueError: If insufficient keystroke data in current session
        """
        if not current_data.get("flight_times"):
            raise ValueError("No keystroke data captured for risk computation.")

        return risk_engine.compute_multifactor_risk(baseline, current_data)

    # ------------------------------------------------------------------
    # Convenience: verify in one call
    # ------------------------------------------------------------------

    def verify_user(self, current_data: dict) -> dict:
        """
        Load baseline and compute risk in a single call.

        Args:
            current_data: Dict from keystroke.capture_keystrokes()

        Returns:
            Risk assessment dict, or error dict if baseline missing
        """
        try:
            baseline = self.load_baseline()
            return self.compute_risk(current_data, baseline)
        except FileNotFoundError as e:
            return {"error": str(e)}


# ---------------------------------------------------------------------------
# Module-level convenience functions (backward-compatible)
# ---------------------------------------------------------------------------

def create_baseline(data: dict) -> dict:
    """Module-level shortcut for TrustEngine().create_baseline()."""
    return TrustEngine().create_baseline(data)


def save_baseline(profile: dict) -> None:
    """Module-level shortcut for TrustEngine().save_baseline()."""
    TrustEngine().save_baseline(profile)


def load_baseline() -> dict:
    """Module-level shortcut for TrustEngine().load_baseline()."""
    return TrustEngine().load_baseline()


def compute_risk(current_data: dict, baseline: dict) -> dict:
    """Module-level shortcut for TrustEngine().compute_risk()."""
    return TrustEngine().compute_risk(current_data, baseline)

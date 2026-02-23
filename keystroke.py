"""
keystroke.py - Multi-Metric Keystroke Capture Engine
=====================================================
Captures the following behavioral biometric signals:
  - Flight times  : interval between consecutive key presses
  - Dwell times   : duration each key is held down (release - press)
  - Bigram timings: flight time for specific consecutive character pairs
  - Rhythm vector : ordered list of all flight times (full temporal sequence)

Returns a structured dict for downstream risk analysis.
"""

import time
from pynput import keyboard
import threading
import sys


# Bigrams of interest – can be extended for any passphrase
TARGET_BIGRAMS = [
    "ze", "er", "ro", "co", "on", "nt", "ti", "in",
    "se", "ec", "ur", "ri", "it", "tr", "ru", "us",
    "st", "em", "au", "th", "he", "en", "ca", "at",
    "io", "an",
]


class KeystrokeCapture:
    """
    Dual-listener keystroke capture.

    Registers both on_press and on_release callbacks so that:
      - press timestamps  → flight times & bigram times
      - release timestamps → dwell times
    """

    def __init__(self):
        # --- timing accumulators ---
        self.flight_times = []      # interval between consecutive presses
        self.dwell_times = []       # how long each key was held
        self.bigrams = {}           # {"co": [0.18, 0.20], ...}
        self.rhythm_vector = []     # same as flight_times (explicit copy for vector math)

        # --- internal state ---
        self._press_times = {}      # key → press timestamp (for dwell)
        self._last_press_time = None
        self._prev_char = None      # previous character (for bigram detection)
        self._typed_chars = []      # running list of typed characters

        self.capturing = False
        self.capture_complete = threading.Event()
        self.listener = None

        # Filter out pauses longer than this (seconds)
        self.max_interval = 3.0

        # Escape sequence state (:q to finish)
        self._recent_chars = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def capture_keystrokes(self, prompt_text: str) -> dict:
        """
        Capture multi-metric keystroke data for the given prompt.

        Args:
            prompt_text (str): Sentence the user is asked to type.

        Returns:
            dict with keys:
                flight_times  (list[float])
                dwell_times   (list[float])
                bigrams       (dict[str, list[float]])
                rhythm_vector (list[float])
                chars         (str)
        """
        # Reset state
        self.flight_times = []
        self.dwell_times = []
        self.bigrams = {}
        self.rhythm_vector = []
        self._press_times = {}
        self._last_press_time = None
        self._prev_char = None
        self._typed_chars = []
        self._recent_chars = []
        self.capturing = True
        self.capture_complete.clear()

        print(f"\nType the following sentence:")
        print(f'  "{prompt_text}"')
        print("Type ':q' when finished.\n")
        print("Start typing...")

        try:
            sys.stdin.flush()
        except Exception:
            pass

        try:
            self.listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release,
            )
            self.listener.daemon = True
            self.listener.start()
            # Wait up to 90 seconds for the user to finish
            self.capture_complete.wait(timeout=90)
        except Exception as e:
            print(f"Keyboard listener error: {e}")
            return self._empty_result()

        # Clean up listener
        if self.listener:
            try:
                self.listener.stop()
                self.listener.join(timeout=2.0)
            except Exception:
                pass

        time.sleep(0.2)

        try:
            sys.stdin.flush()
        except Exception:
            pass

        return {
            "flight_times":  self.flight_times,
            "dwell_times":   self.dwell_times,
            "bigrams":       self.bigrams,
            "rhythm_vector": list(self.flight_times),  # identical sequence, separate reference
            "chars":         "".join(self._typed_chars),
        }

    # ------------------------------------------------------------------
    # Internal event handlers
    # ------------------------------------------------------------------

    def _on_key_press(self, key):
        """Record key-press timestamp; derive flight time and bigram timing."""
        if not self.capturing:
            return

        current_time = time.time()

        try:
            char = key.char
            if char is None:
                return
        except AttributeError:
            # Special key (Shift, Ctrl, …) – skip
            return

        char_lower = char.lower()
        self._typed_chars.append(char_lower)

        # --- Escape sequence detection (:q) ---
        self._recent_chars.append(char_lower)
        if len(self._recent_chars) > 2:
            self._recent_chars.pop(0)
        if (len(self._recent_chars) == 2
                and self._recent_chars[0] == ':'
                and self._recent_chars[1] == 'q'):
            self._finish_capture()
            return

        # --- Flight time (interval between consecutive presses) ---
        if self._last_press_time is not None:
            flight = current_time - self._last_press_time
            if flight <= self.max_interval:
                self.flight_times.append(round(flight, 4))
                self.rhythm_vector.append(round(flight, 4))

                # --- Bigram timing ---
                if self._prev_char is not None:
                    bigram_key = self._prev_char + char_lower
                    if bigram_key in TARGET_BIGRAMS:
                        self.bigrams.setdefault(bigram_key, []).append(round(flight, 4))

        # Update state for next keypress
        self._last_press_time = current_time
        self._prev_char = char_lower

        # Record press time for dwell computation
        self._press_times[char_lower + str(current_time)] = current_time

    def _on_key_release(self, key):
        """Record key-release timestamp; compute dwell time."""
        if not self.capturing:
            return

        release_time = time.time()

        try:
            char = key.char
            if char is None:
                return
        except AttributeError:
            return

        char_lower = char.lower()

        # Find the most recent unmatched press for this character
        # Key in _press_times is "char + str(press_timestamp)"
        candidates = [
            (k, v) for k, v in self._press_times.items()
            if k.startswith(char_lower)
        ]
        if candidates:
            # Take the earliest unmatched press
            candidates.sort(key=lambda x: x[1])
            key_id, press_time = candidates[0]
            del self._press_times[key_id]

            dwell = release_time - press_time
            if 0 < dwell <= self.max_interval:
                self.dwell_times.append(round(dwell, 4))

    def _finish_capture(self):
        """Signal end of capture session."""
        self.capturing = False
        self.capture_complete.set()
        n_flight = len(self.flight_times)
        n_dwell  = len(self.dwell_times)
        n_bigram = sum(len(v) for v in self.bigrams.values())
        print(f"\n  ✓ Captured {n_flight} flight times | "
              f"{n_dwell} dwell times | "
              f"{n_bigram} bigram samples across {len(self.bigrams)} bigrams.")
        time.sleep(0.1)

    @staticmethod
    def _empty_result() -> dict:
        return {
            "flight_times":  [],
            "dwell_times":   [],
            "bigrams":       {},
            "rhythm_vector": [],
            "chars":         "",
        }


# ---------------------------------------------------------------------------
# Convenience module-level function
# ---------------------------------------------------------------------------

def capture_keystrokes(prompt_text: str) -> dict:
    """
    Capture multi-metric keystroke data.

    Returns:
        dict with flight_times, dwell_times, bigrams, rhythm_vector, chars
    """
    capture = KeystrokeCapture()
    return capture.capture_keystrokes(prompt_text)


# Legacy shim so any old code calling capture_keystroke_intervals still works.
def capture_keystroke_intervals(prompt_text: str) -> list:
    """Backward-compatible shim. Returns flight_times only."""
    return capture_keystrokes(prompt_text).get("flight_times", [])

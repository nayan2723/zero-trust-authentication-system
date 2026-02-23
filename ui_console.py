"""
ui_console.py - Zero Trust Security Console UI Helpers
=======================================================
Provides ALL terminal presentation utilities:
  - Screen clearing
  - Colorized output via colorama
  - Security console header
  - Risk score visualization bar
  - Security event logging to security_log.txt

IMPORTANT: This module contains ZERO authentication logic.
           It is purely a presentation / logging layer.
"""

import os
import sys
import time
import datetime

import config

# ---------------------------------------------------------------------------
# Colorama initialization – graceful fallback if not installed
# ---------------------------------------------------------------------------
try:
    from colorama import init as _colorama_init, Fore, Back, Style
    _colorama_init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False

    # Stub out color constants so the rest of the code works unchanged
    class _Stub:
        def __getattr__(self, _):
            return ""
    Fore  = _Stub()
    Back  = _Stub()
    Style = _Stub()


# ---------------------------------------------------------------------------
# Constants — sourced from config.py (single source of truth)
# ---------------------------------------------------------------------------
LOG_FILE   = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           config.LOG_FILE)
WIDTH      = config.UI_WIDTH
BAR_WIDTH  = config.BAR_WIDTH
FILLED_CHAR = config.FILLED_CHAR
EMPTY_CHAR  = config.EMPTY_CHAR

HEADER = f"""
{Fore.CYAN}{'=' * WIDTH}
{'  ZERO TRUST CONTINUOUS AUTHENTICATION ENGINE':^{WIDTH}}
{'  Behavioral Biometrics Security Console  v2.0':^{WIDTH}}
{'=' * WIDTH}{Style.RESET_ALL}
{Fore.GREEN}  Behavioral Biometric Monitoring : ACTIVE
  Trust Engine Status             : OPERATIONAL
  Continuous Re-Verification      : ENABLED{Style.RESET_ALL}
{Fore.CYAN}{'=' * WIDTH}{Style.RESET_ALL}"""


# ---------------------------------------------------------------------------
# 1. Screen refresh
# ---------------------------------------------------------------------------

def clear_screen() -> None:
    """Clear the terminal screen (cross-platform)."""
    os.system("cls" if os.name == "nt" else "clear")


# ---------------------------------------------------------------------------
# 2. Header
# ---------------------------------------------------------------------------

def print_header() -> None:
    """Print the security console header."""
    print(HEADER)


def section_banner(title: str, color: str = "") -> None:
    """Print a section divider with a title."""
    reset = Style.RESET_ALL if COLORS_AVAILABLE else ""
    bar   = "─" * WIDTH
    print(f"\n{color}{bar}")
    print(f"  {title}")
    print(f"{bar}{reset}")


# ---------------------------------------------------------------------------
# 3. Color-coded status printers
# ---------------------------------------------------------------------------

def print_trusted(message: str) -> None:
    """Print a TRUSTED / success message in green."""
    print(f"{Fore.GREEN}  {message}{Style.RESET_ALL}")


def print_alert(message: str) -> None:
    """Print a SUSPICIOUS / alert message in red."""
    print(f"{Fore.RED}  {message}{Style.RESET_ALL}")


def print_warning(message: str) -> None:
    """Print a WARNING message in yellow."""
    print(f"{Fore.YELLOW}  {message}{Style.RESET_ALL}")


def print_info(message: str) -> None:
    """Print an INFO/neutral message in cyan."""
    print(f"{Fore.CYAN}  {message}{Style.RESET_ALL}")


def print_label(label: str, value: str, width: int = 40) -> None:
    """Print a key-value pair with label in white and value in cyan."""
    print(f"  {label:<{width}}{Fore.CYAN}{value}{Style.RESET_ALL}")


# ---------------------------------------------------------------------------
# 4. Risk score visualization bar
# ---------------------------------------------------------------------------

# BAR_WIDTH, FILLED_CHAR, EMPTY_CHAR are imported from config at module level above.


def display_risk_bar(risk: float, threshold: float) -> None:
    """
    Display a visual risk progress bar.

    Normalises the risk score against 2× the threshold so that a score
    exactly at threshold lands at 50% and critical scores fill the bar.
    The bar colour shifts green → yellow → red as risk rises.

    Args:
        risk      : Weighted risk score from risk_engine
        threshold : Adaptive threshold from risk_engine
    """
    # Normalise: we consider 2 × threshold as the "full bar" point
    scale        = max(threshold * 2, 0.001)
    ratio        = min(risk / scale, 1.0)
    filled       = int(round(ratio * BAR_WIDTH))
    empty        = BAR_WIDTH - filled
    pct          = int(round(ratio * 100))

    bar_str = FILLED_CHAR * filled + EMPTY_CHAR * empty

    # Colour the bar based on severity
    if risk < threshold * 0.6:
        bar_color = Fore.GREEN
    elif risk < threshold:
        bar_color = Fore.YELLOW
    else:
        bar_color = Fore.RED

    reset = Style.RESET_ALL
    print(f"\n  Risk Score   : {Fore.CYAN}{risk:.4f}{reset}  "
          f"Threshold: {Fore.CYAN}{threshold:.4f}{reset}")
    print(f"  Risk Level   : {bar_color}{bar_str}{reset}  {pct}%")


# ---------------------------------------------------------------------------
# 5. Security event logging
# ---------------------------------------------------------------------------

def log_event(level: str, message: str) -> None:
    """
    Append a timestamped security event to security_log.txt.

    Args:
        level   : "INFO" | "ALERT" | "LOCK" | "WARN" | "BOOT" | "EXIT"
        message : Human-readable event description
    """
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{ts}] [{level:<5}] {message}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except OSError:
        pass   # Logging must never crash the auth flow


# ---------------------------------------------------------------------------
# 6. Formatted risk table (replaces plain _print_risk_table in main.py)
# ---------------------------------------------------------------------------

def print_risk_table(assessment: dict, label: str = "AUTHENTICATION RESULT") -> None:
    """
    Print a color-coded risk breakdown table and risk bar.

    Args:
        assessment : Dict from TrustEngine.compute_risk() / risk_engine
        label      : Title for the table
    """
    status    = assessment.get("status", "UNKNOWN")
    trusted   = (status == "TRUSTED")
    hdr_color = Fore.GREEN if trusted else Fore.RED
    reset     = Style.RESET_ALL

    def row(metric, value):
        print(f"  {metric:<32} {Fore.CYAN}{value}{reset}")

    print(f"\n{hdr_color}{'=' * WIDTH}{reset}")
    print(f"{hdr_color}  {label:^{WIDTH - 2}}{reset}")
    print(f"{hdr_color}{'=' * WIDTH}{reset}")

    print(f"  {'Metric':<32} {'Score'}")
    print(f"  {'─' * (WIDTH - 2)}")
    row("Flight Time Deviation",    f"{assessment.get('flight_dev',  0):.4f} s")
    row("Dwell Time Deviation",     f"{assessment.get('dwell_dev',   0):.4f} s")
    row("Bigram Timing Deviation",  f"{assessment.get('bigram_dev',  0):.4f} s")
    row("Rhythm Vector Distance",   f"{assessment.get('vector_dist', 0):.4f}")
    row("Cosine Similarity",        f"{assessment.get('cosine_sim',  0):.4f}")
    print(f"  {'─' * (WIDTH - 2)}")
    row("Weighted Risk Score",      f"{assessment.get('risk_score',  0):.4f}")
    row("Adaptive Threshold",       f"{assessment.get('threshold',   0):.4f}")
    print(f"  {'─' * (WIDTH - 2)}")

    # Risk bar
    display_risk_bar(
        assessment.get("risk_score", 0.0),
        max(assessment.get("threshold", 0.1), 0.001),
    )

    # Status line
    print()
    if trusted:
        print_trusted(f"[TRUSTED]   Identity verified. Behavioral pattern matches baseline.")
    else:
        print_alert(f"[ALERT]     Behavioral anomaly detected. Pattern does NOT match baseline.")

    print(f"{hdr_color}{'=' * WIDTH}{reset}")


# ---------------------------------------------------------------------------
# 7. Log viewer
# ---------------------------------------------------------------------------

def view_security_logs(max_lines: int = 40) -> None:
    """
    Display the last N lines of security_log.txt in the terminal.

    Args:
        max_lines: Maximum number of recent log entries to display
    """
    section_banner("SECURITY EVENT LOG", Fore.CYAN)
    if not os.path.exists(LOG_FILE):
        print_warning("No security log file found yet. Events will appear after first use.")
        return

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if not lines:
            print_info("Log file is empty.")
            return

        recent = lines[-max_lines:]
        print(f"{Fore.CYAN}  Showing last {len(recent)} of {len(lines)} events:{Style.RESET_ALL}\n")

        for line in recent:
            line = line.rstrip()
            if "[ALERT]" in line or "[LOCK ]" in line:
                print(f"  {Fore.RED}{line}{Style.RESET_ALL}")
            elif "[WARN ]" in line:
                print(f"  {Fore.YELLOW}{line}{Style.RESET_ALL}")
            elif "[BOOT ]" in line or "[INFO ]" in line:
                print(f"  {Fore.GREEN}{line}{Style.RESET_ALL}")
            else:
                print(f"  {Fore.CYAN}{line}{Style.RESET_ALL}")

    except OSError as e:
        print_alert(f"Could not read log file: {e}")


# ---------------------------------------------------------------------------
# 8. Trust Engine diagnostic display
# ---------------------------------------------------------------------------

def view_trust_diagnostics(
    trust_engine,
    last_assessment: dict | None = None,
    threshold: float | None = None,
) -> None:
    """
    Display read-only diagnostic metrics from the loaded baseline profile.

    Args:
        trust_engine    : TrustEngine instance (for .load_baseline())
        last_assessment : Most recent risk assessment dict, or None
        threshold       : Pre-computed adaptive threshold (avoids importing
                          risk_engine here — caller computes and passes it)
    """
    section_banner("TRUST ENGINE DIAGNOSTICS  [READ-ONLY]", Fore.CYAN)

    try:
        baseline = trust_engine.load_baseline()
    except FileNotFoundError:
        print_warning("No baseline profile found. Please register first (Option 1).")
        return

    # Threshold comes from the caller; fall back to config-based calculation
    # only if not provided, to keep this module free of risk_engine imports.
    if threshold is None:
        flight_std = baseline.get("flight_std", config.FLOOR_STD)
        threshold  = max(flight_std, config.FLOOR_STD) * config.THRESHOLD_K

    print(f"\n{Fore.CYAN}  --- Baseline Profile ---{Style.RESET_ALL}")
    print_label("Flight time average  :",   f"{baseline.get('flight_avg', 0):.4f} s")
    print_label("Flight time std dev  :",   f"{baseline.get('flight_std', 0):.4f} s")
    print_label("Dwell time average   :",   f"{baseline.get('dwell_avg',  0):.4f} s")
    print_label("Dwell time std dev   :",   f"{baseline.get('dwell_std',  0):.4f} s")
    print_label("Adaptive threshold   :",   f"{threshold:.4f}")
    print_label("Bigrams in profile   :",   str(len(baseline.get("bigram_avg", {}))))
    print_label("Rhythm vector length :",   str(len(baseline.get("rhythm_vector", []))))

    bigrams = baseline.get("bigram_avg", {})
    if bigrams:
        print(f"\n{Fore.CYAN}  --- Bigram Averages ---{Style.RESET_ALL}")
        for i, (bg, avg) in enumerate(list(bigrams.items())[:10]):
            print(f"  {Fore.WHITE}  '{bg}'{Style.RESET_ALL} -> {Fore.CYAN}{avg:.4f} s{Style.RESET_ALL}")
        if len(bigrams) > 10:
            print(f"  {Fore.CYAN}  ... and {len(bigrams) - 10} more{Style.RESET_ALL}")

    if last_assessment:
        print(f"\n{Fore.CYAN}  --- Last Session Result ---{Style.RESET_ALL}")
        print_label("Risk score  :",  f"{last_assessment.get('risk_score', 0):.4f}")
        print_label("Threshold   :",  f"{last_assessment.get('threshold',  0):.4f}")
        status = last_assessment.get("status", "N/A")
        if status == "TRUSTED":
            print_label("Status      :", f"{Fore.GREEN}{status}{Style.RESET_ALL}")
        else:
            print_label("Status      :", f"{Fore.RED}{status}{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.YELLOW}  No session data available. Run Option 2 or 3 first.{Style.RESET_ALL}")


# ---------------------------------------------------------------------------
# 9. Countdown display
# ---------------------------------------------------------------------------

def countdown_display(seconds: int, label: str = "Re-verification") -> bool:
    """
    Display a live countdown. Returns False if interrupted by Ctrl+C.

    Args:
        seconds : Total seconds to count down
        label   : Label to show in the countdown line

    Returns:
        True if countdown completed normally, False if Ctrl+C was pressed
    """
    print(f"\n{Fore.CYAN}  Monitoring Session...{Style.RESET_ALL}")
    print(f"  {label} in: {seconds}s")
    print(f"  (Press Ctrl+C to end session early.)")
    try:
        for remaining in range(seconds, 0, -1):
            bar_w   = 20
            filled  = int((seconds - remaining) / seconds * bar_w)
            bar     = "\u2588" * filled + "\u2591" * (bar_w - filled)
            print(
                f"  {Fore.CYAN}[{bar}]{Style.RESET_ALL} "
                f"{Fore.YELLOW}{remaining:>3}s{Style.RESET_ALL} remaining...",
                end="\r",
                flush=True,
            )
            time.sleep(1)
        print(" " * 70, end="\r")   # clear line
        return True
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}  Session ended by user (Ctrl+C).{Style.RESET_ALL}")
        return False

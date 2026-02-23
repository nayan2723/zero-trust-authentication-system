"""
main.py - Zero Trust Security Console  v2.0
============================================
Entry point and orchestrator for the multi-metric behavioral
biometric authentication engine.

Menu (5 options):
  1. Initialize Behavioral Profile   (register baseline)
  2. Activate Continuous Authentication (one-shot verify)
  3. Session Monitor                 (continuous re-verification)
  4. View Security Logs
  5. View Trust Engine Metrics
  6. Exit System

PRESENTATION ONLY changes vs v1:
  - colorama color coding
  - risk bar visualization
  - security event logging
  - 6-option menu (added log viewer + diagnostics)
  - clear screen on each menu refresh
  - professional ASCII header

Authentication logic is 100% UNCHANGED.
"""

import os
import time
import threading

from keystroke import capture_keystrokes
from trust_engine import TrustEngine
import ui_console as ui


# ---------------------------------------------------------------------------
# Configuration  (authentication logic – DO NOT CHANGE)
# ---------------------------------------------------------------------------

REGISTRATION_TEXT   = "zero trust systems rely on continuous verification"
VERIFICATION_TEXT   = "continuous authentication enhances security posture"
REVERIFICATION_TEXT = "trust no one verify always"
RE_VERIFY_INTERVAL  = 30


# ---------------------------------------------------------------------------
# Core authentication class
# ---------------------------------------------------------------------------

class ZeroTrustAuthSystem:
    """
    Orchestrates keystroke capture, trust-engine calls, and session management.
    Presentation delegated to ui_console; auth logic untouched.
    """

    def __init__(self):
        self.trust_engine      = TrustEngine()
        self._session_active   = False
        self._session_lock     = threading.Lock()
        self._last_assessment  = None   # held in memory for diagnostics display

    # ------------------------------------------------------------------
    # Menu
    # ------------------------------------------------------------------

    def display_menu(self) -> None:
        ui.clear_screen()
        ui.print_header()
        ui.print_info("Main Menu – Select an operation:")
        print()
        print("  [1]  Initialize Behavioral Profile")
        print("  [2]  Activate Continuous Authentication")
        print("  [3]  Session Monitor  (continuous re-verification)")
        print("  [4]  View Security Logs")
        print("  [5]  View Trust Engine Metrics")
        print("  [6]  Exit System")
        print(f"\n  {'─' * 58}")

    # ------------------------------------------------------------------
    # Option 1 – Register Baseline
    # ------------------------------------------------------------------

    def register_baseline(self) -> None:
        ui.clear_screen()
        ui.print_header()
        ui.section_banner("[ 1 ]  INITIALIZE BEHAVIORAL PROFILE")

        ui.print_info("Capturing your natural typing dynamics...")
        ui.print_info("Please type the phrase below naturally – do not rush.\n")

        try:
            data = capture_keystrokes(REGISTRATION_TEXT)

            if not data["flight_times"]:
                ui.print_alert("No keystroke data captured. Please try again.")
                ui.log_event("WARN ", "Baseline registration failed – no data captured")
                return

            baseline = self.trust_engine.create_baseline(data)
            self.trust_engine.save_baseline(baseline)

            # ---- Summary table ----
            threshold = baseline["flight_std"] * 2.5
            ui.print_trusted("Behavioral profile initialized successfully!")
            print()
            ui.print_label("Flight time average  :", f"{baseline['flight_avg']:.4f} s")
            ui.print_label("Flight time std dev  :", f"{baseline['flight_std']:.4f} s")
            ui.print_label("Dwell time average   :", f"{baseline['dwell_avg']:.4f} s")
            ui.print_label("Bigrams captured     :", str(len(baseline["bigram_avg"])))
            ui.print_label("Rhythm vector length :", str(len(baseline["rhythm_vector"])))
            ui.print_label("Adaptive threshold   :", f"{threshold:.4f}")

            ui.log_event("INFO ", "Baseline behavioral profile registered successfully")

        except ValueError as e:
            ui.print_alert(f"Registration failed: {e}")
            ui.log_event("WARN ", f"Baseline registration error: {e}")
        except Exception as e:
            ui.print_alert(f"Unexpected error: {e}")
            ui.log_event("WARN ", f"Unexpected registration error: {e}")

    # ------------------------------------------------------------------
    # Option 2 – One-shot Authentication
    # ------------------------------------------------------------------

    def login_and_verify(self) -> dict | None:
        ui.clear_screen()
        ui.print_header()
        ui.section_banner("[ 2 ]  ACTIVATE CONTINUOUS AUTHENTICATION")

        try:
            baseline = self.trust_engine.load_baseline()
        except FileNotFoundError as e:
            ui.print_alert(str(e))
            ui.log_event("WARN ", "Authentication attempted without baseline profile")
            return None

        ui.print_info("Identity verification in progress...")

        try:
            data = capture_keystrokes(VERIFICATION_TEXT)
            if not data["flight_times"]:
                ui.print_alert("No keystroke data captured. Please try again.")
                return None

            # --- Core auth call (UNCHANGED) ---
            assessment = self.trust_engine.compute_risk(data, baseline)
            self._last_assessment = assessment

            # --- UI: colored table + risk bar ---
            ui.print_risk_table(assessment, "AUTHENTICATION RESULT")

            if assessment["status"] == "TRUSTED":
                ui.print_trusted("Access GRANTED. Welcome.")
                ui.log_event("INFO ", f"Session TRUSTED  | risk={assessment['risk_score']:.4f}  threshold={assessment['threshold']:.4f}")
            else:
                ui.print_alert("Access DENIED. Behavioral anomaly detected.")
                ui.print_alert("Session Locked. Please re-register or contact admin.")
                ui.log_event("ALERT", f"Session SUSPICIOUS | risk={assessment['risk_score']:.4f}  threshold={assessment['threshold']:.4f}")

            return assessment

        except ValueError as e:
            ui.print_alert(f"Verification error: {e}")
            ui.log_event("WARN ", f"Verification error: {e}")
        except Exception as e:
            ui.print_alert(f"Unexpected error: {e}")
            ui.log_event("WARN ", f"Unexpected verification error: {e}")

        return None

    # ------------------------------------------------------------------
    # Option 3 – Continuous Session Monitor
    # ------------------------------------------------------------------

    def session_monitor(self) -> None:
        ui.clear_screen()
        ui.print_header()
        ui.section_banner("[ 3 ]  SESSION MONITOR – Continuous Re-Verification")

        # ---- Step 1: Load baseline ----
        try:
            baseline = self.trust_engine.load_baseline()
        except FileNotFoundError as e:
            ui.print_alert(str(e))
            ui.log_event("WARN ", "Session Monitor started without baseline profile")
            return

        # ---- Step 2: Initial login ----
        ui.print_info("Step 1 of 2 – Initial identity verification...")
        data = capture_keystrokes(VERIFICATION_TEXT)

        if not data["flight_times"]:
            ui.print_alert("No keystroke data. Aborting session.")
            ui.log_event("WARN ", "Session Monitor aborted – no keystroke data at login")
            return

        assessment = self.trust_engine.compute_risk(data, baseline)
        self._last_assessment = assessment
        ui.print_risk_table(assessment, "INITIAL VERIFICATION")

        if assessment["status"] != "TRUSTED":
            ui.print_alert("Initial verification FAILED. Session not started.")
            ui.log_event("ALERT", f"Session Monitor initial verification FAILED | risk={assessment['risk_score']:.4f}")
            return

        ui.print_trusted("Initial verification passed. Session is now ACTIVE.")
        ui.print_info(f"Re-verification every {RE_VERIFY_INTERVAL} seconds.")
        ui.print_info("(Press Ctrl+C at any time to end the session.)\n")
        ui.log_event("INFO ", "Session Monitor started – initial verification TRUSTED")

        # ---- Step 3: Continuous re-verification loop ----
        self._session_active = True
        recheck_count = 0

        while self._session_active:
            # Cosmetic countdown display (no logic change)
            completed = ui.countdown_display(RE_VERIFY_INTERVAL, "Re-verification")
            if not completed:
                self._session_active = False
                ui.log_event("INFO ", "Session ended by user (Ctrl+C)")
                break

            if not self._session_active:
                break

            recheck_count += 1
            ui.section_banner(f"RE-VERIFICATION CHECK #{recheck_count}", "")
            ui.print_info("Your session requires periodic identity confirmation.")

            data = capture_keystrokes(REVERIFICATION_TEXT)

            if not data["flight_times"]:
                ui.print_warning("No typing data received. Locking session for safety.")
                ui.log_event("LOCK ", f"Re-check #{recheck_count} – no data received, session locked")
                self._lock_session()
                break

            # --- Core auth call (UNCHANGED) ---
            check = self.trust_engine.compute_risk(data, baseline)
            self._last_assessment = check
            ui.print_risk_table(check, f"RE-VERIFICATION #{recheck_count} RESULT")

            if check["status"] == "TRUSTED":
                ui.print_trusted(f"Re-verification #{recheck_count} passed. Session continues.")
                ui.log_event("INFO ", f"Re-check #{recheck_count} TRUSTED | risk={check['risk_score']:.4f}")
            else:
                ui.print_alert(f"Behavioral deviation detected during re-check #{recheck_count}!")
                ui.log_event("ALERT", f"Re-check #{recheck_count} SUSPICIOUS | risk={check['risk_score']:.4f}")
                self._lock_session()
                break

        if self._session_active:
            ui.print_info("Session ended normally.")
            self._session_active = False
            ui.log_event("INFO ", "Session Monitor ended normally")

    def _countdown(self, seconds: int) -> None:
        """Internal countdown (delegates to ui_console for cosmetics)."""
        completed = ui.countdown_display(seconds, "Re-verification")
        if not completed:
            self._session_active = False

    def _lock_session(self) -> None:
        """Immediately terminate the session – presentation only, logic unchanged."""
        self._session_active = False
        from colorama import Fore, Style
        print(f"\n{Fore.RED}{'!' * 62}{Style.RESET_ALL}")
        ui.print_alert("  SESSION LOCKED")
        ui.print_alert("  Typing behavior deviated significantly from your baseline.")
        ui.print_alert("  Access has been REVOKED for security.")
        ui.print_alert("  Please re-register or contact your system administrator.")
        print(f"{Fore.RED}{'!' * 62}{Style.RESET_ALL}")
        ui.log_event("LOCK ", "SESSION LOCKED – behavioral anomaly exceeded threshold")

    # ------------------------------------------------------------------
    # Option 4 – View Security Logs
    # ------------------------------------------------------------------

    def view_logs(self) -> None:
        ui.clear_screen()
        ui.print_header()
        ui.view_security_logs(max_lines=50)

    # ------------------------------------------------------------------
    # Option 5 – Trust Engine Diagnostics (read-only)
    # ------------------------------------------------------------------

    def view_diagnostics(self) -> None:
        ui.clear_screen()
        ui.print_header()
        ui.view_trust_diagnostics(self.trust_engine, self._last_assessment)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Application main loop."""
        ui.log_event("BOOT ", "Zero Trust Authentication System v2.0 started")
        ui.print_info("Initializing Zero Trust Security Console...")
        time.sleep(0.5)

        while True:
            try:
                self.display_menu()
                choice = self._get_menu_choice()

                if   choice == "1":
                    self.register_baseline()
                elif choice == "2":
                    self.login_and_verify()
                elif choice == "3":
                    self.session_monitor()
                elif choice == "4":
                    self.view_logs()
                elif choice == "5":
                    self.view_diagnostics()
                elif choice == "6":
                    ui.clear_screen()
                    ui.print_header()
                    ui.print_info("Exiting Zero Trust Security Console.")
                    ui.print_info("Stay secure. Trust nothing. Verify everything.")
                    ui.log_event("EXIT ", "Zero Trust Authentication System shut down")
                    print()
                    break

                self._safe_pause()

            except KeyboardInterrupt:
                print("\n")
                ui.print_warning("Keyboard interrupt received. Exiting...")
                ui.log_event("EXIT ", "System exited via KeyboardInterrupt")
                break
            except Exception as e:
                ui.print_alert(f"Unexpected error: {e}")
                ui.log_event("WARN ", f"Unhandled exception in main loop: {e}")
                self._safe_pause()

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _get_menu_choice(self) -> str:
        while True:
            try:
                choice = input("\n  Enter your choice (1-6): ").strip()
                if choice in ("1", "2", "3", "4", "5", "6"):
                    return choice
                ui.print_warning("Invalid choice. Please enter 1 through 6.")
            except (EOFError, KeyboardInterrupt):
                return "6"

    def _safe_pause(self) -> None:
        try:
            input("\n  Press Enter to return to menu...")
        except (EOFError, KeyboardInterrupt):
            pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    try:
        ZeroTrustAuthSystem().run()
    except Exception as e:
        ui.print_alert(f"Fatal system error: {e}")
        ui.log_event("WARN ", f"Fatal system error: {e}")


if __name__ == "__main__":
    main()

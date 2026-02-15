import os
from keystroke import capture_keystroke_intervals
from trust_engine import TrustEngine


class ZeroTrustAuthSystem:
    def __init__(self):
        self.trust_engine = TrustEngine()
        self.registration_text = "zero trust systems rely on continuous verification"
        self.verification_text = "continuous authentication enhances security posture"
    
    def display_menu(self):
        """Display the main menu options."""
        print("\n" + "="*60)
        print("    ZERO TRUST CONTINUOUS AUTHENTICATION SYSTEM")
        print("="*60)
        print("This system demonstrates Zero Trust principles through")
        print("keystroke behavioral biometrics for continuous authentication.")
        print("="*60)
        print("1. Register Baseline")
        print("2. Login and Verify")
        print("3. Exit")
        print("="*60)
    
    def register_baseline(self):
        """Register user's typing baseline."""
        print("\n--- BASELINE REGISTRATION ---")
        print("Creating your unique typing profile...")
        
        try:
            # Capture keystroke intervals
            intervals = capture_keystroke_intervals(self.registration_text)
            
            if not intervals:
                print("Error: No keystroke data captured. Please try again.")
                return
            
            # Create baseline profile
            baseline = self.trust_engine.create_baseline(intervals)
            
            # Save baseline
            self.trust_engine.save_baseline(baseline)
            
            print(f"\n✓ Baseline created successfully!")
            print(f"  Average typing interval: {baseline['avg_interval']}s")
            print(f"  Standard deviation: {baseline['std_interval']}s")
            print(f"  Total keystrokes captured: {len(intervals)}")
            
        except Exception as e:
            print(f"Error during registration: {e}")
    
    def login_and_verify(self):
        """Verify user using continuous authentication."""
        print("\n--- CONTINUOUS AUTHENTICATION ---")
        print("Verifying your typing behavior...")
        
        try:
            # Check if baseline exists
            baseline = self.trust_engine.load_baseline()
            
            # Capture current typing behavior
            intervals = capture_keystroke_intervals(self.verification_text)
            
            if not intervals:
                print("Error: No keystroke data captured. Please try again.")
                return
            
            # Compute risk score
            risk_assessment = self.trust_engine.compute_risk(intervals, baseline)
            
            # Display results
            print("\n" + "-"*50)
            print("AUTHENTICATION RESULTS")
            print("-"*50)
            print(f"Baseline speed: {risk_assessment['baseline_speed']}s")
            print(f"Current speed: {risk_assessment['current_speed']}s")
            print(f"Risk score: {risk_assessment['risk_score']}")
            print(f"Session Status: {risk_assessment['status']}")
            print("-"*50)
            
            # Handle session status
            if risk_assessment['status'] == "TRUSTED":
                print("✓ Session TRUSTED - Access granted")
                print("  Your typing behavior matches the baseline profile.")
            else:
                print("⚠ Session SUSPICIOUS - Access denied")
                print("  Your typing behavior deviates from the baseline.")
                print("  Session Locked.")
                print("\nSecurity Alert: Anomaly detected in typing pattern.")
                print("Recommended action: Re-register baseline or verify identity.")
            
        except FileNotFoundError:
            print("Error: No baseline profile found.")
            print("Please register a baseline first (Option 1).")
        except Exception as e:
            print(f"Error during verification: {e}")
    
    def run(self):
        """Main program loop."""
        print("Initializing Zero Trust Authentication System...")
        
        while True:
            try:
                self.display_menu()
                
                # Get and validate user input
                while True:
                    try:
                        choice = input("\nEnter your choice (1-3): ").strip()
                        if choice in ['1', '2', '3']:
                            break
                        else:
                            print("Invalid choice. Please enter 1, 2, or 3.")
                    except (EOFError, KeyboardInterrupt):
                        print("\nExiting Zero Trust Authentication System...")
                        return
                
                if choice == '1':
                    self.register_baseline()
                elif choice == '2':
                    self.login_and_verify()
                elif choice == '3':
                    print("\nExiting Zero Trust Authentication System...")
                    print("Thank you for demonstrating continuous authentication!")
                    break
                
                # Pause before showing menu again
                self._safe_input_pause()
                
            except KeyboardInterrupt:
                print("\n\nExiting Zero Trust Authentication System...")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                self._safe_input_pause()
    
    def _safe_input_pause(self):
        """Safely pause for user input without interference."""
        try:
            input("\nPress Enter to continue...")
        except (EOFError, KeyboardInterrupt):
            pass


def main():
    """Main entry point of the application."""
    try:
        # Create and run the authentication system
        auth_system = ZeroTrustAuthSystem()
        auth_system.run()
    except Exception as e:
        print(f"System error: {e}")


if __name__ == "__main__":
    main()

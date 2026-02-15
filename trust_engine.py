import json
import statistics
import os


class TrustEngine:
    def __init__(self, baseline_file="baseline_profile.json"):
        self.baseline_file = baseline_file
        self.threshold = 0.08  # Risk threshold for authentication
    
    def create_baseline(self, intervals):
        """
        Create a baseline profile from keystroke intervals.
        
        Args:
            intervals (list): List of time intervals between keystrokes
            
        Returns:
            dict: Baseline profile with average and standard deviation
        """
        if not intervals:
            raise ValueError("No intervals provided for baseline creation")
        
        # Filter out extreme intervals (already done in keystroke.py, but double-check)
        filtered_intervals = [interval for interval in intervals if interval <= 3.0]
        
        if not filtered_intervals:
            raise ValueError("No valid intervals after filtering extreme pauses")
        
        avg_interval = statistics.mean(filtered_intervals)
        std_interval = statistics.stdev(filtered_intervals) if len(filtered_intervals) > 1 else 0.01
        
        baseline = {
            "avg_interval": round(avg_interval, 3),
            "std_interval": round(std_interval, 3)
        }
        
        return baseline
    
    def save_baseline(self, profile):
        """
        Save baseline profile to JSON file.
        
        Args:
            profile (dict): Baseline profile to save
        """
        with open(self.baseline_file, 'w') as f:
            json.dump(profile, f, indent=2)
        print(f"Baseline profile saved to {self.baseline_file}")
    
    def load_baseline(self):
        """
        Load baseline profile from JSON file.
        
        Returns:
            dict: Loaded baseline profile
            
        Raises:
            FileNotFoundError: If baseline file doesn't exist
        """
        if not os.path.exists(self.baseline_file):
            raise FileNotFoundError(f"Baseline file {self.baseline_file} not found")
        
        with open(self.baseline_file, 'r') as f:
            profile = json.load(f)
        
        return profile
    
    def compute_risk(self, current_intervals, baseline):
        """
        Compute risk score by comparing current typing with baseline.
        
        Args:
            current_intervals (list): Current keystroke intervals
            baseline (dict): Baseline profile
            
        Returns:
            dict: Risk assessment with score and status
        """
        if not current_intervals:
            raise ValueError("No intervals provided for risk computation")
        
        current_avg = statistics.mean(current_intervals)
        baseline_avg = baseline["avg_interval"]
        
        # Calculate risk score as absolute deviation from baseline
        risk_score = abs(current_avg - baseline_avg)
        
        # Determine session status
        if risk_score < self.threshold:
            status = "TRUSTED"
        else:
            status = "SUSPICIOUS"
        
        return {
            "baseline_speed": baseline_avg,
            "current_speed": round(current_avg, 3),
            "risk_score": round(risk_score, 3),
            "status": status
        }
    
    def verify_user(self, current_intervals):
        """
        Verify user based on current typing behavior.
        
        Args:
            current_intervals (list): Current keystroke intervals
            
        Returns:
            dict: Verification result with risk assessment
        """
        try:
            baseline = self.load_baseline()
            return self.compute_risk(current_intervals, baseline)
        except FileNotFoundError:
            return {
                "error": "No baseline profile found. Please register first."
            }


def create_baseline(intervals):
    """Convenience function to create baseline."""
    engine = TrustEngine()
    return engine.create_baseline(intervals)


def save_baseline(profile):
    """Convenience function to save baseline."""
    engine = TrustEngine()
    engine.save_baseline(profile)


def load_baseline():
    """Convenience function to load baseline."""
    engine = TrustEngine()
    return engine.load_baseline()


def compute_risk(current_intervals, baseline):
    """Convenience function to compute risk score."""
    engine = TrustEngine()
    return engine.compute_risk(current_intervals, baseline)

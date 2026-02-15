import time
from pynput import keyboard
import threading
import sys


class KeystrokeCapture:
    def __init__(self):
        self.intervals = []
        self.last_time = None
        self.capturing = False
        self.target_text = ""
        self.typed_text = ""
        self.capture_complete = threading.Event()
        self.listener = None
        self.max_interval = 3.0  # Filter out pauses longer than 3 seconds
        self.recent_chars = []  # Track recent characters for :q detection
    
    def capture_keystroke_intervals(self, prompt_text):
        """
        Capture keystroke intervals for a given prompt text.
        
        Args:
            prompt_text (str): The text user should type
            
        Returns:
            list: List of time intervals between keystrokes
        """
        self.target_text = prompt_text.lower()
        self.intervals = []
        self.last_time = None
        self.typed_text = ""
        self.recent_chars = []
        self.capturing = True
        self.capture_complete.clear()
        
        print(f"\nType the following sentence:")
        print(f'"{prompt_text}"')
        print("Type ':q' when finished typing.\n")
        print("Start typing...")
        
        # Clear any pending input
        sys.stdin.flush()
        
        # Start keyboard listener with better error handling
        try:
            self.listener = keyboard.Listener(on_press=self._on_key_press)
            self.listener.daemon = True  # Set as daemon thread
            self.listener.start()
            
            # Wait for capture to complete with timeout
            self.capture_complete.wait(timeout=60)  # 60 second timeout
            
        except Exception as e:
            print(f"Error starting keyboard listener: {e}")
            return []
        
        # Stop listener and wait for thread to finish
        if self.listener:
            try:
                self.listener.stop()
                self.listener.join(timeout=2.0)  # Wait up to 2 seconds for thread to finish
            except Exception:
                pass  # Ignore cleanup errors
        
        # Add delay to ensure complete cleanup
        time.sleep(0.2)
        
        # Simple input buffer clear
        try:
            sys.stdin.flush()
        except:
            pass
        
        # Filter out extreme intervals (pauses longer than 3 seconds)
        filtered_intervals = [interval for interval in self.intervals if interval <= self.max_interval]
        
        return filtered_intervals
    
    def _on_key_press(self, key):
        """Handle key press events."""
        if not self.capturing:
            return
        
        current_time = time.time()
        
        try:
            # Handle regular character keys
            if hasattr(key, 'char') and key.char is not None:
                char = key.char.lower()
                self.typed_text += char
                
                # Track recent characters for :q detection
                self.recent_chars.append(char)
                if len(self.recent_chars) > 2:
                    self.recent_chars.pop(0)
                
                # Check for :q pattern
                if len(self.recent_chars) == 2 and self.recent_chars[0] == ':' and self.recent_chars[1] == 'q':
                    self._finish_capture()
                    return
                
                # Record interval after first character
                if self.last_time is not None:
                    interval = current_time - self.last_time
                    # Only record intervals under 3 seconds to filter out extreme pauses
                    if interval <= self.max_interval:
                        self.intervals.append(interval)
                
                self.last_time = current_time
                    
        except AttributeError:
            # Ignore special keys completely - we only care about character keys
            pass
    
    def _finish_capture(self):
        """Finish the capture process."""
        self.capturing = False
        self.capture_complete.set()
        print(f"\nCaptured {len(self.intervals)} keystroke intervals.")
        
        # Add a small delay to ensure all events are processed
        time.sleep(0.1)


def capture_keystroke_intervals(prompt_text):
    """
    Convenience function to capture keystroke intervals.
    
    Args:
        prompt_text (str): The text the user should type
        
    Returns:
        list: List of time intervals between keystrokes
    """
    capture = KeystrokeCapture()
    return capture.capture_keystroke_intervals(prompt_text)

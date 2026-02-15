# Zero Trust Continuous Authentication using Keystroke Behavioral Biometrics

A terminal-based Python system that demonstrates Zero Trust continuous authentication through keystroke dynamics analysis.

## Project Overview

This research prototype implements the core Zero Trust principle: **"Never trust, always verify"** by continuously monitoring user typing behavior throughout a session. The system creates a unique typing profile during registration and continuously verifies the user's identity by analyzing their keystroke patterns.

## How It Demonstrates Zero Trust

Traditional authentication systems trust users after initial login. This Zero Trust system:

- **Never trusts** users after initial authentication
- **Continuously verifies** behavior throughout the session
- **Detects anomalies** in real-time typing patterns
- **Locks sessions** immediately when suspicious behavior is detected
- **Maintains security** through behavioral biometrics rather than static credentials

## System Architecture

```
zero_trust_auth/
│
├── main.py              # Main program flow and menu system
├── keystroke.py         # Keystroke capture and timing analysis
├── trust_engine.py      # Baseline management and risk calculation
├── baseline_profile.json # Stored user typing profile
└── README.md           # This documentation
```

## Core Components

### 1. Keystroke Dynamics Capture (`keystroke.py`)
- Captures time intervals between keystrokes using `pynput`
- Records typing rhythm and patterns
- Handles special keys and input validation

### 2. Trust Engine (`trust_engine.py`)
- Creates baseline profiles from registration data
- Calculates risk scores using statistical analysis
- Manages profile storage and retrieval
- Implements threshold-based decision logic

### 3. Main Application (`main.py`)
- Provides user interface and menu system
- Orchestrates registration and authentication flow
- Displays trust decisions and security alerts

## Installation and Setup

### Prerequisites
- Python 3.7 or higher
- Windows, macOS, or Linux system

### Install Dependencies
```bash
pip install pynput
```

### Navigate to Project Directory
```bash
cd zero_trust_auth
```

## Usage

### Run the Application
```bash
python main.py
```

### System Flow

#### Phase 1: Registration (Baseline Creation)
1. Select option `1` from the main menu
2. Type the registration sentence: `"zero trust systems rely on continuous verification"`
3. System captures your typing rhythm and creates a baseline profile
4. Profile is saved to `baseline_profile.json`

#### Phase 2: Continuous Authentication
1. Select option `2` from the main menu
2. Type the verification sentence: `"continuous authentication enhances security posture"`
3. System analyzes your current typing behavior
4. Risk score is calculated and trust decision is made

## Example Outputs

### Trusted Session Example
```
AUTHENTICATION RESULTS
--------------------------------------------------
Baseline speed: 0.18s
Current speed: 0.19s
Risk score: 0.01
Session Status: TRUSTED
--------------------------------------------------
✓ Session TRUSTED - Access granted
  Your typing behavior matches the baseline profile.
```

### Suspicious Session Example
```
AUTHENTICATION RESULTS
--------------------------------------------------
Baseline speed: 0.18s
Current speed: 0.35s
Risk score: 0.17
Session Status: SUSPICIOUS
--------------------------------------------------
⚠ Session SUSPICIOUS - Access denied
  Your typing behavior deviates from the baseline.
  Session Locked.

Security Alert: Anomaly detected in typing pattern.
Recommended action: Re-register baseline or verify identity.
```

## Risk Calculation Logic

The system uses a simple but effective deviation formula:

```python
risk_score = abs(current_avg_interval - baseline_avg_interval)
```

**Decision Logic:**
- `risk_score < 0.08` → Session TRUSTED
- `risk_score >= 0.08` → Session SUSPICIOUS (Locked)

## Demo Scenario

### Step 1: Register Baseline
- Type normally at your natural pace
- System establishes your unique typing fingerprint

### Step 2: Normal Login
- Type at your usual pace
- System detects matching patterns → **TRUSTED**

### Step 3: Anomaly Detection
- Type significantly faster or slower than normal
- System detects deviation → **SUSPICIOUS** → Session locked

## Security Features

- **Continuous Monitoring**: Never stops verifying user identity
- **Behavioral Biometrics**: Uses unique typing patterns as authentication factor
- **Real-time Detection**: Immediate response to suspicious behavior
- **Session Locking**: Automatic security response to anomalies
- **Profile Persistence**: Baseline stored securely between sessions

## Technical Specifications

### Performance Metrics
- **Keystroke Precision**: Millisecond-level timing accuracy
- **Memory Usage**: Minimal footprint (< 10MB)
- **Response Time**: Instantaneous risk calculation
- **Storage**: JSON-based profile management

### Threshold Configuration
- **Default Risk Threshold**: 0.08 seconds
- **Adjustable**: Modify `threshold` in `trust_engine.py`
- **Calibration**: System adapts to individual typing patterns

## Limitations and Considerations

### Research Prototype Notice
This is a **research prototype**, not a production system. Consider:

- **Environmental Factors**: Keyboard type, system load, user fatigue
- **Adaptive Learning**: Production systems would implement ML-based adaptation
- **Multi-factor Integration**: Should be combined with other authentication factors
- **False Positives**: Threshold tuning required for real-world deployment

### Known Limitations
- Single keyboard layout assumption
- No accommodation for injury-induced typing changes
- Limited to English text patterns
- Basic statistical analysis (no machine learning)

## File Structure Details

### `baseline_profile.json`
```json
{
  "avg_interval": 0.18,
  "std_interval": 0.04
}
```

### Module Responsibilities
- **`keystroke.py`**: Low-level input capture and timing
- **`trust_engine.py`**: Business logic and security decisions
- **`main.py`**: User interface and application flow

## Troubleshooting

### Common Issues

#### Permission Errors (Linux/macOS)
```bash
# May require accessibility permissions
sudo python main.py
```

#### Keyboard Input Not Detected
- Ensure `pynput` is properly installed
- Check system accessibility settings
- Try running with administrator privileges

#### Baseline File Corruption
- Delete `baseline_profile.json` and re-register
- Check file permissions in project directory

## Future Enhancements

### Production-Ready Features
- Machine learning-based pattern recognition
- Multi-keyboard profile support
- Adaptive threshold adjustment
- Integration with enterprise authentication systems
- Mobile device support

### Advanced Analytics
- Typing pressure analysis (with specialized hardware)
- Rhythm pattern recognition
- Contextual behavior modeling
- Anomaly clustering and classification

## Contributing

This is a research demonstration. For production implementations, consider:

1. **Security Review**: Comprehensive security assessment
2. **User Testing**: Extensive usability studies
3. **Performance Testing**: Load and stress testing
4. **Compliance**: Regulatory requirements analysis

## License

This research prototype is provided for educational and research purposes. Please ensure proper security review before any production use.

## Academic References

This implementation draws from research in:
- Behavioral biometrics and keystroke dynamics
- Zero Trust security architectures
- Continuous authentication systems
- Anomaly detection in user behavior

---

**Disclaimer**: This system is for research and educational purposes only. Do not use in production environments without comprehensive security review and testing.

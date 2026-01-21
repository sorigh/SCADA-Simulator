import numpy as np

class SignalGenerator:
    """
    Handles math generation for signals.
    Updated to be deterministic based on simulation time.
    """
    def __init__(self, amplitude=10, frequency=0.1, noise=0.5, offset=20.0):
        self.amplitude = amplitude
        self.frequency = frequency
        self.noise = noise
        self.offset = offset
        self.signal_type = "Sine Wave"

    def set_signal_type(self, new_type):
        """Sets the waveform type (Sine, Square, Sawtooth)."""
        self.signal_type = new_type
    
    def get_analog_value(self, current_time):
        """
        Calculates value based on the EXACT simulation time passed from main.py.
        This fixes the 'jittery' or 'vertical line' look.
        """
        base_value = 0.0

        # --- WAVEFORM SELECTION LOGIC ---
        if self.signal_type == "Sine Wave":
            # Standard sinusoidal wave
            base_value = self.amplitude * np.sin(2 * np.pi * self.frequency * current_time)
        elif self.signal_type == "Square Wave":
            # Digital-like switching: +Amplitude or -Amplitude
            sine_val = np.sin(2 * np.pi * self.frequency * current_time)
            base_value = self.amplitude * np.sign(sine_val)
        elif self.signal_type == "Sawtooth Wave":
            # Linear rise from -Amplitude to +Amplitude
            period = 1.0 / self.frequency if self.frequency > 0 else 1.0
            # Normalize time to 0..1 within the period
            fraction = (current_time % period) / period
            # Scale to range [-Amplitude, +Amplitude]
            base_value = 2 * self.amplitude * (fraction - 0.5)

        final_value = self.offset + base_value
        # Add random noise
        random_noise = np.random.normal(0, self.noise)

        return final_value + random_noise
    
    def get_digital_value(self, valoare_analogica, threshold=20.0):
        """Returns 1 if analog value > threshold, else 0."""
        return 1 if valoare_analogica > threshold else 0

    def update_params(self, amp=None, freq=None):
        """Updates parameters dynamically."""
        if amp is not None:
            self.amplitude = amp
        if freq is not None:
            self.frequency = freq
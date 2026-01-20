import numpy as np

class SignalGenerator:
    """
    Handles math generation for signals.
    Updated to be deterministic based on simulation time.
    """
    def __init__(self, amplitudine=10, frecventa=0.1, zgomot=0.5):
        self.amplitudine = amplitudine
        self.frecventa = frecventa
        self.zgomot = zgomot

    def get_analog_value(self, current_time):
        """
        Calculates value based on the EXACT simulation time passed from main.py.
        This fixes the 'jittery' or 'vertical line' look.
        """
        # Clean Sine Wave: A * sin(2 * pi * f * t)
        valoare = self.amplitudine * np.sin(2 * np.pi * self.frecventa * current_time)
        
        # Add random noise
        zgomot_random = np.random.normal(0, self.zgomot)
        
        return valoare + zgomot_random

    def get_digital_value(self, valoare_analogica, prag=5):
        """Returns 1 if analog value > threshold, else 0."""
        return 1 if valoare_analogica > prag else 0

    def update_params(self, amp=None, freq=None):
        """Updates parameters dynamically."""
        if amp is not None:
            self.amplitudine = amp
        if freq is not None:
            self.frecventa = freq
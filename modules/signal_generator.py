import numpy as np
import time

class SignalGenerator:
    """
    This class is responsible solely for the mathematical generation of signals.
    It mimics the behavior of physical sensors.
    """
    def __init__(self, amplitudine=10, frecventa=0.1, zgomot=0.5):
        self.amplitudine = amplitudine
        self.frecventa = frecventa
        self.zgomot = zgomot
        self.timp_start = time.time()

    def get_analog_value(self):
        # generates a continuous value (e.g., Temperature)
        timp_curent = time.time() - self.timp_start
        # Formula: A * sin(wt) + zgomot
        valoare = self.amplitudine * np.sin(2 * np.pi * self.frecventa * timp_curent)
        zgomot_random = np.random.normal(0, self.zgomot)
        return valoare + zgomot_random

    def get_digital_value(self, valoare_analogica, prag=5):
        """
        generates a discrete value (e.g., Motor ON/OFF)
        ex: If Temp > 5 degrees, Motor ON (1).
        """
        return 1 if valoare_analogica > prag else 0

    def update_params(self, amp=None, freq=None):
        """Enable updating signal parameters on the fly."""
        if amp is not None:
            self.amplitudine = amp
        if freq is not None:
            self.frecventa = freq
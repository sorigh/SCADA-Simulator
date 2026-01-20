class AlarmSystem:
    """
    Logic unit for monitoring safety thresholds.
    Determines if the system is in a safe state or alarm state.
    """
    def __init__(self, high_limit=25.0, low_limit=-10.0):
        self.high_limit = high_limit
        self.low_limit = low_limit
        self.alarm_triggered = False

    def check_status(self, current_value):
        """
        Evaluates the current analog value against thresholds.
        Returns a tuple: (is_alarm_active, status_message, color_code)
        """
        if current_value >= self.high_limit:
            self.alarm_triggered = True
            return (True, "CRITICAL: HIGH TEMP", "red")
        
        elif current_value <= self.low_limit:
            self.alarm_triggered = True
            return (True, "WARNING: LOW TEMP", "orange")
        
        else:
            self.alarm_triggered = False
            return (False, "SYSTEM NORMAL", "green")

    def set_thresholds(self, high, low):
        """Updates thresholds dynamically from the GUI."""
        self.high_limit = high
        self.low_limit = low
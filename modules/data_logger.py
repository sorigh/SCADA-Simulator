import csv
import os
from datetime import datetime

class DataLogger:
    """
    Handles logging of sensor data to a CSV file.
    Designed to allow post-process analysis in Excel or MATLAB.
    """
    def __init__(self, filename='data/process_history.csv'):
        self.filename = filename
        self.ensure_directory_exists()
        self.initialize_file()

    def ensure_directory_exists(self):
        """Creates the 'data' directory if it doesn't exist."""
        directory = os.path.dirname(self.filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

    def initialize_file(self):
        """Checks if file exists; if not, creates it with headers."""
        if not os.path.exists(self.filename):
            with open(self.filename, mode='w', newline='') as file:
                writer = csv.writer(file)
                # Standard CSV Header
                writer.writerow(["Timestamp", "Date_Time", "Analog_Value", "Digital_Value", "Status"])

    def log_step(self, timestamp, analog_val, digital_val, status_msg):
        """
        Appends a single simulation step to the CSV file.
        """
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            with open(self.filename, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([
                    f"{timestamp:.2f}",  # Simulation time (float)
                    current_time_str,    # Real wall-clock time
                    f"{analog_val:.4f}", # Formatted precision
                    int(digital_val),    # 0 or 1
                    status_msg           # e.g., "NORMAL", "WARNING"
                ])
        except Exception as e:
            print(f"[ERROR] Could not write to log file: {e}")
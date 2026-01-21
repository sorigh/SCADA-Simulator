import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.animation as animation
import json 
import sys

# --- IMPORT MODULES ---
from modules.signal_generator import SignalGenerator
from modules.alarm_logic import AlarmSystem
from modules.data_logger import DataLogger
from modules.ui_builder import UIBuilder 

class IndustrialDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("SCADA System - Industrial Monitoring Process")
        self.root.geometry("1200x900")
        
        # --- LOAD CONFIG ---
        self.config = self.load_config() 
        print(f"Loaded config: {self.config}")

        # --- INITIALIZE MODULES ---
        self.generator = SignalGenerator(amplitude=10, frequency=0.1, offset=20.0)
        self.alarm_system = AlarmSystem(high_limit=self.config["alarm_high"], low_limit=self.config["alarm_low"])
        self.logger = DataLogger(filename=self.config["log_file"])

        # --- STATE VARIABLES ---
        self.is_running = False
        self.is_logging = False
        self.simulation_time = 0.0
        self.history_len = self.config["history_length"]
        self.manual_override_active = False 
        
        # Data Buffers
        self.x_data = []
        self.y_analog = []
        self.y_digital = []
        
        # Lines Buffers
        self.line_high_data = []    # Buffer for High Alarm
        self.line_low_data = []     # Buffer for Low Alarm
        self.line_base_data = []    # Buffer for Baseline

        # --- BUILD GUI ---
        self.ui = UIBuilder(self, self.root)
        self.ui.build_all()
        
        # --- ANIMATION CONFIG ---
        self.ani = animation.FuncAnimation(
            self.fig, 
            self.update_process, 
            interval=self.config["refresh_rate_ms"], 
            blit=False, 
            cache_frame_data=False 
        )
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_config(self):
        """Loads settings from config.json or uses defaults."""
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Config file not found. Using defaults.")
            return {
                "alarm_high": 32.0, 
                "alarm_low": 0.0,   # [UPDATED] Low threshold default is 0.0
                "log_file": "data/default_log.csv",
                "history_length": 100,
                "refresh_rate_ms": 200
            }

    def toggle_simulation(self):
        self.is_running = not self.is_running
        if self.is_running:
            self.btn_start.config(text="PAUSE SIMULATION")
            self.lbl_status.config(text="RUNNING", bg="#007acc")
        else:
            self.btn_start.config(text="RESUME SIMULATION")
            self.lbl_status.config(text="PAUSED", bg="gray")

    def toggle_logging(self):
        self.is_logging = self.chk_log_var.get()

    def change_signal_type(self, event):
        new_type = self.combo_type.get()
        self.generator.set_signal_type(new_type)

    def update_params(self, _=None):
        if not hasattr(self, 'slider_amp') or not hasattr(self, 'slider_freq'):
            return
        try:
            new_amp = float(self.slider_amp.get())
            new_freq = float(self.slider_freq.get())
            self.generator.update_params(amp=new_amp, freq=new_freq)
        except ValueError:
            pass

    def toggle_manual_ui(self):
        if self.chk_manual_var.get():
            self.btn_manual_toggle.config(state="normal", bg="#f1c40f", text="FORCE MOTOR: OFF")
            self.manual_override_active = False 
        else:
            self.btn_manual_toggle.config(state="disabled", bg="lightgray", text="Auto Mode Active")

    def toggle_motor_manual(self):
        self.manual_override_active = not self.manual_override_active
        if self.manual_override_active:
            self.btn_manual_toggle.config(text="FORCE MOTOR: ON", bg="#2ecc71")
        else:
            self.btn_manual_toggle.config(text="FORCE MOTOR: OFF", bg="#e74c3c")

    def update_process(self, frame):
        if not self.is_running:
            return

        # 1. Update Time
        self.simulation_time += 0.1 

        # 2. Get Data
        analog_val = self.generator.get_analog_value(self.simulation_time)
        
        # Threshold logic for Motor (Center = 20.0)
        threshold_motor = self.generator.offset # Should be 20.0
        
        if self.chk_manual_var.get():
            digital_val = 1 if self.manual_override_active else 0
        else:
            # Fix: Typo corrected here
            digital_val = self.generator.get_digital_value(analog_val, threshold=threshold_motor)

        # 3. Check Alarms
        is_alarm, status_msg, status_color = self.alarm_system.check_status(analog_val)
        
        # Update UI Labels
        self.lbl_status.config(text=status_msg, bg=status_color)
        self.lbl_val_analog.config(text=f"Temp: {analog_val:.2f} °C")
        state_text = "ON" if digital_val else "OFF"
        self.lbl_val_digital.config(text=f"Motor: {state_text}")

        # 4. Data Logging
        if self.is_logging:
            self.logger.log_step(self.simulation_time, analog_val, digital_val, status_msg)

        # 5. Update Buffers (Including new lines)
        self.x_data.append(self.simulation_time)
        self.y_analog.append(analog_val)
        self.y_digital.append(digital_val)
        
        # Add values for the 3 constant lines
        self.line_high_data.append(self.alarm_system.high_limit)
        self.line_low_data.append(self.alarm_system.low_limit)
        self.line_base_data.append(self.generator.offset) # 20.0
        
        # Manage History Length
        if len(self.x_data) > self.history_len:
            self.x_data.pop(0)
            self.y_analog.pop(0)
            self.y_digital.pop(0)
            self.line_high_data.pop(0)
            self.line_low_data.pop(0)
            self.line_base_data.pop(0)

        # 6. Update Stats
        if len(self.y_analog) > 0:
            self.lbl_stat_max.config(text=f"MAX: {np.max(self.y_analog):.2f} °C")
            self.lbl_stat_min.config(text=f"MIN: {np.min(self.y_analog):.2f} °C")
            self.lbl_stat_avg.config(text=f"AVG: {np.mean(self.y_analog):.2f} °C")

        # 7. Update Graph Lines (All 4 lines on top graph)
        self.line_analog.set_data(self.x_data, self.y_analog)
        self.line_alarm_limit.set_data(self.x_data, self.line_high_data)
        self.line_alarm_low.set_data(self.x_data, self.line_low_data)
        self.line_baseline.set_data(self.x_data, self.line_base_data)
        
        self.line_digital.set_data(self.x_data, self.y_digital)
        
        # 8. Scale Axes
        if len(self.x_data) > 1:
            self.ax1.set_xlim(min(self.x_data), max(self.x_data))
            self.ax2.set_xlim(min(self.x_data), max(self.x_data))
            
            y_min, y_max = min(self.y_analog), max(self.y_analog)
            padding = (y_max - y_min) * 0.2
            if padding < 5: padding = 5
            self.ax1.set_ylim(y_min - padding, y_max + padding)
            
            self.ax2.set_ylim(-0.5, 1.5)

        # 9. HMI Animation
        color_motor = "#2ecc71" if digital_val > 0.5 else "#95a5a6"
        self.canvas_hmi.itemconfig(self.motor_id, fill=color_motor)

        safe_analog = max(0, min(analog_val, 40)) 
        fill_ratio = safe_analog / 40.0
        fill_height = fill_ratio * 98 
        new_top_y = 128 - fill_height
        self.canvas_hmi.coords(self.liquid_id, 32, new_top_y, 88, 128)

        if "CRITICAL" in status_msg:
            self.canvas_hmi.itemconfig(self.liquid_id, fill="#e74c3c")
        elif "WARNING" in status_msg:
            self.canvas_hmi.itemconfig(self.liquid_id, fill="#e67e22") # Orange for low
        else:
            self.canvas_hmi.itemconfig(self.liquid_id, fill="#3498db")

        # Must return all lines that are animated
        return self.line_analog, self.line_digital, self.line_alarm_limit, self.line_alarm_low, self.line_baseline
    
    def on_close(self):
        print("Closing application...")
        self.is_running = False
        if self.ani.event_source:
            self.ani.event_source.stop()
        self.root.destroy()
        self.root.quit()
        sys.exit(0)
    
    def reset_simulation(self):
        print("System Reset.")
        self.simulation_time = 0.0
        self.x_data.clear()
        self.y_analog.clear()
        self.y_digital.clear()
        
        self.line_high_data.clear()
        self.line_low_data.clear()
        self.line_base_data.clear()

        self.line_analog.set_data([], [])
        self.line_digital.set_data([], [])
        self.line_alarm_limit.set_data([], [])
        self.line_alarm_low.set_data([], [])
        self.line_baseline.set_data([], [])
        
        self.lbl_stat_max.config(text="MAX: 0.00")
        self.lbl_stat_min.config(text="MIN: 0.00")
        self.lbl_stat_avg.config(text="AVG: 0.00")

        self.canvas.draw()

        if self.is_logging:
            self.logger.log_step(0, 0, 0, "SYSTEM RESET")

if __name__ == "__main__":
    root = tk.Tk()
    try:
        style = ttk.Style()
        style.theme_use('clam') 
    except:
        pass
    app = IndustrialDashboard(root)
    root.mainloop()
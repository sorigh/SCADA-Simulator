import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import os
import sys

# --- IMPORT MODULES ---
from modules.signal_generator import SignalGenerator
from modules.alarm_logic import AlarmSystem
from modules.data_logger import DataLogger

class IndustrialDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("SCADA System - Industrial Monitoring Process")
        self.root.geometry("1200x900")
        
        # --- INITIALIZE MODULES ---
        self.generator = SignalGenerator(amplitude=10, frequency=0.1)
        self.alarm_system = AlarmSystem(high_limit=18.0, low_limit=-15.0)
        self.logger = DataLogger(filename='data/simulation_log.csv')

        # --- STATE VARIABLES ---
        self.is_running = False
        self.is_logging = False
        self.simulation_time = 0.0
        self.history_len = 200 # More points for a smoother look
        
        # Buffers
        self.x_data = []
        self.y_analog = []
        self.y_digital = []
        self.alarm_threshold_line = [] 

        # --- GUI SETUP ---
        self.setup_ui()
        
        # --- ANIMATION CONFIG ---
        # cache_frame_data=False prevents memory warnings
        self.ani = animation.FuncAnimation(
            self.fig, 
            self.update_process, 
            interval=50,   # 50ms = 20 FPS (Smooth)
            blit=False, 
            cache_frame_data=False 
        )
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_ui(self):
        main_layout = ttk.Frame(self.root)
        main_layout.pack(fill=tk.BOTH, expand=True)

        # === LEFT PANEL (CONTROLS) ===
        control_panel = ttk.LabelFrame(main_layout, text="Control Panel", padding=15)
        control_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        # Start/Stop Button
        self.btn_start = ttk.Button(control_panel, text="START SIMULATION", command=self.toggle_simulation)
        self.btn_start.pack(fill=tk.X, pady=10)
        # Reset Button
        self.btn_reset = ttk.Button(control_panel, text="RESET SYSTEM", command=self.reset_simulation)
        self.btn_reset.pack(fill=tk.X, pady=5)
        # Data Logging Checkbox
        self.chk_log_var = tk.BooleanVar(value=False)
        self.chk_log = ttk.Checkbutton(control_panel, text="Enable Data Logging (CSV)", variable=self.chk_log_var, command=self.toggle_logging)
        self.chk_log.pack(fill=tk.X, pady=5)

        ttk.Separator(control_panel, orient='horizontal').pack(fill='x', pady=15)


        # --- LIVE STATISTICS SECTION ---
        ttk.Label(control_panel, text="LIVE STATISTICS (Window):").pack(anchor="w")
        
        # Frame pentru a le alinia frumos
        stats_frame = ttk.Frame(control_panel)
        stats_frame.pack(fill=tk.X, pady=5)

        # MAX Value
        self.lbl_stat_max = ttk.Label(stats_frame, text="MAX: 0.00", font=("Consolas", 10), foreground="red")
        self.lbl_stat_max.pack(anchor="w")

        # MIN Value
        self.lbl_stat_min = ttk.Label(stats_frame, text="MIN: 0.00", font=("Consolas", 10), foreground="blue")
        self.lbl_stat_min.pack(anchor="w")

        # AVG Value
        self.lbl_stat_avg = ttk.Label(stats_frame, text="AVG: 0.00", font=("Consolas", 10, "bold"))
        self.lbl_stat_avg.pack(anchor="w")



        # Sliders
        ttk.Label(control_panel, text="Signal Amplitude:").pack(anchor="w")
        self.slider_amp = ttk.Scale(control_panel, from_=0, to=40, orient=tk.HORIZONTAL, command=self.update_params)
        self.slider_amp.set(15) # Default amplitude higher
        self.slider_amp.pack(fill=tk.X, pady=5)

        ttk.Label(control_panel, text="Process Frequency:").pack(anchor="w")
        self.slider_freq = ttk.Scale(control_panel, from_=0.01, to=0.5, orient=tk.HORIZONTAL, command=self.update_params)
        self.slider_freq.set(0.1)
        self.slider_freq.pack(fill=tk.X, pady=5)


        # Signal Type Selector (NEW FEATURE)
        ttk.Label(control_panel, text="Signal Type:").pack(anchor="w", pady=(10, 0))
        signal_options = ["Sine Wave", "Square Wave", "Sawtooth Wave"]
        self.combo_type = ttk.Combobox(control_panel, values=signal_options, state="readonly")
        self.combo_type.set("Sine Wave") # Default value
        self.combo_type.pack(fill=tk.X, pady=5)
        self.combo_type.bind("<<ComboboxSelected>>", self.change_signal_type)

        ttk.Separator(control_panel, orient='horizontal').pack(fill='x', pady=15)

        # Status & Values
        ttk.Label(control_panel, text="SYSTEM STATUS:").pack(anchor="w")
        self.lbl_status = tk.Label(control_panel, text="IDLE", bg="gray", fg="white", font=("Arial", 14, "bold"), height=2, width=22)
        self.lbl_status.pack(fill=tk.X, pady=5)

        self.lbl_val_analog = ttk.Label(control_panel, text="Temp: 0.00 °C", font=("Consolas", 14))
        self.lbl_val_analog.pack(anchor="w", pady=10)
        
        self.lbl_val_digital = ttk.Label(control_panel, text="Motor: OFF", font=("Consolas", 14))
        self.lbl_val_digital.pack(anchor="w", pady=5)

        # === RIGHT PANEL (GRAPHS) ===
        graph_frame = ttk.Frame(main_layout)
        graph_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Figure setup
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, sharex=True, gridspec_kw={'height_ratios': [3, 1]})
        self.fig.set_facecolor('#f0f0f0')
        plt.subplots_adjust(bottom=0.1, right=0.95, top=0.95, hspace=0.3)

        # 1. Analog Plot Configuration
        self.ax1.set_title("Analog Signal (Temperature)", fontsize=11, fontweight='bold')
        self.ax1.set_ylabel("Temperature (°C)")
        self.ax1.grid(True, linestyle='--', alpha=0.7)
        # Thicker line (lw=2.5) for better visibility
        self.line_analog, = self.ax1.plot([], [], color='#007acc', lw=2.5, label='Process Value')
        self.line_alarm_limit, = self.ax1.plot([], [], color='red', linestyle='--', lw=1.5, label='Alarm Threshold')
        self.ax1.legend(loc='upper right')

        # 2. Digital Plot Configuration
        self.ax2.set_title("Digital Output (Motor State)", fontsize=11, fontweight='bold')
        self.ax2.set_ylabel("State (0/1)")
        # FIX: Set Y-limits wider than [0,1] so the line is not cut off
        self.ax2.set_ylim(-0.5, 1.5) 
        self.ax2.set_yticks([0, 1])
        self.ax2.set_yticklabels(['OFF', 'ON'])
        self.ax2.grid(True, linestyle='-', alpha=0.5)
        # Use steps-post for square wave
        self.line_digital, = self.ax2.plot([], [], color='#2ca02c', lw=3, drawstyle='steps-post')

        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

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
        """Callback when user selects a new signal type from dropdown."""
        new_type = self.combo_type.get()
        # Pass the selection to the generator module
        self.generator.set_signal_type(new_type)


    def update_params(self, _=None):
        if not hasattr(self, 'slider_amp') or not hasattr(self, 'slider_freq'):
            return
        try:
            # Send values to generator
            new_amp = float(self.slider_amp.get())
            new_freq = float(self.slider_freq.get())
            self.generator.update_params(amp=new_amp, freq=new_freq)
        except ValueError:
            pass

    def update_process(self, frame):
        if not self.is_running:
            return

        # 1. INCREMENT TIME
        self.simulation_time += 0.1 

        # 2. GET DATA (Pass exact time to generator for smooth wave)
        analog_val = self.generator.get_analog_value(self.simulation_time)
        
        # Logic: If Temp > 5.0, Motor turns ON
        digital_val = self.generator.get_digital_value(analog_val, prag=5.0)
        
        # 3. CHECK ALARMS
        is_alarm, status_msg, status_color = self.alarm_system.check_status(analog_val)
        
        # Update Labels
        self.lbl_status.config(text=status_msg, bg=status_color)
        self.lbl_val_analog.config(text=f"Temp: {analog_val:.2f} °C")
        state_text = "ON" if digital_val else "OFF"
        self.lbl_val_digital.config(text=f"Motor: {state_text}")

        # 4. LOGGING
        if self.is_logging:
            self.logger.log_step(self.simulation_time, analog_val, digital_val, status_msg)

        # 5. UPDATE DATA LISTS
        self.x_data.append(self.simulation_time)
        self.y_analog.append(analog_val)
        self.y_digital.append(digital_val)
        self.alarm_threshold_line.append(self.alarm_system.high_limit)
        # --- UPDATE STATISTICS ---
        # Calculate MAX, MIN, AVG over current window
        if len(self.y_analog) > 0:
            current_max = np.max(self.y_analog)
            current_min = np.min(self.y_analog)
            current_avg = np.mean(self.y_analog)

            self.lbl_stat_max.config(text=f"MAX: {current_max:.2f} °C")
            self.lbl_stat_min.config(text=f"MIN: {current_min:.2f} °C")
            self.lbl_stat_avg.config(text=f"AVG: {current_avg:.2f} °C")

        # Sliding window logic
        if len(self.x_data) > self.history_len:
            self.x_data.pop(0)
            self.y_analog.pop(0)
            self.y_digital.pop(0)
            self.alarm_threshold_line.pop(0)

        # 6. UPDATE PLOTS
        self.line_analog.set_data(self.x_data, self.y_analog)
        self.line_alarm_limit.set_data(self.x_data, self.alarm_threshold_line)
        self.line_digital.set_data(self.x_data, self.y_digital)
        
        # --- FIX: SCALING LOGIC ---
        if len(self.x_data) > 1:
            # Set X-Axis to show current window
            self.ax1.set_xlim(min(self.x_data), max(self.x_data))
            self.ax2.set_xlim(min(self.x_data), max(self.x_data))
            
            # Set Y-Axis for Analog (Auto-scale but with MINIMUM range)
            # This prevents zooming into noise when amplitude is 0
            y_min, y_max = min(self.y_analog), max(self.y_analog)
            limit = max(abs(y_min), abs(y_max), 20) # Ensure at least +/- 20 range
            self.ax1.set_ylim(-(limit + 5), limit + 5)
            
            # Set Y-Axis for Digital (Fixed to show ON/OFF clearly)
            self.ax2.set_ylim(-0.5, 1.5)

        return self.line_analog, self.line_digital, self.line_alarm_limit
    
    def on_close(self):
        """Stops the animation and kills the process."""
        print("Closing application...")
        self.is_running = False
        if self.ani.event_source:
            self.ani.event_source.stop()
        self.root.destroy()
        self.root.quit()
        sys.exit(0)
    
    def reset_simulation(self):
        """
        Clears the visual graphs and resets time to 0.
        Does NOT delete the CSV file, but logs a 'RESET' event if logging is active.
        """
        print("System Reset triggered.")
        
        # 1. Reset Time
        self.simulation_time = 0.0

        # 2. Clear Data Buffers
        self.x_data.clear()
        self.y_analog.clear()
        self.y_digital.clear()
        self.alarm_threshold_line.clear()

        # 3. Clear Visual Lines immediately
        self.line_analog.set_data([], [])
        self.line_digital.set_data([], [])
        self.line_alarm_limit.set_data([], [])
        

        # Reset Stats Labels
        self.lbl_stat_max.config(text="MAX: 0.00")
        self.lbl_stat_min.config(text="MIN: 0.00")
        self.lbl_stat_avg.config(text="AVG: 0.00")

        # 4. Force a redraw of the canvas to clear old lines instantly
        self.canvas.draw()

        # 5. Log the reset event (Audit Trail)
        if self.is_logging:
            self.logger.log_step(0, 0, 0, "SYSTEM RESET PERFORMED")

if __name__ == "__main__":
    root = tk.Tk()
    try:
        style = ttk.Style()
        style.theme_use('clam') 
    except:
        pass
    app = IndustrialDashboard(root)
    root.mainloop()
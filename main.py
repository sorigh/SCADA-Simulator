import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import os

# --- IMPORTING OUR CUSTOM MODULES ---
from modules.signal_generator import SignalGenerator
from modules.alarm_logic import AlarmSystem
from modules.data_logger import DataLogger

class IndustrialDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("SCADA System - Industrial Monitoring Process")
        self.root.geometry("1200x800")
        
        # --- INITIALIZE MODULES ---
        # 1. Signal Generator: Simulates the physical sensors
        self.generator = SignalGenerator(amplitudine=10, frecventa=0.1)
        
        # 2. Alarm System: Monitors safety limits (High: 18.0, Low: -15.0)
        self.alarm_system = AlarmSystem(high_limit=18.0, low_limit=-15.0)
        
        # 3. Data Logger: Handles CSV recording
        self.logger = DataLogger(filename='data/simulation_log.csv')

        # --- PROCESS STATE VARIABLES ---
        self.is_running = False
        self.is_logging = False
        self.simulation_time = 0
        self.history_len = 100  # Number of points to display on graph
        
        # Data buffers for plotting
        self.x_data = []
        self.y_analog = []
        self.y_digital = []
        self.alarm_threshold_line = [] # To visualize the limit

        # --- GUI LAYOUT SETUP ---
        self.setup_ui()
        
        # --- ANIMATION LOOP ---
        # Refreshes the plot every 50ms
        self.ani = animation.FuncAnimation(self.fig, self.update_process, interval=50, blit=False)

    def setup_ui(self):
        """Builds the visual interface: Side Panel (Control) + Main Area (Graphs)"""
        
        # 1. Main Container
        main_layout = ttk.Frame(self.root)
        main_layout.pack(fill=tk.BOTH, expand=True)

        # 2. Left Control Panel
        control_panel = ttk.LabelFrame(main_layout, text="Control Panel", padding=10)
        control_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        # --- CONTROLS ---
        
        # Start/Stop Button
        self.btn_start = ttk.Button(control_panel, text="START SIMULATION", command=self.toggle_simulation)
        self.btn_start.pack(fill=tk.X, pady=10)

        # Logging Toggle
        self.chk_log_var = tk.BooleanVar(value=False)
        self.chk_log = ttk.Checkbutton(control_panel, text="Enable Data Logging (CSV)", variable=self.chk_log_var, command=self.toggle_logging)
        self.chk_log.pack(fill=tk.X, pady=5)

        # Separator
        ttk.Separator(control_panel, orient='horizontal').pack(fill='x', pady=15)

        # Amplitude Slider
        ttk.Label(control_panel, text="Signal Amplitude:").pack(anchor="w")
        self.slider_amp = ttk.Scale(control_panel, from_=5, to=30, orient=tk.HORIZONTAL, command=self.update_params)
        self.slider_amp.set(10)
        self.slider_amp.pack(fill=tk.X, pady=5)

        # Frequency Slider
        ttk.Label(control_panel, text="Process Frequency:").pack(anchor="w")
        self.slider_freq = ttk.Scale(control_panel, from_=0.01, to=0.5, orient=tk.HORIZONTAL, command=self.update_params)
        self.slider_freq.set(0.1)
        self.slider_freq.pack(fill=tk.X, pady=5)

        # Separator
        ttk.Separator(control_panel, orient='horizontal').pack(fill='x', pady=15)

        # Status Indicator Box
        ttk.Label(control_panel, text="SYSTEM STATUS:").pack(anchor="w")
        self.lbl_status = tk.Label(control_panel, text="IDLE", bg="gray", fg="white", font=("Arial", 14, "bold"), height=2)
        self.lbl_status.pack(fill=tk.X, pady=5)

        # Live Values Display
        self.lbl_val_analog = ttk.Label(control_panel, text="Temp: 0.00 °C", font=("Consolas", 12))
        self.lbl_val_analog.pack(anchor="w", pady=5)
        
        self.lbl_val_digital = ttk.Label(control_panel, text="Motor: OFF", font=("Consolas", 12))
        self.lbl_val_digital.pack(anchor="w", pady=5)

        # 3. Right Graph Area
        graph_frame = ttk.Frame(main_layout)
        graph_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Matplotlib Figure
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, sharex=True, gridspec_kw={'height_ratios': [3, 1]})
        self.fig.set_facecolor('#f0f0f0')

        # Analog Plot (Temperature)
        self.ax1.set_title("Analog Signal Monitoring (Temperature)", fontsize=10)
        self.ax1.set_ylabel("Amplitude")
        self.ax1.grid(True, linestyle='--', alpha=0.6)
        self.line_analog, = self.ax1.plot([], [], color='#007acc', lw=2, label='Process Value')
        self.line_alarm_limit, = self.ax1.plot([], [], color='red', linestyle='--', label='Alarm Threshold')
        self.ax1.legend(loc='upper right', fontsize='small')

        # Digital Plot (Motor State)
        self.ax2.set_title("Digital Output (Actuator State)", fontsize=10)
        self.ax2.set_ylabel("State")
        self.ax2.set_yticks([0, 1])
        self.ax2.set_yticklabels(['OFF', 'ON'])
        self.ax2.grid(True)
        self.line_digital, = self.ax2.plot([], [], color='#2ca02c', lw=2, drawstyle='steps-pre')

        # Canvas Embedding
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def toggle_simulation(self):
        """Starts or pauses the visualization loop."""
        self.is_running = not self.is_running
        if self.is_running:
            self.btn_start.config(text="PAUSE SIMULATION")
            self.lbl_status.config(text="RUNNING", bg="#007acc")
        else:
            self.btn_start.config(text="RESUME SIMULATION")
            self.lbl_status.config(text="PAUSED", bg="gray")

    def toggle_logging(self):
        """Callback for the logging checkbox."""
        self.is_logging = self.chk_log_var.get()

    def update_params(self, _=None):
        """Updates the backend generator when sliders are moved."""
        new_amp = float(self.slider_amp.get())
        new_freq = float(self.slider_freq.get())
        # Call the method in signal_generator module
        self.generator.update_params(amp=new_amp, freq=new_freq)

    def update_process(self, frame):
        """Main loop: Fetch Data -> Check Alarm -> Log -> Update Graph."""
        if not self.is_running:
            return

        # 1. GET DATA (from SignalGenerator module)
        analog_val = self.generator.get_analog_value()
        digital_val = self.generator.get_digital_value(analog_val, prag=5.0)
        
        self.simulation_time += 0.1 # Increment internal time

        # 2. CHECK LOGIC (from AlarmSystem module)
        is_alarm, status_msg, status_color = self.alarm_system.check_status(analog_val)
        
        # Update UI Status Label
        self.lbl_status.config(text=status_msg, bg=status_color)
        self.lbl_val_analog.config(text=f"Temp: {analog_val:.2f} °C")
        state_text = "ON" if digital_val else "OFF"
        self.lbl_val_digital.config(text=f"Motor: {state_text}")

        # 3. LOG DATA (using DataLogger module)
        if self.is_logging:
            self.logger.log_step(self.simulation_time, analog_val, digital_val, status_msg)

        # 4. UPDATE LISTS FOR PLOTTING
        self.x_data.append(self.simulation_time)
        self.y_analog.append(analog_val)
        self.y_digital.append(digital_val)
        self.alarm_threshold_line.append(self.alarm_system.high_limit)

        # Keep lists at fixed size (sliding window)
        if len(self.x_data) > self.history_len:
            self.x_data.pop(0)
            self.y_analog.pop(0)
            self.y_digital.pop(0)
            self.alarm_threshold_line.pop(0)

        # 5. REFRESH GRAPH
        self.line_analog.set_data(self.x_data, self.y_analog)
        self.line_alarm_limit.set_data(self.x_data, self.alarm_threshold_line)
        self.line_digital.set_data(self.x_data, self.y_digital)
        
        # Dynamic Y-axis scaling
        self.ax1.set_xlim(min(self.x_data), max(self.x_data))
        current_max = max(abs(min(self.y_analog)), abs(max(self.y_analog)), self.alarm_system.high_limit)
        self.ax1.set_ylim(-(current_max + 5), current_max + 5)
        self.ax2.set_xlim(min(self.x_data), max(self.x_data))

        return self.line_analog, self.line_digital, self.line_alarm_limit

if __name__ == "__main__":
    # Create the main window
    root = tk.Tk()
    
    # Apply a modern theme if available
    try:
        style = ttk.Style()
        style.theme_use('clam') 
    except:
        pass
        
    app = IndustrialDashboard(root)
    root.mainloop()
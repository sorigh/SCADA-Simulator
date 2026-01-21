import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class UIBuilder:
    """
    Handles the construction of the User Interface.
    Separates the visual layout from the main simulation logic.
    """
    def __init__(self, app_instance, root):
        self.app = app_instance  # Reference to the main IndustrialDashboard instance
        self.root = root

    def build_all(self):
        """Constructs the entire UI layout."""
        main_layout = ttk.Frame(self.root)
        main_layout.pack(fill=tk.BOTH, expand=True)

        # 1. Build Control Panel (Left Side)
        self._build_control_panel(main_layout)
        
        # 2. Build Graphs Area (Right Side)
        self._build_graphs(main_layout)

    def _build_control_panel(self, parent):
        control_panel = ttk.LabelFrame(parent, text="Control Panel", padding=15)
        control_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        # --- Simulation Controls ---
        self.app.btn_start = ttk.Button(control_panel, text="START SIMULATION", command=self.app.toggle_simulation)
        self.app.btn_start.pack(fill=tk.X, pady=10)
        
        self.app.btn_reset = ttk.Button(control_panel, text="RESET SYSTEM", command=self.app.reset_simulation)
        self.app.btn_reset.pack(fill=tk.X, pady=5)
        
        self.app.chk_log_var = tk.BooleanVar(value=False)
        self.app.chk_log = ttk.Checkbutton(
            control_panel, 
            text="Enable Data Logging (CSV)", 
            variable=self.app.chk_log_var, 
            command=self.app.toggle_logging
        )
        self.app.chk_log.pack(fill=tk.X, pady=5)

        # --- Manual Control Section ---
        ttk.Separator(control_panel, orient='horizontal').pack(fill='x', pady=10)
        ttk.Label(control_panel, text="Motor Control:", font=("Arial", 10, "bold")).pack(anchor="w")

        self.app.chk_manual_var = tk.BooleanVar(value=False)
        self.app.chk_manual = ttk.Checkbutton(
            control_panel, 
            text="Enable Manual Mode", 
            variable=self.app.chk_manual_var,
            command=self.app.toggle_manual_ui
        )
        self.app.chk_manual.pack(fill=tk.X, pady=2)

        self.app.btn_manual_toggle = tk.Button(
            control_panel, 
            text="FORCE MOTOR: OFF", 
            bg="lightgray",
            state="disabled",
            command=self.app.toggle_motor_manual
        )
        self.app.btn_manual_toggle.pack(fill=tk.X, pady=5)

        ttk.Separator(control_panel, orient='horizontal').pack(fill='x', pady=15)

        # --- Statistics ---
        ttk.Label(control_panel, text="LIVE STATISTICS (Window):").pack(anchor="w")
        stats_frame = ttk.Frame(control_panel)
        stats_frame.pack(fill=tk.X, pady=5)

        self.app.lbl_stat_max = ttk.Label(stats_frame, text="MAX: 0.00", font=("Consolas", 10), foreground="red")
        self.app.lbl_stat_max.pack(anchor="w")
        self.app.lbl_stat_min = ttk.Label(stats_frame, text="MIN: 0.00", font=("Consolas", 10), foreground="blue")
        self.app.lbl_stat_min.pack(anchor="w")
        self.app.lbl_stat_avg = ttk.Label(stats_frame, text="AVG: 0.00", font=("Consolas", 10, "bold"))
        self.app.lbl_stat_avg.pack(anchor="w")

        # --- Parameter Sliders ---
        ttk.Label(control_panel, text="Signal Amplitude:").pack(anchor="w", pady=(10,0))
        self.app.slider_amp = ttk.Scale(control_panel, from_=0, to=40, orient=tk.HORIZONTAL, command=self.app.update_params)
        self.app.slider_amp.set(15)
        self.app.slider_amp.pack(fill=tk.X, pady=5)

        ttk.Label(control_panel, text="Process Frequency:").pack(anchor="w")
        self.app.slider_freq = ttk.Scale(control_panel, from_=0.01, to=0.5, orient=tk.HORIZONTAL, command=self.app.update_params)
        self.app.slider_freq.set(0.1)
        self.app.slider_freq.pack(fill=tk.X, pady=5)

        # --- Signal Type Selector ---
        ttk.Label(control_panel, text="Signal Type:").pack(anchor="w", pady=(10, 0))
        signal_options = ["Sine Wave", "Square Wave", "Sawtooth Wave"]
        self.app.combo_type = ttk.Combobox(control_panel, values=signal_options, state="readonly")
        self.app.combo_type.set("Sine Wave")
        self.app.combo_type.pack(fill=tk.X, pady=5)
        self.app.combo_type.bind("<<ComboboxSelected>>", self.app.change_signal_type)

        # --- HMI Visualization (Tank & Motor) ---
        ttk.Separator(control_panel, orient='horizontal').pack(fill='x', pady=10)
        ttk.Label(control_panel, text="PROCESS VISUALIZATION:", font=("Arial", 10, "bold")).pack(anchor="w")

        self.app.canvas_hmi = tk.Canvas(control_panel, width=250, height=150, bg="white", highlightthickness=1, highlightbackground="#aaaaaa")
        self.app.canvas_hmi.pack(pady=5)

        # Draw Static Elements
        self.app.canvas_hmi.create_rectangle(30, 30, 90, 130, outline="black", width=3) 
        self.app.canvas_hmi.create_text(60, 140, text="Tank", font=("Arial", 8)) # Translated
        
        # Draw Dynamic Liquid (Saved in liquid_id)
        self.app.liquid_id = self.app.canvas_hmi.create_rectangle(32, 128, 88, 128, fill="#3498db", outline="")

        # Draw Pipe
        self.app.canvas_hmi.create_line(90, 100, 160, 100, width=4, fill="#555")

        # Draw Dynamic Motor
        self.app.motor_id = self.app.canvas_hmi.create_oval(160, 75, 210, 125, fill="gray", outline="black", width=2)
        self.app.canvas_hmi.create_text(185, 140, text="Motor", font=("Arial", 8))
        self.app.canvas_hmi.create_text(185, 85, text="M", font=("Arial", 12, "bold"), fill="white")

        ttk.Separator(control_panel, orient='horizontal').pack(fill='x', pady=15)

        # --- Status Labels ---
        ttk.Label(control_panel, text="SYSTEM STATUS:").pack(anchor="w")
        self.app.lbl_status = tk.Label(control_panel, text="IDLE", bg="gray", fg="white", font=("Arial", 14, "bold"), height=2, width=22)
        self.app.lbl_status.pack(fill=tk.X, pady=5)

        self.app.lbl_val_analog = ttk.Label(control_panel, text="Temp: 0.00 °C", font=("Consolas", 14))
        self.app.lbl_val_analog.pack(anchor="w", pady=10)
        
        self.app.lbl_val_digital = ttk.Label(control_panel, text="Motor: OFF", font=("Consolas", 14))
        self.app.lbl_val_digital.pack(anchor="w", pady=5)

    def _build_graphs(self, parent):
        graph_frame = ttk.Frame(parent)
        graph_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Matplotlib Figure Setup
        self.app.fig, (self.app.ax1, self.app.ax2) = plt.subplots(2, 1, sharex=True, gridspec_kw={'height_ratios': [3, 1]})
        self.app.fig.set_facecolor('#f0f0f0')
        plt.subplots_adjust(bottom=0.1, right=0.95, top=0.95, hspace=0.3)

        # Analog Plot
        self.app.ax1.set_title("Analog Signal (Temperature)", fontsize=11, fontweight='bold')
        self.app.ax1.set_ylabel("Temperature (°C)")
        self.app.ax1.grid(True, linestyle='--', alpha=0.7)
        self.app.line_analog, = self.app.ax1.plot([], [], color='#007acc', lw=2.5, label='Process Value')
        self.app.line_alarm_limit, = self.app.ax1.plot([], [], color='red', linestyle='--', lw=1.5, label='Alarm Threshold')
        self.app.ax1.legend(loc='upper right')

        # Digital Plot
        self.app.ax2.set_title("Digital Output (Motor State)", fontsize=11, fontweight='bold')
        self.app.ax2.set_ylabel("State (0/1)")
        self.app.ax2.set_ylim(-0.5, 1.5) 
        self.app.ax2.set_yticks([0, 1])
        self.app.ax2.set_yticklabels(['OFF', 'ON'])
        self.app.ax2.grid(True, linestyle='-', alpha=0.5)
        self.app.line_digital, = self.app.ax2.plot([], [], color='#2ca02c', lw=3, drawstyle='steps-post')

        # Canvas Embedding
        self.app.canvas = FigureCanvasTkAgg(self.app.fig, master=graph_frame)
        self.app.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
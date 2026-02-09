import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import time

class RoboticArmApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Robotic Arm Controller")
        self.root.geometry("500x600")
        
        # Serial connection
        self.ser = None
        self.is_connected = False
        
        # Servo States (Initialize to Middle/Safe Position)
        self.servo_angles = {
            1: 90, # Base
            2: 90, # Shoulder
            3: 90, # Elbow
            4: 90, # Wrist
            5: 90   # Gripper (0=Open)
        }
        
        # GUI Setup
        self.setup_ui()
        
    def setup_ui(self):
        # --- Connection Frame ---
        conn_frame = ttk.LabelFrame(self.root, text="Connection")
        conn_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(conn_frame, text="Port:").pack(side="left", padx=5)
        
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(conn_frame, textvariable=self.port_var)
        self.port_combo.pack(side="left", padx=5, fill="x", expand=True)
        self.update_ports()
        
        self.refresh_btn = ttk.Button(conn_frame, text="Refresh", command=self.update_ports)
        self.refresh_btn.pack(side="left", padx=2)
        
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.toggle_connection)
        self.connect_btn.pack(side="left", padx=5)
        
        # --- Controls Frame ---
        controls_frame = ttk.LabelFrame(self.root, text="Manual Control")
        controls_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.sliders = {}
        labels = {
            1: "Base (Z-Axis)",
            2: "Shoulder",
            3: "Elbow",
            4: "Wrist",
            5: "Gripper"
        }
        
        self.angle_vars = {} # To store StringVar for labels
        
        for id in range(1, 6):
            frame = ttk.Frame(controls_frame)
            frame.pack(fill="x", padx=5, pady=5)
            
            lbl = ttk.Label(frame, text=f"{labels[id]} (ID {id}):")
            lbl.pack(anchor="w")
            
            # Row for Minus | Value | Plus
            control_row = ttk.Frame(frame)
            control_row.pack(fill="x", expand=True)

            # Minus Button
            minus_btn = ttk.Button(control_row, text="-", width=5)
            minus_btn.pack(side="left", padx=5)
            minus_btn.bind("<ButtonPress-1>", lambda event, s_id=id: self.start_move(s_id, -1))
            minus_btn.bind("<ButtonRelease-1>", self.stop_move)

            # Value Label (replaces Slider)
            self.angle_vars[id] = tk.StringVar(value=str(self.servo_angles[id]))
            val_lbl = ttk.Label(control_row, textvariable=self.angle_vars[id], width=5, anchor="center", font=("Arial", 14, "bold"))
            val_lbl.pack(side="left", fill="x", expand=True, padx=5)

            # Plus Button
            plus_btn = ttk.Button(control_row, text="+", width=5)
            plus_btn.pack(side="left", padx=5)
            plus_btn.bind("<ButtonPress-1>", lambda event, s_id=id: self.start_move(s_id, 1))
            plus_btn.bind("<ButtonRelease-1>", self.stop_move)

        # --- Presets Frame ---
        presets_frame = ttk.LabelFrame(self.root, text="Presets")
        presets_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(presets_frame, text="Home (Upright)", command=self.preset_home).pack(side="left", padx=10, pady=10)

        # --- Status Bar ---
        self.status_var = tk.StringVar()
        self.status_var.set("Disconnected")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.pack(side="bottom", fill="x")
        
        # State for hold-to-move
        self.move_job = None
        self.move_direction = 0 # -1 or 1
        self.current_moving_servo = None

    def start_move(self, servo_id, direction):
        self.move_direction = direction
        self.current_moving_servo = servo_id
        self.move_servo_step()

    def stop_move(self, event=None):
        if self.move_job:
            self.root.after_cancel(self.move_job)
            self.move_job = None
        self.move_direction = 0
        self.current_moving_servo = None

    def move_servo_step(self):
        if self.current_moving_servo is not None and self.move_direction != 0:
            current_val = self.servo_angles[self.current_moving_servo]
            new_val = current_val + self.move_direction
            
            # Clamp value
            if 0 <= new_val <= 180:
                self.set_single_servo(self.current_moving_servo, new_val)
            
            # Schedule next step
            self.move_job = self.root.after(50, self.move_servo_step)



    def update_ports(self):
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        self.port_combo['values'] = port_list
        if port_list:
            self.port_combo.current(0)
            
    def toggle_connection(self):
        if not self.is_connected:
            try:
                port = self.port_var.get()
                if not port:
                    messagebox.showerror("Error", "No port selected")
                    return
                    
                self.ser = serial.Serial(port, 9600, timeout=2)
                
                # Wait for Arduino Auto-Reset and Handshake
                self.status_var.set("Connecting... Waiting for device...")
                self.root.update()
                
                # Retrieve Handshake
                time.sleep(2) # Wait for bootloader
                handshake = ""
                if self.ser.in_waiting > 0:
                    handshake = self.ser.readline().decode('utf-8').strip()
                
                device_type = "Generic"
                if "READY_NANO" in handshake:
                    device_type = "Arduino Nano"
                elif "READY" in handshake:
                    device_type = "Arduino Uno"
                
                self.is_connected = True
                self.connect_btn.config(text="Disconnect")
                self.status_var.set(f"Connected to {device_type} ({port})")
                self.preset_home() # Sync position
                
                # Start Monitoring
                self.monitor_job = self.root.after(1000, self.check_connection_monitor)
                
            except Exception as e:
                messagebox.showerror("Connection Error", str(e))
                self.perform_disconnect()
        else:
            self.perform_disconnect()

    def perform_disconnect(self):
        if self.ser:
            try:
                self.ser.close()
            except:
                pass
        self.ser = None
        self.is_connected = False
        self.connect_btn.config(text="Connect")
        self.status_var.set("Disconnected")
        
        # Cancel monitor if running
        if hasattr(self, 'monitor_job') and self.monitor_job:
            self.root.after_cancel(self.monitor_job)
            self.monitor_job = None

    def check_connection_monitor(self):
        if self.is_connected and self.ser:
            try:
                # 1. Simple check: Check if port still exists in system
                ports = [p.device for p in serial.tools.list_ports.comports()]
                if self.ser.port not in ports:
                    raise serial.SerialException("Device not found")
                
                # 2. IO Check: Try reading in_waiting (low cost)
                _ = self.ser.in_waiting
                
                # Schedule next check
                self.monitor_job = self.root.after(1000, self.check_connection_monitor)
            except (serial.SerialException, OSError):
                self.perform_disconnect()
                messagebox.showerror("Error", "Device Disconnected")
        elif not self.is_connected:
            # Should not happen but safety cleanup
            if hasattr(self, 'monitor_job') and self.monitor_job:
                self.root.after_cancel(self.monitor_job)
                self.monitor_job = None

    def send_command(self, servo_id, angle):
        if self.is_connected and self.ser:
            try:
                # Command format: S<ID>:<Angle>\n
                # Check bounds
                angle = max(0, min(180, int(angle)))
                cmd = f"S{servo_id}:{angle}\n"
                self.ser.write(cmd.encode('utf-8'))
                # Optional: Read response if needed
                # print(f"Sent: {cmd.strip()}") 
            except Exception as e:
                print(f"Serial Error: {e}")
                self.perform_disconnect()
                messagebox.showerror("Error", f"Command Failed: {e}")

    def set_single_servo(self, servo_id, angle):
        angle = int(angle)
        self.servo_angles[servo_id] = angle
        # Update display
        if servo_id in self.angle_vars:
            self.angle_vars[servo_id].set(str(angle))
        # Send command
        self.send_command(servo_id, angle)
        
    def preset_home(self):
        """Move all servos to Home (90 degrees default)"""
        target_angles = {
            1: 90,
            2: 90,
            3: 90,
            4: 90,
            5: 90
        }
        self.apply_preset(target_angles)

    def apply_preset(self, target_angles):
        # Stop any manual holding movement
        self.stop_move()
        
        # Calculate steps for smooth transition
        start_angles = self.servo_angles.copy()
        
        # Find maximum distance to travel
        max_delta = 0
        for id, target in target_angles.items():
            if id in start_angles:
                current = start_angles[id]
                max_delta = max(max_delta, abs(target - current))
        
        if max_delta == 0: return

        # Speed configuration
        step_size = 2 # degrees per frame
        interval_ms = 20 # milliseconds between frames
        
        total_steps = int(max_delta / step_size)
        if total_steps < 1: total_steps = 1
        
        self.animate_preset(target_angles, start_angles, total_steps, 1, interval_ms)

    def animate_preset(self, targets, starts, total_steps, current_step, interval):
        if current_step > total_steps:
            # Finalize to exact target
            for id, target in targets.items():
                if id in self.angle_vars:
                    self.set_single_servo(id, target)
            return

        progress = current_step / total_steps
        
        for id, target in targets.items():
            if id in self.angle_vars:
                start = starts.get(id, target) # Fallback to target if missing
                # Linear Interpolation
                new_angle = start + (target - start) * progress
                self.set_single_servo(id, int(new_angle))
        
        # Schedule next frame
        # We use a unique job name or just a variable if we want to cancel it later
        # For now, simple recursion is fine as long as we don't spam presets.
        self.root.after(interval, lambda: self.animate_preset(targets, starts, total_steps, current_step + 1, interval))

if __name__ == "__main__":
    root = tk.Tk()
    app = RoboticArmApp(root)
    root.mainloop()

# -------------------------------------------------------------------------
# CALIBRATION GUIDE
# -------------------------------------------------------------------------
# If your robot arm is not pointing straight up when all sliders are at 0:
# 1. Unpower the servos.
# 2. Physically remove the servo horns (arms) from the splines.
# 3. Connect the Arduino and run this software.
# 4. Click "Home" (Sends 0 degrees to all servos).
# 5. Re-attach the servo horns so that the arm segments are legally aligned 
#    (pointing straight up or however you define '0').
# 6. Secure the screws.
# 
# If the servo range is inverted (scaling 0-180 moves it backwards):
# - You would need to invert the value in code before sending:
#   angle = 180 - angle
#   (Modify send_command or on_slider_change)
# -------------------------------------------------------------------------

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import serial
import time

# --- CONFIGURATION ---
H_BASE = 75.0
L_SHOULDER = 55.0
L_ELBOW = 50.0
L_WRIST = 45.0
SERIAL_PORT = '/dev/cu.usbserial-A1080HTD'
BAUD_RATE = 9600

ser = None
current_angles_to_send = None  # Stores calculated angles


# --- MATH CORE ---
def get_transformation_matrix(theta, d, a, alpha):
    c, s = np.cos(theta), np.sin(theta)
    ca, sa = np.cos(alpha), np.sin(alpha)
    return np.array([
        [c, -s * ca, s * sa, a * c],
        [s, c * ca, -c * sa, a * s],
        [0, sa, ca, d],
        [0, 0, 0, 1]
    ])


def forward_kinematics_chain(thetas):
    t1, t2, t3, t4 = thetas
    T01 = get_transformation_matrix(t1, H_BASE, 0, np.pi / 2)
    T12 = get_transformation_matrix(t2, 0, L_SHOULDER, 0)
    T23 = get_transformation_matrix(t3, 0, L_ELBOW, 0)
    T34 = get_transformation_matrix(t4, 0, L_WRIST, 0)

    P0 = np.array([0, 0, 0, 1])
    P1 = T01 @ P0
    P2 = (T01 @ T12) @ P0
    P3 = (T01 @ T12 @ T23) @ P0
    P4 = (T01 @ T12 @ T23 @ T34) @ P0

    return [P0[:3], P1[:3], P2[:3], P3[:3], P4[:3]], P4[:3]


def inverse_kinematics_jacobian(target_pos, target_pitch_deg):
    target_x, target_y, target_z = target_pos
    target_pitch_rad = np.radians(target_pitch_deg)

    # Initial Guess
    guess_base = np.arctan2(target_y, target_x)
    current_thetas = np.array([guess_base, np.radians(45), np.radians(-45), np.radians(-45)])

    learning_rate = 0.2

    for i in range(50):
        joints, tip_pos = forward_kinematics_chain(current_thetas)[0:2]
        curr_x, curr_y, curr_z = tip_pos
        curr_pitch = current_thetas[1] + current_thetas[2] + current_thetas[3]

        err = np.array([
            target_x - curr_x,
            target_y - curr_y,
            target_z - curr_z,
            target_pitch_rad - curr_pitch
        ])

        if np.linalg.norm(err[:3]) < 0.5: break

        J = np.zeros((4, 4))
        delta = 1e-4
        for j in range(4):
            temp_thetas = current_thetas.copy()
            temp_thetas[j] += delta
            _, temp_pos = forward_kinematics_chain(temp_thetas)[0:2]
            temp_pitch = temp_thetas[1] + temp_thetas[2] + temp_thetas[3]
            J[0, j] = (temp_pos[0] - curr_x) / delta
            J[1, j] = (temp_pos[1] - curr_y) / delta
            J[2, j] = (temp_pos[2] - curr_z) / delta
            J[3, j] = (temp_pitch - curr_pitch) / delta

        d_theta = np.linalg.pinv(J) @ err
        current_thetas += d_theta * learning_rate

        # SAFETY CLAMPS
        limit = np.pi / 2 + 0.1
        current_thetas[1] = np.clip(current_thetas[1], -limit, limit)
        current_thetas[2] = np.clip(current_thetas[2], -limit, limit)
        current_thetas[3] = np.clip(current_thetas[3], -limit, limit)

    t1, t2, t3, t4 = current_thetas
    b_deg = int(np.degrees(t1) + 90)
    s_deg = int(np.degrees(t2))
    e_deg = int(np.degrees(t3) + 90)
    w_deg = int(np.degrees(t4) + 90)

    return [b_deg, s_deg, e_deg, w_deg]


# --- GUI LOGIC ---
def connect_serial():
    global ser
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        time.sleep(2)
        status_lbl.config(text=f"Connected: {SERIAL_PORT}", fg="green")
    except:
        status_lbl.config(text="Simulation Mode", fg="red")


def send_command(angles):
    if not angles: return
    b, s, e, w, g = angles
    # Clamp final output
    b = max(0, min(180, b))
    s = max(0, min(180, s))
    e = max(0, min(180, e))
    w = max(0, min(180, w))
    g = max(90, min(130, g))

    cmd = f"{b},{s},{e},{w},{g}\n"
    if ser:
        try:
            ser.write(cmd.encode())
            print(f"Sent: {cmd.strip()}")
        except:
            pass


# --- BUTTON FUNCTIONS ---
def calculate_preview():
    """Only calculates math and updates the plot"""
    global current_angles_to_send
    try:
        x = float(ent_x.get())
        y = float(ent_y.get())
        z = float(ent_z.get())
        p = float(ent_p.get())
        g = int(ent_g.get())
    except:
        status_lbl.config(text="Invalid Input Numbers", fg="red")
        return

    # 1. Run Math
    angles = inverse_kinematics_jacobian([x, y, z], p)
    b, s, e, w = angles

    # 2. Store for later
    current_angles_to_send = [b, s, e, w, g]

    # 3. Update Label
    lbl_ang.config(text=f"Preview: B:{b} S:{s} E:{e} W:{w}")

    # 4. Draw Plot
    math_thetas = [np.radians(b - 90), np.radians(s), np.radians(e - 90), np.radians(w - 90)]
    joints = forward_kinematics_chain(math_thetas)[0]

    ax.clear()
    xs, ys, zs = [p[0] for p in joints], [p[1] for p in joints], [p[2] for p in joints]
    ax.plot(xs, ys, zs, 'o-', lw=5, color='blue')
    ax.scatter([x], [y], [z], c='red', marker='x', s=100)
    ax.set_xlim(-200, 200);
    ax.set_ylim(-200, 200);
    ax.set_zlim(0, 300)
    ax.set_xlabel('X');
    ax.set_ylabel('Y');
    ax.set_zlabel('Z')
    canvas.draw()

    status_lbl.config(text="Preview Updated. Click MOVE to send.", fg="blue")


def execute_move():
    """Sends the already calculated angles to the robot"""
    if current_angles_to_send:
        send_command(current_angles_to_send)
        status_lbl.config(text="Command Sent!", fg="green")
    else:
        status_lbl.config(text="Click 'UPDATE VIEW' first!", fg="orange")


def force_reset():
    """Resets GUI and Robot to Home"""
    # 1. Reset Text
    ent_x.delete(0, tk.END);
    ent_x.insert(0, "0")
    ent_y.delete(0, tk.END);
    ent_y.insert(0, "0")
    ent_z.delete(0, tk.END);
    ent_z.insert(0, "225")
    ent_p.delete(0, tk.END);
    ent_p.insert(0, "90")
    ent_g.delete(0, tk.END);
    ent_g.insert(0, "90")

    # 2. Force Robot Move
    print("Forcing Reset...")
    send_command([90, 90, 90, 90, 90])

    # 3. Update Plot to match
    lbl_ang.config(text="Reset: 90 90 90 90")
    math_thetas = [0, np.radians(90), 0, 0]  # Straight up in math terms
    joints = forward_kinematics_chain(math_thetas)[0]

    ax.clear()
    xs, ys, zs = [p[0] for p in joints], [p[1] for p in joints], [p[2] for p in joints]
    ax.plot(xs, ys, zs, 'o-', lw=5, color='blue')
    ax.set_xlim(-200, 200);
    ax.set_ylim(-200, 200);
    ax.set_zlim(0, 300)
    canvas.draw()
    status_lbl.config(text="Reset Complete", fg="black")


# --- LAYOUT ---
root = tk.Tk()
root.title("Preview & Move Controller")
root.geometry("1000x600")

f_ctrl = tk.Frame(root, padx=20, pady=20)
f_ctrl.pack(side=tk.LEFT, fill=tk.Y)


def make_inp(lbl, val):
    f = tk.Frame(f_ctrl);
    f.pack(fill=tk.X, pady=2)
    tk.Label(f, text=lbl, width=10).pack(side=tk.LEFT)
    e = tk.Entry(f, width=10);
    e.insert(0, val);
    e.pack(side=tk.RIGHT)
    return e


tk.Label(f_ctrl, text="Control Panel", font=("Arial", 14, "bold")).pack(pady=10)

ent_x = make_inp("X:", "0")
ent_y = make_inp("Y:", "0")
ent_z = make_inp("Z:", "225")
ent_p = make_inp("Pitch:", "90")
ent_g = make_inp("Grip:", "90")

# --- BUTTONS ---
tk.Button(f_ctrl, text="1. UPDATE VIEW", command=calculate_preview, height=2).pack(pady=(20, 5), fill=tk.X)
tk.Button(f_ctrl, text="2. MOVE ROBOT", command=execute_move, height=2, bg="#dddddd").pack(pady=5, fill=tk.X)
tk.Button(f_ctrl, text="RESET HOME", command=force_reset, fg="red").pack(pady=20, fill=tk.X)

lbl_ang = tk.Label(f_ctrl, text="--", font=("Courier", 10))
lbl_ang.pack(pady=10)
status_lbl = tk.Label(f_ctrl, text="Connecting...", fg="blue")
status_lbl.pack(side=tk.BOTTOM)

fig = plt.figure(figsize=(5, 5))
ax = fig.add_subplot(111, projection='3d')
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

root.after(100, connect_serial)
root.mainloop()

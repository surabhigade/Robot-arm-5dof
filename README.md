# 5DOF 3D Printed Robot Arm 
This project demonstrates a complete pipeline from mechanical design to mathematical control of a 5DOF robotic arm.

The system allows commanding real-world Cartesian coordinates (X, Y, Z, Pitch) instead of manually tuning servo angles.

---
## 1. Blog Documentation

Full project write-up and detailed explanation:
 
🔗 [Read the Blog Here]((https://medium.com/p/e40b554355a6))

---

## 2. Project Overview

This robot arm is built using micro servos (MG90S / SG90) and 3D printed components.

The control system is split into two layers:
  - Python → Performs kinematics, visualization, and motion planning
  - Arduino → Executes final servo commands

The result is a coordinate-driven robotic system with live 3D preview and Jacobian-based inverse kinematics.

---
## 3. Features
- Cartesian control (X, Y, Z, Wrist Pitch)
- 3D visualization using Matplotlib
- Denavit-Hartenberg based Forward Kinematics
- Jacobian pseudo-inverse Inverse Kinematics solver
- Serial communication with Arduino
- Preview-before-move architecture

---

## 4. How to Run

1. Update SERIAL_PORT inside the Python script.

2. Upload Arduino firmware to Nano.

3. Run the Python controller:
  
  python ik_GUI.py
  
4. Click "UPDATE VIEW" to preview.

5. Click "MOVE ROBOT" to execute.
---


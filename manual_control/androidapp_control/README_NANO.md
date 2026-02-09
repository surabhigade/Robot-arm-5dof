# Arduino Nano Setup - Robotic Arm

This project supports **Arduino Nano** as a controller. The logic and pinouts are compatible with the default configuration, but this guide provides specific details for the Nano form factor.

## Key Differences
- **Size**: Nano is breadboard-friendly.
- **USB**: Typically uses **Mini-USB** (older clones) or **USB-C** (newer revisions).
- **Pinout**: While pin numbers match (D3, D5 etc.), the physical location differs from the Uno header layout.

## Pinout Map (Nano)

Connect Servos to these Digital Pins (PWM capable):

| Joint | Servo ID | Nano Pin |
|-------|----------|----------|
| **Base** | 1 | **D3** |
| **Shoulder** | 2 | **D5** |
| **Elbow** | 3 | **D6** |
| **Wrist** | 4 | **D9** |
| **Gripper** | 5 | **D10** |

## Wiring Guide
1. **Power**: 
   - Plug the Nano into a breadboard.
   - Connect Servo **GND** and **5V** to an external power rail (Power Supply).
   - **IMPORTANT**: Connect the Power Supply **GND** to the Nano **GND**.
   - **DO NOT** power servos from the Nano's `5V` pin directly; it cannot handle the current.

2. **Signals**:
   - Jumper wires from the Nano pins ($D3, D5, D6, D9, D10$) to the Servo Signal pins (Orange/Yellow).

## Installation
1. Open `robotic_arm_firmware_nano/robotic_arm_firmware_nano.ino` in Arduino IDE.
2. Go to **Tools > Board** and select **Arduino Nano**.
3. **Processor Selection** (Crucial for Clones):
   - Try **ATmega328P** first.
   - If upload fails, try **ATmega328P (Old Bootloader)**.
4. Select Port and Upload.

## Using the Python Controller
The Python controller works identically for both Uno and Nano.
1. Run `python arm_controller.py`.
2. Select the new COM port (often shows as `USB Serial` or `CH340`).
3. Connect and Control.

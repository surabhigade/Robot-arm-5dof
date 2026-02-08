#include <Servo.h>

Servo base, shoulder, elbow, wrist, gripper;

// PINS
const int pinBase = 3;
const int pinShoulder = 5;
const int pinElbow = 6;
const int pinWrist = 9;
const int pinGripper = 10;

// --- TUNING ---
const long STEP_DELAY = 30; 

// DATA
String inputString = "";
bool stringComplete = false;

float currentAngles[5] = {90, 90, 90, 90, 90}; 
int targetAngles[5] = {90, 90, 90, 90, 90};

unsigned long lastMoveTime = 0;

void setup() {
  Serial.begin(9600);
  base.attach(pinBase);
  shoulder.attach(pinShoulder);
  elbow.attach(pinElbow);
  wrist.attach(pinWrist);
  gripper.attach(pinGripper);

  // Snap to home immediately on startup
  writeServos();
}

void loop() {
  // 1. Process Incoming Data
  if (stringComplete) {
    parseData();
    inputString = "";
    stringComplete = false;
  }

  // 2. Smooth Movement Handler (Non-Blocking)
  if (millis() - lastMoveTime >= STEP_DELAY) {
    lastMoveTime = millis();
    updatePositions();
  }
}

void updatePositions() {
  bool moved = false;
  // Move 1 degree at a time towards target
  float step = 1.0; 

  for (int i = 0; i < 5; i++) {
    float diff = targetAngles[i] - currentAngles[i];
    
    if (abs(diff) > 0.5) { // If we are not at target
      if (diff > 0) currentAngles[i] += step;
      else currentAngles[i] -= step;
      moved = true;
    }
  }

  if (moved) writeServos();
}

void writeServos() {
  base.write((int)currentAngles[0]);
  shoulder.write((int)currentAngles[1]);
  elbow.write((int)currentAngles[2]);
  wrist.write((int)currentAngles[3]);
  gripper.write((int)currentAngles[4]);
}

void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    inputString += inChar;
    if (inChar == '\n') stringComplete = true;
  }
}

void parseData() {
  // Expects: "90,90,90,90,90"
  int idx1 = inputString.indexOf(',');
  int idx2 = inputString.indexOf(',', idx1 + 1);
  int idx3 = inputString.indexOf(',', idx2 + 1);
  int idx4 = inputString.indexOf(',', idx3 + 1);

  if (idx1 > 0 && idx4 > 0) {
    targetAngles[0] = inputString.substring(0, idx1).toInt();
    targetAngles[1] = inputString.substring(idx1 + 1, idx2).toInt();
    targetAngles[2] = inputString.substring(idx2 + 1, idx3).toInt();
    targetAngles[3] = inputString.substring(idx3 + 1, idx4).toInt();
    targetAngles[4] = inputString.substring(idx4 + 1).toInt();
  }
}

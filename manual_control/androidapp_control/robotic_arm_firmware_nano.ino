/**
 * 5-DOF Robotic Arm Firmware - Arduino Nano Version
 *
 * Hardware Config (Nano):
 * - Base: Pin 3
 * - Shoulder: Pin 5
 * - Elbow: Pin 6
 * - Wrist: Pin 9
 * - Gripper: Pin 10
 *
 * Protocol:
 * comma-separated commands: S<ID>:<Angle>
 * Example: S1:90,S2:45\n
 */

#include <Servo.h>

// Servo Objects
Servo baseServo;     // ID 1
Servo shoulderServo; // ID 2
Servo elbowServo;    // ID 3
Servo wristServo;    // ID 4
Servo gripServo;     // ID 5

// Pin Definitions (Nano and Uno share these PWM pins)
const int PIN_BASE = 3;
const int PIN_SHOULDER = 5;
const int PIN_ELBOW = 6;
const int PIN_WRIST = 9;
const int PIN_GRIP = 10;

// Current States
int valBase = 90;
int valShoulder = 90;
int valElbow = 90;
int valWrist = 90;
int valGrip = 90; // 0 = Open, 180 = Closed (approx)

String inputString = "";     // a String to hold incoming data
bool stringComplete = false; // whether the string is complete

void setup() {
  // Initialize Serial
  Serial.begin(9600);
  inputString.reserve(200);

  // Attach Servos
  baseServo.attach(PIN_BASE);
  shoulderServo.attach(PIN_SHOULDER);
  elbowServo.attach(PIN_ELBOW);
  wristServo.attach(PIN_WRIST);
  gripServo.attach(PIN_GRIP);

  // Move to Home/Initial Position
  homeServos();
  Serial.println("READY_NANO"); // Modified handshake to confirm Nano firmware
}

void loop() {
  if (stringComplete) {
    parseCommand(inputString);
    // clear the string:
    inputString = "";
    stringComplete = false;
  }
}

void homeServos() {
  baseServo.write(90);
  shoulderServo.write(90);
  elbowServo.write(90);
  wristServo.write(90);
  gripServo.write(90);
}

/*
  SerialEvent occurs whenever a new data comes in the hardware serial RX. This
  routine is run between each time loop() runs, so using delay inside loop can
  delay response. Multiple bytes of data may be available.
*/
void serialEvent() {
  while (Serial.available()) {
    // get the new byte:
    char inChar = (char)Serial.read();
    // add it to the inputString:
    inputString += inChar;
    // if the incoming character is a newline, set a flag so the main loop can
    // do something about it:
    if (inChar == '\n') {
      stringComplete = true;
    }
  }
}

void parseCommand(String command) {
  // Expected format: S1:90,S2:45...
  int startIndex = 0;
  int commaIndex = command.indexOf(',');

  while (true) {
    String segment;
    if (commaIndex == -1) {
      segment = command.substring(startIndex); // Last segment
    } else {
      segment = command.substring(startIndex, commaIndex);
    }

    segment.trim();
    if (segment.length() > 0) {
      processSegment(segment);
    }

    if (commaIndex == -1)
      break;
    startIndex = commaIndex + 1;
    commaIndex = command.indexOf(',', startIndex);
  }
}

void processSegment(String segment) {
  // Segment e.g. "S1:90"
  if (segment.charAt(0) == 'S') {
    int colonIndex = segment.indexOf(':');
    if (colonIndex > 1) {
      int id = segment.substring(1, colonIndex).toInt();
      int angle = segment.substring(colonIndex + 1).toInt();

      // Constraint check
      if (angle < 0)
        angle = 0;
      if (angle > 180)
        angle = 180;

      switch (id) {
      case 1:
        baseServo.write(angle);
        break;
      case 2:
        shoulderServo.write(angle);
        break;
      case 3:
        elbowServo.write(angle);
        break;
      case 4:
        wristServo.write(angle);
        break;
      case 5:
        gripServo.write(angle);
        break;
      }
    }
  }
}

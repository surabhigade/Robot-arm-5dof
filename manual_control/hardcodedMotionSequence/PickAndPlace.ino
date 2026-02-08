#include <Servo.h>

// --- 1. CONFIGURATION: OBJECTS ---
Servo base;
Servo shoulder;
Servo elbow;
Servo wrist;
Servo gripper;

// --- 2. CONFIGURATION: PINS ---
const int basePin = 3;
const int shoulderPin = 5;
const int elbowPin = 6;
const int wristPin = 9;
const int gripperPin = 10;

// --- 3. CONFIGURATION: ANGLES ---

// HOME Position
int homeBase = 90;
int homeShoulder = 90; 
int homeElbow = 90;    
int homeWrist = 90;
int homeGripper = 130; 

// PICKUP Position 
int pickBase = 135;      
int pickShoulder = 150;  
int pickElbow = 150;     
int pickWrist = 130;      

// DROPOFF Position
int dropBase = 45;       
int dropShoulder = 150;
int dropElbow = 150;
int dropWrist = 130;

// GRIPPER ANGLES
int gripperClosed = 85; 
int gripperOpen = 130;

// SPEED CONTROL
int moveSpeed = 30; 

void setup() {
  Serial.begin(9600);
  Serial.println("Initializing Soft Start...");

  // --- SOFT START ---
  base.write(homeBase);
  shoulder.write(homeShoulder);
  elbow.write(homeElbow);
  wrist.write(homeWrist);
  gripper.write(homeGripper);
  
  delay(100); 

  base.attach(basePin);
  shoulder.attach(shoulderPin);
  elbow.attach(elbowPin);
  wrist.attach(wristPin);
  gripper.attach(gripperPin);

  Serial.println("Arm Ready. Waiting 2 seconds...");
  delay(2000); 
}

void loop() {
  // 1. Move to Pick
  Serial.println("Moving to Pick...");
  moveServo(base, pickBase);
  moveServo(shoulder, pickShoulder);
  moveServo(elbow, pickElbow);
  moveServo(wrist, pickWrist);
  delay(1000);

  // 2. Grab
  Serial.println("Grabbing...");
  moveServo(gripper, gripperClosed);
  delay(500);

  // 3. Lift to Home (Safety move before rotating)
  Serial.println("Lifting...");
  moveServo(shoulder, homeShoulder);
  moveServo(elbow, homeElbow);
  delay(500);

  // 4. Move to Drop
  Serial.println("Moving to Drop...");
  moveServo(base, dropBase);
  moveServo(shoulder, dropShoulder);
  moveServo(elbow, dropElbow);
  moveServo(wrist, dropWrist);
  delay(1000);

  // 5. Release
  Serial.println("Releasing...");
  moveServo(gripper, gripperOpen);
  delay(500);

  // 6. Lift
  Serial.println("Clearing Drop Zone...");
  moveServo(shoulder, homeShoulder); 
  moveServo(elbow, homeElbow);       
  delay(500);
  Serial.println("Going Home...");
  moveServo(base, homeBase);
  moveServo(wrist, homeWrist);
  
  delay(2000); 
}

// --- HELPER: SMOOTH MOVEMENT ---
void moveServo(Servo &servo, int targetAngle) {
  int currentAngle = servo.read();
  
  if (currentAngle < targetAngle) {
    for (int i = currentAngle; i <= targetAngle; i++) {
      servo.write(i);
      delay(moveSpeed); 
    }
  } else {
    for (int i = currentAngle; i >= targetAngle; i--) {
      servo.write(i);
      delay(moveSpeed);
    }
  }
}

// --- HELPER: HOME ---
void moveToHome() {
  moveServo(gripper, homeGripper); 
  moveServo(shoulder, homeShoulder);
  moveServo(elbow, homeElbow);
  moveServo(wrist, homeWrist);
  moveServo(base, homeBase); 
}

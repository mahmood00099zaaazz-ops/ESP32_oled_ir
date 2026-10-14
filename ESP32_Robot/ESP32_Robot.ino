// ESP32 obstacle-avoiding robot with OLED "robot eyes".
// Builds on OLED_IR_CODE.ino: the same OLED (U8g2) and IR sensor on GPIO34,
// plus an L298N driver with two DC motors.
//
// Behaviour:
//   - No obstacle  -> drive forward, eyes blink.
//   - Obstacle     -> stop, eyes look up (surprised), reverse, turn, carry on.

#include <U8g2lib.h>
#include <Wire.h>

U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, /* reset=*/U8X8_PIN_NONE);

// ---------- Pins ----------
const int IR_PIN = 34;      // IR obstacle sensor OUT (LOW = obstacle)

const int ENA = 25;         // left motor speed (PWM)
const int IN1 = 26;         // left motor direction
const int IN2 = 27;
const int ENB = 14;         // right motor speed (PWM)
const int IN3 = 33;         // right motor direction
const int IN4 = 32;

// ---------- Tuning ----------
const int SPEED_FORWARD = 180;   // 0..255
const int SPEED_TURN    = 170;
const unsigned long STOP_TIME    = 300;  // ms
const unsigned long REVERSE_TIME = 400;  // ms
const unsigned long TURN_TIME    = 450;  // ms

// ---------- Robot state ----------
enum RobotState { FORWARD, STOPPING, REVERSING, TURNING };
RobotState robotState = FORWARD;
unsigned long stateStart = 0;

// ---------- Eye animation (from OLED_IR_CODE.ino) ----------
enum EyeState { EYE_OPEN, EYE_CLOSE, EYE_IDLE };
EyeState eyeState = EYE_IDLE;
unsigned long eyeMillis = 0;
const long interval1 = 1000; // eyes open for 1 s
const long interval2 = 300;  // eyes closed for 300 ms

void setup() {
  pinMode(IR_PIN, INPUT);

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  pinMode(ENA, OUTPUT);
  pinMode(ENB, OUTPUT);
  stopMotors();

  u8g2.begin();
  eye_open();
  delay(1000);  // short pause before the robot starts moving
}

void loop() {
  unsigned long now = millis();
  bool obstacle = (digitalRead(IR_PIN) == LOW);

  switch (robotState) {
    case FORWARD:
      if (obstacle) {
        stopMotors();
        eye_up();
        changeState(STOPPING, now);
      } else {
        drive(SPEED_FORWARD, SPEED_FORWARD);
        blinkEyes(now);
      }
      break;

    case STOPPING:
      if (now - stateStart >= STOP_TIME) {
        drive(-SPEED_FORWARD, -SPEED_FORWARD);
        changeState(REVERSING, now);
      }
      break;

    case REVERSING:
      if (now - stateStart >= REVERSE_TIME) {
        drive(-SPEED_TURN, SPEED_TURN);  // spin left in place
        eye_close();
        changeState(TURNING, now);
      }
      break;

    case TURNING:
      // Keep turning until the turn time is over and the path is clear.
      if (now - stateStart >= TURN_TIME && !obstacle) {
        eyeState = EYE_IDLE;
        changeState(FORWARD, now);
      }
      break;
  }
}

void changeState(RobotState next, unsigned long now) {
  robotState = next;
  stateStart = now;
}

// ---------- Motors ----------
// speed: -255..255, negative = backwards
void setMotor(int en, int inA, int inB, int speed) {
  speed = constrain(speed, -255, 255);
  digitalWrite(inA, speed > 0 ? HIGH : LOW);
  digitalWrite(inB, speed < 0 ? HIGH : LOW);
  analogWrite(en, abs(speed));
}

void drive(int left, int right) {
  setMotor(ENA, IN1, IN2, left);
  setMotor(ENB, IN3, IN4, right);
}

void stopMotors() {
  drive(0, 0);
}

// ---------- Eyes ----------
void blinkEyes(unsigned long now) {
  switch (eyeState) {
    case EYE_IDLE:
      eye_open();
      eyeMillis = now;
      eyeState = EYE_CLOSE;
      break;

    case EYE_CLOSE:
      if (now - eyeMillis >= interval1) {
        eye_close();
        eyeMillis = now;
        eyeState = EYE_OPEN;
      }
      break;

    case EYE_OPEN:
      if (now - eyeMillis >= interval2) {
        eye_open();
        eyeMillis = now;
        eyeState = EYE_IDLE;
      }
      break;
  }
}

void eye_up() {
  u8g2.clearBuffer();
  u8g2.setFontMode(1);
  u8g2.setBitmapMode(1);
  u8g2.drawBox(80, 12, 40, 20);
  u8g2.drawBox(10, 12, 40, 20);
  u8g2.drawFilledEllipse(99.5, 13, 19.5, 11);
  u8g2.drawFilledEllipse(29.5, 13, 19.5, 11);
  u8g2.sendBuffer();
}

void eye_open() {
  u8g2.clearBuffer();
  u8g2.setBitmapMode(1);
  u8g2.drawBox(14, 13, 36, 36);
  u8g2.drawBox(78, 13, 36, 36);
  u8g2.sendBuffer();
}

void eye_close() {
  u8g2.clearBuffer();
  u8g2.setBitmapMode(1);
  u8g2.drawBox(14, 27, 36, 7);
  u8g2.drawBox(78, 27, 36, 7);
  u8g2.sendBuffer();
}

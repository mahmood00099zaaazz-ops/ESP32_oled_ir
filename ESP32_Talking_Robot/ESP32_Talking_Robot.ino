// ESP32 talking robot — Kurdish (Badini), Arabic and English.
// Builds on ESP32_Robot: OLED eyes, IR sensor and L298N motors, plus
//   - a DFPlayer Mini + speaker that plays recorded MP3 phrases, and
//   - the same phrases written on the OLED (pictures from texts.h).
// A push button switches the language: Kurdish -> Arabic -> English.
//
// microSD card layout (the folder number is the language):
//   /01/001.mp3 .. 004.mp3   Kurdish
//   /02/001.mp3 .. 004.mp3   Arabic
//   /03/001.mp3 .. 004.mp3   English
// File 001 = greeting, 002 = obstacle, 003 = path clear, 004 = language name.

#include <U8g2lib.h>
#include <Wire.h>
#include <DFRobotDFPlayerMini.h>
#include "texts.h"

U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, /* reset=*/U8X8_PIN_NONE);
DFRobotDFPlayerMini player;

// ---------- Pins ----------
const int IR_PIN = 34;      // IR obstacle sensor OUT (LOW = obstacle)
const int BUTTON_PIN = 4;   // push button to GND, changes the language

const int ENA = 25;         // left motor speed (PWM)
const int IN1 = 26;         // left motor direction
const int IN2 = 27;
const int ENB = 14;         // right motor speed (PWM)
const int IN3 = 33;         // right motor direction
const int IN4 = 32;

const int DF_RX = 16;       // ESP32 RX2  <- DFPlayer TX
const int DF_TX = 17;       // ESP32 TX2  -> DFPlayer RX (through a 1k resistor)

// ---------- Tuning ----------
const bool USE_MOTORS = true;    // false = test talking without moving
const int VOLUME = 25;           // 0..30

const int SPEED_FORWARD = 180;   // 0..255
const int SPEED_TURN    = 170;
const unsigned long STOP_TIME    = 1500; // ms, long enough to say the phrase
const unsigned long REVERSE_TIME = 400;  // ms
const unsigned long TURN_TIME    = 450;  // ms
const unsigned long TEXT_TIME    = 2000; // ms a phrase stays on the screen

// ---------- Language and phrases ----------
enum Language { KURDISH, ARABIC, ENGLISH };
enum Phrase { GREETING, OBSTACLE, CLEAR, LANGUAGE_NAME };

Language language = KURDISH;
bool playerReady = false;
unsigned long textUntil = 0;     // eyes wait until this time

// ---------- Robot state ----------
enum RobotState { FORWARD, STOPPING, REVERSING, TURNING };
RobotState robotState = FORWARD;
unsigned long stateStart = 0;

// ---------- Eye animation ----------
enum EyeState { EYE_OPEN, EYE_CLOSE, EYE_IDLE };
EyeState eyeState = EYE_IDLE;
unsigned long eyeMillis = 0;
const long interval1 = 1000; // eyes open for 1 s
const long interval2 = 300;  // eyes closed for 300 ms

// ---------- Button ----------
int lastButton = HIGH;
unsigned long lastButtonChange = 0;

void setup() {
  pinMode(IR_PIN, INPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  pinMode(ENA, OUTPUT);
  pinMode(ENB, OUTPUT);
  stopMotors();

  Serial.begin(115200);
  u8g2.begin();

  Serial2.begin(9600, SERIAL_8N1, DF_RX, DF_TX);
  playerReady = player.begin(Serial2);
  if (playerReady) {
    player.volume(VOLUME);
  } else {
    Serial.println("DFPlayer not found: check wiring and the microSD card");
  }

  say(GREETING, millis());
  delay(TEXT_TIME);  // greet before the robot starts moving
}

void loop() {
  unsigned long now = millis();
  bool obstacle = (digitalRead(IR_PIN) == LOW);

  checkButton(now);

  switch (robotState) {
    case FORWARD:
      if (obstacle) {
        stopMotors();
        say(OBSTACLE, now);
        changeState(STOPPING, now);
      } else {
        drive(SPEED_FORWARD, SPEED_FORWARD);
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
        changeState(TURNING, now);
      }
      break;

    case TURNING:
      // Keep turning until the turn time is over and the path is clear.
      if (now - stateStart >= TURN_TIME && !obstacle) {
        say(CLEAR, now);
        changeState(FORWARD, now);
      }
      break;
  }

  // Show the eyes again once the phrase has been on screen long enough.
  if ((long)(now - textUntil) >= 0) {
    blinkEyes(now);
  }
}

void changeState(RobotState next, unsigned long now) {
  robotState = next;
  stateStart = now;
}

// ---------- Talking ----------
// Plays /0<language+1>/00<phrase+1>.mp3 and writes the phrase on the OLED.
void say(Phrase phrase, unsigned long now) {
  u8g2.clearBuffer();
  u8g2.drawXBMP(0, 0, 128, 64, TEXTS[language][phrase]);
  u8g2.sendBuffer();
  textUntil = now + TEXT_TIME;
  eyeState = EYE_IDLE;

  if (playerReady) {
    player.playFolder(language + 1, phrase + 1);
  }
}

void checkButton(unsigned long now) {
  int reading = digitalRead(BUTTON_PIN);
  if (reading != lastButton && now - lastButtonChange > 50) {
    lastButtonChange = now;
    lastButton = reading;
    if (reading == LOW) {  // pressed
      language = (Language)((language + 1) % 3);
      say(LANGUAGE_NAME, now);
    }
  }
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
  if (!USE_MOTORS) {
    left = 0;
    right = 0;
  }
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

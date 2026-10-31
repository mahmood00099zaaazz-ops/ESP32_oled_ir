// Robot face: ESP32 + 128x64 OLED + IR sensor.
// The Raspberry Pi (brain) sends one word per line over USB serial:
//   IDLE   -> blinking eyes
//   LISTEN -> wide open eyes
//   THINK  -> eyes looking up
//   TALK   -> eyes + moving mouth
// The ESP32 sends "PERSON" when the IR sensor sees someone.

#include <U8g2lib.h>
#include <Wire.h>

U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, /* reset=*/U8X8_PIN_NONE);
int ir = 34;

enum Mood { IDLE, LISTEN, THINK, TALK };
Mood mood = IDLE;

unsigned long previousMillis = 0;
unsigned long lastPersonMillis = 0;
bool blinkClosed = false;
bool mouthOpen = false;
String line;

void setup() {
  Serial.begin(115200);
  pinMode(ir, INPUT);
  u8g2.begin();
  draw_face(false, false);
}

void loop() {
  read_serial();
  check_ir();

  unsigned long currentMillis = millis();
  switch (mood) {
    case IDLE:
      // Open 2 s, closed 150 ms.
      if (currentMillis - previousMillis >= (blinkClosed ? 150 : 2000)) {
        blinkClosed = !blinkClosed;
        draw_face(blinkClosed, false);
        previousMillis = currentMillis;
      }
      break;
    case TALK:
      if (currentMillis - previousMillis >= 180) {
        mouthOpen = !mouthOpen;
        draw_face(false, mouthOpen);
        previousMillis = currentMillis;
      }
      break;
    default:
      break;
  }
}

void read_serial() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      line.trim();
      if (line == "IDLE")        { mood = IDLE; }
      else if (line == "LISTEN") { mood = LISTEN; eye_wide(); }
      else if (line == "THINK")  { mood = THINK; eye_up(); }
      else if (line == "TALK")   { mood = TALK; }
      line = "";
    } else {
      line += c;
    }
  }
}

void check_ir() {
  // IR module output is LOW when something is in front of it.
  if (digitalRead(ir) == 0 && millis() - lastPersonMillis > 5000) {
    Serial.println("PERSON");
    lastPersonMillis = millis();
  }
}

void draw_face(bool closed, bool mouth) {
  u8g2.clearBuffer();
  if (closed) {
    u8g2.drawBox(14, 27, 36, 7);
    u8g2.drawBox(78, 27, 36, 7);
  } else {
    u8g2.drawRBox(14, 8, 36, 36, 8);
    u8g2.drawRBox(78, 8, 36, 36, 8);
  }
  if (mouth) {
    u8g2.drawFilledEllipse(64, 54, 14, 7);
  } else {
    u8g2.drawBox(50, 54, 28, 3);
  }
  u8g2.sendBuffer();
}

void eye_wide() {
  u8g2.clearBuffer();
  u8g2.drawDisc(32, 28, 20);
  u8g2.drawDisc(96, 28, 20);
  u8g2.setDrawColor(0);
  u8g2.drawDisc(32, 28, 7);
  u8g2.drawDisc(96, 28, 7);
  u8g2.setDrawColor(1);
  u8g2.sendBuffer();
}

void eye_up() {
  u8g2.clearBuffer();
  u8g2.drawBox(80, 12, 40, 20);
  u8g2.drawBox(10, 12, 40, 20);
  u8g2.drawFilledEllipse(99, 13, 19, 11);
  u8g2.drawFilledEllipse(29, 13, 19, 11);
  u8g2.sendBuffer();
}

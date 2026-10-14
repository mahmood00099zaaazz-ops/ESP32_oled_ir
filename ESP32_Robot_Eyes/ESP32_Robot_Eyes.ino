// چاڤێن ڕۆبۆتی — ESP32 + OLED SSD1306 128x64 (I2C)
// Robot eyes: blink, look left/right, happy face, and surprised eyes when
// the IR sensor sees something. Prints checks to the Serial Monitor (115200).
//
// Wiring:  OLED VCC -> 3V3   GND -> GND   SCL -> GPIO22   SDA -> GPIO21
//          IR OUT -> GPIO34 (optional)

#include <U8g2lib.h>
#include <Wire.h>

const int SDA_PIN = 21;
const int SCL_PIN = 22;
const int IR_PIN  = 34;          // LOW = something in front of the sensor
const bool USE_IR = true;        // false if no IR sensor is connected

U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, /* reset=*/U8X8_PIN_NONE,
                                         /* clock=*/SCL_PIN, /* data=*/SDA_PIN);

// Eye size and position
const int EYE_W = 36;
const int EYE_H = 36;
const int EYE_R = 8;             // corner roundness
const int LEFT_X  = 14;
const int RIGHT_X = 78;
const int EYE_Y   = 14;

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println();
  Serial.println("Robot eyes starting...");

  if (USE_IR) {
    pinMode(IR_PIN, INPUT);
  }

  // Check that the screen answers on the I2C bus before using it.
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.beginTransmission(0x3C);
  bool at3C = (Wire.endTransmission() == 0);
  Wire.beginTransmission(0x3D);
  bool at3D = (Wire.endTransmission() == 0);

  if (at3C) {
    Serial.println("OK: screen found at 0x3C");
  } else if (at3D) {
    Serial.println("OK: screen found at 0x3D");
    u8g2.setI2CAddress(0x3D * 2);
  } else {
    Serial.println("ERROR: screen not found - check VCC, GND, SDA=21, SCL=22");
  }

  u8g2.begin();
  u8g2.setContrast(255);

  // Start-up test: whole screen white for half a second.
  u8g2.clearBuffer();
  u8g2.drawBox(0, 0, 128, 64);
  u8g2.sendBuffer();
  delay(500);

  drawEyes(0, EYE_H);
  Serial.println("Running");
}

void loop() {
  // Normal look with a blink
  drawEyes(0, EYE_H);
  if (waitOrSurprise(1500)) return;
  blink();

  // Look left, then right
  drawEyes(-10, EYE_H);
  if (waitOrSurprise(800)) return;
  drawEyes(10, EYE_H);
  if (waitOrSurprise(800)) return;

  drawEyes(0, EYE_H);
  if (waitOrSurprise(1000)) return;
  blink();

  // Happy eyes
  drawHappy();
  if (waitOrSurprise(1200)) return;
}

// ---------- Drawing ----------

// offsetX moves both eyes left (-) or right (+); height < EYE_H closes them.
void drawEyes(int offsetX, int height) {
  if (height < 4) height = 4;
  int y = EYE_Y + (EYE_H - height) / 2;
  int r = (height < 2 * EYE_R + 1) ? height / 2 - 1 : EYE_R;
  if (r < 1) r = 1;

  u8g2.clearBuffer();
  u8g2.drawRBox(LEFT_X + offsetX,  y, EYE_W, height, r);
  u8g2.drawRBox(RIGHT_X + offsetX, y, EYE_W, height, r);
  u8g2.sendBuffer();
}

void blink() {
  for (int h = EYE_H; h >= 4; h -= 8) {
    drawEyes(0, h);
    delay(15);
  }
  delay(60);
  for (int h = 4; h <= EYE_H; h += 8) {
    drawEyes(0, h);
    delay(15);
  }
  drawEyes(0, EYE_H);
}

void drawHappy() {
  u8g2.clearBuffer();
  u8g2.drawRBox(LEFT_X,  EYE_Y, EYE_W, EYE_H, EYE_R);
  u8g2.drawRBox(RIGHT_X, EYE_Y, EYE_W, EYE_H, EYE_R);
  // Cut the bottom of each eye with a black circle to make a smile shape.
  u8g2.setDrawColor(0);
  u8g2.drawDisc(LEFT_X + EYE_W / 2,  EYE_Y + EYE_H + 8, 24);
  u8g2.drawDisc(RIGHT_X + EYE_W / 2, EYE_Y + EYE_H + 8, 24);
  u8g2.setDrawColor(1);
  u8g2.sendBuffer();
}

void drawSurprised() {
  u8g2.clearBuffer();
  u8g2.drawDisc(LEFT_X + EYE_W / 2,  EYE_Y + EYE_H / 2, 20);
  u8g2.drawDisc(RIGHT_X + EYE_W / 2, EYE_Y + EYE_H / 2, 20);
  u8g2.setDrawColor(0);
  u8g2.drawDisc(LEFT_X + EYE_W / 2,  EYE_Y + EYE_H / 2, 7);
  u8g2.drawDisc(RIGHT_X + EYE_W / 2, EYE_Y + EYE_H / 2, 7);
  u8g2.setDrawColor(1);
  u8g2.sendBuffer();
}

// ---------- IR sensor ----------

bool somethingInFront() {
  return USE_IR && digitalRead(IR_PIN) == LOW;
}

// Waits up to ms milliseconds. If the IR sensor sees something, shows
// surprised eyes until it is gone and returns true.
bool waitOrSurprise(unsigned long ms) {
  unsigned long start = millis();
  while (millis() - start < ms) {
    if (somethingInFront()) {
      Serial.println("IR: something in front!");
      drawSurprised();
      while (somethingInFront()) {
        delay(20);
      }
      delay(300);
      return true;
    }
    delay(10);
  }
  return false;
}

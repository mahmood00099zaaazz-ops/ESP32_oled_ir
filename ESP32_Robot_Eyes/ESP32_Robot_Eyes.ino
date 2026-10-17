/*
  ESP32 Robot Eyes - OLED 128x64 + IR sensor
  ------------------------------------------
  Animated robot eyes that blink and look around by themselves.
  When the IR sensor detects something, the robot looks up and smiles.

  Hardware:
    - ESP32 DevKit
    - SSD1306 OLED 128x64 (I2C)   VCC -> 3V3, GND -> GND, SDA -> GPIO21, SCL -> GPIO22
    - IR obstacle sensor           VCC -> 3V3, GND -> GND, OUT -> GPIO34
      (the sensor output is LOW when it detects an object)

  Library:
    - U8g2 by olikraus (Arduino IDE: Sketch > Include Library > Manage Libraries > "U8g2")
      Only install it. Do NOT use "Sketch > Include Library > U8g2": that adds
      #include <MUIU8g2.h> at the top of this file and causes compile errors.

  Board:
    - Tools > Board > esp32 > "ESP32 Dev Module"
*/

#include <Arduino.h>
#include <U8g2lib.h>
#include <Wire.h>

// ---------------- Pins ----------------
const int IR_PIN = 34;   // input-only pin, fine for the IR sensor output
const int SDA_PIN = 21;
const int SCL_PIN = 22;

// ---------------- Display ----------------
U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, /* reset=*/U8X8_PIN_NONE);

const int SCREEN_W = 128;
const int SCREEN_H = 64;

// ---------------- Eye shape ----------------
const int EYE_W = 36;
const int EYE_H = 36;
const int EYE_RADIUS = 8;
const int EYE_GAP = 28;                    // space between the two eyes
const int LEFT_EYE_X = SCREEN_W / 2 - EYE_GAP / 2 - EYE_W / 2;   // eye centers
const int RIGHT_EYE_X = SCREEN_W / 2 + EYE_GAP / 2 + EYE_W / 2;
const int EYE_Y = SCREEN_H / 2;

// ---------------- Timing ----------------
const unsigned long FRAME_MS = 20;         // ~50 frames per second
const unsigned long BLINK_CLOSE_MS = 90;
const unsigned long BLINK_OPEN_MS = 110;
const unsigned long IR_DEBOUNCE_MS = 40;
const unsigned long IR_HOLD_MS = 800;      // keep looking up a bit after the object leaves

// ---------------- Moods ----------------
enum Mood { MOOD_NORMAL, MOOD_HAPPY };

// ---------------- State ----------------
float lookX = 0, lookY = 0;                // current eye offset (pixels)
float targetX = 0, targetY = 0;            // where the eyes are moving to
float openness = 1.0;                      // 1.0 = open, 0.0 = closed

enum BlinkState { BLINK_NONE, BLINK_CLOSING, BLINK_OPENING };
BlinkState blinkState = BLINK_NONE;
unsigned long blinkStart = 0;
unsigned long nextBlinkAt = 0;
unsigned long nextLookAt = 0;
unsigned long lastFrame = 0;

bool irStable = false;                     // true = object detected (debounced)
bool irLastRaw = false;
unsigned long irChangedAt = 0;
unsigned long irLastSeen = 0;

Mood mood = MOOD_NORMAL;

// ---------------- Helpers ----------------
void scheduleNextBlink(unsigned long now) {
  nextBlinkAt = now + random(1500, 5000);
}

void scheduleNextLook(unsigned long now) {
  nextLookAt = now + random(1200, 3500);
}

void startBlink(unsigned long now) {
  if (blinkState == BLINK_NONE) {
    blinkState = BLINK_CLOSING;
    blinkStart = now;
  }
}

// Read the IR sensor with debounce. Returns true while an object is detected.
bool readIr(unsigned long now) {
  bool raw = (digitalRead(IR_PIN) == LOW);
  if (raw != irLastRaw) {
    irLastRaw = raw;
    irChangedAt = now;
  }
  if (now - irChangedAt >= IR_DEBOUNCE_MS && irStable != raw) {
    irStable = raw;
    Serial.println(irStable ? "IR: object detected" : "IR: clear");
  }
  return irStable;
}

void updateBlink(unsigned long now) {
  switch (blinkState) {
    case BLINK_NONE:
      openness = 1.0;
      if (now >= nextBlinkAt) {
        startBlink(now);
      }
      break;

    case BLINK_CLOSING: {
      unsigned long t = now - blinkStart;
      if (t >= BLINK_CLOSE_MS) {
        openness = 0.0;
        blinkState = BLINK_OPENING;
        blinkStart = now;
      } else {
        openness = 1.0 - (float)t / BLINK_CLOSE_MS;
      }
      break;
    }

    case BLINK_OPENING: {
      unsigned long t = now - blinkStart;
      if (t >= BLINK_OPEN_MS) {
        openness = 1.0;
        blinkState = BLINK_NONE;
        scheduleNextBlink(now);
      } else {
        openness = (float)t / BLINK_OPEN_MS;
      }
      break;
    }
  }
}

void updateLook(unsigned long now, bool objectNear) {
  if (objectNear) {
    // Look up at the object
    targetX = 0;
    targetY = -12;
  } else if (now >= nextLookAt) {
    // Pick a random place to look at
    switch (random(0, 7)) {
      case 0: targetX = -12; targetY = 0;  break;  // left
      case 1: targetX = 12;  targetY = 0;  break;  // right
      case 2: targetX = 0;   targetY = -8; break;  // up
      case 3: targetX = 0;   targetY = 8;  break;  // down
      case 4: targetX = -10; targetY = -6; break;  // up-left
      case 5: targetX = 10;  targetY = -6; break;  // up-right
      default: targetX = 0;  targetY = 0;  break;  // center
    }
    scheduleNextLook(now);
  }

  // Smooth movement towards the target
  lookX += (targetX - lookX) * 0.25;
  lookY += (targetY - lookY) * 0.25;
}

// Draw one eye centered at (cx, cy)
void drawEye(int cx, int cy, Mood m) {
  int h = (int)(EYE_H * openness);
  if (h < 2) h = 2;                        // fully closed = thin line
  int w = EYE_W;
  int x = cx - w / 2;
  int y = cy - h / 2;

  u8g2.setDrawColor(1);
  int r = EYE_RADIUS;
  if (r > h / 2 - 1) r = h / 2 - 1;        // U8g2 needs the radius to fit inside the box
  if (r >= 1) {
    u8g2.drawRBox(x, y, w, h, r);
  } else {
    u8g2.drawBox(x, y, w, h);
  }

  if (m == MOOD_HAPPY && h > 12) {
    // Cut the bottom of the eye with a black ellipse -> smiling "^ ^" eyes
    u8g2.setDrawColor(0);
    u8g2.drawFilledEllipse(cx, y + h + 6, w / 2 + 6, h / 2);
    u8g2.setDrawColor(1);
  }
}

void drawFace() {
  u8g2.clearBuffer();
  int ox = (int)lookX;
  int oy = (int)lookY;
  drawEye(LEFT_EYE_X + ox, EYE_Y + oy, mood);
  drawEye(RIGHT_EYE_X + ox, EYE_Y + oy, mood);
  u8g2.sendBuffer();
}

void showStartup() {
  u8g2.clearBuffer();
  u8g2.setFont(u8g2_font_ncenB14_tr);
  const char *text = "Hello!";
  int w = u8g2.getStrWidth(text);
  u8g2.drawStr((SCREEN_W - w) / 2, 38, text);
  u8g2.sendBuffer();
  delay(1000);
}

// ---------------- Arduino ----------------
void setup() {
  Serial.begin(115200);
  pinMode(IR_PIN, INPUT);

  Wire.begin(SDA_PIN, SCL_PIN);
  u8g2.begin();

  randomSeed(esp_random());
  showStartup();

  unsigned long now = millis();
  scheduleNextBlink(now);
  scheduleNextLook(now);
  Serial.println("Robot eyes ready");
}

void loop() {
  unsigned long now = millis();
  if (now - lastFrame < FRAME_MS) {
    return;
  }
  lastFrame = now;

  bool objectNear = readIr(now);
  if (objectNear) {
    irLastSeen = now;
  }
  bool reacting = objectNear || (irLastSeen != 0 && now - irLastSeen < IR_HOLD_MS);

  Mood newMood = reacting ? MOOD_HAPPY : MOOD_NORMAL;
  if (newMood != mood) {
    mood = newMood;
    startBlink(now);                       // blink when the mood changes
  }

  updateBlink(now);
  updateLook(now, reacting);
  drawFace();
}

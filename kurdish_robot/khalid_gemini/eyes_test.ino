// Khalid eyes: moving robot eyes on the OLED (no WiFi, no sound).
// The eyes look around, blink, and sometimes wink, get angry or happy.
// Wiring: OLED VCC 3V3, GND, SCL 22, SDA 21. Library: U8g2.

#include <Wire.h>
#include <U8g2lib.h>

U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, U8X8_PIN_NONE);

float eyeX = 0, eyeY = 0;      // where the eyes look now
float goalX = 0, goalY = 0;    // where they are moving to
int mood = 0;                  // 0 normal, 1 happy, 2 angry, 3 wink, 4 surprised
unsigned long nextMove = 0, nextBlink = 0, moodUntil = 0;

void drawEye(int cx, int cy, bool left, bool closed) {
  int x = cx - 16, y = cy - 18;
  if (closed || (mood == 3 && !left)) {
    u8g2.drawRBox(x, cy - 2, 32, 5, 2);
    return;
  }
  if (mood == 4) {
    u8g2.drawDisc(cx, cy, 17);
    u8g2.setDrawColor(0);
    u8g2.drawDisc(cx, cy, 6);
    u8g2.setDrawColor(1);
    return;
  }
  u8g2.drawRBox(x, y, 32, 36, 9);
  u8g2.setDrawColor(0);
  if (mood == 1) u8g2.drawDisc(cx, cy + 20, 19);  // happy: bottom cut round
  if (mood == 2) {                                 // angry: slanted brows
    if (left) u8g2.drawTriangle(x - 1, y - 1, x + 33, y - 1, x + 33, y + 16);
    else      u8g2.drawTriangle(x - 1, y - 1, x + 33, y - 1, x - 1, y + 16);
  }
  u8g2.setDrawColor(1);
}

void setup() {
  u8g2.begin();
  randomSeed(analogRead(36));
}

void loop() {
  unsigned long now = millis();

  if (now > nextMove) {  // pick a new place to look
    goalX = random(-14, 15);
    goalY = random(-6, 7);
    nextMove = now + random(800, 2500);
    int dice = random(10);
    if (dice == 0) { mood = 3; moodUntil = now + 1200; }       // wink
    else if (dice == 1) { mood = 2; moodUntil = now + 1500; }  // angry
    else if (dice == 2) { mood = 1; moodUntil = now + 1500; }  // happy
    else if (dice == 3) { mood = 4; moodUntil = now + 1000; }  // surprised
  }
  if (now > moodUntil) mood = 0;

  eyeX += (goalX - eyeX) * 0.25f;  // smooth movement
  eyeY += (goalY - eyeY) * 0.25f;

  bool blink = false;
  if (now > nextBlink) {
    blink = true;
    if (now > nextBlink + 120) nextBlink = now + random(2000, 5000);
  }

  u8g2.clearBuffer();
  drawEye(40 + (int)eyeX, 32 + (int)eyeY, true, blink);
  drawEye(88 + (int)eyeX, 32 + (int)eyeY, false, blink);
  u8g2.sendBuffer();
  delay(30);
}

#include <U8g2lib.h>
#include <Wire.h>

// OLED: SDA = P21, SCL = P22
U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, /* reset=*/U8X8_PIN_NONE);

#define BTN_ON  19   // screen ON button  (other leg -> GND)
#define BTN_OFF 18   // screen OFF button (other leg -> GND)

bool screenOn = true;
unsigned long previousMillis = 0;
bool eyesOpen = true;

void setup() {
  pinMode(BTN_ON,  INPUT_PULLUP);
  pinMode(BTN_OFF, INPUT_PULLUP);
  u8g2.begin();
}

void loop() {
  if (digitalRead(BTN_ON) == LOW) {
    u8g2.setPowerSave(0);
    screenOn = true;
  }
  if (digitalRead(BTN_OFF) == LOW) {
    u8g2.setPowerSave(1);
    screenOn = false;
  }

  if (!screenOn) return;

  // blink: open 1 s, closed 300 ms
  unsigned long now = millis();
  if (eyesOpen && now - previousMillis >= 1000) {
    eye_close();
    eyesOpen = false;
    previousMillis = now;
  } else if (!eyesOpen && now - previousMillis >= 300) {
    eye_open();
    eyesOpen = true;
    previousMillis = now;
  }
}

void eye_open() {
  u8g2.clearBuffer();
  u8g2.drawBox(14, 13, 36, 36);
  u8g2.drawBox(78, 13, 36, 36);
  u8g2.sendBuffer();
}

void eye_close() {
  u8g2.clearBuffer();
  u8g2.drawBox(14, 27, 36, 7);
  u8g2.drawBox(78, 27, 36, 7);
  u8g2.sendBuffer();
}

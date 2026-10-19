/*
  ESP32 Talking Robot - OLED face + DFPlayer Mini + IR sensor
  ----------------------------------------------------------
  The robot has eyes and a mouth on the OLED. It plays sentences you
  recorded yourself (MP3 on a microSD card) and moves its mouth while it talks.

    - At start-up it says sentence 1 (hello).
    - When the IR sensor sees someone, it says a random greeting (2..4).
    - When nobody is there for a while, it says something by itself (5..6).
    - In the Serial Monitor (115200 baud) type 1..9 to play that sentence.

  Hardware:
    OLED SSD1306 128x64 (I2C)  VCC -> 3V3, GND -> GND, SDA -> GPIO21, SCL -> GPIO22
    IR obstacle sensor         VCC -> 3V3, GND -> GND, OUT -> GPIO34 (LOW = object)
    DFPlayer Mini              VCC -> 5V (VIN), GND -> GND
                               TX  -> GPIO16
                               RX  -> 1k resistor -> GPIO17
                               BUSY -> GPIO4 (LOW while playing)
                               SPK_1 / SPK_2 -> speaker (3W, 4-8 ohm)

  microSD card (FAT32): make a folder called "mp3" and put the files in it:
    mp3/0001.mp3  hello            ("Silav! Ez robot im")
    mp3/0002.mp3  greeting 1       ("Silav, tu cawa yi?")
    mp3/0003.mp3  greeting 2       ("Navê te çi ye?")
    mp3/0004.mp3  greeting 3       ("Ez te dibînim!")
    mp3/0005.mp3  alone 1          ("Kes li vir nîne...")
    mp3/0006.mp3  alone 2          ("Haha!")

  Libraries (install only, do NOT use "Sketch > Include Library"):
    - U8g2 by olikraus
    - DFRobotDFPlayerMini by DFRobot

  Board: "ESP32 Dev Module"
*/

#include <Arduino.h>
#include <U8g2lib.h>
#include <Wire.h>
#include <DFRobotDFPlayerMini.h>

// ---------------- Pins ----------------
const int IR_PIN = 34;
const int SDA_PIN = 21;
const int SCL_PIN = 22;
const int DF_RX_PIN = 16;      // ESP32 receives here  <- DFPlayer TX
const int DF_TX_PIN = 17;      // ESP32 sends here     -> DFPlayer RX (through 1k)
const int DF_BUSY_PIN = 4;     // LOW while the DFPlayer is playing

// ---------------- Sentences on the SD card ----------------
const int TRACK_HELLO = 1;
const int GREET_FIRST = 2, GREET_LAST = 4;
const int ALONE_FIRST = 5, ALONE_LAST = 6;
const int VOLUME = 25;                     // 0..30

// ---------------- Timing ----------------
const unsigned long FRAME_MS = 30;
const unsigned long BLINK_CLOSE_MS = 90;
const unsigned long BLINK_OPEN_MS = 110;
const unsigned long IR_DEBOUNCE_MS = 40;
const unsigned long GREET_COOLDOWN_MS = 6000;   // don't greet again too quickly
const unsigned long BUSY_GRACE_MS = 400;        // BUSY needs a moment to go LOW after a command

// ---------------- Display ----------------
U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, /* reset=*/U8X8_PIN_NONE);

const int EYE_W = 30;
const int EYE_H = 26;
const int EYE_RADIUS = 7;
const int LEFT_EYE_X = 38;
const int RIGHT_EYE_X = 90;
const int EYE_Y = 22;
const int MOUTH_X = 64;
const int MOUTH_Y = 51;

// ---------------- Sound ----------------
HardwareSerial dfSerial(2);
DFRobotDFPlayerMini player;
bool playerOk = false;
unsigned long talkStartedAt = 0;

// ---------------- State ----------------
float lookX = 0, lookY = 0, targetX = 0, targetY = 0;
float openness = 1.0;
int mouthOpen = 0;                         // mouth height in pixels while talking
unsigned long nextMouthAt = 0;

enum BlinkState { BLINK_NONE, BLINK_CLOSING, BLINK_OPENING };
BlinkState blinkState = BLINK_NONE;
unsigned long blinkStart = 0, nextBlinkAt = 0, nextLookAt = 0, lastFrame = 0;

bool irStable = false, irLastRaw = false;
unsigned long irChangedAt = 0;
unsigned long lastGreetAt = 0;
unsigned long nextAloneTalkAt = 0;

// ---------------- Sound helpers ----------------
void say(int track) {
  if (!playerOk) {
    Serial.println("No DFPlayer - cannot talk");
    return;
  }
  player.playMp3Folder(track);
  talkStartedAt = millis();
  Serial.print("Saying sentence ");
  Serial.println(track);
}

bool isTalking(unsigned long now) {
  if (!playerOk) return false;
  if (talkStartedAt != 0 && now - talkStartedAt < BUSY_GRACE_MS) return true;
  return digitalRead(DF_BUSY_PIN) == LOW;
}

void scheduleAloneTalk(unsigned long now) {
  nextAloneTalkAt = now + random(30000, 60000);
}

// ---------------- Eyes ----------------
void startBlink(unsigned long now) {
  if (blinkState == BLINK_NONE) {
    blinkState = BLINK_CLOSING;
    blinkStart = now;
  }
}

void updateBlink(unsigned long now) {
  unsigned long t = now - blinkStart;
  switch (blinkState) {
    case BLINK_NONE:
      openness = 1.0;
      if (now >= nextBlinkAt) startBlink(now);
      break;
    case BLINK_CLOSING:
      if (t >= BLINK_CLOSE_MS) {
        openness = 0.0;
        blinkState = BLINK_OPENING;
        blinkStart = now;
      } else {
        openness = 1.0 - (float)t / BLINK_CLOSE_MS;
      }
      break;
    case BLINK_OPENING:
      if (t >= BLINK_OPEN_MS) {
        openness = 1.0;
        blinkState = BLINK_NONE;
        nextBlinkAt = now + random(1500, 5000);
      } else {
        openness = (float)t / BLINK_OPEN_MS;
      }
      break;
  }
}

void updateLook(unsigned long now, bool someoneThere) {
  if (someoneThere) {
    targetX = 0;                           // look straight at the person
    targetY = 0;
  } else if (now >= nextLookAt) {
    switch (random(0, 5)) {
      case 0: targetX = -8; targetY = 0;  break;
      case 1: targetX = 8;  targetY = 0;  break;
      case 2: targetX = 0;  targetY = -4; break;
      case 3: targetX = -6; targetY = -3; break;
      default: targetX = 0; targetY = 0;  break;
    }
    nextLookAt = now + random(1200, 3500);
  }
  lookX += (targetX - lookX) * 0.25;
  lookY += (targetY - lookY) * 0.25;
}

void drawEye(int cx, int cy) {
  int h = (int)(EYE_H * openness);
  if (h < 2) h = 2;
  int r = EYE_RADIUS;
  if (r > h / 2 - 1) r = h / 2 - 1;
  if (r >= 1) {
    u8g2.drawRBox(cx - EYE_W / 2, cy - h / 2, EYE_W, h, r);
  } else {
    u8g2.drawBox(cx - EYE_W / 2, cy - h / 2, EYE_W, h);
  }
}

// ---------------- Mouth ----------------
void updateMouth(unsigned long now, bool talking) {
  if (!talking) {
    mouthOpen = 0;
    return;
  }
  if (now >= nextMouthAt) {
    mouthOpen = random(2, 13);             // new mouth shape every ~90 ms looks like speech
    nextMouthAt = now + random(70, 130);
  }
}

void drawMouth(bool talking, bool happy) {
  int x = MOUTH_X + (int)(lookX / 2);
  if (talking) {
    int h = mouthOpen < 3 ? 3 : mouthOpen;
    int w = 24 + mouthOpen;
    int r = h / 2 - 1;
    if (r >= 1) {
      u8g2.drawRBox(x - w / 2, MOUTH_Y - h / 2, w, h, r);
    } else {
      u8g2.drawBox(x - w / 2, MOUTH_Y - h / 2, w, h);
    }
  } else if (happy) {
    // smile: lower half of an ellipse, drawn twice for a thicker line
    u8g2.drawEllipse(x, MOUTH_Y - 6, 14, 7, U8G2_DRAW_LOWER_LEFT | U8G2_DRAW_LOWER_RIGHT);
    u8g2.drawEllipse(x, MOUTH_Y - 5, 14, 7, U8G2_DRAW_LOWER_LEFT | U8G2_DRAW_LOWER_RIGHT);
  } else {
    u8g2.drawRBox(x - 12, MOUTH_Y - 1, 24, 3, 1);   // calm, closed mouth
  }
}

void drawFace(bool talking, bool happy) {
  u8g2.clearBuffer();
  int ox = (int)lookX;
  int oy = (int)lookY;
  drawEye(LEFT_EYE_X + ox, EYE_Y + oy);
  drawEye(RIGHT_EYE_X + ox, EYE_Y + oy);
  drawMouth(talking, happy);
  u8g2.sendBuffer();
}

// ---------------- IR ----------------
bool readIr(unsigned long now) {
  bool raw = (digitalRead(IR_PIN) == LOW);
  if (raw != irLastRaw) {
    irLastRaw = raw;
    irChangedAt = now;
  }
  if (now - irChangedAt >= IR_DEBOUNCE_MS && irStable != raw) {
    irStable = raw;
    Serial.println(irStable ? "IR: someone is here" : "IR: clear");
  }
  return irStable;
}

// ---------------- Arduino ----------------
void showMessage(const char *line1, const char *line2) {
  u8g2.clearBuffer();
  u8g2.setFont(u8g2_font_ncenB10_tr);
  u8g2.drawStr((128 - u8g2.getStrWidth(line1)) / 2, 28, line1);
  u8g2.setFont(u8g2_font_6x10_tr);
  u8g2.drawStr((128 - u8g2.getStrWidth(line2)) / 2, 48, line2);
  u8g2.sendBuffer();
}

void setup() {
  Serial.begin(115200);
  pinMode(IR_PIN, INPUT);
  pinMode(DF_BUSY_PIN, INPUT_PULLUP);

  Wire.begin(SDA_PIN, SCL_PIN);
  u8g2.begin();
  randomSeed(esp_random());

  showMessage("Hello!", "starting sound...");
  delay(1500);                             // the DFPlayer needs a moment after power-on

  dfSerial.begin(9600, SERIAL_8N1, DF_RX_PIN, DF_TX_PIN);
  playerOk = player.begin(dfSerial);       // with ACK: tells us if the DFPlayer + SD card answer
  if (playerOk) {
    // The library can wait up to 0.5 s for a reply before each new command,
    // which would freeze the face. Wait at most 100 ms instead. (loop() also
    // reads the replies every frame, so normally there is no wait at all.)
    player.setTimeOut(100);
    player.volume(VOLUME);
    Serial.println("DFPlayer ready");
  } else {
    Serial.println("DFPlayer NOT found: check wiring and the SD card");
    showMessage("No sound!", "check DFPlayer + SD");
    delay(2500);
  }

  unsigned long now = millis();
  nextBlinkAt = now + 2000;
  nextLookAt = now + 1500;
  scheduleAloneTalk(now);
  say(TRACK_HELLO);
}

void loop() {
  unsigned long now = millis();

  // Serial Monitor: type a number 1..9 to play that sentence
  if (Serial.available()) {
    int c = Serial.read();
    if (c >= '1' && c <= '9') {
      say(c - '0');
    }
  }

  if (now - lastFrame < FRAME_MS) {
    return;
  }
  lastFrame = now;

  // Read (and drop) messages from the DFPlayer, e.g. "sentence finished",
  // so they don't pile up in the serial buffer.
  if (playerOk && player.available()) {
    player.readType();
  }

  bool someoneThere = readIr(now);
  bool talking = isTalking(now);

  // Someone came: greet them (not too often, and not while already talking)
  static bool wasThere = false;
  if (someoneThere && !wasThere && !talking && now - lastGreetAt > GREET_COOLDOWN_MS) {
    say(random(GREET_FIRST, GREET_LAST + 1));
    lastGreetAt = now;
    startBlink(now);
  }
  wasThere = someoneThere;

  // Nobody here for a long time: say something by itself
  if (!someoneThere && !talking && now >= nextAloneTalkAt) {
    say(random(ALONE_FIRST, ALONE_LAST + 1));
    scheduleAloneTalk(now);
  }

  talking = isTalking(now);
  updateBlink(now);
  updateLook(now, someoneThere);
  updateMouth(now, talking);
  drawFace(talking, someoneThere);
}

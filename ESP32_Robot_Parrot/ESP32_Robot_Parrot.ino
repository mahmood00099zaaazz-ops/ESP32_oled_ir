/*
  ESP32 Parrot Robot - listens, reacts and repeats your voice (no WiFi needed)
  ---------------------------------------------------------------------------
    - LISTENS all the time: a loud sound (clap, shout) makes the robot look
      surprised, then smile. Its eyes grow a little when it hears sound.
    - PARROT: wave your hand at the IR sensor (or press BOOT). After the beep,
      say something (up to 3 seconds). The robot repeats it with a funny
      robot/parrot voice and moves its mouth while talking.

  Hardware (same pins as images/full_audio_robot_wiring.png):
    OLED SSD1306 128x64 (I2C)  VCC -> 3V3, GND, SDA -> GPIO21, SCL -> GPIO22
    IR obstacle sensor         VCC -> 3V3, GND, OUT -> GPIO34 (LOW = hand)
    INMP441 microphone         VDD -> 3V3 (NOT 5V), GND, L/R -> GND,
                               WS -> GPIO33, SCK -> GPIO32, SD -> GPIO35
    MAX98357A amplifier        Vin -> 5V, GND, LRC -> GPIO25, BCLK -> GPIO26, DIN -> GPIO27
                               GAIN and SD not connected, speaker on the green terminal

  Software:
    - Board package "esp32" by Espressif, version 3.x  (Board: "ESP32 Dev Module")
    - Library: U8g2 by olikraus (install only, do NOT use "Sketch > Include Library")
    - Serial Monitor at 115200 shows the sound level: use it to tune LOUD_LEVEL.
*/

#include <Arduino.h>
#include <ESP_I2S.h>
#include <U8g2lib.h>
#include <Wire.h>

// ===================== YOU CAN CHANGE THESE =====================
const int LOUD_LEVEL = 9000;        // sound level that counts as "loud" (0..32767)
const int VOICE_LEVEL = 1500;       // sound level that counts as "someone is talking"
const float PARROT_SPEED = 1.35;    // 1.0 = your real voice, bigger = higher, funnier voice
const float VOLUME = 0.8;           // 0.0 .. 1.0
const int MIC_GAIN_SHIFT = 13;      // 32-bit mic sample >> 13 -> 16-bit (bigger = quieter)
// ================================================================

// ---------------- Pins ----------------
const int IR_PIN = 34;
const int BOOT_PIN = 0;
const int SDA_PIN = 21, SCL_PIN = 22;
const int MIC_SCK = 32, MIC_WS = 33, MIC_SD = 35;
const int SPK_BCLK = 26, SPK_LRC = 25, SPK_DIN = 27;

// ---------------- Audio ----------------
const uint32_t RATE = 16000;        // microphone and speaker use the same rate
const int RECORD_SECONDS = 3;
const int CHUNK = 256;              // samples per microphone read (16 ms)

U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, /* reset=*/U8X8_PIN_NONE);
I2SClass mic;
I2SClass speaker;

int16_t *recording = nullptr;       // the recorded words
const size_t RECORD_SAMPLES = RATE * RECORD_SECONDS;

// =====================================================================
//                              MICROPHONE
// =====================================================================
// Read one chunk from the microphone into `out` (16-bit). Returns the loudest sample.
int readMic(int16_t *out, int count) {
  static int32_t raw[CHUNK];
  size_t bytes = mic.readBytes((char *)raw, count * sizeof(int32_t));
  int n = bytes / sizeof(int32_t);
  int peak = 0;
  for (int i = 0; i < n; i++) {
    int32_t s = raw[i] >> MIC_GAIN_SHIFT;
    if (s > 32767) s = 32767;
    if (s < -32768) s = -32768;
    if (out) out[i] = (int16_t)s;
    int a = abs((int)s);
    if (a > peak) peak = a;
  }
  return peak;
}

// Throw away microphone data for `ms` (e.g. so the robot doesn't hear its own beep).
void drainMic(int ms) {
  unsigned long start = millis();
  while (millis() - start < (unsigned long)ms) {
    readMic(nullptr, CHUNK);
  }
}

// =====================================================================
//                                FACE
// =====================================================================
enum Face { FACE_IDLE, FACE_SURPRISED, FACE_HAPPY, FACE_LISTEN, FACE_TALK, FACE_CONFUSED };

float lookX = 0, targetX = 0;
float eyeGrow = 0;                  // eyes get bigger with sound
unsigned long nextLookAt = 0, nextBlinkAt = 0, blinkUntil = 0;

void drawEyes(int dx, int dy, int w, int h) {
  for (int cx : {38, 90}) {
    int x = cx + dx - w / 2;
    int y = 22 + dy - h / 2;
    int r = h / 2 - 1;
    if (r > 8) r = 8;
    if (r >= 1) {
      u8g2.drawRBox(x, y, w, h, r);
    } else {
      u8g2.drawBox(x, y, w, h);
    }
  }
}

void drawFace(Face face, int mouth = 0) {
  u8g2.clearBuffer();
  unsigned long now = millis();
  int lx = (int)lookX;
  switch (face) {
    case FACE_IDLE: {
      int g = (int)eyeGrow;
      int h = now < blinkUntil ? 3 : 24 + g;
      drawEyes(lx, 0, 28 + g / 2, h);
      u8g2.drawRBox(52 + lx / 2, 51, 24, 3, 1);
      break;
    }
    case FACE_SURPRISED:
      for (int cx : {38, 90}) {                    // big round eyes
        u8g2.drawDisc(cx, 22, 15);
        u8g2.setDrawColor(0);
        u8g2.drawDisc(cx, 22, 6);                  // pupils
        u8g2.setDrawColor(1);
      }
      u8g2.drawEllipse(64, 52, 6, 8);              // "O" mouth
      u8g2.drawEllipse(64, 52, 5, 7);
      break;
    case FACE_HAPPY:
      drawEyes(0, 0, 30, 26);
      u8g2.setDrawColor(0);                        // cut the bottom -> smiling ^ ^ eyes
      u8g2.drawFilledEllipse(38, 42, 20, 13);
      u8g2.drawFilledEllipse(90, 42, 20, 13);
      u8g2.setDrawColor(1);
      u8g2.drawEllipse(64, 46, 16, 9, U8G2_DRAW_LOWER_LEFT | U8G2_DRAW_LOWER_RIGHT);
      u8g2.drawEllipse(64, 47, 16, 9, U8G2_DRAW_LOWER_LEFT | U8G2_DRAW_LOWER_RIGHT);
      break;
    case FACE_LISTEN:
      drawEyes(0, 0, 30, 30);
      u8g2.drawCircle(64, 50, 4);
      break;
    case FACE_TALK: {
      drawEyes(0, 0, 28, 24);
      int h = mouth < 3 ? 3 : mouth;
      int w = 20 + mouth;
      int r = h / 2 - 1;
      if (r >= 1) {
        u8g2.drawRBox(64 - w / 2, 51 - h / 2, w, h, r);
      } else {
        u8g2.drawBox(64 - w / 2, 51 - h / 2, w, h);
      }
      break;
    }
    case FACE_CONFUSED:
      drawEyes(0, 0, 28, 24);
      u8g2.setDrawColor(0);
      u8g2.drawBox(24, 8, 30, 8);                  // one eyebrow down = confused
      u8g2.setDrawColor(1);
      u8g2.setFont(u8g2_font_ncenB14_tr);
      u8g2.drawStr(58, 62, "?");
      break;
  }
  u8g2.sendBuffer();
}

// =====================================================================
//                               SPEAKER
// =====================================================================
void beep(int freq, int ms) {
  static int16_t buf[CHUNK];
  const int n = RATE * ms / 1000;
  int phase = 0;
  for (int done = 0; done < n;) {
    int count = min(CHUNK, n - done);
    for (int i = 0; i < count; i++, phase++) {
      buf[i] = ((phase * freq * 2 / (int)RATE) % 2) ? 2500 : -2500;
    }
    speaker.write((uint8_t *)buf, count * sizeof(int16_t));
    done += count;
  }
}

// Play the recording faster (higher, funnier voice) and move the mouth.
void playParrot(size_t start, size_t end) {
  // make it loud enough: find the loudest sample and scale to ~24000
  int peak = 1;
  for (size_t i = start; i < end; i++) {
    int a = abs((int)recording[i]);
    if (a > peak) peak = a;
  }
  float gain = min(24000.0f / peak, 8.0f) * VOLUME;

  static int16_t out[CHUNK];
  float pos = start;
  unsigned long lastDraw = 0;
  while (pos < end - 1) {
    int n = 0, loud = 0;
    while (n < CHUNK && pos < end - 1) {
      // linear interpolation between two samples -> smooth pitch shift
      size_t i = (size_t)pos;
      float f = pos - i;
      float s = (recording[i] * (1 - f) + recording[i + 1] * f) * gain;
      if (s > 32767) s = 32767;
      if (s < -32768) s = -32768;
      out[n++] = (int16_t)s;
      int a = abs((int)s);
      if (a > loud) loud = a;
      pos += PARROT_SPEED;
    }
    speaker.write((uint8_t *)out, n * sizeof(int16_t));
    if (millis() - lastDraw > 90) {
      lastDraw = millis();
      drawFace(FACE_TALK, map(min(loud, 20000), 0, 20000, 0, 14));
    }
  }
  drawFace(FACE_TALK, 0);
}

// =====================================================================
//                                PARROT
// =====================================================================
void parrot() {
  beep(1000, 120);
  drainMic(150);                                   // don't record our own beep

  // Record until the buffer is full, or ~0.8 s of silence after talking
  size_t got = 0;
  bool heardVoice = false;
  unsigned long lastVoiceAt = millis(), lastDraw = 0;
  int level = 0;
  while (got + CHUNK <= RECORD_SAMPLES) {
    int peak = readMic(recording + got, CHUNK);
    got += CHUNK;
    if (peak > VOICE_LEVEL) {
      heardVoice = true;
      lastVoiceAt = millis();
    }
    if (peak > level) level = peak;
    if (heardVoice && millis() - lastVoiceAt > 800) break;
    if (millis() - lastDraw > 100) {               // level bar while listening
      lastDraw = millis();
      drawFace(FACE_LISTEN);
      int bar = map(min(level, 16000), 0, 16000, 0, 100);
      u8g2.drawFrame(13, 58, 102, 6);
      u8g2.drawBox(14, 59, bar, 4);
      u8g2.sendBuffer();
      level = 0;
    }
  }
  beep(700, 60);
  Serial.printf("Recorded %u samples, voice: %s\n", (unsigned)got, heardVoice ? "yes" : "no");

  if (!heardVoice) {
    drawFace(FACE_CONFUSED);
    delay(1500);
    return;
  }

  // cut the silence at the start (keep 0.1 s before the first word)
  size_t start = 0;
  while (start < got && abs((int)recording[start]) < VOICE_LEVEL) start++;
  start = start > RATE / 10 ? start - RATE / 10 : 0;

  delay(200);
  playParrot(start, got);
  drawFace(FACE_HAPPY);
  delay(800);
  drainMic(200);
}

// =====================================================================
//                               ARDUINO
// =====================================================================
void setup() {
  Serial.begin(115200);
  pinMode(IR_PIN, INPUT);
  pinMode(BOOT_PIN, INPUT_PULLUP);

  Wire.begin(SDA_PIN, SCL_PIN);
  u8g2.begin();
  u8g2.setBusClock(400000);
  randomSeed(esp_random());

  mic.setPins(MIC_SCK, MIC_WS, -1, MIC_SD);
  bool micOk = mic.begin(I2S_MODE_STD, RATE, I2S_DATA_BIT_WIDTH_32BIT, I2S_SLOT_MODE_MONO, I2S_STD_SLOT_LEFT);
  speaker.setPins(SPK_BCLK, SPK_LRC, SPK_DIN);
  bool spkOk = speaker.begin(I2S_MODE_STD, RATE, I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_MONO);
  recording = (int16_t *)malloc(RECORD_SAMPLES * sizeof(int16_t));

  if (!micOk || !spkOk || !recording) {
    Serial.printf("Problem: mic %s, speaker %s, memory %s\n", micOk ? "OK" : "FAIL",
                  spkOk ? "OK" : "FAIL", recording ? "OK" : "FAIL");
    u8g2.clearBuffer();
    u8g2.setFont(u8g2_font_6x10_tr);
    u8g2.drawStr(4, 20, micOk ? "Mic OK" : "Mic FAIL");
    u8g2.drawStr(4, 36, spkOk ? "Speaker OK" : "Speaker FAIL");
    u8g2.drawStr(4, 52, recording ? "Memory OK" : "Memory FAIL");
    u8g2.sendBuffer();
    while (true) delay(1000);
  }

  beep(880, 80);
  beep(1320, 80);
  drainMic(300);
  Serial.println("Parrot robot ready");
}

void loop() {
  static unsigned long reactUntil = 0, happyUntil = 0, lastPrint = 0;
  unsigned long now = millis();

  // Parrot: hand in front of the IR sensor, or BOOT button
  if (digitalRead(IR_PIN) == LOW || digitalRead(BOOT_PIN) == LOW) {
    parrot();
    while (digitalRead(IR_PIN) == LOW) {          // wait until the hand is gone
      drawFace(FACE_HAPPY);
      delay(50);
    }
    drainMic(100);
    return;
  }

  // Listen all the time (this read also paces the loop: 16 ms)
  int level = readMic(nullptr, CHUNK);
  if (now - lastPrint > 500) {
    lastPrint = now;
    Serial.printf("sound level: %d\n", level);
  }

  // Loud sound -> surprised, then happy
  if (level > LOUD_LEVEL && now > reactUntil + 1500) {
    Serial.println("Loud sound!");
    reactUntil = now + 1000;
    happyUntil = reactUntil + 1500;
    beep(1500, 40);
    drainMic(100);
  }

  // Eyes grow a little with sound, look around, blink
  float grow = map(min(level, LOUD_LEVEL), 0, LOUD_LEVEL, 0, 8);
  eyeGrow += (grow - eyeGrow) * 0.3;
  if (now >= nextLookAt) {
    targetX = random(-8, 9);
    nextLookAt = now + random(1500, 4000);
  }
  if (now >= nextBlinkAt) {
    blinkUntil = now + 120;
    nextBlinkAt = now + random(2000, 5000);
  }
  lookX += (targetX - lookX) * 0.25;

  static unsigned long lastDraw = 0;
  if (now - lastDraw >= 40) {
    lastDraw = now;
    if (now < reactUntil) {
      drawFace(FACE_SURPRISED);
    } else if (now < happyUntil) {
      drawFace(FACE_HAPPY);
    } else {
      drawFace(FACE_IDLE);
    }
  }
}

// ڕۆبۆتێ کۆمیدی - Funny robot
// ESP32 + OLED 128x64 (SSD1306) + INMP441 mic + MAX98357A amp + 8 ohm speaker
//
// Wiring (same as the xiaozhi bread-compact-esp32 board):
//   OLED      SDA -> GPIO4    SCL -> GPIO15   VCC -> 3V3   GND -> GND
//   INMP441   WS  -> GPIO25   SCK -> GPIO26   SD  -> GPIO32
//             VDD -> 3V3      GND -> GND      L/R -> GND
//   MAX98357A LRC -> GPIO27   BCLK -> GPIO14  DIN -> GPIO33
//             Vin -> 5V       GND -> GND      GAIN, SD -> not connected
//
// What it does:
//   - Idle: blinks and looks around, and every few seconds does a random joke
//     (wink + boing, dizzy eyes, robot beeps, a little tune).
//   - Clap or shout: surprised eyes + whistle, then laughs "HA HA".
//   - Quiet for a long time: falls asleep and snores. Any sound wakes it up.
//
// Library: U8g2 (Arduino Library Manager -> "U8g2" by oliver).
// Board: "ESP32 Dev Module".

#include <U8g2lib.h>
#include <Wire.h>
#include <driver/i2s.h>
#include <math.h>

// ---------- Pins ----------
#define OLED_SDA 4
#define OLED_SCL 15

#define MIC_WS   25
#define MIC_SCK  26
#define MIC_SD   32

#define SPK_LRC  27
#define SPK_BCLK 14
#define SPK_DIN  33

// ---------- Settings ----------
// Keep the volume low when running from the battery without a boost module,
// otherwise the ESP32 can reset when the speaker plays.
const int   VOLUME          = 5000;   // 0..32767
const int   CLAP_LEVEL      = 3000;   // raise this if it reacts to small noises
const long  SLEEP_AFTER_MS  = 60000;  // fall asleep after 1 minute of quiet
const int   SAMPLE_RATE     = 16000;

#define SPK_PORT I2S_NUM_0
#define MIC_PORT I2S_NUM_1

U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, /* reset=*/U8X8_PIN_NONE,
                                         /* clock=*/OLED_SCL, /* data=*/OLED_SDA);

unsigned long lastSoundMillis = 0;
unsigned long nextBlinkMillis = 0;
unsigned long nextJokeMillis = 0;
bool sleeping = false;

// ======================================================================
// Audio
// ======================================================================

void setupSpeaker() {
  i2s_config_t cfg = {};
  cfg.mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX);
  cfg.sample_rate = SAMPLE_RATE;
  cfg.bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT;
  cfg.channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT;
  cfg.communication_format = I2S_COMM_FORMAT_STAND_I2S;
  cfg.intr_alloc_flags = 0;
  cfg.dma_buf_count = 8;
  cfg.dma_buf_len = 256;
  cfg.tx_desc_auto_clear = true;

  i2s_pin_config_t pins = {};
  pins.mck_io_num = I2S_PIN_NO_CHANGE;
  pins.bck_io_num = SPK_BCLK;
  pins.ws_io_num = SPK_LRC;
  pins.data_out_num = SPK_DIN;
  pins.data_in_num = I2S_PIN_NO_CHANGE;

  i2s_driver_install(SPK_PORT, &cfg, 0, NULL);
  i2s_set_pin(SPK_PORT, &pins);
  i2s_zero_dma_buffer(SPK_PORT);
}

void setupMic() {
  i2s_config_t cfg = {};
  cfg.mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX);
  cfg.sample_rate = SAMPLE_RATE;
  cfg.bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT;
  cfg.channel_format = I2S_CHANNEL_FMT_ONLY_LEFT;  // L/R pin is on GND
  cfg.communication_format = I2S_COMM_FORMAT_STAND_I2S;
  cfg.intr_alloc_flags = 0;
  cfg.dma_buf_count = 4;
  cfg.dma_buf_len = 256;

  i2s_pin_config_t pins = {};
  pins.mck_io_num = I2S_PIN_NO_CHANGE;
  pins.bck_io_num = MIC_SCK;
  pins.ws_io_num = MIC_WS;
  pins.data_out_num = I2S_PIN_NO_CHANGE;
  pins.data_in_num = MIC_SD;

  i2s_driver_install(MIC_PORT, &cfg, 0, NULL);
  i2s_set_pin(MIC_PORT, &pins);
}

// Plays a tone that slides from f1 to f2 (Hz). f1 == f2 gives a plain beep.
// A frequency of 0 is silence.
void sweep(float f1, float f2, int ms, int vol = VOLUME) {
  const int CHUNK = 128;
  int16_t buf[CHUNK * 2];
  int total = (long)SAMPLE_RATE * ms / 1000;
  static float phase = 0;

  for (int i = 0; i < total; i += CHUNK) {
    int n = min(CHUNK, total - i);
    for (int j = 0; j < n; j++) {
      float t = (float)(i + j) / total;
      float f = f1 + (f2 - f1) * t;
      // short fade in/out so it does not click
      float env = min(1.0f, min((i + j) / 80.0f, (total - i - j) / 80.0f));
      int16_t s = (f > 0) ? (int16_t)(sinf(phase) * vol * env) : 0;
      phase += 2.0f * PI * f / SAMPLE_RATE;
      if (phase > 2.0f * PI) phase -= 2.0f * PI;
      buf[j * 2] = s;
      buf[j * 2 + 1] = s;
    }
    size_t written;
    i2s_write(SPK_PORT, buf, n * 4, &written, portMAX_DELAY);
  }
}

void beep(float f, int ms) { sweep(f, f, ms); }
void rest(int ms) { sweep(0, 0, ms); }

void soundBoing() {
  sweep(900, 180, 120);
  sweep(500, 250, 120);
  sweep(350, 200, 100);
}

void soundWhistle() {      // "fiuu-fiuuu"
  sweep(800, 2200, 180);
  rest(60);
  sweep(900, 2600, 120);
  sweep(2600, 1200, 220);
}

void soundLaugh() {        // "ha-ha-ha-ha"
  for (int i = 0; i < 5; i++) {
    float f = 700 - i * 60;
    sweep(f, f - 150, 90);
    rest(60);
  }
}

void soundRobotTalk() {    // random R2D2 style beeps
  for (int i = 0; i < 8; i++) {
    float f = random(600, 2400);
    if (random(3) == 0) sweep(f, random(400, 2600), random(40, 110));
    else beep(f, random(40, 90));
  }
}

void soundSnore() {
  sweep(90, 140, 600, VOLUME / 2);
  rest(200);
  sweep(160, 90, 500, VOLUME / 3);
}

void soundTune() {         // little "ta-da" melody
  const float notes[] = {523, 659, 784, 1047, 0, 784, 1047};
  const int   lens[]  = {120, 120, 120, 250, 80, 120, 350};
  for (int i = 0; i < 7; i++) sweep(notes[i], notes[i], lens[i]);
}

void soundYawn() {
  sweep(500, 900, 400, VOLUME / 2);
  sweep(900, 300, 700, VOLUME / 2);
}

// Average loudness of the microphone for ~16 ms.
int micLevel() {
  int32_t samples[256];
  size_t bytesRead = 0;
  i2s_read(MIC_PORT, samples, sizeof(samples), &bytesRead, 20);
  int n = bytesRead / 4;
  if (n == 0) return 0;

  long long sum = 0, mean = 0;
  for (int i = 0; i < n; i++) mean += samples[i] >> 14;
  mean /= n;
  for (int i = 0; i < n; i++) sum += llabs((long long)(samples[i] >> 14) - mean);
  return sum / n;
}

// ======================================================================
// Eyes
// ======================================================================

const int EYE_L = 30, EYE_R = 98, EYE_Y = 30;   // eye centers

void eyesOpen(int dx = 0, int dy = 0) {
  u8g2.clearBuffer();
  u8g2.drawRBox(EYE_L - 18 + dx, EYE_Y - 18 + dy, 36, 36, 9);
  u8g2.drawRBox(EYE_R - 18 + dx, EYE_Y - 18 + dy, 36, 36, 9);
  u8g2.drawBox(56, 55, 16, 3);  // small mouth
  u8g2.sendBuffer();
}

void eyesClosed() {
  u8g2.clearBuffer();
  u8g2.drawBox(EYE_L - 18, EYE_Y, 36, 4);
  u8g2.drawBox(EYE_R - 18, EYE_Y, 36, 4);
  u8g2.drawBox(56, 55, 16, 3);
  u8g2.sendBuffer();
}

void eyesHappy(int bounce = 0) {   // ^  ^
  u8g2.clearBuffer();
  for (int t = 0; t < 4; t++) {
    u8g2.drawLine(EYE_L - 16, EYE_Y + 8 - bounce + t, EYE_L, EYE_Y - 8 - bounce + t);
    u8g2.drawLine(EYE_L, EYE_Y - 8 - bounce + t, EYE_L + 16, EYE_Y + 8 - bounce + t);
    u8g2.drawLine(EYE_R - 16, EYE_Y + 8 - bounce + t, EYE_R, EYE_Y - 8 - bounce + t);
    u8g2.drawLine(EYE_R, EYE_Y - 8 - bounce + t, EYE_R + 16, EYE_Y + 8 - bounce + t);
  }
  u8g2.drawFilledEllipse(64, 52, 14, 8 - (bounce & 1) * 3);  // open mouth
  u8g2.sendBuffer();
}

void eyesSurprised() {
  u8g2.clearBuffer();
  u8g2.drawDisc(EYE_L, EYE_Y, 20);
  u8g2.drawDisc(EYE_R, EYE_Y, 20);
  u8g2.setDrawColor(0);
  u8g2.drawDisc(EYE_L, EYE_Y, 7);
  u8g2.drawDisc(EYE_R, EYE_Y, 7);
  u8g2.setDrawColor(1);
  u8g2.drawCircle(64, 57, 5);
  u8g2.sendBuffer();
}

void eyesWink() {
  u8g2.clearBuffer();
  u8g2.drawRBox(EYE_L - 18, EYE_Y - 18, 36, 36, 9);
  u8g2.drawBox(EYE_R - 18, EYE_Y, 36, 4);
  u8g2.drawLine(52, 52, 64, 58);
  u8g2.drawLine(64, 58, 76, 52);
  u8g2.sendBuffer();
}

void eyesDizzy(int frame) {        // spinning X eyes
  u8g2.clearBuffer();
  float a = frame * 0.5f;
  for (int e = 0; e < 2; e++) {
    int cx = e ? EYE_R : EYE_L;
    for (int k = 0; k < 2; k++) {
      float ang = a + k * PI / 2;
      int x = cos(ang) * 16, y = sin(ang) * 16;
      u8g2.drawLine(cx - x, EYE_Y - y, cx + x, EYE_Y + y);
      u8g2.drawLine(cx - x + 1, EYE_Y - y, cx + x + 1, EYE_Y + y);
    }
  }
  u8g2.drawFrame(54, 53, 20, 4);
  u8g2.sendBuffer();
}

void eyesSleepy(int zFrame) {
  u8g2.clearBuffer();
  u8g2.drawBox(EYE_L - 18, EYE_Y + 4, 36, 3);
  u8g2.drawBox(EYE_R - 18, EYE_Y + 4, 36, 3);
  u8g2.setFont(u8g2_font_6x10_tf);
  int z = zFrame % 3;
  u8g2.drawStr(100 + z * 6, 18 - z * 5, "z");
  if (z > 0) u8g2.drawStr(110, 10, "Z");
  u8g2.sendBuffer();
}

void showText(const char *txt) {
  u8g2.clearBuffer();
  u8g2.setFont(u8g2_font_logisoso24_tr);
  int w = u8g2.getStrWidth(txt);
  u8g2.drawStr((128 - w) / 2, 44, txt);
  u8g2.sendBuffer();
}

// ======================================================================
// Little comedy scenes
// ======================================================================

void sceneLaugh() {
  for (int i = 0; i < 3; i++) {
    eyesHappy(i % 2 ? 4 : 0);
    sweep(700 - i * 80, 550 - i * 80, 90);
    eyesHappy(i % 2 ? 0 : 4);
    rest(60);
  }
  showText("HA HA!");
  soundLaugh();
  eyesHappy();
  delay(400);
}

void sceneClap() {
  eyesSurprised();
  soundWhistle();
  delay(300);
  sceneLaugh();
}

void sceneWink() {
  eyesWink();
  soundBoing();
  delay(500);
}

void sceneDizzy() {
  for (int f = 0; f < 24; f++) {
    eyesDizzy(f);
    sweep(400 + (f % 6) * 120, 300 + (f % 6) * 120, 40, VOLUME / 2);
  }
  eyesOpen();
  delay(300);
}

void sceneTalk() {
  for (int i = 0; i < 3; i++) {
    eyesOpen(0, i % 2 ? -3 : 0);
    soundRobotTalk();
  }
  eyesOpen();
}

void sceneLookAround() {
  eyesOpen(-10, 0); delay(500);
  eyesOpen(10, 0);  delay(500);
  eyesOpen(0, -6);  delay(300);
  eyesSurprised();  beep(1400, 80);
  eyesOpen();
}

void sceneTaDa() {
  showText("TA-DA!");
  soundTune();
  eyesWink();
  delay(600);
}

void sceneSleep() {
  sleeping = true;
  eyesHappy(); soundYawn();
  eyesClosed(); delay(300);
}

void sceneWakeUp() {
  sleeping = false;
  eyesSurprised();
  sweep(300, 1800, 250);
  delay(200);
  sceneLookAround();
}

// ======================================================================

void setup() {
  Serial.begin(115200);
  randomSeed(esp_random());

  u8g2.begin();
  setupSpeaker();
  setupMic();

  showText("SALAV!");   // "Hello" in Kurdish (latin letters; OLED font has no Kurdish letters)
  soundTune();
  eyesOpen();

  lastSoundMillis = millis();
  nextBlinkMillis = millis() + 2000;
  nextJokeMillis = millis() + 8000;
}

void loop() {
  unsigned long now = millis();
  int level = micLevel();

  // Uncomment to see the mic level in Serial Monitor and tune CLAP_LEVEL
  // Serial.println(level);

  if (level > CLAP_LEVEL) {
    lastSoundMillis = now;
    if (sleeping) sceneWakeUp();
    else sceneClap();
    i2s_zero_dma_buffer(SPK_PORT);
    // throw away the robot's own sound that the mic just heard
    for (int i = 0; i < 20; i++) micLevel();
    nextJokeMillis = millis() + random(8000, 15000);
    return;
  }

  if (sleeping) {
    static int z = 0;
    eyesSleepy(z++);
    if (z % 6 == 0) {
      soundSnore();
      for (int i = 0; i < 20; i++) micLevel();  // do not wake up from own snore
    } else {
      delay(400);
    }
    return;
  }

  if (now - lastSoundMillis > SLEEP_AFTER_MS) {
    sceneSleep();
    for (int i = 0; i < 20; i++) micLevel();
    return;
  }

  if (now > nextBlinkMillis) {
    eyesClosed(); delay(120); eyesOpen();
    nextBlinkMillis = now + random(2000, 5000);
  }

  if (now > nextJokeMillis) {
    switch (random(5)) {
      case 0: sceneWink(); break;
      case 1: sceneDizzy(); break;
      case 2: sceneTalk(); break;
      case 3: sceneLookAround(); break;
      case 4: sceneTaDa(); break;
    }
    eyesOpen();
    for (int i = 0; i < 20; i++) micLevel();
    nextJokeMillis = millis() + random(8000, 15000);
  }
}

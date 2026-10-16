/*
 * Roboti Badini - ESP32 talking robot with OLED eyes
 * ---------------------------------------------------
 * روبوتێ ب بادینی دئاخڤیت - چاڤێن وی ل سەر شاشا OLED
 *
 * Hardware (see the Fritzing picture / README):
 *   ESP32 DevKit (WROOM-32)
 *   SSD1306 OLED 128x64 I2C    -> eyes + mouth
 *   INMP441 I2S microphone     -> listens to you
 *   MAX98357A I2S amplifier    -> speaker
 *
 * How it works:
 *   1. The robot listens with the INMP441. When you speak (sound is louder
 *      than the background noise) it starts recording.
 *   2. The audio is streamed over WiFi to the small Python server in
 *      ../server (runs on your PC / Raspberry Pi).
 *   3. The server turns speech into text (Kurmanji/Badini), asks Claude for
 *      a short answer in Badini, turns the answer into speech and sends the
 *      audio back.
 *   4. The ESP32 plays the answer on the speaker and moves the mouth on the
 *      OLED while it talks.
 *
 * Libraries (Arduino Library Manager):
 *   - U8g2 by oliver
 * Board: "ESP32 Dev Module" (esp32 core 2.x or 3.x)
 */

#include <Arduino.h>
#include <WiFi.h>
#include <Wire.h>
#include <U8g2lib.h>
#include <driver/i2s.h>

// ===================== CHANGE THESE ===========================
const char *WIFI_SSID   = "YOUR_WIFI_NAME";
const char *WIFI_PASS   = "YOUR_WIFI_PASSWORD";
const char *SERVER_HOST = "192.168.1.100";  // IP of the PC running server.py
const uint16_t SERVER_PORT = 8000;
// ==============================================================

// ---------------- Pins (match your wiring) --------------------
// OLED (I2C)
#define OLED_SDA 21
#define OLED_SCL 22

// INMP441 microphone (L/R pin -> GND, VDD -> 3.3V)
#define MIC_SCK 33
#define MIC_WS  25
#define MIC_SD  32

// MAX98357A amplifier (Vin -> 5V/VIN, GND -> GND)
#define AMP_BCLK 27
#define AMP_LRC  14
#define AMP_DIN  26

// Optional IR sensor from the original project (0 = not used)
#define USE_IR 0
#define IR_PIN 34
// --------------------------------------------------------------

// ---------------- Audio settings ------------------------------
#define SAMPLE_RATE       16000
#define MIC_PORT          I2S_NUM_0
#define AMP_PORT          I2S_NUM_1
#define FRAME_SAMPLES     512           // 32 ms per frame
#define PREROLL_FRAMES    6             // ~200 ms kept before speech starts
#define MAX_RECORD_MS     8000          // longest question
#define SILENCE_END_MS    900           // stop after this much silence
#define MIN_SPEECH_MS     300           // ignore very short noises
#define MIC_GAIN_SHIFT    14            // 32-bit mic sample -> 16-bit (lower = louder)
#define SPEAKER_VOLUME    0.8f          // 0.0 .. 1.0
#define SERVER_TIMEOUT_MS 60000
// --------------------------------------------------------------

U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, U8X8_PIN_NONE, OLED_SCL, OLED_SDA);

// ---------------- Robot face state ----------------------------
enum FaceState { FACE_IDLE, FACE_LISTEN, FACE_THINK, FACE_TALK, FACE_ERROR, FACE_LOOKUP };
volatile FaceState faceState = FACE_IDLE;
volatile uint8_t mouthLevel = 0;  // 0..10, set while the robot talks

int16_t frameBuf[FRAME_SAMPLES];
int32_t micRaw[FRAME_SAMPLES];
int16_t preroll[PREROLL_FRAMES][FRAME_SAMPLES];
float noiseFloor = 300;

// ===================== FACE / EYES ============================
// Draw one eye. cx, cy = centre, h = height (small = blinking)
void drawEye(int cx, int cy, int w, int h, bool happy) {
  if (h < 4) {  // closed eye = a line
    u8g2.drawBox(cx - w / 2, cy - 2, w, 4);
    return;
  }
  int r = min(8, h / 2 - 1);
  u8g2.drawRBox(cx - w / 2, cy - h / 2, w, h, r);
  if (happy) {  // cut the bottom with a black ellipse -> "^ ^" eyes
    u8g2.setDrawColor(0);
    u8g2.drawFilledEllipse(cx, cy + h / 2 + 4, w / 2 + 2, h / 2);
    u8g2.setDrawColor(1);
  }
}

void drawFace() {
  static uint32_t nextBlink = 0, blinkStart = 0, nextLook = 0;
  static int lookX = 0, lookY = 0;
  uint32_t now = millis();

  int eyeW = 34, eyeH = 34, cy = 26, offX = 0, offY = 0;
  bool happy = false;

  // blinking (all states except error)
  if (now > nextBlink) { blinkStart = now; nextBlink = now + random(2000, 5000); }
  uint32_t bt = now - blinkStart;
  if (bt < 120) eyeH = map(bt, 0, 120, 34, 2);
  else if (bt < 240) eyeH = map(bt, 120, 240, 2, 34);

  // look around a little while idle
  if (now > nextLook) {
    lookX = random(-8, 9); lookY = random(-4, 5);
    nextLook = now + random(1500, 4000);
  }

  u8g2.clearBuffer();
  switch (faceState) {
    case FACE_IDLE:
      offX = lookX; offY = lookY;
      break;
    case FACE_LISTEN:  // big, wide open eyes
      eyeW = 38;
      if (bt >= 240) eyeH = 38;
      break;
    case FACE_THINK: {  // eyes look up and move left/right, dots below
      offY = -6;
      offX = (int)(8 * sin(now / 300.0));
      eyeH = min(eyeH, 26);
      int dots = (now / 300) % 4;
      for (int i = 0; i < dots; i++) u8g2.drawDisc(54 + i * 10, 58, 2);
      break;
    }
    case FACE_TALK: {  // happy eyes + moving mouth
      happy = true;
      eyeH = 30; cy = 22;
      int mh = 2 + mouthLevel * 1.4;
      u8g2.drawRBox(64 - 14, 54 - mh / 2, 28, mh, mh > 4 ? 3 : 1);
      break;
    }
    case FACE_ERROR:  // X X eyes
      for (int e = 0; e < 2; e++) {
        int x = e ? 96 : 32;
        for (int t = -1; t <= 1; t++) {
          u8g2.drawLine(x - 12 + t, 14, x + 12 + t, 38);
          u8g2.drawLine(x + 12 + t, 14, x - 12 + t, 38);
        }
      }
      u8g2.sendBuffer();
      return;
    case FACE_LOOKUP:  // original IR "look up" eyes
      offY = -10; eyeH = 22;
      break;
  }

  drawEye(32 + offX, cy + offY, eyeW, eyeH, happy);
  drawEye(96 + offX, cy + offY, eyeW, eyeH, happy);
  u8g2.sendBuffer();
}

// The face runs in its own task so it keeps moving while WiFi / audio work
void faceTask(void *) {
  for (;;) {
    drawFace();
    vTaskDelay(pdMS_TO_TICKS(30));
  }
}

// ===================== I2S AUDIO ==============================
void setupMic() {
  i2s_config_t cfg = {};
  cfg.mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX);
  cfg.sample_rate = SAMPLE_RATE;
  cfg.bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT;
  cfg.channel_format = I2S_CHANNEL_FMT_ONLY_LEFT;
  cfg.communication_format = I2S_COMM_FORMAT_STAND_I2S;
  cfg.intr_alloc_flags = ESP_INTR_FLAG_LEVEL1;
  cfg.dma_buf_count = 8;
  cfg.dma_buf_len = 256;
  cfg.use_apll = false;

  i2s_pin_config_t pins = {};
  pins.mck_io_num = I2S_PIN_NO_CHANGE;
  pins.bck_io_num = MIC_SCK;
  pins.ws_io_num = MIC_WS;
  pins.data_out_num = I2S_PIN_NO_CHANGE;
  pins.data_in_num = MIC_SD;

  i2s_driver_install(MIC_PORT, &cfg, 0, NULL);
  i2s_set_pin(MIC_PORT, &pins);
  i2s_zero_dma_buffer(MIC_PORT);
}

void setupAmp() {
  i2s_config_t cfg = {};
  cfg.mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX);
  cfg.sample_rate = SAMPLE_RATE;
  cfg.bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT;
  cfg.channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT;
  cfg.communication_format = I2S_COMM_FORMAT_STAND_I2S;
  cfg.intr_alloc_flags = ESP_INTR_FLAG_LEVEL1;
  cfg.dma_buf_count = 8;
  cfg.dma_buf_len = 256;
  cfg.use_apll = false;
  cfg.tx_desc_auto_clear = true;

  i2s_pin_config_t pins = {};
  pins.mck_io_num = I2S_PIN_NO_CHANGE;
  pins.bck_io_num = AMP_BCLK;
  pins.ws_io_num = AMP_LRC;
  pins.data_out_num = AMP_DIN;
  pins.data_in_num = I2S_PIN_NO_CHANGE;

  i2s_driver_install(AMP_PORT, &cfg, 0, NULL);
  i2s_set_pin(AMP_PORT, &pins);
  i2s_zero_dma_buffer(AMP_PORT);
}

// Read one frame from the mic into frameBuf (16-bit). Returns RMS level.
float readMicFrame() {
  size_t bytesRead = 0;
  i2s_read(MIC_PORT, micRaw, sizeof(micRaw), &bytesRead, portMAX_DELAY);
  int n = bytesRead / 4;
  double sum = 0;
  for (int i = 0; i < n; i++) {
    int32_t s = micRaw[i] >> MIC_GAIN_SHIFT;
    if (s > 32767) s = 32767;
    if (s < -32768) s = -32768;
    frameBuf[i] = (int16_t)s;
    sum += (double)s * s;
  }
  for (int i = n; i < FRAME_SAMPLES; i++) frameBuf[i] = 0;
  return n ? sqrt(sum / n) : 0;
}

void calibrateNoise() {
  float total = 0;
  for (int i = 0; i < 5; i++) readMicFrame();  // throw away first frames
  for (int i = 0; i < 30; i++) total += readMicFrame();
  noiseFloor = max(total / 30, 100.0f);
  Serial.printf("Noise floor: %.0f\n", noiseFloor);
}

// ===================== HTTP helpers ===========================
void sendChunk(WiFiClient &c, const uint8_t *data, size_t len) {
  c.printf("%X\r\n", (unsigned)len);
  c.write(data, len);
  c.print("\r\n");
}

// Play the server's answer (raw 16-bit mono PCM, 16 kHz) on the speaker.
void playResponse(WiFiClient &c) {
  // --- status line + headers ---
  uint32_t t0 = millis();
  while (!c.available()) {
    if (!c.connected() || millis() - t0 > SERVER_TIMEOUT_MS) {
      Serial.println("Server timeout");
      faceState = FACE_ERROR;
      return;
    }
    delay(10);
  }
  String status = c.readStringUntil('\n');
  Serial.println(status);
  long contentLength = -1;
  for (;;) {
    String line = c.readStringUntil('\n');
    line.trim();
    if (line.length() == 0) break;
    String lower = line;
    lower.toLowerCase();
    if (lower.startsWith("content-length:")) contentLength = line.substring(15).toInt();
    if (lower.startsWith("x-robot-text:")) Serial.println("Robot: " + line.substring(13));
    if (lower.startsWith("x-user-text:")) Serial.println("You:   " + line.substring(12));
  }
  if (status.indexOf("200") < 0 || contentLength <= 0) {
    // 204 = nothing understood -> just go back to idle
    faceState = status.indexOf("204") >= 0 ? FACE_IDLE : FACE_ERROR;
    return;
  }

  // --- audio body ---
  faceState = FACE_TALK;
  static int16_t in[256];
  static int16_t out[512];
  long remaining = contentLength;
  uint8_t carry = 0;
  bool hasCarry = false;
  t0 = millis();
  while (remaining > 0 && (c.connected() || c.available())) {
    int avail = c.available();
    if (avail <= 0) {
      if (millis() - t0 > 5000) break;
      delay(1);
      continue;
    }
    t0 = millis();
    uint8_t *dst = (uint8_t *)in;
    int off = 0;
    if (hasCarry) { dst[0] = carry; off = 1; hasCarry = false; }
    int want = min((long)sizeof(in) - off, remaining);
    int got = c.read(dst + off, want);
    if (got <= 0) continue;
    remaining -= got;
    int total = got + off;
    if (total & 1) { carry = dst[total - 1]; hasCarry = true; total--; }
    int samples = total / 2;

    int peak = 0;
    for (int i = 0; i < samples; i++) {
      int16_t s = (int16_t)(in[i] * SPEAKER_VOLUME);
      out[2 * i] = s;       // left
      out[2 * i + 1] = s;   // right
      peak = max(peak, abs((int)s));
    }
    mouthLevel = min(10, peak / 1800);
    size_t written;
    i2s_write(AMP_PORT, out, samples * 4, &written, portMAX_DELAY);
  }
  i2s_zero_dma_buffer(AMP_PORT);
  mouthLevel = 0;
  faceState = FACE_IDLE;
}

// Record one question while streaming it to the server, then play the answer.
void talkToServer(int prerollStart, int prerollCount) {
  WiFiClient client;
  client.setTimeout(SERVER_TIMEOUT_MS / 1000);
  if (!client.connect(SERVER_HOST, SERVER_PORT)) {
    Serial.println("Cannot connect to server!");
    faceState = FACE_ERROR;
    delay(1500);
    faceState = FACE_IDLE;
    return;
  }
  client.setNoDelay(true);
  client.printf("POST /talk HTTP/1.1\r\nHost: %s\r\n", SERVER_HOST);
  client.print("Content-Type: application/octet-stream\r\n");
  client.print("Transfer-Encoding: chunked\r\nConnection: close\r\n\r\n");

  // audio from just before the speech started
  for (int i = 0; i < prerollCount; i++) {
    int idx = (prerollStart + i) % PREROLL_FRAMES;
    sendChunk(client, (uint8_t *)preroll[idx], sizeof(preroll[idx]));
  }

  uint32_t start = millis(), lastVoice = millis();
  float threshold = noiseFloor * 2.5f;
  while (millis() - start < MAX_RECORD_MS) {
    float level = readMicFrame();
    sendChunk(client, (uint8_t *)frameBuf, sizeof(frameBuf));
    if (level > threshold) lastVoice = millis();
    if (millis() - lastVoice > SILENCE_END_MS) break;
  }
  client.print("0\r\n\r\n");  // end of chunked body

  faceState = FACE_THINK;
  playResponse(client);
  client.stop();
}

// ===================== SETUP / LOOP ===========================
void setup() {
  Serial.begin(115200);
#if USE_IR
  pinMode(IR_PIN, INPUT);
#endif
  u8g2.begin();
  randomSeed(esp_random());
  xTaskCreatePinnedToCore(faceTask, "face", 4096, NULL, 1, NULL, 0);

  faceState = FACE_THINK;
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("WiFi");
  while (WiFi.status() != WL_CONNECTED) { delay(300); Serial.print("."); }
  Serial.printf("\nIP: %s\n", WiFi.localIP().toString().c_str());

  setupMic();
  setupAmp();
  calibrateNoise();
  faceState = FACE_IDLE;
}

void loop() {
  static int prerollPos = 0, prerollCount = 0;
  static uint32_t voiceSince = 0;

  if (WiFi.status() != WL_CONNECTED) {
    faceState = FACE_ERROR;
    WiFi.reconnect();
    delay(2000);
    return;
  }

#if USE_IR
  if (digitalRead(IR_PIN) == 0) faceState = FACE_LOOKUP;
  else if (faceState == FACE_LOOKUP) faceState = FACE_IDLE;
#endif

  float level = readMicFrame();
  memcpy(preroll[prerollPos], frameBuf, sizeof(frameBuf));
  prerollPos = (prerollPos + 1) % PREROLL_FRAMES;
  if (prerollCount < PREROLL_FRAMES) prerollCount++;

  if (level > noiseFloor * 3.0f) {
    if (voiceSince == 0) voiceSince = millis();
    faceState = FACE_LISTEN;
    if (millis() - voiceSince >= MIN_SPEECH_MS) {
      Serial.println("Listening...");
      int start = (prerollPos - prerollCount + PREROLL_FRAMES) % PREROLL_FRAMES;
      talkToServer(start, prerollCount);
      prerollCount = 0;
      voiceSince = 0;
      i2s_zero_dma_buffer(MIC_PORT);
    }
  } else {
    if (voiceSince && millis() - voiceSince > MIN_SPEECH_MS * 2) voiceSince = 0;
    if (voiceSince == 0 && faceState == FACE_LISTEN) faceState = FACE_IDLE;
    // slowly follow the background noise
    noiseFloor = noiseFloor * 0.995f + level * 0.005f;
    if (noiseFloor < 100) noiseFloor = 100;
  }
}

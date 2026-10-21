/*
  ESP32 Gemini Voice Robot
  ------------------------
  Ask the robot a question with your voice, and it answers with its voice.

    1. Wave your hand in front of the IR sensor (or press the BOOT button).
    2. After the short beep, speak for 3 seconds.
    3. The robot sends your voice to Gemini over WiFi, gets a short answer,
       turns the answer into speech with Gemini, and plays it on the speaker.
       The OLED face shows: listening -> thinking -> talking.

  Hardware:
    OLED SSD1306 128x64 (I2C)  VCC -> 3V3, GND, SDA -> GPIO21, SCL -> GPIO22
    IR obstacle sensor         VCC -> 3V3, GND, OUT -> GPIO34 (LOW = hand)
    INMP441 microphone         VDD -> 3V3 (NOT 5V), GND, L/R -> GND,
                               WS -> GPIO33, SCK -> GPIO32, SD -> GPIO35
    MAX98357A amplifier        Vin -> 5V, GND, LRC -> GPIO25, BCLK -> GPIO26, DIN -> GPIO27
                               GAIN and SD not connected, speaker on the green terminal

  Software:
    - Board package "esp32" by Espressif, version 3.x  (Board: "ESP32 Dev Module")
    - Library: U8g2 by olikraus (install only, do NOT use "Sketch > Include Library")
    - A Gemini API key from https://aistudio.google.com  (keep it secret!)

  If Gemini answers "404 model not found", the model names below have changed:
  look up the current names on https://ai.google.dev/gemini-api/docs/models
*/

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ESP_I2S.h>
#include <U8g2lib.h>
#include <Wire.h>

// ===================== CHANGE THESE =====================
const char *WIFI_SSID = "YOUR_WIFI_NAME";
const char *WIFI_PASS = "YOUR_WIFI_PASSWORD";
const char *GEMINI_API_KEY = "YOUR_GEMINI_API_KEY";

const char *MODEL_TEXT = "gemini-flash-lite-latest";       // understands your voice, writes the answer
const char *MODEL_TTS = "gemini-3.1-flash-tts-preview";    // turns the answer into speech
const char *VOICE_NAME = "Kore";
// Badini Kurdish, written in Latin letters (Kurmanji alphabet) so the speech voice can read it aloud.
// Other examples: "the same language the person speaks", "Arabic", "English"
const char *ANSWER_LANGUAGE = "Kurdish, Badini (Behdini) dialect, written in the Latin Kurmanji alphabet";
const float SPEAKER_VOLUME = 0.6;                          // 0.0 .. 1.0
// true only when the IR sensor is connected: an unconnected GPIO34 floats and
// keeps "waving", which made the robot report "No WiFi" over and over.
const bool USE_IR_SENSOR = false;
// ========================================================

// ---------------- Pins ----------------
const int IR_PIN = 34;
const int BUTTON_PIN = 0;
const int SDA_PIN = 21, SCL_PIN = 22;
const int MIC_SCK = 32, MIC_WS = 33, MIC_SD = 35;
const int SPK_BCLK = 26, SPK_LRC = 25, SPK_DIN = 27;

// ---------------- Audio settings ----------------
const uint32_t MIC_RATE = 16000;        // what we send to Gemini
const uint32_t TTS_RATE = 24000;        // Gemini TTS returns 24 kHz, 16-bit, mono PCM
const int MIC_GAIN_SHIFT = 13;          // 32-bit mic sample >> 13 -> 16-bit (bigger = quieter)

// ---------------- Objects ----------------
U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, /* reset=*/U8X8_PIN_NONE);
I2SClass mic;
I2SClass speaker;

int16_t *recording = nullptr;           // the recorded question (16-bit PCM)
size_t recordingSamples = 0;            // capacity in samples

// =====================================================================
//                               FACE
// =====================================================================
enum Face { FACE_IDLE, FACE_LISTEN, FACE_THINK, FACE_TALK, FACE_ERROR };

float lookX = 0, targetX = 0;
unsigned long nextLookAt = 0, nextBlinkAt = 0, blinkUntil = 0;

void drawEyes(int dx, int dy, int h) {
  const int w = 30;
  for (int cx : {38, 90}) {
    int x = cx + dx - w / 2;
    int y = 22 + dy - h / 2;
    int r = (h / 2 - 1 < 7) ? h / 2 - 1 : 7;
    if (r >= 1) {
      u8g2.drawRBox(x, y, w, h, r);
    } else {
      u8g2.drawBox(x, y, w, h);
    }
  }
}

void drawFace(Face face, int mouthOpen, const char *message) {
  u8g2.clearBuffer();
  unsigned long now = millis();
  switch (face) {
    case FACE_IDLE: {
      int h = now < blinkUntil ? 3 : 26;
      drawEyes((int)lookX, 0, h);
      u8g2.drawRBox(52 + (int)(lookX / 2), 50, 24, 3, 1);
      break;
    }
    case FACE_LISTEN:
      drawEyes(0, 0, 30);                                  // wide open eyes
      u8g2.drawCircle(64, 52, 5);                          // small "o" mouth
      u8g2.drawCircle(64, 52, 4);
      break;
    case FACE_THINK: {
      drawEyes(6, -8, 18);                                 // looking up and to the side
      int dots = (now / 300) % 4;
      for (int i = 0; i < dots; i++) {
        u8g2.drawDisc(54 + i * 10, 52, 2);
      }
      break;
    }
    case FACE_TALK: {
      drawEyes(0, 0, 26);
      int h = mouthOpen < 3 ? 3 : mouthOpen;
      int w = 22 + mouthOpen;
      int r = h / 2 - 1;
      if (r >= 1) {
        u8g2.drawRBox(64 - w / 2, 51 - h / 2, w, h, r);
      } else {
        u8g2.drawBox(64 - w / 2, 51 - h / 2, w, h);
      }
      break;
    }
    case FACE_ERROR:
      for (int cx : {38, 90}) {                            // X X eyes
        u8g2.drawLine(cx - 10, 12, cx + 10, 32);
        u8g2.drawLine(cx + 10, 12, cx - 10, 32);
        u8g2.drawLine(cx - 9, 12, cx + 11, 32);
        u8g2.drawLine(cx + 11, 12, cx - 9, 32);
      }
      break;
  }
  if (message) {
    u8g2.setFont(u8g2_font_6x10_tr);
    u8g2.drawStr((128 - u8g2.getStrWidth(message)) / 2, 63, message);
  }
  u8g2.sendBuffer();
}

void updateIdleFace() {
  unsigned long now = millis();
  if (now >= nextLookAt) {
    targetX = random(-8, 9);
    nextLookAt = now + random(1500, 4000);
  }
  if (now >= nextBlinkAt) {
    blinkUntil = now + 120;
    nextBlinkAt = now + random(2000, 5000);
  }
  lookX += (targetX - lookX) * 0.25;
  drawFace(FACE_IDLE, 0, nullptr);
}

void showError(const char *message) {
  Serial.print("ERROR: ");
  Serial.println(message);
  drawFace(FACE_ERROR, 0, message);
  delay(3000);
}

// =====================================================================
//                         SPEAKER AND MICROPHONE
// =====================================================================
void beep(int freq, int ms) {
  const int n = TTS_RATE * ms / 1000;
  int16_t buf[256];
  int phase = 0;
  for (int done = 0; done < n;) {
    int count = min(256, n - done);
    for (int i = 0; i < count; i++, phase++) {
      // simple square wave, quiet
      buf[i] = ((phase * freq * 2 / (int)TTS_RATE) % 2) ? 3000 : -3000;
    }
    speaker.write((uint8_t *)buf, count * sizeof(int16_t));
    done += count;
  }
}

// Record `seconds` of audio into `recording`. Returns the number of samples recorded.
size_t recordQuestion() {
  static int32_t raw[512];
  // throw away ~100 ms so the microphone settles
  for (int i = 0; i < 4; i++) {
    mic.readBytes((char *)raw, sizeof(raw));
  }
  size_t got = 0;
  int level = 0;
  unsigned long lastDraw = 0;
  while (got < recordingSamples) {
    size_t bytes = mic.readBytes((char *)raw, sizeof(raw));
    size_t n = bytes / sizeof(int32_t);
    for (size_t i = 0; i < n && got < recordingSamples; i++) {
      int32_t s = raw[i] >> MIC_GAIN_SHIFT;
      if (s > 32767) s = 32767;
      if (s < -32768) s = -32768;
      recording[got++] = (int16_t)s;
      int a = abs((int)s);
      if (a > level) level = a;
    }
    if (millis() - lastDraw > 100) {             // a small sound-level bar while listening
      lastDraw = millis();
      drawFace(FACE_LISTEN, 0, nullptr);
      int bar = map(min(level, 12000), 0, 12000, 0, 100);
      u8g2.drawFrame(13, 59, 102, 5);
      u8g2.drawBox(14, 60, bar, 3);
      u8g2.sendBuffer();
      level = 0;
    }
  }
  return got;
}

// =====================================================================
//              STREAMING HELPERS (the ESP32 has little memory)
// =====================================================================

// The request body for "here is my voice, answer it": JSON text + base64 of a WAV file,
// produced on the fly so the base64 text never has to fit in memory.
class AudioRequestBody : public Stream {
 public:
  AudioRequestBody(const String &head, const int16_t *pcm, size_t samples, const String &tail)
      : head_(head), tail_(tail), pcm_((const uint8_t *)pcm) {
    rawLen_ = 44 + samples * 2;
    b64Len_ = 4 * ((rawLen_ + 2) / 3);
    makeWavHeader(samples);
  }

  size_t totalSize() const { return head_.length() + b64Len_ + tail_.length(); }

  int available() override {
    size_t left = totalSize() - pos_;
    return left > 0x7FFFFFFF ? 0x7FFFFFFF : (int)left;
  }
  int read() override {
    char c;
    return readBytes(&c, 1) == 1 ? (uint8_t)c : -1;
  }
  int peek() override { return -1; }
  size_t write(uint8_t) override { return 0; }

  size_t readBytes(char *buf, size_t len) override {
    size_t n = 0;
    while (n < len && pos_ < totalSize()) {
      buf[n++] = charAt(pos_++);
    }
    return n;
  }

 private:
  char charAt(size_t p) {
    if (p < head_.length()) return head_[p];
    p -= head_.length();
    if (p < b64Len_) return base64Char(p);
    return tail_[p - b64Len_];
  }

  uint8_t rawAt(size_t i) const { return i < 44 ? wav_[i] : pcm_[i - 44]; }

  char base64Char(size_t p) const {
    static const char *T = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    size_t g = p / 4, k = p % 4, i = g * 3;
    uint32_t v = (uint32_t)rawAt(i) << 16;
    size_t have = rawLen_ - i;                    // bytes available in this group (1, 2 or 3+)
    if (have > 1) v |= (uint32_t)rawAt(i + 1) << 8;
    if (have > 2) v |= rawAt(i + 2);
    if (k == 2 && have < 2) return '=';
    if (k == 3 && have < 3) return '=';
    return T[(v >> (18 - 6 * k)) & 0x3F];
  }

  void makeWavHeader(size_t samples) {
    uint32_t dataBytes = samples * 2, byteRate = MIC_RATE * 2;
    memcpy(wav_, "RIFF", 4);
    put32(4, 36 + dataBytes);
    memcpy(wav_ + 8, "WAVEfmt ", 8);
    put32(16, 16);
    put16(20, 1);                                 // PCM
    put16(22, 1);                                 // mono
    put32(24, MIC_RATE);
    put32(28, byteRate);
    put16(32, 2);                                 // block align
    put16(34, 16);                                // bits per sample
    memcpy(wav_ + 36, "data", 4);
    put32(40, dataBytes);
  }
  void put16(int at, uint16_t v) { wav_[at] = v & 0xFF; wav_[at + 1] = v >> 8; }
  void put32(int at, uint32_t v) { for (int i = 0; i < 4; i++) wav_[at + i] = (v >> (8 * i)) & 0xFF; }

  String head_, tail_;
  const uint8_t *pcm_;
  uint8_t wav_[44];
  size_t rawLen_, b64Len_, pos_ = 0;
};

// Receives the TTS answer JSON piece by piece, finds "data": "<base64 PCM>",
// decodes it and plays it on the speaker straight away. Moves the mouth while talking.
class SpeechPlayer : public Stream {
 public:
  bool foundAudio() const { return found_; }
  size_t bytesPlayed() const { return played_; }

  size_t write(uint8_t c) override {
    handle(c);
    return 1;
  }
  size_t write(const uint8_t *buf, size_t len) override {
    for (size_t i = 0; i < len; i++) handle(buf[i]);
    return len;
  }
  int available() override { return 0; }
  int read() override { return -1; }
  int peek() override { return -1; }

  void finish() {
    flushPcm();
    drawFace(FACE_TALK, 0, nullptr);
  }

 private:
  enum State { FIND_KEY, FIND_QUOTE, DECODE, DONE };

  void handle(uint8_t c) {
    static const char *KEY = "\"data\"";
    switch (state_) {
      case FIND_KEY:
        if (c == (uint8_t)KEY[match_]) {
          if (KEY[++match_] == 0) {
            state_ = FIND_QUOTE;
            match_ = 0;
          }
        } else {
          match_ = (c == '"') ? 1 : 0;
        }
        break;
      case FIND_QUOTE:
        if (c == '"') {
          state_ = DECODE;
          found_ = true;
        } else if (c != ':' && c != ' ' && c != '\n' && c != '\r' && c != '\t') {
          state_ = FIND_KEY;                        // it was something else called "data"
        }
        break;
      case DECODE: {
        if (c == '"') {
          state_ = DONE;
          return;
        }
        int v = b64Value(c);
        if (v < 0) return;                          // '=' padding or a line break
        quad_ = (quad_ << 6) | v;
        if (++quadCount_ == 4) {
          pushByte((quad_ >> 16) & 0xFF);
          pushByte((quad_ >> 8) & 0xFF);
          pushByte(quad_ & 0xFF);
          quad_ = 0;
          quadCount_ = 0;
        }
        break;
      }
      case DONE:
        break;
    }
  }

  void pushByte(uint8_t b) {
    pcm_[pcmLen_++] = b;
    if (pcmLen_ >= PCM_CHUNK) flushPcm();
  }

  void flushPcm() {
    // leftover base64 (padding at the very end): 2 chars = 1 byte, 3 chars = 2 bytes
    if (state_ == DONE && quadCount_ > 1) {
      uint32_t q = quad_ << (6 * (4 - quadCount_));
      pcm_[pcmLen_++] = (q >> 16) & 0xFF;
      if (quadCount_ == 3) pcm_[pcmLen_++] = (q >> 8) & 0xFF;
      quadCount_ = 0;
    }
    size_t even = pcmLen_ & ~(size_t)1;
    if (even == 0) return;
    int16_t *s = (int16_t *)pcm_;
    int peak = 0;
    for (size_t i = 0; i < even / 2; i++) {
      s[i] = (int16_t)(s[i] * SPEAKER_VOLUME);
      int a = abs((int)s[i]);
      if (a > peak) peak = a;
    }
    speaker.write(pcm_, even);
    played_ += even;
    if (pcmLen_ > even) {                           // keep an odd byte for next time
      pcm_[0] = pcm_[even];
    }
    pcmLen_ -= even;
    if (millis() - lastMouth_ > 120) {              // mouth follows the loudness
      lastMouth_ = millis();
      drawFace(FACE_TALK, map(min(peak, 16000), 0, 16000, 0, 14), nullptr);
    }
  }

  static int b64Value(uint8_t c) {
    if (c >= 'A' && c <= 'Z') return c - 'A';
    if (c >= 'a' && c <= 'z') return c - 'a' + 26;
    if (c >= '0' && c <= '9') return c - '0' + 52;
    if (c == '+') return 62;
    if (c == '/') return 63;
    return -1;
  }

  State state_ = FIND_KEY;
  int match_ = 0;
  bool found_ = false;
  uint32_t quad_ = 0;
  int quadCount_ = 0;
  static const size_t PCM_CHUNK = 1024;
  // +2 spare bytes for the last base64 group; aligned because it is read as int16_t
  alignas(4) uint8_t pcm_[PCM_CHUNK + 2];
  size_t pcmLen_ = 0;
  size_t played_ = 0;
  unsigned long lastMouth_ = 0;
};

// =====================================================================
//                              JSON HELPERS
// =====================================================================
String jsonEscape(const String &s) {
  String out;
  out.reserve(s.length() + 16);
  for (size_t i = 0; i < s.length(); i++) {
    char c = s[i];
    switch (c) {
      case '"': out += "\\\""; break;
      case '\\': out += "\\\\"; break;
      case '\n': out += "\\n"; break;
      case '\r': break;
      case '\t': out += "\\t"; break;
      default: out += c;
    }
  }
  return out;
}

void appendUtf8(String &out, uint32_t cp) {
  if (cp < 0x80) {
    out += (char)cp;
  } else if (cp < 0x800) {
    out += (char)(0xC0 | (cp >> 6));
    out += (char)(0x80 | (cp & 0x3F));
  } else if (cp < 0x10000) {
    out += (char)(0xE0 | (cp >> 12));
    out += (char)(0x80 | ((cp >> 6) & 0x3F));
    out += (char)(0x80 | (cp & 0x3F));
  } else {
    out += (char)(0xF0 | (cp >> 18));
    out += (char)(0x80 | ((cp >> 12) & 0x3F));
    out += (char)(0x80 | ((cp >> 6) & 0x3F));
    out += (char)(0x80 | (cp & 0x3F));
  }
}

// Read 4 hex digits (as in س) starting at `at`.
uint32_t hex4(const String &s, int at) {
  uint32_t v = 0;
  for (int k = 0; k < 4; k++) {
    char c = s[at + k];
    int d = (c >= '0' && c <= '9') ? c - '0' : (c >= 'a' && c <= 'f') ? c - 'a' + 10 : (c >= 'A' && c <= 'F') ? c - 'A' + 10 : 0;
    v = (v << 4) | d;
  }
  return v;
}

// Find "key": "value" after position `from` and return the decoded value ("" if not found).
String jsonStringAfter(const String &json, const char *key, int from) {
  String k = String("\"") + key + "\"";
  int p = json.indexOf(k, from);
  if (p < 0) return "";
  p = json.indexOf(':', p + k.length());
  if (p < 0) return "";
  p = json.indexOf('"', p);
  if (p < 0) return "";
  String out;
  for (int i = p + 1; i < (int)json.length(); i++) {
    char c = json[i];
    if (c == '"') return out;
    if (c != '\\') {
      out += c;
      continue;
    }
    char e = json[++i];
    switch (e) {
      case 'n': out += '\n'; break;
      case 't': out += ' '; break;
      case 'r': break;
      case 'u': {
        uint32_t cp = hex4(json, i + 1);
        i += 4;
        if (cp >= 0xD800 && cp <= 0xDBFF && json[i + 1] == '\\' && json[i + 2] == 'u') {
          uint32_t lo = hex4(json, i + 3);
          cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
          i += 6;
        }
        appendUtf8(out, cp);
        break;
      }
      default: out += e;                            // \" \\ \/
    }
  }
  return out;
}

// =====================================================================
//                              GEMINI
// =====================================================================
// With no certificate (nullptr), HTTPClient uses HTTPS without checking the certificate.
const char *NO_CERTIFICATE = nullptr;

String geminiUrl(const char *model) {
  return String("https://generativelanguage.googleapis.com/v1beta/models/") + model + ":generateContent";
}

// Step 1: voice -> short text answer
String askGemini(size_t samples) {
  String prompt = String("You are a small, friendly robot. Listen to the question in the audio and answer it ") +
                  "in one or two short sentences, in " + ANSWER_LANGUAGE +
                  ". Use plain words only, no lists or symbols. If the audio is silent, say that you did not hear anything.";
  String head = String("{\"contents\":[{\"parts\":[{\"text\":\"") + jsonEscape(prompt) +
                "\"},{\"inline_data\":{\"mime_type\":\"audio/wav\",\"data\":\"";
  String tail = "\"}}]}],\"generationConfig\":{\"maxOutputTokens\":1024}}";
  AudioRequestBody body(head, recording, samples, tail);

  HTTPClient http;
  http.setTimeout(30000);
  if (!http.begin(geminiUrl(MODEL_TEXT), NO_CERTIFICATE)) return "";
  http.addHeader("Content-Type", "application/json");
  http.addHeader("x-goog-api-key", GEMINI_API_KEY);

  Serial.printf("Sending %u bytes of audio to %s ...\n", (unsigned)(samples * 2), MODEL_TEXT);
  int code = http.sendRequest("POST", &body, body.totalSize());
  String response = http.getString();
  http.end();
  Serial.printf("HTTP %d\n", code);
  if (code != 200) {
    Serial.println(response);
    return "";
  }
  int cand = response.indexOf("\"candidates\"");
  String answer = jsonStringAfter(response, "text", cand < 0 ? 0 : cand);
  answer.trim();
  return answer;
}

// Step 2: text answer -> speech, played while it downloads
bool speak(const String &text) {
  String body = String("{\"contents\":[{\"parts\":[{\"text\":\"") + jsonEscape(text) +
                "\"}]}],\"generationConfig\":{\"responseModalities\":[\"AUDIO\"],"
                "\"speechConfig\":{\"voiceConfig\":{\"prebuiltVoiceConfig\":{\"voiceName\":\"" +
                VOICE_NAME + "\"}}}}}";

  HTTPClient http;
  http.setTimeout(30000);
  if (!http.begin(geminiUrl(MODEL_TTS), NO_CERTIFICATE)) return false;
  http.addHeader("Content-Type", "application/json");
  http.addHeader("x-goog-api-key", GEMINI_API_KEY);

  Serial.printf("Asking %s to speak ...\n", MODEL_TTS);
  int code = http.POST(body);
  Serial.printf("HTTP %d\n", code);
  if (code != 200) {
    Serial.println(http.getString());
    http.end();
    return false;
  }
  SpeechPlayer player;
  http.writeToStream(&player);
  player.finish();
  http.end();
  Serial.printf("Played %u bytes of speech\n", (unsigned)player.bytesPlayed());
  return player.foundAudio() && player.bytesPlayed() > 0;
}

// =====================================================================
//                              ARDUINO
// =====================================================================
void setup() {
  Serial.begin(115200);
  pinMode(IR_PIN, INPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  Wire.begin(SDA_PIN, SCL_PIN);
  u8g2.begin();
  u8g2.setBusClock(400000);                         // faster screen updates while talking
  randomSeed(esp_random());

  // Microphone: INMP441 sends 32-bit samples on the left slot
  mic.setPins(MIC_SCK, MIC_WS, -1, MIC_SD);
  if (!mic.begin(I2S_MODE_STD, MIC_RATE, I2S_DATA_BIT_WIDTH_32BIT, I2S_SLOT_MODE_MONO, I2S_STD_SLOT_LEFT)) {
    showError("Mic not working");
  }
  // Speaker: MAX98357A, 16-bit mono at the TTS rate
  speaker.setPins(SPK_BCLK, SPK_LRC, SPK_DIN);
  if (!speaker.begin(I2S_MODE_STD, TTS_RATE, I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_MONO)) {
    showError("Speaker not working");
  }

  // Memory for the recording: 5 s with PSRAM, otherwise 3 s (96 KB)
  int seconds = psramFound() ? 5 : 3;
  recordingSamples = MIC_RATE * seconds;
  recording = (int16_t *)ps_malloc(recordingSamples * sizeof(int16_t));
  if (!recording) {
    recordingSamples = MIC_RATE * 2;
    recording = (int16_t *)malloc(recordingSamples * sizeof(int16_t));
  }
  if (!recording) {
    showError("No memory");
  }
  Serial.printf("Recording time: %u s\n", (unsigned)(recordingSamples / MIC_RATE));

  // WiFi starts after the audio is set up, as in the first version: starting
  // it earlier made the speaker fail to start ("Speaker not working").
  drawFace(FACE_THINK, 0, "WiFi...");
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  // Wait for WiFi (phone hotspots can be slow to hand out an address)
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 45000) {
    drawFace(FACE_THINK, 0, "WiFi...");
    delay(200);
  }
  wl_status_t st = WiFi.status();
  Serial.printf("WiFi status: %d\n", (int)st);
  if (st == WL_CONNECTED) {
    Serial.print("WiFi OK, IP ");
    Serial.println(WiFi.localIP());
    drawFace(FACE_IDLE, 0, "WiFi OK");
    beep(880, 80);
    beep(1320, 80);
    delay(1000);
  } else if (String(WIFI_SSID) == "YOUR_WIFI_NAME") {
    showError("Set WiFi name!");
  } else if (st == WL_NO_SSID_AVAIL) {
    showError("WiFi not found");
  } else if (st == WL_CONNECT_FAILED) {
    showError("Wrong WiFi password");
  } else {
    showError("No WiFi");                           // keeps trying in the background
  }
}

bool handWaved() {
  return USE_IR_SENSOR && digitalRead(IR_PIN) == LOW;
}

void loop() {
  bool trigger = handWaved();
  if (digitalRead(BUTTON_PIN) == LOW) {
    trigger = true;
  }
  if (!recording) {
    trigger = false;
  }
  if (!trigger) {
    updateIdleFace();
    delay(30);
    return;
  }

  if (WiFi.status() != WL_CONNECTED) {
    // Give the automatic reconnect time to work instead of restarting it.
    unsigned long waitStart = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - waitStart < 10000) {
      drawFace(FACE_THINK, 0, "WiFi...");
      delay(200);
    }
    if (WiFi.status() != WL_CONNECTED) {
      showError("No WiFi");
      return;
    }
  }

  // 1. Listen
  beep(1000, 120);
  size_t samples = recordQuestion();
  beep(700, 80);

  // 2. Think
  drawFace(FACE_THINK, 0, nullptr);
  String answer = askGemini(samples);
  if (answer.length() == 0) {
    showError("Gemini error");
    return;
  }
  Serial.print("Answer: ");
  Serial.println(answer);

  // 3. Talk
  drawFace(FACE_TALK, 4, nullptr);
  if (!speak(answer)) {
    showError("Speech error");
  }

  // wait until the hand is gone, so it does not start again by itself
  while (handWaved()) {
    updateIdleFace();
    delay(30);
  }
}

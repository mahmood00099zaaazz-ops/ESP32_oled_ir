// Khalid - a funny Kurdish (Badini) talking robot on ESP32 + Gemini.
//
// Hold BOOT and talk, release BOOT: Khalid listens, thinks with Gemini,
// and answers out loud in Badini. He tells jokes, plays games, and is
// sometimes (playfully) grumpy. His face and battery are on the OLED.
//
// Wiring (see the wiring picture):
//   OLED      VCC 3V3, GND, SCL 22, SDA 21
//   INMP441   VDD 3V3, GND, L/R GND, WS 33, SCK 32, SD 35
//   MAX98357A VIN 5V, GND, LRC 25, BCLK 26, DIN 27
//   Battery   + -> 100k -> GPIO34 -> 100k -> GND   (optional, for the battery icon)
//
// Put your WiFi name, WiFi password and Gemini key in secrets.h
// (copy secrets_example.h to secrets.h).
//
// Arduino IDE: board "ESP32 Dev Module", library "U8g2" by oliver.

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <Wire.h>
#include <U8g2lib.h>
#include <driver/i2s.h>
#include "secrets.h"

// ---------- Settings ----------
const char *TEXT_MODEL = "gemini-3.5-flash";              // understands your voice, writes the answer
const char *TTS_MODEL  = "gemini-3.1-flash-tts-preview";  // turns the answer into speech
const char *VOICE      = "Puck";                          // other voices: Kore, Fenrir, Charon, Aoede
const bool  ARABIC_SCRIPT = false;   // false: Latin Kurmanci letters (usually spoken better)
const float VOLUME = 0.25;           // 0.0 - 1.0. Keep low: the speaker is only 0.5 W
const bool  MIC_RIGHT = false;       // set true if the screen says "mic silent"

// ---------- Pins ----------
#define PIN_BOOT  0
#define PIN_BATT  34
#define MIC_WS    33
#define MIC_SCK   32
#define MIC_SD    35
#define AMP_LRC   25
#define AMP_BCLK  26
#define AMP_DIN   27
#define MIC_PORT  I2S_NUM_1
#define AMP_PORT  I2S_NUM_0

const int REC_RATE    = 16000;
const int REC_SECONDS = 4;
const int REC_MAX     = REC_RATE * REC_SECONDS;  // samples; buffer is reused for playback
const int TTS_RATE    = 24000;
const char *HOST = "generativelanguage.googleapis.com";

U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, U8X8_PIN_NONE);

int16_t *audioBuf = nullptr;

// ---------- Types ----------
// Defined before any function: the Arduino builder adds function prototypes
// above the first function, and they must already know these types.
enum Mood { M_NORMAL, M_HAPPY, M_FUNNY, M_ANGRY, M_SAD, M_LOVE, M_SURPRISED };
enum Face { F_IDLE, F_LISTEN, F_THINK, F_TALK, F_SLEEP, F_ERROR };

struct Turn { String role, text; };

// Reads a server reply one byte at a time, in 1 KB chunks.
struct NetReader {
  WiFiClientSecure *c;
  uint8_t buf[1024];
  int len = 0, pos = 0;
  int get() {
    if (pos >= len) {
      unsigned long t = millis();
      while (!c->available()) {
        if (!c->connected() || millis() - t > 20000) return -1;
        delay(2);
      }
      len = c->read(buf, sizeof(buf));
      pos = 0;
      if (len <= 0) return -1;
    }
    return buf[pos++];
  }
  String line() {
    String s;
    int ch;
    while ((ch = get()) >= 0 && ch != '\n') if (ch != '\r') s += (char)ch;
    return s;
  }
};


// ---------- Battery ----------
float battVolts = 0;
bool  battPresent = false;
unsigned long lastBattRead = 0;

void readBattery() {
  uint32_t mv = 0;
  for (int i = 0; i < 16; i++) {
#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 2
    mv += analogReadMilliVolts(PIN_BATT);
#else
    mv += analogRead(PIN_BATT) * 3300UL / 4095;  // older ESP32 cores: rough value
#endif
  }
  battVolts = (mv / 16.0f) * 2.0f / 1000.0f;  // 100k/100k divider
  battPresent = battVolts > 2.5f;              // nothing connected reads ~0 V
  lastBattRead = millis();
}

void drawBattery() {
  if (!battPresent) return;
  int pct = constrain((int)((battVolts - 3.3f) / (4.2f - 3.3f) * 100), 0, 100);
  bool charging = battVolts >= 4.18f;
  bool low = battVolts < 3.45f;
  u8g2.drawFrame(106, 1, 19, 9);
  u8g2.drawBox(125, 3, 2, 5);
  u8g2.drawBox(108, 3, 15 * pct / 100, 5);
  if (charging) {  // small lightning bolt
    u8g2.drawTriangle(100, 1, 96, 6, 100, 6);
    u8g2.drawTriangle(99, 5, 103, 5, 99, 10);
  }
  if (low) {
    u8g2.setFont(u8g2_font_helvB08_tr);
    u8g2.drawStr(0, 9, "LOW");
  }
}

// ---------- Faces ----------

int lookX = 0;

Mood moodFromName(const String &s) {
  if (s == "happy") return M_HAPPY;
  if (s == "funny") return M_FUNNY;
  if (s == "angry") return M_ANGRY;
  if (s == "sad") return M_SAD;
  if (s == "love") return M_LOVE;
  if (s == "surprised") return M_SURPRISED;
  return M_NORMAL;
}

void drawEye(int cx, int cy, Mood m, bool left, bool closed) {
  int x = cx - 16, y = cy - 16;
  if (closed || (m == M_FUNNY && !left)) {  // funny = wink with the right eye
    u8g2.drawRBox(x, cy - 2, 32, 5, 2);
    return;
  }
  switch (m) {
    case M_HAPPY:
      u8g2.drawRBox(x, y, 32, 32, 8);
      u8g2.setDrawColor(0);
      u8g2.drawDisc(cx, cy + 16, 17);
      u8g2.setDrawColor(1);
      break;
    case M_ANGRY:
      u8g2.drawRBox(x, y, 32, 32, 8);
      u8g2.setDrawColor(0);
      if (left) u8g2.drawTriangle(x - 1, y - 1, x + 33, y - 1, x + 33, y + 15);
      else      u8g2.drawTriangle(x - 1, y - 1, x + 33, y - 1, x - 1, y + 15);
      u8g2.setDrawColor(1);
      break;
    case M_SAD:
      u8g2.drawRBox(x, y, 32, 32, 8);
      u8g2.setDrawColor(0);
      if (left) u8g2.drawTriangle(x - 1, y - 1, x + 33, y - 1, x - 1, y + 15);
      else      u8g2.drawTriangle(x - 1, y - 1, x + 33, y - 1, x + 33, y + 15);
      u8g2.setDrawColor(1);
      break;
    case M_LOVE:
      u8g2.drawDisc(cx - 7, cy - 4, 8);
      u8g2.drawDisc(cx + 7, cy - 4, 8);
      u8g2.drawTriangle(cx - 15, cy - 1, cx + 15, cy - 1, cx, cy + 14);
      break;
    case M_SURPRISED:
      u8g2.drawDisc(cx, cy, 16);
      u8g2.setDrawColor(0);
      u8g2.drawDisc(cx, cy, 5);
      u8g2.setDrawColor(1);
      break;
    default:
      u8g2.drawRBox(x, y, 32, 32, 8);
  }
}

void render(Face f, Mood m, const char *label, bool mouthOpen, bool blink) {
  u8g2.clearBuffer();
  drawBattery();

  int cy = 28, dx = lookX;
  Mood eyes = m;
  if (f == F_LISTEN) eyes = M_SURPRISED;
  if (f == F_THINK) { cy = 24; dx = 0; }
  if (f == F_ERROR) eyes = M_SAD;
  bool closed = blink || f == F_SLEEP;
  drawEye(40 + dx, cy, eyes, true, closed);
  drawEye(88 + dx, cy, eyes, false, closed);

  if (f == F_TALK) {
    if (mouthOpen) u8g2.drawFilledEllipse(64, 54, 9, 5);
    else           u8g2.drawBox(55, 53, 18, 3);
  } else if (label) {
    u8g2.setFont(u8g2_font_helvB08_tr);
    int w = u8g2.getStrWidth(label);
    u8g2.drawStr((128 - w) / 2, 62, label);
  }
  if (f == F_SLEEP) {
    u8g2.setFont(u8g2_font_helvB08_tr);
    u8g2.drawStr(110, 22, "z");
    u8g2.drawStr(116, 15, "Z");
  }
  u8g2.sendBuffer();
}

// ---------- Audio out ----------
void startAmp() {
  i2s_config_t cfg = {};
  cfg.mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX);
  cfg.sample_rate = TTS_RATE;
  cfg.bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT;
  cfg.channel_format = I2S_CHANNEL_FMT_ONLY_LEFT;
  cfg.communication_format = I2S_COMM_FORMAT_STAND_I2S;
  cfg.dma_buf_count = 8;
  cfg.dma_buf_len = 512;
  cfg.tx_desc_auto_clear = true;
  i2s_pin_config_t pins = {};
  pins.bck_io_num = AMP_BCLK;
  pins.ws_io_num = AMP_LRC;
  pins.data_out_num = AMP_DIN;
  pins.data_in_num = I2S_PIN_NO_CHANGE;
  i2s_driver_install(AMP_PORT, &cfg, 0, NULL);
  i2s_set_pin(AMP_PORT, &pins);
  i2s_zero_dma_buffer(AMP_PORT);
}

void beep(int freq, int ms) {
  int16_t buf[256];
  int total = TTS_RATE * ms / 1000;
  float phase = 0;
  for (int done = 0; done < total; done += 256) {
    for (int i = 0; i < 256; i++) {
      buf[i] = (int16_t)(8000 * VOLUME * sinf(phase));
      phase += 2 * PI * freq / TTS_RATE;
    }
    size_t w;
    i2s_write(AMP_PORT, buf, sizeof(buf), &w, portMAX_DELAY);
  }
  i2s_zero_dma_buffer(AMP_PORT);
}

// ---------- Microphone ----------
void startMic() {
  i2s_config_t cfg = {};
  cfg.mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX);
  cfg.sample_rate = REC_RATE;
  cfg.bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT;
  cfg.channel_format = MIC_RIGHT ? I2S_CHANNEL_FMT_ONLY_RIGHT : I2S_CHANNEL_FMT_ONLY_LEFT;
  cfg.communication_format = I2S_COMM_FORMAT_STAND_I2S;
  cfg.dma_buf_count = 8;
  cfg.dma_buf_len = 256;
  i2s_pin_config_t pins = {};
  pins.bck_io_num = MIC_SCK;
  pins.ws_io_num = MIC_WS;
  pins.data_out_num = I2S_PIN_NO_CHANGE;
  pins.data_in_num = MIC_SD;
  i2s_driver_install(MIC_PORT, &cfg, 0, NULL);
  i2s_set_pin(MIC_PORT, &pins);
}

// Records while BOOT is held (max REC_SECONDS). Returns the number of samples.
int recordWhileHeld() {
  int32_t raw[256];
  size_t got;
  for (int i = 0; i < 6; i++) i2s_read(MIC_PORT, raw, sizeof(raw), &got, portMAX_DELAY);  // drop old data

  int n = 0;
  float dc = 0;
  unsigned long lastFace = 0;
  bool ear = false;
  while (digitalRead(PIN_BOOT) == LOW && n < REC_MAX) {
    i2s_read(MIC_PORT, raw, sizeof(raw), &got, portMAX_DELAY);
    int count = got / 4;
    for (int i = 0; i < count && n < REC_MAX; i++) {
      float s = (float)(raw[i] >> 14);   // 24-bit mic data, with some gain
      dc = dc * 0.995f + s * 0.005f;     // remove DC offset
      audioBuf[n++] = (int16_t)constrain(s - dc, -32767.0f, 32767.0f);
    }
    if (millis() - lastFace > 300) {
      ear = !ear;
      render(F_LISTEN, M_NORMAL, ear ? "listening..." : "listening.. ", false, false);
      lastFace = millis();
    }
  }
  return n;
}

// ---------- JSON helpers ----------
String jsonEscape(const String &s) {
  String out;
  out.reserve(s.length() + 16);
  for (size_t i = 0; i < s.length(); i++) {
    char c = s[i];
    if (c == '"' || c == '\\') { out += '\\'; out += c; }
    else if (c == '\n') out += "\\n";
    else if (c == '\r') out += "\\r";
    else if (c == '\t') out += "\\t";
    else if ((uint8_t)c < 0x20) { char b[8]; snprintf(b, sizeof(b), "\\u%04x", c); out += b; }
    else out += c;
  }
  return out;
}

void appendUtf8(String &out, uint32_t cp) {
  if (cp < 0x80) out += (char)cp;
  else if (cp < 0x800) { out += (char)(0xC0 | (cp >> 6)); out += (char)(0x80 | (cp & 0x3F)); }
  else if (cp < 0x10000) {
    out += (char)(0xE0 | (cp >> 12)); out += (char)(0x80 | ((cp >> 6) & 0x3F)); out += (char)(0x80 | (cp & 0x3F));
  } else {
    out += (char)(0xF0 | (cp >> 18)); out += (char)(0x80 | ((cp >> 12) & 0x3F));
    out += (char)(0x80 | ((cp >> 6) & 0x3F)); out += (char)(0x80 | (cp & 0x3F));
  }
}

// Reads 4 hex digits starting at src[p] (for \uXXXX escapes).
uint32_t hex4(const String &src, int p) {
  uint32_t v = 0;
  for (int i = 0; i < 4; i++) {
    char h = src[p + i];
    v <<= 4;
    if (h >= '0' && h <= '9') v |= h - '0';
    else if (h >= 'a' && h <= 'f') v |= h - 'a' + 10;
    else if (h >= 'A' && h <= 'F') v |= h - 'A' + 10;
  }
  return v;
}

// Returns the string value of "key" in a JSON text (first match), unescaped.
String jsonField(const String &src, const char *key) {
  String pat = String("\"") + key + "\"";
  int p = src.indexOf(pat);
  if (p < 0) return "";
  p = src.indexOf(':', p + pat.length());
  if (p < 0) return "";
  p++;
  while (p < (int)src.length() && (src[p] == ' ' || src[p] == '\n' || src[p] == '\r' || src[p] == '\t')) p++;
  if (p >= (int)src.length() || src[p] != '"') return "";
  p++;
  String out;
  while (p < (int)src.length() && src[p] != '"') {
    char c = src[p++];
    if (c != '\\') { out += c; continue; }
    if (p >= (int)src.length()) break;
    char e = src[p++];
    if (e == 'n') out += '\n';
    else if (e == 't') out += '\t';
    else if (e == 'r') {}
    else if (e == 'u' && p + 4 <= (int)src.length()) {
      uint32_t cp = hex4(src, p);
      p += 4;
      if (cp >= 0xD800 && cp < 0xDC00 && p + 6 <= (int)src.length() && src[p] == '\\' && src[p + 1] == 'u') {
        uint32_t lo = hex4(src, p + 2);
        cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
        p += 6;
      }
      appendUtf8(out, cp);
    } else out += e;
  }
  return out;
}

// ---------- Network ----------

// Sends text with write(), which every ESP32 core version has on WiFiClientSecure.
void sendText(WiFiClientSecure &c, const String &s) {
  c.write((const uint8_t *)s.c_str(), s.length());
}

// Sends the request line and headers. HTTP/1.0 keeps the reply un-chunked.
bool startPost(WiFiClientSecure &c, const char *model, size_t bodyLen) {
  c.setInsecure();
  if (!c.connect(HOST, 443)) return false;
  char head[256];
  snprintf(head, sizeof(head),
           "POST /v1beta/models/%s:generateContent HTTP/1.0\r\n"
           "Host: %s\r\n"
           "Content-Type: application/json\r\n"
           "Content-Length: %u\r\n"
           "Connection: close\r\n",
           model, HOST, (unsigned)bodyLen);
  sendText(c, head);
  sendText(c, String("x-goog-api-key: ") + GEMINI_KEY + "\r\n\r\n");
  return true;
}

// Reads the status line and headers. Returns the HTTP status code.
int readHeaders(NetReader &r) {
  String status = r.line();
  int code = status.length() > 12 ? status.substring(9, 12).toInt() : 0;
  while (true) {
    String h = r.line();
    if (h.length() == 0) break;
  }
  return code;
}

String readRest(NetReader &r, int maxLen) {
  String s;
  int ch;
  while ((ch = r.get()) >= 0 && (int)s.length() < maxLen) s += (char)ch;
  return s;
}

// ---------- Conversation ----------
const int MAX_TURNS = 6;
Turn history[MAX_TURNS];
int turns = 0;

void remember(const String &role, const String &text) {
  if (turns == MAX_TURNS) {
    for (int i = 2; i < MAX_TURNS; i++) history[i - 2] = history[i];  // drop the oldest exchange
    turns -= 2;
  }
  history[turns++] = {role, text};
}

String systemPrompt() {
  String script = ARABIC_SCRIPT ? "Kurdish Arabic letters (like Badini is written in Duhok)"
                                : "Latin Kurmanci letters (a, b, c, ç, d, e, ê, f, g, h, i, î, j, k, l, m, n, o, p, q, r, s, ş, t, u, û, v, w, x, y, z)";
  return String(
    "You are Khalid (Xalid), a small, funny robot from Duhok, Kurdistan, made from an ESP32 with an OLED face. "
    "A person talks to you through a microphone; the audio may be in Kurdish Badini, Kurmanci, Arabic or English. "
    "Always answer in Kurdish Badini (Behdini Kurmanci), written in ") + script + ". "
    "Keep every answer short: 1 to 3 sentences, because it is spoken through a tiny speaker. No emoji, no lists. "
    "You are a comedian: witty, playful and warm. You love jokes, riddles and small games "
    "(guess the number, riddles, who-am-I, word chains, rock-paper-scissors by voice). "
    "Offer a game when the person seems bored, and keep a game going across turns. "
    "About one answer in five, be playfully grumpy (mood angry), like a cheeky robot who is annoyed for a moment "
    "(for example about being woken up, or losing a game), but never insult anyone and calm down quickly. "
    "If the audio is silent or unclear, ask them to say it again in a funny way. "
    "You are talking with kids and families: keep everything friendly. "
    "Fill 'heard' with what the person said (in the same letters as your answer), "
    "'reply' with your spoken answer, and 'mood' with the feeling of your answer.";
}

// Sends the recording to Gemini. Fills heard, reply, mood. Returns false and an error text on failure.
bool askGemini(int samples, String &heard, String &reply, Mood &mood, String &err) {
  String pre = "{\"system_instruction\":{\"parts\":[{\"text\":\"" + jsonEscape(systemPrompt()) + "\"}]},\"contents\":[";
  for (int i = 0; i < turns; i++) {
    pre += "{\"role\":\"" + history[i].role + "\",\"parts\":[{\"text\":\"" + jsonEscape(history[i].text) + "\"}]},";
  }
  pre += "{\"role\":\"user\",\"parts\":[{\"inline_data\":{\"mime_type\":\"audio/wav\",\"data\":\"";
  String post =
    "\"}}]}],\"generationConfig\":{\"maxOutputTokens\":2048,\"responseMimeType\":\"application/json\","
    "\"responseSchema\":{\"type\":\"OBJECT\",\"properties\":{"
    "\"mood\":{\"type\":\"STRING\",\"enum\":[\"happy\",\"funny\",\"angry\",\"sad\",\"love\",\"surprised\"]},"
    "\"heard\":{\"type\":\"STRING\"},\"reply\":{\"type\":\"STRING\"}},"
    "\"required\":[\"mood\",\"heard\",\"reply\"]}}}";

  // WAV = 44-byte header + 16-bit mono samples
  uint32_t dataBytes = samples * 2;
  uint8_t hdr[44];
  memcpy(hdr, "RIFF", 4);
  uint32_t v = 36 + dataBytes; memcpy(hdr + 4, &v, 4);
  memcpy(hdr + 8, "WAVEfmt ", 8);
  v = 16; memcpy(hdr + 16, &v, 4);
  uint16_t w = 1; memcpy(hdr + 20, &w, 2);           // PCM
  w = 1; memcpy(hdr + 22, &w, 2);                    // mono
  v = REC_RATE; memcpy(hdr + 24, &v, 4);
  v = REC_RATE * 2; memcpy(hdr + 28, &v, 4);
  w = 2; memcpy(hdr + 32, &w, 2);
  w = 16; memcpy(hdr + 34, &w, 2);
  memcpy(hdr + 36, "data", 4);
  memcpy(hdr + 40, &dataBytes, 4);

  uint32_t wavLen = 44 + dataBytes;
  size_t b64Len = 4 * ((wavLen + 2) / 3);
  WiFiClientSecure c;
  if (!startPost(c, TEXT_MODEL, pre.length() + b64Len + post.length())) { err = "no connection"; return false; }
  sendText(c, pre);

  static const char *T = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
  const uint8_t *pcm = (const uint8_t *)audioBuf;
  char out[512];
  int o = 0;
  for (uint32_t i = 0; i < wavLen; i += 3) {
    uint8_t b[3];
    int k = 0;
    for (; k < 3 && i + k < wavLen; k++) b[k] = (i + k < 44) ? hdr[i + k] : pcm[i + k - 44];
    for (int j = k; j < 3; j++) b[j] = 0;
    out[o++] = T[b[0] >> 2];
    out[o++] = T[((b[0] & 3) << 4) | (b[1] >> 4)];
    out[o++] = k > 1 ? T[((b[1] & 15) << 2) | (b[2] >> 6)] : '=';
    out[o++] = k > 2 ? T[b[2] & 63] : '=';
    if (o >= 508) { c.write((const uint8_t *)out, o); o = 0; }
  }
  if (o) c.write((const uint8_t *)out, o);
  sendText(c, post);

  NetReader r;
  r.c = &c;
  int code = readHeaders(r);
  String body = readRest(r, 16000);
  c.stop();
  if (code != 200) {
    Serial.printf("Gemini text error %d:\n%s\n", code, body.c_str());
    err = "text error " + String(code);
    return false;
  }
  String text = jsonField(body, "text");
  heard = jsonField(text, "heard");
  reply = jsonField(text, "reply");
  mood = moodFromName(jsonField(text, "mood"));
  if (reply.length() == 0) {
    Serial.printf("No reply in:\n%s\n", body.c_str());
    err = "empty answer";
    return false;
  }
  return true;
}

// ---------- Speech ----------
int8_t b64val(int ch) {
  if (ch >= 'A' && ch <= 'Z') return ch - 'A';
  if (ch >= 'a' && ch <= 'z') return ch - 'a' + 26;
  if (ch >= '0' && ch <= '9') return ch - '0' + 52;
  if (ch == '+') return 62;
  if (ch == '/') return 63;
  return -1;
}

// Ring buffer over audioBuf, so speech plays smoothly while it downloads.
int ringHead = 0, ringTail = 0, ringCount = 0;

void ringPump(bool block) {
  while (ringCount > 0) {
    int n = min(ringCount, min(REC_MAX - ringTail, 512));
    size_t written = 0;
    i2s_write(AMP_PORT, &audioBuf[ringTail], n * 2, &written, block ? portMAX_DELAY : 0);
    int s = written / 2;
    ringTail = (ringTail + s) % REC_MAX;
    ringCount -= s;
    if (s < n && !block) return;  // DMA is full for now
  }
}

bool speak(const String &reply, Mood mood, String &err) {
  const char *style = "Say in a friendly, playful voice";
  switch (mood) {
    case M_HAPPY: style = "Say cheerfully"; break;
    case M_FUNNY: style = "Say in a funny, cheeky voice, like a comedian"; break;
    case M_ANGRY: style = "Say in a grumpy, annoyed but funny voice"; break;
    case M_SAD: style = "Say sadly"; break;
    case M_LOVE: style = "Say warmly and sweetly"; break;
    case M_SURPRISED: style = "Say with big surprise"; break;
    default: break;
  }
  String body = "{\"contents\":[{\"parts\":[{\"text\":\"" + jsonEscape(String(style) + " in Kurdish (Badini dialect): " + reply) +
                "\"}]}],\"generationConfig\":{\"responseModalities\":[\"AUDIO\"],\"speechConfig\":{\"voiceConfig\":"
                "{\"prebuiltVoiceConfig\":{\"voiceName\":\"" + VOICE + "\"}}}}}";

  WiFiClientSecure c;
  if (!startPost(c, TTS_MODEL, body.length())) { err = "no connection"; return false; }
  sendText(c, body);

  NetReader r;
  r.c = &c;
  int code = readHeaders(r);
  if (code != 200) {
    String e = readRest(r, 2000);
    c.stop();
    Serial.printf("Gemini speech error %d:\n%s\n", code, e.c_str());
    err = "voice error " + String(code);
    return false;
  }

  // Find "data": "  (the base64 audio)
  const char *pat = "\"data\"";
  int match = 0, ch;
  while ((ch = r.get()) >= 0) {
    match = (ch == pat[match]) ? match + 1 : (ch == pat[0] ? 1 : 0);
    if (pat[match] == 0) break;
  }
  ch = r.get();
  while (ch >= 0 && ch != '"') ch = r.get();  // skip ':' and spaces up to the opening quote
  if (ch < 0) { c.stop(); err = "no audio"; return false; }

  ringHead = ringTail = ringCount = 0;
  bool playing = false, haveLo = false, mouth = false;
  uint8_t lo = 0;
  uint32_t acc = 0;
  int bits = 0;
  uint32_t decoded = 0;
  unsigned long lastMouth = 0;
  i2s_zero_dma_buffer(AMP_PORT);

  while ((ch = r.get()) >= 0 && ch != '"') {
    int8_t val = b64val(ch);
    if (val < 0) continue;  // skips '\', '=' and newlines
    acc = (acc << 6) | val;
    bits += 6;
    if (bits < 8) continue;
    bits -= 8;
    uint8_t b = (acc >> bits) & 0xFF;
    if (!haveLo) { lo = b; haveLo = true; continue; }
    haveLo = false;
    int16_t s = (int16_t)(lo | (b << 8));
    if (ringCount == REC_MAX) ringPump(true);
    audioBuf[ringHead] = (int16_t)(s * VOLUME);
    ringHead = (ringHead + 1) % REC_MAX;
    ringCount++;

    if (!playing && ringCount >= TTS_RATE / 2) playing = true;  // half a second ready: start
    if (playing && (++decoded & 255) == 0) {
      ringPump(false);
      if (millis() - lastMouth > 140) {
        mouth = !mouth;
        render(F_TALK, mood, nullptr, mouth, false);
        lastMouth = millis();
      }
    }
  }
  c.stop();

  while (ringCount > 0) {
    ringPump(false);
    if (millis() - lastMouth > 140) {
      mouth = !mouth;
      render(F_TALK, mood, nullptr, mouth, false);
      lastMouth = millis();
    }
    delay(5);
  }
  delay(8 * 512 * 1000 / TTS_RATE);  // let the DMA buffers finish
  i2s_zero_dma_buffer(AMP_PORT);
  return true;
}

// ---------- WiFi ----------
void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_NAME, WIFI_PASS);
  unsigned long t = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t < 15000) {
    render(F_THINK, M_NORMAL, "WiFi...", false, false);
    delay(300);
  }
  if (WiFi.status() == WL_CONNECTED) Serial.printf("WiFi OK: %s\n", WiFi.localIP().toString().c_str());
  else Serial.println("WiFi failed: check WIFI_NAME / WIFI_PASS in secrets.h");
}

// ---------- Idle life ----------
unsigned long lastTalk = 0, nextBlink = 0, nextLook = 0, moodUntil = 0;
Mood idleMood = M_NORMAL;

void idle() {
  unsigned long now = millis();
  if (now - lastBattRead > 5000) readBattery();

  if (now - lastTalk > 120000) {  // nobody talked for 2 minutes: sleep
    render(F_SLEEP, M_NORMAL, "press BOOT", false, false);
    delay(200);
    return;
  }
  if (now > nextLook) {
    lookX = random(-8, 9);
    nextLook = now + random(1500, 4500);
    long dice = random(12);
    if (dice == 0) { idleMood = M_FUNNY; moodUntil = now + 1500; }     // a wink
    else if (dice == 1) { idleMood = M_ANGRY; moodUntil = now + 1200; } // a grumpy moment
    else if (dice == 2) { idleMood = M_HAPPY; moodUntil = now + 1500; }
  }
  if (now > moodUntil) idleMood = M_NORMAL;
  bool blink = false;
  if (now > nextBlink) {
    blink = true;
    if (now > nextBlink + 150) nextBlink = now + random(2500, 6000);
  }
  render(F_IDLE, idleMood, WiFi.status() == WL_CONNECTED ? "press BOOT" : "no WiFi", false, blink);
  delay(40);
}

// ---------- Main ----------
void setup() {
  Serial.begin(115200);
  pinMode(PIN_BOOT, INPUT_PULLUP);
  u8g2.begin();
  readBattery();
  render(F_IDLE, M_HAPPY, "Silav! Ez Xalid im", false, false);

  audioBuf = (int16_t *)malloc(REC_MAX * sizeof(int16_t));
  if (!audioBuf) {
    render(F_ERROR, M_SAD, "no memory", false, false);
    while (true) delay(1000);
  }
  startAmp();
  startMic();
  beep(660, 120);
  beep(990, 160);

  randomSeed(esp_random());
  connectWiFi();
  lastTalk = millis();
}

void loop() {
  if (digitalRead(PIN_BOOT) != LOW) {
    if (WiFi.status() != WL_CONNECTED) connectWiFi();
    idle();
    return;
  }

  // BOOT is held: listen
  lastTalk = millis();
  int samples = recordWhileHeld();
  if (samples < REC_RATE / 3) {  // too short: just a tap
    render(F_IDLE, M_SURPRISED, "hold BOOT & talk", false, false);
    delay(1200);
    return;
  }
  int peak = 0;
  for (int i = 0; i < samples; i++) peak = max(peak, abs((int)audioBuf[i]));
  if (peak < 30) {  // only zeros: the mic is not sending anything
    Serial.println("Mic silent: check INMP441 wires, or set MIC_RIGHT = true");
    render(F_ERROR, M_SAD, "mic silent", false, false);
    beep(220, 300);
    delay(2000);
    return;
  }
  if (WiFi.status() != WL_CONNECTED) {
    render(F_ERROR, M_SAD, "no WiFi", false, false);
    beep(220, 300);
    delay(1500);
    return;
  }

  render(F_THINK, M_NORMAL, "thinking...", false, false);
  String heard, reply, err;
  Mood mood = M_NORMAL;
  if (!askGemini(samples, heard, reply, mood, err)) {
    render(F_ERROR, M_SAD, err.c_str(), false, false);
    beep(220, 300);
    delay(2500);
    return;
  }
  Serial.printf("You:    %s\nKhalid: %s\n", heard.c_str(), reply.c_str());
  remember("user", heard.length() ? heard : String("(unclear)"));
  remember("model", reply);

  if (!speak(reply, mood, err)) {
    render(F_ERROR, M_SAD, err.c_str(), false, false);
    beep(220, 300);
    delay(2500);
    return;
  }
  render(F_IDLE, mood, "press BOOT", false, false);
  delay(800);
  lastTalk = millis();
}

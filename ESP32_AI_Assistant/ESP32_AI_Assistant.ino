/*
  ESP32 AI Assistant  —  Gemini  —  Kurdî (Badînî) / English / العربية
  =======================================================================
  Parts:
    - ESP32 or ESP32-S3 board (Arduino core 3.x)
    - OLED SSD1306 128x64 (I2C)                         -> screen
    - INMP441 I2S microphone                            -> microphone
    - LM386 amplifier module + 8 ohm speaker            -> speaker
    - 18650 / Li-ion battery + TP4056 + MT3608 (5V) + slide switch -> battery
    - BOOT button (GPIO0, already on the board)         -> talk button
    - WiFi + Bluetooth (BLE) built in
  How to use:
    - Hold BOOT and speak, release -> Gemini answers with voice + text.
    - Double-click BOOT -> change screen language (KU / EN / AR).
    - Phone app "Serial Bluetooth Terminal" (BLE) -> device "ESP32-AI":
        any text           = ask a question
        wifi:NAME,PASSWORD = save WiFi
        key:GEMINI_KEY     = save Gemini API key
        lang:ku | en | ar  = screen language
        vol:0..100         = volume
        bat                = battery voltage
        sleep              = turn off (deep sleep), BOOT wakes it
    - The same commands work from the Serial Monitor (115200).
  Libraries (Library Manager): U8g2 (oliver), ArduinoJson (Benoit Blanchon, v7)
  Board: Tools -> Board -> esp32 -> "ESP32 Dev Module" or "ESP32S3 Dev Module"
         For ESP32-S3 with PSRAM: Tools -> PSRAM -> "OPI PSRAM" (or "QSPI PSRAM")
*/

#include <Arduino.h>
#include <esp_arduino_version.h>
#if ESP_ARDUINO_VERSION_MAJOR < 3
#error "Install esp32 by Espressif version 3.x (Tools -> Board -> Boards Manager)"
#endif

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <Preferences.h>
#include <Wire.h>
#include <U8g2lib.h>
#include <ArduinoJson.h>
#include <ESP_I2S.h>
#include <esp_heap_caps.h>
#include <esp_sleep.h>

#define ENABLE_BLE 1          // 0 = no Bluetooth (saves ~60 KB RAM)
#if ENABLE_BLE
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#endif

// ======================= SETTINGS (change these) =======================
const char* DEFAULT_WIFI_SSID = "YOUR_WIFI_NAME";
const char* DEFAULT_WIFI_PASS = "YOUR_WIFI_PASSWORD";
const char* DEFAULT_GEMINI_KEY = "YOUR_GEMINI_API_KEY";   // https://aistudio.google.com/apikey

const char* CHAT_MODEL = "gemini-2.5-flash";              // listens + answers
const char* TTS_MODEL  = "gemini-2.5-flash-preview-tts";  // speaks
const char* TTS_VOICE  = "Kore";

const int   MAX_RECORD_SEC   = 6;     // with PSRAM; without PSRAM it uses what fits
const int   MAX_PLAY_SEC     = 30;
const int   IDLE_SLEEP_MIN   = 15;    // turn off after N minutes idle (0 = never)
const bool  USE_BATTERY      = false; // true after you connect the battery + 100k/100k divider
const float BAT_DIVIDER      = 2.0;   // 100k + 100k divider -> x2
const float BAT_FULL_V       = 4.20;
const float BAT_EMPTY_V      = 3.30;
const int   MIC_GAIN_SHIFT   = 13;    // smaller = louder mic (11..16)

// ======================= PINS =======================
#if CONFIG_IDF_TARGET_ESP32S3
const int PIN_SDA = 8,  PIN_SCL = 9;
const int PIN_MIC_SCK = 4, PIN_MIC_WS = 5, PIN_MIC_SD = 6;
const int PIN_SPK = 7;
const int PIN_BAT = 1;
#else  // classic ESP32
const int PIN_SDA = 21, PIN_SCL = 22;
const int PIN_MIC_SCK = 14, PIN_MIC_WS = 15, PIN_MIC_SD = 32;
const int PIN_SPK = 25;
const int PIN_BAT = 34;
#endif
const int PIN_BTN = 0;   // BOOT button

// ======================= AUDIO =======================
const int MIC_RATE  = 16000;   // microphone sample rate
const int TTS_RATE  = 24000;   // Gemini TTS output rate
const int PLAY_RATE = 12000;   // we keep every pair averaged -> 12 kHz, 8-bit

// ======================= GLOBALS =======================
U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, U8X8_PIN_NONE, PIN_SCL, PIN_SDA);
I2SClass   i2s;
Preferences prefs;

String wifiSsid, wifiPass, apiKey;
uint8_t uiLang = 0;            // 0 = Kurdish, 1 = English, 2 = Arabic
int volumePct = 80;
unsigned long lastActivity = 0;
unsigned long lastBlink = 0;
unsigned long lastBatCheck = 0;

struct Turn { String user, bot; };
const int HIST = 3;
Turn history[HIST];
int histCount = 0;

struct Answer { String lang, heard, say, show; };

#if ENABLE_BLE
BLECharacteristic* bleTx = nullptr;
volatile bool bleConnected = false;
volatile bool bleHasMsg = false;
String bleInbox;
#endif

// ======================= UI TEXT (3 languages, Latin letters for the OLED) ===
enum Msg { M_HOLD, M_LISTEN, M_THINK, M_SPEAK, M_NOWIFI, M_NOKEY, M_ERROR,
            M_BYE, M_LOWBAT, M_LANG, M_WIFI, M_SHORT, M_COUNT };
const char* UI[3][M_COUNT] = {
  { "Bişkoka BOOT bigre û biaxive", "Guhdarî dikim...", "Hizir dikim...", "Diaxivim...",
    "WiFi nîne", "Kilîta Gemini nîne", "Xeletî", "Xatirê te", "Pîl kêm e",
    "Ziman: Kurdî", "Girêdana WiFi...", "Gelek kurt bû" },
  { "Hold BOOT and talk", "Listening...", "Thinking...", "Speaking...",
    "No WiFi", "No Gemini key", "Error", "Goodbye", "Battery low",
    "Language: English", "Connecting WiFi...", "Too short" },
  { "Idghat BOOT w takallam", "Asma3ak...", "Ufakkir...", "Atakallam...",
    "La yujad WiFi", "La yujad muftah Gemini", "Khata2", "Ma3a assalama", "Al-batariya da3ifa",
    "Al-lugha: Arabi", "Al-ittisal bi WiFi...", "Qasir jiddan" }
};
const char* LANG_TAG[3] = { "KU", "EN", "AR" };
const char* LANG_NAME[3] = { "Kurdish Badini (Behdini, written in Arabic script)", "English", "Arabic" };

// ======================= LED (ESP32-S3 RGB) =======================
void led(uint8_t r, uint8_t g, uint8_t b) {
#ifdef RGB_BUILTIN
  rgbLedWrite(RGB_BUILTIN, r, g, b);
#else
  (void)r; (void)g; (void)b;
#endif
}

// ======================= BATTERY =======================
float batteryVolts() {
  uint32_t mv = 0;
  for (int i = 0; i < 8; i++) mv += analogReadMilliVolts(PIN_BAT);
  return (mv / 8.0f) * BAT_DIVIDER / 1000.0f;
}
bool batteryPresent(float v) { return USE_BATTERY && v > 2.5f; }   // nothing connected -> ~0 V
int batteryPercent(float v) {
  int p = (int)((v - BAT_EMPTY_V) * 100.0f / (BAT_FULL_V - BAT_EMPTY_V));
  return constrain(p, 0, 100);
}

// ======================= DISPLAY =======================
void drawStatusBar() {
  u8g2.setFont(u8g2_font_5x7_tr);
  // WiFi bars
  if (WiFi.status() == WL_CONNECTED) {
    long rssi = WiFi.RSSI();
    int bars = rssi > -60 ? 3 : rssi > -72 ? 2 : 1;
    for (int i = 0; i < 3; i++) {
      int h = 2 + i * 2;
      if (i < bars) u8g2.drawBox(1 + i * 3, 7 - h, 2, h);
      else          u8g2.drawFrame(1 + i * 3, 7 - h, 2, h);
    }
  } else {
    u8g2.drawStr(0, 7, "x");
  }
#if ENABLE_BLE
  if (bleConnected) u8g2.drawStr(14, 7, "BT");
#endif
  u8g2.drawStr(30, 7, LANG_TAG[uiLang]);

  float v = batteryVolts();
  if (batteryPresent(v)) {
    int p = batteryPercent(v);
    char buf[6]; snprintf(buf, sizeof(buf), "%d%%", p);
    u8g2.drawStr(84, 7, buf);
    u8g2.drawFrame(110, 0, 16, 8);
    u8g2.drawBox(126, 2, 2, 4);
    u8g2.drawBox(112, 2, (12 * p) / 100, 4);
  } else {
    u8g2.drawStr(108, 7, "USB");
  }
  u8g2.drawHLine(0, 9, 128);
}

// word-wrap UTF-8 text into lines that fit the screen width
int wrapText(const String& text, String* lines, int maxLines, int width) {
  int n = 0;
  String line = "";
  int i = 0, len = text.length();
  while (i <= len && n < maxLines) {
    int sp = text.indexOf(' ', i);
    if (sp < 0) sp = len;
    String word = text.substring(i, sp);
    i = sp + 1;
    String test = line.length() ? line + " " + word : word;
    if (u8g2.getUTF8Width(test.c_str()) <= width) {
      line = test;
    } else {
      if (line.length()) { lines[n++] = line; line = ""; if (n >= maxLines) break; }
      // very long word: cut by characters
      while (u8g2.getUTF8Width(word.c_str()) > width && n < maxLines) {
        int cut = word.length();
        while (cut > 1 && u8g2.getUTF8Width(word.substring(0, cut).c_str()) > width) {
          cut--;
          while (cut > 1 && ((uint8_t)word[cut] & 0xC0) == 0x80) cut--;   // UTF-8 boundary
        }
        lines[n++] = word.substring(0, cut);
        word = word.substring(cut);
      }
      line = word;
    }
    if (sp >= len) break;
  }
  if (line.length() && n < maxLines) lines[n++] = line;
  return n;
}

void showText(const String& text) {
  u8g2.clearBuffer();
  drawStatusBar();
  u8g2.setFont(u8g2_font_6x12_te);
  String lines[4];
  int n = wrapText(text, lines, 4, 126);
  for (int i = 0; i < n; i++) u8g2.drawUTF8(1, 22 + i * 12, lines[i].c_str());
  u8g2.sendBuffer();
}

void showMsg(Msg m) { showText(UI[uiLang][m]); }

// show a long text page by page (4 lines per page)
void showPages(const String& text, int pageMs) {
  u8g2.setFont(u8g2_font_6x12_te);
  String lines[24];
  int n = wrapText(text, lines, 24, 126);
  for (int p = 0; p < n; p += 4) {
    u8g2.clearBuffer();
    drawStatusBar();
    u8g2.setFont(u8g2_font_6x12_te);
    for (int i = 0; i < 4 && p + i < n; i++) u8g2.drawUTF8(1, 22 + i * 12, lines[p + i].c_str());
    u8g2.sendBuffer();
    if (p + 4 < n) delay(pageMs);
  }
}

void drawEyes(bool open) {
  u8g2.clearBuffer();
  drawStatusBar();
  if (open) {
    u8g2.drawRBox(18, 18, 34, 38, 8);
    u8g2.drawRBox(76, 18, 34, 38, 8);
  } else {
    u8g2.drawRBox(18, 35, 34, 5, 2);
    u8g2.drawRBox(76, 35, 34, 5, 2);
  }
  u8g2.sendBuffer();
}

void drawLevel(int level) {   // microphone level bar while recording
  u8g2.clearBuffer();
  drawStatusBar();
  u8g2.setFont(u8g2_font_6x12_te);
  u8g2.drawUTF8(1, 24, UI[uiLang][M_LISTEN]);
  u8g2.drawFrame(4, 40, 120, 12);
  u8g2.drawBox(6, 42, constrain(level, 0, 116), 8);
  u8g2.sendBuffer();
}

// ======================= DEEP SLEEP (software power switch) ==============
void goSleep() {
  showMsg(M_BYE);
  led(0, 0, 0);
  delay(1500);
  u8g2.setPowerSave(1);
  WiFi.disconnect(true);
  esp_sleep_enable_ext0_wakeup((gpio_num_t)PIN_BTN, 0);   // BOOT wakes it
  esp_deep_sleep_start();
}

// ======================= BLUETOOTH (BLE UART) =======================
#if ENABLE_BLE
#define NUS_SERVICE "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
#define NUS_RX      "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
#define NUS_TX      "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

class ServerCB : public BLEServerCallbacks {
  void onConnect(BLEServer*) override { bleConnected = true; }
  void onDisconnect(BLEServer*) override { bleConnected = false; BLEDevice::startAdvertising(); }
};
class RxCB : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic* c) override {
    String v = String(c->getValue().c_str());
    v.trim();
    if (v.length() && !bleHasMsg) { bleInbox = v; bleHasMsg = true; }
  }
};

void bleBegin() {
  BLEDevice::init("ESP32-AI");
  BLEDevice::setMTU(185);
  BLEServer* server = BLEDevice::createServer();
  server->setCallbacks(new ServerCB());
  BLEService* svc = server->createService(NUS_SERVICE);
  bleTx = svc->createCharacteristic(NUS_TX, BLECharacteristic::PROPERTY_NOTIFY);
  bleTx->addDescriptor(new BLE2902());
  BLECharacteristic* rx = svc->createCharacteristic(
      NUS_RX, BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_WRITE_NR);
  rx->setCallbacks(new RxCB());
  svc->start();
  BLEAdvertising* adv = BLEDevice::getAdvertising();
  adv->addServiceUUID(NUS_SERVICE);
  adv->setScanResponse(true);
  BLEDevice::startAdvertising();
}
#endif

// send text to Serial and (if connected) to the phone
void say(const String& s) {
  Serial.println(s);
#if ENABLE_BLE
  if (!bleConnected || !bleTx) return;
  String msg = s + "\n";
  int i = 0, len = msg.length();
  while (i < len) {
    int end = min(i + 160, len);
    while (end < len && ((uint8_t)msg[end] & 0xC0) == 0x80) end--;   // keep UTF-8 letters whole
    String part = msg.substring(i, end);
    bleTx->setValue((uint8_t*)part.c_str(), part.length());
    bleTx->notify();
    delay(15);
    i = end;
  }
#endif
}

// ======================= WIFI =======================
void wifiConnect(bool wait) {
  if (wifiSsid.length() == 0) return;
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(wifiSsid.c_str(), wifiPass.c_str());
  if (!wait) return;
  showMsg(M_WIFI);
  unsigned long t = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t < 15000) delay(250);
  if (WiFi.status() == WL_CONNECTED) say("WiFi OK: " + WiFi.localIP().toString());
  else say("WiFi failed");
}

// ======================= JSON helpers =======================
String jsonEscape(const String& s) {
  String o;
  o.reserve(s.length() + 16);
  for (size_t i = 0; i < s.length(); i++) {
    char c = s[i];
    switch (c) {
      case '"':  o += "\\\""; break;
      case '\\': o += "\\\\"; break;
      case '\n': o += "\\n";  break;
      case '\r': break;
      case '\t': o += "\\t";  break;
      default:
        if ((uint8_t)c < 0x20) { char b[8]; snprintf(b, sizeof(b), "\\u%04x", c); o += b; }
        else o += c;
    }
  }
  return o;
}

String systemPrompt() {
  String p =
    "You are a small, friendly voice assistant robot living on an ESP32 with a tiny screen. "
    "The user speaks Kurdish Badini (Behdini dialect of Northern Kurdish, Duhok region), Arabic, or English. "
    "Detect the language and always answer in that same language. "
    "Kurdish answers must be Badini dialect written in Kurdish Arabic script (like: ئەز باشم، سوپاس). "
    "Keep answers short and clear: at most 2-3 sentences. ";
  p += "If you cannot tell the language, use ";
  p += LANG_NAME[uiLang];
  p += ". Reply ONLY with JSON: {\"lang\":\"ku\" or \"ar\" or \"en\", "
       "\"heard\":\"what the user said, in their script\", "
       "\"say\":\"your answer in the user's language and normal script\", "
       "\"show\":\"the same answer written with Latin letters only, max 150 characters: "
       "Kurdish in the Kurmanji Latin alphabet (with ç ê î ş û), Arabic in Arabizi, English as normal\"}";
  return p;
}

String historyJson() {
  String h;
  for (int i = 0; i < histCount; i++) {
    h += "{\"role\":\"user\",\"parts\":[{\"text\":\"" + jsonEscape(history[i].user) + "\"}]},";
    h += "{\"role\":\"model\",\"parts\":[{\"text\":\"" + jsonEscape(history[i].bot) + "\"}]},";
  }
  return h;
}

void remember(const String& u, const String& b) {
  if (histCount == HIST) {
    for (int i = 1; i < HIST; i++) history[i - 1] = history[i];
    histCount--;
  }
  history[histCount++] = { u, b };
}

// ======================= request body that base64-encodes the audio on the fly =====
static const char B64[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

class AudioJsonBody : public Stream {
 public:
  String pre, post;
  uint8_t hdr[44];
  const uint8_t* pcm = nullptr;
  size_t pcmLen = 0;
  size_t pos = 0;

  bool audio = true;
  size_t binLen() const { return audio ? sizeof(hdr) + pcmLen : 0; }
  size_t b64Len() const { return ((binLen() + 2) / 3) * 4; }
  size_t total() const { return pre.length() + b64Len() + post.length(); }

  uint8_t binAt(size_t i) const { return i < sizeof(hdr) ? hdr[i] : pcm[i - sizeof(hdr)]; }
  char charAt(size_t p) const {
    if (p < pre.length()) return pre[p];
    p -= pre.length();
    if (p < b64Len()) {
      size_t g = p / 4, k = p % 4, i = g * 3, n = binLen();
      if (k == 2 && i + 1 >= n) return '=';
      if (k == 3 && i + 2 >= n) return '=';
      uint32_t v = (uint32_t)binAt(i) << 16;
      if (i + 1 < n) v |= (uint32_t)binAt(i + 1) << 8;
      if (i + 2 < n) v |= binAt(i + 2);
      return B64[(v >> (18 - 6 * k)) & 63];
    }
    p -= b64Len();
    return post[p];
  }
  int available() { return pos < total() ? (int)(total() - pos) : 0; }
  int read() { return pos < total() ? (uint8_t)charAt(pos++) : -1; }
  int peek() { return pos < total() ? (uint8_t)charAt(pos) : -1; }
  size_t readBytes(char* buf, size_t len) {
    size_t n = 0, t = total();
    while (n < len && pos < t) buf[n++] = charAt(pos++);
    return n;
  }
  size_t write(uint8_t) { return 0; }
  void flush() {}

  void makeWavHeader(uint32_t dataBytes, uint32_t rate) {
    uint32_t byteRate = rate * 2;
    memcpy(hdr, "RIFF", 4);  put32(4, 36 + dataBytes);
    memcpy(hdr + 8, "WAVEfmt ", 8);
    put32(16, 16); put16(20, 1); put16(22, 1);
    put32(24, rate); put32(28, byteRate); put16(32, 2); put16(34, 16);
    memcpy(hdr + 36, "data", 4); put32(40, dataBytes);
  }
 private:
  void put32(int o, uint32_t v) { for (int i = 0; i < 4; i++) hdr[o + i] = (v >> (8 * i)) & 0xFF; }
  void put16(int o, uint16_t v) { hdr[o] = v & 0xFF; hdr[o + 1] = v >> 8; }
};

// ======================= GEMINI: question -> answer =======================
// ---- small HTTPS client (no HTTPClient library needed) ----
const char* GEMINI_HOST = "generativelanguage.googleapis.com";

long hexToLong(const String& t) {   // "1a2f" -> 6703
  long v = 0;
  for (unsigned int i = 0; i < t.length(); i++) {
    char ch = t[i];
    int d;
    if (ch >= '0' && ch <= '9') d = ch - '0';
    else if (ch >= 'a' && ch <= 'f') d = ch - 'a' + 10;
    else if (ch >= 'A' && ch <= 'F') d = ch - 'A' + 10;
    else break;
    v = v * 16 + d;
  }
  return v;
}

struct NetReader {
  WiFiClientSecure* s;
  uint8_t buf[512];
  int len = 0, idx = 0;
  bool chunked = false;
  long chunkLeft = 0;

  int rawNext(uint32_t timeoutMs = 15000) {
    if (idx < len) return buf[idx++];
    unsigned long t = millis();
    while (true) {
      int a = s->available();
      if (a > 0) {
        len = s->read(buf, a < (int)sizeof(buf) ? a : (int)sizeof(buf));
        idx = 0;
        if (len > 0) return buf[idx++];
      } else {
        if (!s->connected()) return -1;
        if (millis() - t > timeoutMs) return -1;
        delay(2);
      }
    }
  }
  String readLine() {
    String l; int c;
    while ((c = rawNext()) >= 0 && c != '\n') if (c != '\r') l += (char)c;
    return l;
  }
  // next byte of the body (handles "Transfer-Encoding: chunked")
  int next() {
    if (!chunked) return rawNext();
    if (chunkLeft == 0) {
      String l = readLine();
      if (l.length() == 0) l = readLine();          // CRLF after previous chunk
      chunkLeft = hexToLong(l);
      if (chunkLeft <= 0) return -1;
    }
    int c = rawNext();
    if (c >= 0) chunkLeft--;
    return c;
  }
  // reads status line + headers, returns HTTP status code
  int readHeaders() {
    String status = readLine();
    int sp = status.indexOf(' ');
    int code = sp > 0 ? status.substring(sp + 1).toInt() : -1;
    while (true) {
      String h = readLine();
      if (h.length() == 0) break;
      h.toLowerCase();
      if (h.startsWith("transfer-encoding:") && h.indexOf("chunked") > 0) chunked = true;
    }
    return code;
  }
  String readAll(size_t maxLen = 20000) {
    String o; int c;
    while (o.length() < maxLen && (c = next()) >= 0) o += (char)c;
    return o;
  }
};

bool httpsPostStart(WiFiClientSecure& c, const char* model, size_t contentLength) {
  c.setInsecure();
  if (!c.connect(GEMINI_HOST, 443)) { say("Cannot connect to Gemini"); return false; }
  String h = String("POST /v1beta/models/") + model + ":generateContent HTTP/1.1\r\n" +
             "Host: " + GEMINI_HOST + "\r\n" +
             "Content-Type: application/json\r\n" +
             "x-goog-api-key: " + apiKey + "\r\n" +
             "Content-Length: " + String((unsigned long)contentLength) + "\r\n" +
             "Connection: close\r\n\r\n";
  c.write((const uint8_t*)h.c_str(), h.length());
  return true;
}

bool sendStream(WiFiClientSecure& c, Stream& body) {
  char buf[1024];
  while (body.available() > 0) {
    size_t n = body.readBytes(buf, sizeof(buf));
    size_t w = 0;
    unsigned long t = millis();
    while (w < n) {
      size_t k = c.write((const uint8_t*)buf + w, n - w);
      if (k == 0) { if (!c.connected() || millis() - t > 15000) return false; delay(5); }
      w += k;
    }
  }
  return true;
}

bool parseAnswer(const String& payload, Answer& a) {
  JsonDocument doc;
  if (deserializeJson(doc, payload)) return false;
  const char* t = doc["candidates"][0]["content"]["parts"][0]["text"];
  if (!t) return false;
  JsonDocument inner;
  if (deserializeJson(inner, t) == DeserializationError::Ok && inner["say"].is<const char*>()) {
    a.lang  = inner["lang"]  | "en";
    a.heard = inner["heard"] | "";
    a.say   = inner["say"]   | "";
    a.show  = inner["show"]  | a.say.c_str();
  } else {
    a.lang = "en"; a.heard = ""; a.say = t; a.show = t;
  }
  return a.say.length() > 0;
}

// audio == nullptr -> text question
bool askGemini(const int16_t* audio, size_t samples, const String& text, Answer& out) {
  AudioJsonBody body;
  String start = "{\"system_instruction\":{\"parts\":[{\"text\":\"" + jsonEscape(systemPrompt()) +
                 "\"}]},\"contents\":[" + historyJson() + "{\"role\":\"user\",\"parts\":[";
  String end = ",\"generationConfig\":{\"responseMimeType\":\"application/json\","
               "\"maxOutputTokens\":800,\"thinkingConfig\":{\"thinkingBudget\":0}}}";
  if (audio) {
    body.pre  = start + "{\"inline_data\":{\"mime_type\":\"audio/wav\",\"data\":\"";
    body.post = "\"}}]}]" + end;
    body.pcm = (const uint8_t*)audio;
    body.pcmLen = samples * 2;
    body.makeWavHeader(samples * 2, MIC_RATE);
  } else {
    body.pre  = start + "{\"text\":\"" + jsonEscape(text) + "\"}]}]" + end;
    body.post = "";
    body.audio = false;
  }

  WiFiClientSecure client;
  if (!httpsPostStart(client, CHAT_MODEL, body.total())) return false;
  if (!sendStream(client, body)) { client.stop(); say("Upload failed"); return false; }

  NetReader r{ &client };
  int code = r.readHeaders();
  String payload = r.readAll();
  client.stop();
  if (code != 200) {
    say("Gemini error " + String(code) + ": " + payload.substring(0, 300));
    return false;
  }
  return parseAnswer(payload, out);
}

// ======================= GEMINI TTS: text -> 8-bit audio buffer =======================
static int b64val(int c) {
  if (c >= 'A' && c <= 'Z') return c - 'A';
  if (c >= 'a' && c <= 'z') return c - 'a' + 26;
  if (c >= '0' && c <= '9') return c - '0' + 52;
  if (c == '+') return 62;
  if (c == '/') return 63;
  return -1;
}


size_t speechToBuffer(const String& text, const String& lang, uint8_t* out, size_t cap) {
  String how = lang == "ku" ? "Say this in Kurdish, Badini (Behdini) dialect, warm and clear: "
             : lang == "ar" ? "Say this in Arabic, warm and clear: "
                            : "Say this in English, warm and clear: ";
  String body = "{\"contents\":[{\"parts\":[{\"text\":\"" + jsonEscape(how + text) +
                "\"}]}],\"generationConfig\":{\"responseModalities\":[\"AUDIO\"],"
                "\"speechConfig\":{\"voiceConfig\":{\"prebuiltVoiceConfig\":{\"voiceName\":\"" +
                String(TTS_VOICE) + "\"}}}}}";

  WiFiClientSecure client;
  if (!httpsPostStart(client, TTS_MODEL, body.length())) return 0;
  client.write((const uint8_t*)body.c_str(), body.length());

  NetReader r{ &client };
  int code = r.readHeaders();
  if (code != 200) {
    say("TTS error " + String(code) + ": " + r.readAll(300));
    client.stop();
    return 0;
  }

  // find  "data"  then the opening quote of its value
  const char* key = "\"data\"";
  int matched = 0, c;
  while (key[matched] && (c = r.next()) >= 0) matched = (c == key[matched]) ? matched + 1 : (c == key[0] ? 1 : 0);
  if (key[matched]) { client.stop(); return 0; }
  while ((c = r.next()) >= 0 && c != '"') {}
  if (c < 0) { client.stop(); return 0; }

  // decode base64 -> 16-bit PCM 24 kHz -> average pairs -> 8-bit 12 kHz
  uint32_t acc = 0; int bits = 0;
  bool haveLo = false; uint8_t lo = 0;
  bool haveA = false; int a = 0;
  size_t n = 0;
  while (n < cap && (c = r.next()) >= 0 && c != '"') {
    int v = b64val(c);
    if (v < 0) continue;
    acc = (acc << 6) | v; bits += 6;
    if (bits < 8) continue;
    bits -= 8;
    uint8_t byte = (acc >> bits) & 0xFF;
    acc &= (1u << bits) - 1;
    if (!haveLo) { lo = byte; haveLo = true; continue; }
    haveLo = false;
    int16_t s = (int16_t)(lo | (byte << 8));
    if (!haveA) { a = s; haveA = true; continue; }
    haveA = false;
    int m = ((a + s) / 2) * volumePct / 100;
    m >>= 8;
    out[n++] = (uint8_t)(constrain(m, -128, 127) + 128);
  }
  client.stop();
  return n;
}

// ======================= SPEAKER (PWM -> RC filter -> LM386) =======================
void playAudio(const uint8_t* d, size_t n) {
  ledcAttach(PIN_SPK, 120000, 8);
  ledcWrite(PIN_SPK, 128);
  delay(20);
  unsigned long t0 = micros();
  for (size_t i = 0; i < n; i++) {
    unsigned long due = t0 + (unsigned long)((uint64_t)i * 1000000ULL / PLAY_RATE);
    while ((long)(micros() - due) < 0) {}
    ledcWrite(PIN_SPK, d[i]);
    if ((i & 4095) == 0) yield();
  }
  for (int v = 128; v >= 0; v -= 4) { ledcWrite(PIN_SPK, v); delayMicroseconds(400); }  // soft stop, no pop
  ledcDetach(PIN_SPK);
  pinMode(PIN_SPK, OUTPUT);
  digitalWrite(PIN_SPK, LOW);
}

void speak(const Answer& a) {
  size_t want = (size_t)PLAY_RATE * MAX_PLAY_SEC;
  uint8_t* buf = nullptr;
  if (psramFound()) buf = (uint8_t*)ps_malloc(want);
  if (!buf) {
    size_t lb = heap_caps_get_largest_free_block(MALLOC_CAP_8BIT);
    if (lb > 60000) {
      want = min(want, lb - 45000);
      buf = (uint8_t*)malloc(want);
    }
  }
  showText(a.show);
  if (!buf) { say("No RAM for audio"); return; }

  led(30, 0, 40);
  size_t len = speechToBuffer(a.say, a.lang, buf, want);
  if (len > 0) playAudio(buf, len);
  free(buf);
  if (a.show.length() > 80) showPages(a.show, 2500);
  delay(1500);
}

// ======================= MICROPHONE (INMP441) =======================
bool micBegin() {
  i2s.setPins(PIN_MIC_SCK, PIN_MIC_WS, -1, PIN_MIC_SD);
  return i2s.begin(I2S_MODE_STD, MIC_RATE, I2S_DATA_BIT_WIDTH_32BIT, I2S_SLOT_MODE_MONO, I2S_STD_SLOT_LEFT);
}

// records while the button is held; returns number of samples
size_t recordWhileHeld(int16_t* out, size_t maxSamples, unsigned long& heldMs) {
  int32_t raw[256];
  size_t n = 0;
  int32_t dc = 0;
  int peak = 0;
  unsigned long t0 = millis(), lastDraw = 0;
  led(40, 0, 0);
  while (digitalRead(PIN_BTN) == LOW && n < maxSamples) {
    size_t got = i2s.readBytes((char*)raw, sizeof(raw)) / 4;
    for (size_t i = 0; i < got && n < maxSamples; i++) {
      int32_t x = raw[i] >> MIC_GAIN_SHIFT;
      dc += (x - dc) >> 8;               // remove DC offset
      int32_t y = constrain(x - dc, -32768, 32767);
      out[n++] = (int16_t)y;
      int ay = abs(y);
      if (ay > peak) peak = ay;
    }
    if (millis() - lastDraw > 120) {
      drawLevel(peak * 116 / 20000);
      peak = 0;
      lastDraw = millis();
    }
  }
  heldMs = millis() - t0;
  return n;
}

// ======================= one conversation turn =======================
bool ready() {
  if (WiFi.status() != WL_CONNECTED) { showMsg(M_NOWIFI); say(UI[1][M_NOWIFI]); delay(2000); return false; }
  if (apiKey.length() < 10 || apiKey.startsWith("YOUR_")) { showMsg(M_NOKEY); say(UI[1][M_NOKEY]); delay(2000); return false; }
  return true;
}

void handleAnswer(bool ok, const Answer& a) {
  if (!ok) { showMsg(M_ERROR); led(40, 0, 0); delay(2000); return; }
  say("You: " + a.heard);
  say("Bot: " + a.say);
  remember(a.heard, a.say);
  speak(a);
}

// returns true if it was only a short click (no talking)
bool voiceTurn() {
  size_t maxSamples = (size_t)MIC_RATE * MAX_RECORD_SEC;
  int16_t* rec = nullptr;
  if (psramFound()) rec = (int16_t*)ps_malloc(maxSamples * 2);
  if (!rec) {
    size_t lb = heap_caps_get_largest_free_block(MALLOC_CAP_8BIT);
    if (lb < 70000) { say("No RAM for recording"); return false; }
    maxSamples = min(maxSamples, (lb - 50000) / 2);
    rec = (int16_t*)malloc(maxSamples * 2);
    if (!rec) return false;
  }
  unsigned long held = 0;
  size_t samples = recordWhileHeld(rec, maxSamples, held);
  while (digitalRead(PIN_BTN) == LOW) delay(5);   // buffer full: wait for release

  if (held < 350) { free(rec); return true; }      // just a click
  if (samples < MIC_RATE / 2) { free(rec); showMsg(M_SHORT); delay(800); return false; }
  if (!ready()) { free(rec); return false; }

  showMsg(M_THINK);
  led(0, 0, 40);
  Answer a;
  bool ok = askGemini(rec, samples, "", a);
  free(rec);
  handleAnswer(ok, a);
  return false;
}

void textTurn(const String& q) {
  if (!ready()) return;
  showMsg(M_THINK);
  led(0, 0, 40);
  Answer a;
  bool ok = askGemini(nullptr, 0, q, a);
  if (ok && a.heard.length() == 0) a.heard = q;
  handleAnswer(ok, a);
}

// ======================= commands (BLE + Serial) =======================
void handleCommand(String m) {
  m.trim();
  if (!m.length()) return;
  lastActivity = millis();
  if (m.startsWith("wifi:")) {
    int c = m.indexOf(',', 5);
    if (c < 0) { say("Use: wifi:NAME,PASSWORD"); return; }
    wifiSsid = m.substring(5, c);
    wifiPass = m.substring(c + 1);
    prefs.putString("ssid", wifiSsid);
    prefs.putString("pass", wifiPass);
    WiFi.disconnect();
    wifiConnect(true);
  } else if (m.startsWith("key:")) {
    apiKey = m.substring(4); apiKey.trim();
    prefs.putString("key", apiKey);
    say("Gemini key saved");
  } else if (m.startsWith("lang:")) {
    String l = m.substring(5);
    uiLang = l == "en" ? 1 : l == "ar" ? 2 : 0;
    prefs.putUChar("lang", uiLang);
    showMsg(M_LANG); say(UI[uiLang][M_LANG]); delay(1200);
  } else if (m.startsWith("vol:")) {
    volumePct = constrain(m.substring(4).toInt(), 0, 100);
    prefs.putInt("vol", volumePct);
    say("Volume " + String(volumePct));
  } else if (m == "bat") {
    float v = batteryVolts();
    say(batteryPresent(v) ? String(v, 2) + " V  " + batteryPercent(v) + "%" : String("No battery (USB)"));
  } else if (m == "sleep") {
    goSleep();
  } else {
    textTurn(m);
  }
  drawEyes(true);
}

// ======================= SETUP / LOOP =======================
void setup() {
  Serial.begin(115200);
  pinMode(PIN_BTN, INPUT_PULLUP);
  pinMode(PIN_SPK, OUTPUT);
  digitalWrite(PIN_SPK, LOW);
  analogSetPinAttenuation(PIN_BAT, ADC_11db);

  u8g2.setBusClock(400000);
  u8g2.begin();
  u8g2.enableUTF8Print();

  prefs.begin("ai", false);
  wifiSsid = prefs.getString("ssid", DEFAULT_WIFI_SSID);
  wifiPass = prefs.getString("pass", DEFAULT_WIFI_PASS);
  apiKey   = prefs.getString("key", DEFAULT_GEMINI_KEY);
  uiLang   = prefs.getUChar("lang", 0) % 3;
  volumePct = prefs.getInt("vol", 80);

  if (!micBegin()) say("Microphone (I2S) failed");

#if ENABLE_BLE
  bleBegin();
#endif
  wifiConnect(true);

  showMsg(M_HOLD);
  delay(2000);
  drawEyes(true);
  lastActivity = lastBlink = millis();
}

void loop() {
  // --- button: hold = talk, double click = language ---
  if (digitalRead(PIN_BTN) == LOW) {
    lastActivity = millis();
    if (voiceTurn()) {                              // recording starts at once; short press = click
      unsigned long t2 = millis();                  // short click -> wait for a second click
      bool second = false;
      while (millis() - t2 < 400) { if (digitalRead(PIN_BTN) == LOW) { second = true; break; } delay(5); }
      if (second) {
        while (digitalRead(PIN_BTN) == LOW) delay(5);
        uiLang = (uiLang + 1) % 3;
        prefs.putUChar("lang", uiLang);
        showMsg(M_LANG);
        delay(1200);
      } else {
        showMsg(M_HOLD);
        delay(1500);
      }
    }
    led(0, 10, 0);
    drawEyes(true);
    lastBlink = millis();
  }

  // --- messages from phone (BLE) or Serial Monitor ---
#if ENABLE_BLE
  if (bleHasMsg) {
    String m = bleInbox;
    bleHasMsg = false;
    handleCommand(m);
  }
#endif
  if (Serial.available()) handleCommand(Serial.readStringUntil('\n'));

  // --- idle eyes: blink every ~4 s ---
  if (millis() - lastBlink > 4000) {
    drawEyes(false);
    delay(150);
    drawEyes(true);
    lastBlink = millis();
  }

  // --- battery check every 30 s ---
  if (millis() - lastBatCheck > 30000) {
    lastBatCheck = millis();
    float v = batteryVolts();
    if (batteryPresent(v) && v < BAT_EMPTY_V) {
      showMsg(M_LOWBAT);
      delay(3000);
      goSleep();
    }
  }

  // --- auto off when idle ---
  if (IDLE_SLEEP_MIN > 0 && millis() - lastActivity > (unsigned long)IDLE_SLEEP_MIN * 60000UL) goSleep();

  delay(10);
}

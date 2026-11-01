/*
  ESP32 AI Assistant (short version) - Gemini - Kurdi Badini / English / Arabic
  Hold BOOT and talk -> Gemini answers with voice + text on the OLED.
  Bluetooth (BLE "ESP32-AI") or Serial Monitor: type a question.
  Libraries: U8g2, ArduinoJson (v7).  Board: esp32 by Espressif 3.x
  Parts: OLED SSD1306, INMP441 mic, LM386 + speaker, battery (optional)
*/
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <U8g2lib.h>
#include <ArduinoJson.h>
#include <ESP_I2S.h>
#include <BLEDevice.h>
#include <BLEServer.h>

// ===== SETTINGS =====
const char* WIFI_SSID  = "YOUR_WIFI_NAME";
const char* WIFI_PASS  = "YOUR_WIFI_PASSWORD";
const char* GEMINI_KEY = "YOUR_GEMINI_API_KEY";
const char* CHAT_MODEL = "gemini-2.5-flash";
const char* TTS_MODEL  = "gemini-2.5-flash-preview-tts";
const bool  USE_BATTERY = false;   // true after wiring battery + 100k/100k divider

// ===== PINS (ESP32-S3 / classic ESP32) =====
#if CONFIG_IDF_TARGET_ESP32S3
const int SDA_P = 8,  SCL_P = 9,  MIC_SCK = 4,  MIC_WS = 5,  MIC_SD = 6,  SPK = 7,  BAT = 1;
#else
const int SDA_P = 21, SCL_P = 22, MIC_SCK = 14, MIC_WS = 15, MIC_SD = 32, SPK = 25, BAT = 34;
#endif
const int BTN = 0;               // BOOT button
const int MIC_RATE = 16000, PLAY_RATE = 12000;

U8G2_SSD1306_128X64_NONAME_F_HW_I2C oled(U8G2_R0, U8X8_PIN_NONE, SCL_P, SDA_P);
I2SClass mic;
String bleMsg;
const char* HOST = "generativelanguage.googleapis.com";

// ===== SCREEN =====
void show(const String& text) {
  oled.clearBuffer();
  oled.setFont(u8g2_font_5x7_tr);
  oled.drawStr(0, 7, WiFi.status() == WL_CONNECTED ? "WiFi" : "----");
  if (USE_BATTERY) {
    float v = analogReadMilliVolts(BAT) * 2 / 1000.0;
    int p = constrain((int)((v - 3.3) / 0.9 * 100), 0, 100);
    oled.setCursor(100, 7); oled.print(p); oled.print("%");
  }
  oled.setFont(u8g2_font_6x12_te);
  String line, rest = text + " ";
  int y = 20;
  while (rest.length() && y <= 64) {               // simple word wrap
    int sp = rest.indexOf(' ');
    String w = rest.substring(0, sp + 1);
    if (oled.getUTF8Width((line + w).c_str()) > 128 && line.length()) {
      oled.drawUTF8(0, y, line.c_str()); y += 12; line = "";
    }
    line += w; rest = rest.substring(sp + 1);
  }
  if (y <= 64) oled.drawUTF8(0, y, line.c_str());
  oled.sendBuffer();
}

// ===== HTTPS =====
const char B64[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

void sendRaw(WiFiClientSecure& c, const String& s) { c.write((const uint8_t*)s.c_str(), s.length()); }

bool post(WiFiClientSecure& c, const char* model, size_t len) {
  c.setInsecure();
  if (!c.connect(HOST, 443)) return false;
  sendRaw(c, String("POST /v1beta/models/") + model + ":generateContent HTTP/1.0\r\nHost: " + HOST +
             "\r\nContent-Type: application/json\r\nx-goog-api-key: " + GEMINI_KEY +
             "\r\nContent-Length: " + String((unsigned long)len) + "\r\nConnection: close\r\n\r\n");
  return true;
}

int readByte(WiFiClientSecure& c) {              // waits up to 15 s
  unsigned long t = millis();
  while (!c.available()) { if (!c.connected() || millis() - t > 15000) return -1; delay(1); }
  return c.read();
}

bool findStr(WiFiClientSecure& c, const char* k) {
  int m = 0, ch;
  while (k[m] && (ch = readByte(c)) >= 0) m = ch == k[m] ? m + 1 : (ch == k[0] ? 1 : 0);
  return !k[m];
}

bool skipHeaders(WiFiClientSecure& c) {          // returns true if HTTP 200
  unsigned long t = millis();                    // Gemini may need some seconds
  while (!c.available() && c.connected() && millis() - t < 30000) delay(10);
  String first = c.readStringUntil('\n');
  while (true) { String h = c.readStringUntil('\n'); if (h.length() <= 1) break; }
  return first.indexOf(" 200") > 0;
}

String esc(const String& s) {                    // JSON escape
  String o;
  for (unsigned int i = 0; i < s.length(); i++) {
    char ch = s[i];
    if (ch == '"' || ch == '\\') { o += '\\'; o += ch; }
    else if (ch == '\n') o += "\\n";
    else if ((uint8_t)ch >= 0x20) o += ch;
  }
  return o;
}

// ===== GEMINI: audio or text -> answer =====
const char* PROMPT =
  "You are a small friendly robot on an ESP32. The user speaks Kurdish Badini (Behdini), Arabic or English. "
  "Answer in the same language, max 2 sentences. Kurdish in Kurdish Arabic script. "
  "Reply only JSON: {\"lang\":\"ku|ar|en\",\"say\":\"answer\",\"show\":\"same answer in Latin letters, max 100 chars\"}";

bool ask(int16_t* pcm, size_t samples, const String& text, String& lang, String& say, String& showTxt) {
  String head = String("{\"system_instruction\":{\"parts\":[{\"text\":\"") + esc(PROMPT) +
                "\"}]},\"contents\":[{\"parts\":[";
  String tail = "]}],\"generationConfig\":{\"responseMimeType\":\"application/json\"}}";
  size_t bin = pcm ? 44 + samples * 2 : 0;
  if (pcm) { head += "{\"inline_data\":{\"mime_type\":\"audio/wav\",\"data\":\""; tail = "\"}}" + tail; }
  else head += "{\"text\":\"" + esc(text) + "\"}";

  WiFiClientSecure c;
  if (!post(c, CHAT_MODEL, head.length() + (bin + 2) / 3 * 4 + tail.length())) return false;
  sendRaw(c, head);
  if (pcm) {                                     // WAV header + samples, base64 on the fly
    uint8_t h[44] = {'R','I','F','F'};
    uint32_t d = samples * 2, v[] = {36 + d, 0, 16, 0, (uint32_t)MIC_RATE, (uint32_t)MIC_RATE * 2, 0, 0, d};
    memcpy(h + 8, "WAVEfmt ", 8); memcpy(h + 36, "data", 4);
    memcpy(h + 4, &v[0], 4); memcpy(h + 16, &v[2], 4);
    h[20] = 1; h[22] = 1; memcpy(h + 24, &v[4], 4); memcpy(h + 28, &v[5], 4); h[32] = 2; h[34] = 16;
    memcpy(h + 40, &v[8], 4);
    auto at = [&](size_t i) -> uint8_t { return i < 44 ? h[i] : ((uint8_t*)pcm)[i - 44]; };
    char out[512]; int n = 0;
    for (size_t i = 0; i < bin; i += 3) {
      uint32_t x = at(i) << 16 | (i + 1 < bin ? at(i + 1) << 8 : 0) | (i + 2 < bin ? at(i + 2) : 0);
      out[n++] = B64[x >> 18 & 63]; out[n++] = B64[x >> 12 & 63];
      out[n++] = i + 1 < bin ? B64[x >> 6 & 63] : '=';
      out[n++] = i + 2 < bin ? B64[x & 63] : '=';
      if (n >= 508) { c.write((uint8_t*)out, n); n = 0; }
    }
    c.write((uint8_t*)out, n);
  }
  sendRaw(c, tail);

  bool ok = skipHeaders(c);
  String body; int ch;
  while ((ch = readByte(c)) >= 0) body += (char)ch;
  c.stop();
  if (!ok) { Serial.println(body.substring(0, 300)); return false; }

  JsonDocument doc, ans;
  deserializeJson(doc, body);
  const char* t = doc["candidates"][0]["content"]["parts"][0]["text"] | "";
  if (deserializeJson(ans, t)) { lang = "en"; say = t; showTxt = t; }
  else { lang = ans["lang"] | "en"; say = ans["say"] | ""; showTxt = ans["show"] | say.c_str(); }
  return say.length() > 0;
}

// ===== GEMINI TTS -> speaker =====
int b64val(int c) {
  if (c >= 'A' && c <= 'Z') return c - 'A';
  if (c >= 'a' && c <= 'z') return c - 'a' + 26;
  if (c >= '0' && c <= '9') return c - '0' + 52;
  return c == '+' ? 62 : c == '/' ? 63 : -1;
}

void speak(const String& text, const String& lang) {
  String how = lang == "ku" ? "Say in Kurdish Badini: " : lang == "ar" ? "Say in Arabic: " : "Say: ";
  String body = "{\"contents\":[{\"parts\":[{\"text\":\"" + esc(how + text) + "\"}]}],"
                "\"generationConfig\":{\"responseModalities\":[\"AUDIO\"]}}";
  size_t cap = psramFound() ? (size_t)PLAY_RATE * 30 : min((size_t)PLAY_RATE * 10, (size_t)ESP.getMaxAllocHeap() - 45000);
  uint8_t* buf = (uint8_t*)(psramFound() ? ps_malloc(cap) : malloc(cap));
  if (!buf) return;

  WiFiClientSecure c;
  size_t n = 0;
  if (post(c, TTS_MODEL, body.length())) {
    sendRaw(c, body);
    if (skipHeaders(c) && findStr(c, "\"data\"") && findStr(c, "\"")) {
      uint32_t acc = 0; int bits = 0, half = 0, lo = 0, prev = 0, ch;
      while (n < cap && (ch = readByte(c)) >= 0 && ch != '"') {
        int v = b64val(ch); if (v < 0) continue;
        acc = acc << 6 | v; bits += 6;
        if (bits < 8) continue;
        bits -= 8; int b = acc >> bits & 255;
        if (half % 2 == 0) lo = b;                       // 16-bit little endian, 24 kHz
        else if (half % 4 == 1) prev = (int16_t)(lo | b << 8);
        else buf[n++] = ((prev + (int16_t)(lo | b << 8)) / 2 >> 8) + 128;   // -> 8-bit 12 kHz
        half++;
      }
    }
  }
  c.stop();

  ledcAttach(SPK, 120000, 8);                    // PWM -> 1k + 10nF -> LM386
  unsigned long t0 = micros();
  for (size_t i = 0; i < n; i++) {
    while (micros() - t0 < i * 1000000ULL / PLAY_RATE) {}
    ledcWrite(SPK, buf[i]);
  }
  ledcDetach(SPK);
  free(buf);
}

// ===== one question =====
void handle(int16_t* pcm, size_t samples, const String& text) {
  show("...");
  String lang, say, txt;
  if (!ask(pcm, samples, text, lang, say, txt)) { show("Error / Xeleti"); delay(2000); return; }
  Serial.println(say);
  show(txt);
  speak(say, lang);
  delay(3000);
}

void record() {
  size_t maxS = psramFound() ? (size_t)MIC_RATE * 6 : min((size_t)MIC_RATE * 3, ((size_t)ESP.getMaxAllocHeap() - 50000) / 2);
  int16_t* pcm = (int16_t*)(psramFound() ? ps_malloc(maxS * 2) : malloc(maxS * 2));
  if (!pcm) return;
  show("Guhdari dikim / Listening");
  size_t n = 0; int32_t raw[128], dc = 0;
  while (digitalRead(BTN) == LOW && n < maxS) {
    size_t got = mic.readBytes((char*)raw, sizeof(raw)) / 4;
    for (size_t i = 0; i < got && n < maxS; i++) {
      int32_t x = raw[i] >> 13;
      dc += (x - dc) >> 8;
      pcm[n++] = constrain(x - dc, -32768, 32767);
    }
  }
  if (n > MIC_RATE / 2) handle(pcm, n, "");
  free(pcm);
}

// ===== Bluetooth: type a question =====
class RxCB : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic* c) override { bleMsg = String(c->getValue().c_str()); }
};

void setup() {
  Serial.begin(115200);
  pinMode(BTN, INPUT_PULLUP);
  oled.begin();
  show("Silav / Hello / Marhaba");
  mic.setPins(MIC_SCK, MIC_WS, -1, MIC_SD);
  mic.begin(I2S_MODE_STD, MIC_RATE, I2S_DATA_BIT_WIDTH_32BIT, I2S_SLOT_MODE_MONO, I2S_STD_SLOT_LEFT);

  BLEDevice::init("ESP32-AI");
  BLEService* s = BLEDevice::createServer()->createService("6E400001-B5A3-F393-E0A9-E50E24DCCA9E");
  s->createCharacteristic("6E400002-B5A3-F393-E0A9-E50E24DCCA9E", BLECharacteristic::PROPERTY_WRITE)
    ->setCallbacks(new RxCB());
  s->start();
  BLEDevice::getAdvertising()->addServiceUUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E");
  BLEDevice::startAdvertising();

  WiFi.begin(WIFI_SSID, WIFI_PASS);
  for (int i = 0; i < 40 && WiFi.status() != WL_CONNECTED; i++) delay(250);
  show("Bigre BOOT u biaxive / Hold BOOT and talk");
}

void loop() {
  if (digitalRead(BTN) == LOW) record();
  if (Serial.available()) handle(nullptr, 0, Serial.readStringUntil('\n'));
  if (bleMsg.length()) { String q = bleMsg; bleMsg = ""; handle(nullptr, 0, q); }
  static unsigned long blink = 0;                // idle eyes
  if (millis() - blink > 4000) {
    oled.clearBuffer(); oled.drawRBox(18, 24, 34, 4, 2); oled.drawRBox(76, 24, 34, 4, 2); oled.sendBuffer();
    delay(150);
    oled.clearBuffer(); oled.drawRBox(18, 10, 34, 38, 8); oled.drawRBox(76, 10, 34, 38, 8); oled.sendBuffer();
    blink = millis();
  }
}

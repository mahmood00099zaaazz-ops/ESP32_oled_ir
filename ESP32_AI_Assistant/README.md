# ESP32 AI Assistant (Gemini) — Kurdî Badînî / English / العربية

یاریدەدەرێ دەنگی ل سەر ESP32: تو دئاخڤی، Gemini گوهدارییێ دکەت و ب دەنگ و نڤیسین بەرسڤێ ددەت.

| پارچە | کار |
|---|---|
| OLED SSD1306 128x64 | شاشە: چاڤ، نڤیسینا بەرسڤێ، WiFi/BT/پاتری |
| INMP441 | مایکرۆفۆن |
| LM386 + سپیکەر 8Ω | دەنگ |
| 18650 + TP4056 + MT3608 + سویچ | پاتری و سویچا ON/OFF |
| WiFi | گرێدان ب Gemini |
| Bluetooth (BLE) | پرسیار و ڕێکخستن ژ مۆبایلێ |

Wiring: see `wiring.png`.

## Setup
1. Arduino IDE → Boards Manager → **esp32 by Espressif 3.x**
2. Library Manager → **U8g2**, **ArduinoJson** (v7)
3. Open `ESP32_AI_Assistant.ino`, fill `WIFI_SSID`, `WIFI_PASS`, `GEMINI_KEY` (key: https://aistudio.google.com/apikey)
4. Board: `ESP32S3 Dev Module` (PSRAM: OPI/QSPI if your board has it) or `ESP32 Dev Module`
5. Upload.

## Use
- **Hold BOOT + speak**, release → answer (voice + screen)
- Phone app **Serial Bluetooth Terminal** → BLE → `ESP32-AI` → type a question
- Or type a question in the Serial Monitor (115200)
- Battery: set `USE_BATTERY = true` after wiring the battery divider

## Notes
- The OLED font cannot join Arabic letters, so the screen shows the answer in Latin letters
  (Kurdish Latin / Arabizi / English). The voice and the Bluetooth text use the real script.
- Model names are constants at the top (`CHAT_MODEL`, `TTS_MODEL`); change them if Google renames them.
- An ESP32-S3 with PSRAM works best (longer recordings and answers).

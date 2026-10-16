# 🤖 Roboti Badini — روبوتێ ب بادینی دئاخڤیت

> New version: talking robot (INMP441 mic + MAX98357A speaker + OLED eyes).
> The original IR-sensor sketch is still in `OLED_IR_CODE.ino`.

## چاوا کار دکەت؟ (How it works)
1. **ESP32** گوهـ ل تە دبیت (INMP441). دەمێ تو دئاخڤی، دەنگێ تە دهنێریتە سێرڤەری.
2. **سێرڤەر** (`server/server.py`، ل سەر کومپیوتەرێ تە): دەنگی دکەتە نڤیسین ← **Claude** بەرسڤێ ب بادینی ددەت ← نڤیسینێ دکەتە دەنگ.
3. **ESP32** بەرسڤێ ل سەر سپیکەری لێ ددەت و دەڤێ روبوتی ل سەر شاشێ دلڤیت.

چاڤێن روبوتی: 😐 ئاسایی (چاڤان دقوچینیت و ل دۆرا خۆ دنێریت) · 😮 گوهدارکرن (چاڤێن مەزن) · 🤔 هزرکرن (چاڤ ل ژۆری + خال) · 😊 ئاخفتن (چاڤێن کەیفخۆش + دەڤ) · ✖✖ خەلەتی

## Wiring / گرێدان
| Part | Pin | ESP32 |
|---|---|---|
| OLED SSD1306 | SDA / SCL / VDD / GND | GPIO21 / GPIO22 / 3V3 / GND |
| INMP441 mic | SD / WS / SCK | GPIO32 / GPIO25 / GPIO33 |
| INMP441 mic | L/R, GND / VDD | GND / 3V3 |
| MAX98357A amp | DIN / BCLK / LRC | GPIO26 / GPIO27 / GPIO14 |
| MAX98357A amp | Vin / GND | VIN (5V) / GND |

ئەگەر تە پینێن دی بکار ئینابن، تنێ ژمارێن `#define` ل سەری کودێ `Roboti_Badini/Roboti_Badini.ino` بگوهۆڕە.

## 1) Server (PC / Raspberry Pi)
```bash
cd server
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...      # Windows: set ANTHROPIC_API_KEY=sk-ant-...
python server.py                          # listens on port 8000
python server.py --say "Silav, tu çawa yî?"   # test without robot -> answer.wav
```
- Speech-to-text: Meta MMS (`facebook/mms-1b-all`, Kurmanji adapter)
- Brain: Claude (`claude-opus-5-5`) — answers short, in **Badini, Kurdish Latin letters**
  (the Kurdish TTS voice can only read Latin script: ê î û ç ş …)
- Text-to-speech: Meta MMS TTS (`facebook/mms-tts-kmr-script_latin`)
- First start downloads ~4 GB of models; a GPU is faster but CPU works.

## 2) ESP32
1. Arduino IDE → install board **esp32** and library **U8g2**.
2. Open `Roboti_Badini/Roboti_Badini.ino`, set `WIFI_SSID`, `WIFI_PASS`,
   `SERVER_HOST` (the IP of the PC running `server.py`).
3. Board: **ESP32 Dev Module** → Upload → open Serial Monitor (115200).
4. بئاخڤە! (Speak to it.) It starts recording when your voice is louder than the room
   and stops after ~1 second of silence.

**Tips:** too quiet mic → lower `MIC_GAIN_SHIFT` (e.g. 12); speaker too loud → lower
`SPEAKER_VOLUME`; it reacts to noise → raise the `3.0f` threshold in `loop()`.

---

# ESP32_oled_ir
This repo is about getting started with ESP32.In this repo you will cover two topic sending and receiving data from ESP32.This repo is about receiving data from an IR sensor and  display robotics eyes on an OLED 128x64 display using ESP32.

WATCH FULL TUTORIAL VIDEO --> https://youtu.be/Oq6sax94xng

![image](https://github.com/engrpakistan/ESP32_oled_ir/assets/148635820/fee72dff-e341-498a-9916-ead0c1c06fc5)

**ACT 1 COMPONENT SELECTION**

ESP32:There are many benefits for using ESP32 than Arduino Nano.It is much faster, has more memory, and has built-in Wifi and bluetooth.
![sp322 (1)](https://github.com/engrpakistan/ESP32_oled_ir/assets/148635820/6174df33-46ad-47ab-a269-ee3fd356ff32)
OLED:For this project 128X64 OLED is selected.It has much more pixel than a normal 16x2 display, so it gives more room being creative with the diplay. 
![image](https://github.com/engrpakistan/ESP32_oled_ir/assets/148635820/cde3f397-d719-42fc-a0c0-cc2505d73fdd)

IR SENSOR:The functionality of this IR sensor is that it help us to understand how data is sent to ESP32.If we take it further we can get creative with it.If the IR sensor receives zero it will look up otherwise it will continue to blink.
![image](https://github.com/engrpakistan/ESP32_oled_ir/assets/148635820/a1ad3b4a-e684-43dd-8167-d34b3e9a1d24)

**ACT 2 WIRING**

The wiring diagram shows the pin configuration.The fritzing file and wiring diagram is uploaded in the repo.
![image](https://github.com/engrpakistan/ESP32_oled_ir/assets/148635820/ce511012-e5d0-40cb-81b8-65bf6a7adafe)

**ACT 3 LOPAKA**

After wiring up the circuit it's time to design some animation without little to no effort (you dont need to code).Goto lopaka(https://lopaka.app/) set the libray to U8g2 and display to 128x 64 (you may set accordingly to your need).

![image](https://github.com/engrpakistan/ESP32_oled_ir/assets/148635820/cd812d59-19a7-40ec-a0ab-c117c39b3437)

Now be creative and start designing ENGINEERS!!! 

![image](https://github.com/engrpakistan/ESP32_oled_ir/assets/148635820/b3cf4c67-b5eb-4f1e-a319-9ac751188c14)

After designing copy the code.

![image](https://github.com/engrpakistan/ESP32_oled_ir/assets/148635820/f8fc6fae-9195-4e44-9659-f330babad827)

**ACT 4 CODING**

We are almost there.Coding file is uploaded to this repo.Open your Arduino IDE and search for U8g2 (library by oliver).

![image](https://github.com/engrpakistan/ESP32_oled_ir/assets/148635820/c1402612-29ff-440f-b89a-4647cba3e874)

Set up the U8g2 library.

![image](https://github.com/engrpakistan/ESP32_oled_ir/assets/148635820/037a2828-a3f2-418a-8554-6fe3dd98c4af)

![image](https://github.com/engrpakistan/ESP32_oled_ir/assets/148635820/7b3b175c-23e8-413d-b8f7-0a99c1ab2bb6)

Paste the code you have just copied into the loop function or you can make function and call that function into the loop function.

![image](https://github.com/engrpakistan/ESP32_oled_ir/assets/148635820/e00a871d-79a1-4712-8430-10ff6f9ce221)

Select the board and Upload the code and you have done it ENGINEERS!!!!

![image](https://github.com/engrpakistan/ESP32_oled_ir/assets/148635820/8263b699-2482-412a-8abe-e303d06f43d4)





# چاوا کۆدی ژ لاپتۆپی بۆ ESP32 فرێکەین (Arduino IDE)
# How to upload code from a laptop to the ESP32 (Arduino IDE)

```
 ┌──────────────┐   USB-C (کێبلێ داتا)   ┌──────────────┐
 │   لاپتۆپ      │ ─────────────────────▶ │    ESP32     │
 │ Arduino IDE  │                         │  (BOOT / EN) │
 └──────────────┘                         └──────────────┘
```

## ١. Arduino IDE دابەزینە
- بچە: https://www.arduino.cc/en/software  ←  Windows Win 10 and newer دابەزینە و دامەزرینە.

## ٢. پشتگیریا ESP32 زێدە بکە
1. `File → Preferences`
2. ل خانا **Additional boards manager URLs** ڤێ لینکێ دانە:
   ```
   https://espressif.github.io/arduino-esp32/package_esp32_index.json
   ```
3. `Tools → Board → Boards Manager` ← بنڤیسە `esp32` ← **esp32 by Espressif Systems** ← `Install`.

## ٣. کتێبخانە (Library) دامەزرینە
`Sketch → Include Library → Manage Libraries` ← بنڤیسە `U8g2` ← **U8g2 by oliver** ← `Install`.

## ٤. ESP32 گرێ بدە ب لاپتۆپی
- کێبلێ **USB-C یێ داتا** بکاربینە (هندەک کێبل تنێ بۆ شەحنێ نە و کار ناکەن).
- ئەگەر پۆرت (COM) دیار نەبوو، درایڤەری دابەزینە:
  - CP2102: https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers
  - CH340: https://www.wch-ic.com/downloads/CH341SER_EXE.html
  - (ل سەر بۆردی بنێرە، چیپا بچویک نێزیکی USB ناڤێ وێ دیار دکەت.)

## ٥. بۆرد و پۆرت هەلبژێرە
- `Tools → Board → esp32 → ESP32 Dev Module`
- `Tools → Port → COMx` (بۆ نموونە COM3)

## ٦. Upload
1. `File → Open` ← `OLED_IR_CODE.ino`
2. دوگمەیا ✔ (**Verify**) بکە دا خەلەتی بهێنە دیتن.
3. دوگمەیا ➜ (**Upload**) بکە.
4. ئەگەر `Connecting....____` دیار بوو: دوگمەیا **BOOT** ل سەر ESP32 بگرە تا `Writing...` دەست پێ دکەت، پاشان بهێلە.
5. دەمێ `Hard resetting via RTS pin...` دیار بوو ← کار تمام بوو ✅. ئەگەر کۆد دەست پێ نەکر، دوگمەیا **EN** بکە.

## خەلەتیێن بەربەلاڤ / Common errors
| خەلەتی | چارەسەری |
|---|---|
| Port دیار نابیت | کێبلێ داتا + درایڤەر (CP2102 / CH340) |
| `Failed to connect to ESP32: Timed out` | دوگمەیا BOOT بگرە دەمێ Upload |
| `U8g2lib.h: No such file` | کتێبخانا U8g2 دامەزرینە |
| `no matching member function for call to 'print'` | جۆرێ داتایێ تە بۆ `print()` دشێت نەهێتە پشتگیری کرن — بکە `String(x)` یان `x.c_str()` |

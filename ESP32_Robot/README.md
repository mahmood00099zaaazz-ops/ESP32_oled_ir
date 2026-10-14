# ڕۆبۆتێ ESP32 (ESP32 Robot)

ڕۆبۆتەکێ دوو-تایە یێ کو ڕێکێ دچیت و خۆ ژ ئاستەنگان دپارێزیت. چاڤێن وی ل سەر شاشا OLED
دیار دبن (هەمان چاڤێن `OLED_IR_CODE.ino`)، و سێنسۆرێ IR ئاستەنگان دبینیت.

A two-wheel obstacle-avoiding robot. It reuses the OLED eyes and IR sensor from
`OLED_IR_CODE.ino` and adds an L298N motor driver with two DC motors.

## چاوا کار دکەت (How it works)

| ڕەوش (State) | چ دکەت |
|---|---|
| ڕێ ڤالایە | بەرەڤ پێش دچیت، چاڤ چاڤان دنقینیت (blink) |
| ئاستەنگ هەیە | ڕادوەستیت، چاڤ بلند دبن (eye_up) |
| پشتی 300ms | 400ms بەرەڤ پاش دچیت |
| پاشی | ل جهێ خۆ بەرەڤ چەپێ دزڤڕیت هەتا ڕێ ڤالا دبیت، پاشی دیسا بەرەڤ پێش |

## پێدڤی (Parts)

- ESP32 DevKit
- OLED 128x64 SSD1306 (I2C)
- سێنسۆرێ IR یێ ئاستەنگان (IR obstacle sensor)
- L298N motor driver
- 2× DC gear motor + تایە، و چەرخەکێ ئازاد (caster wheel)
- شاسی (chassis)
- باتری 7–12V بۆ مۆتۆران (بۆ نموونە 2× 18650)

## گرێدان (Wiring)

| پارچە | Pin | ESP32 |
|---|---|---|
| OLED | SDA | GPIO21 |
| OLED | SCL | GPIO22 |
| OLED | VCC / GND | 3.3V / GND |
| IR sensor | OUT | GPIO34 |
| IR sensor | VCC / GND | 3.3V / GND |
| L298N | ENA (left speed) | GPIO25 |
| L298N | IN1 | GPIO26 |
| L298N | IN2 | GPIO27 |
| L298N | ENB (right speed) | GPIO14 |
| L298N | IN3 | GPIO33 |
| L298N | IN4 | GPIO32 |
| L298N | GND | GND (**دڤێت GND یێ هەڤپشک بیت / common ground**) |
| L298N | 12V | باتری + |
| L298N | 5V out | ESP32 VIN (ئەگەر باتری ≥ 7V بیت) |

> بەری کو ENA/ENB گرێ بدەی، jumper ـێن وان ل سەر L298N ڕاکە.
> Remove the ENA/ENB jumpers on the L298N so the ESP32 can control speed.

## بارکرن (Upload)

1. Arduino IDE ڤەکە و ESP32 board package دابنێ.
2. کتێبخانا **U8g2** (by olikraus) دابنێ.
3. `ESP32_Robot/ESP32_Robot.ino` ڤەکە، board هەلبژێرە (ESP32 Dev Module) و Upload بکە.

## ڕێکخستن (Tuning)

ل سەری فایلێ ئەڤ بها دشێی بگوهۆڕی:

- `SPEED_FORWARD`, `SPEED_TURN` — لەز (0..255)
- `REVERSE_TIME`, `TURN_TIME` — دەمێ پاشڤەچوون و زڤڕینێ (ms)

ئەگەر مۆتۆرەک بەرەڤاژی دزڤڕیت، دوو تێلێن وی مۆتۆری ل سەر L298N بگوهۆڕە
(If a motor spins the wrong way, swap its two wires on the L298N).

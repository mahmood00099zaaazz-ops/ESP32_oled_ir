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





**ROBOT EYES PREVIEW**

How the eyes from `OLED_IR_CODE.ino` look on the 128x64 OLED:

![Robot eyes preview](images/robot_eyes_preview.png)

![Robot eyes animation](images/robot_eyes_animation.gif)

To regenerate the images: `python3 tools/render_eyes_preview.py` (needs Pillow).

**ESP32 ROBOT EYES (FULL CODE)**

`ESP32_Robot_Eyes/ESP32_Robot_Eyes.ino` is a complete, improved version of the sketch:

- Rounded robot eyes that blink at random times and look around (left, right, up, down).
- Smooth, non-blocking animation (~50 FPS, no `delay()` in the loop).
- When the IR sensor detects an object, the robot looks up and smiles; it goes back to normal shortly after the object leaves.
- IR input is debounced; status messages are printed to the Serial Monitor (115200 baud).

Wiring: OLED SDA -> GPIO21, SCL -> GPIO22, VCC -> 3V3, GND -> GND. IR sensor OUT -> GPIO34, VCC -> 3V3, GND -> GND.
Library: U8g2 by olikraus. Board: "ESP32 Dev Module".

![ESP32 robot eyes](images/esp32_robot_eyes.gif)

**ESP32 TALKING ROBOT**

`ESP32_Robot_Talk/ESP32_Robot_Talk.ino` gives the robot a voice with a DFPlayer Mini MP3 module.
Record your own sentences (any language) as MP3 and put them on a FAT32 microSD card in a folder
named `mp3` (`mp3/0001.mp3`, `mp3/0002.mp3`, ...). The OLED shows eyes and a mouth that moves while
the robot talks.

- Sentence 1 at start-up, a random greeting (2-4) when the IR sensor sees someone, and a random
  sentence (5-6) when nobody has been around for 30-60 seconds.
- Type 1-9 in the Serial Monitor (115200 baud) to play a sentence.

Wiring: DFPlayer VCC -> 5V (VIN), GND -> GND, TX -> GPIO16, RX -> 1k resistor -> GPIO17,
BUSY -> GPIO4, SPK_1/SPK_2 -> speaker (3W, 4-8 ohm). OLED and IR as above.
Libraries: U8g2 and DFRobotDFPlayerMini.

![ESP32 talking robot face](images/robot_talk.gif)

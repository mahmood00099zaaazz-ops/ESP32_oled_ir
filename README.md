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





**ACT 5 ROBOT**

Turn the eyes into a moving robot: see [`ESP32_Robot/`](ESP32_Robot/README.md) for an obstacle-avoiding robot that adds an L298N motor driver and two DC motors.

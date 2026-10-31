// Hardware test: OLED screen + MAX98357A amplifier + speaker on ESP32.
// Open Serial Monitor at 115200 to read the results.
//
// OLED       ESP32          MAX98357A   ESP32
// VCC   ->   3V3            VIN    ->   VIN (5V)
// GND   ->   GND            GND    ->   GND
// SCL   ->   GPIO22         LRC    ->   GPIO25
// SDA   ->   GPIO21         BCLK   ->   GPIO26
//                           DIN    ->   GPIO27
//                           GAIN, SD -> not connected
// Speaker: the two wires go into the green screw terminal (+ and -).

#include <Wire.h>
#include <U8g2lib.h>
#include <driver/i2s.h>

#define OLED_SDA 21
#define OLED_SCL 22
#define AMP_LRC  25
#define AMP_BCLK 26
#define AMP_DIN  27

const int SAMPLE_RATE = 16000;

// 0.96" screens use SSD1306. If yours is 1.3", comment this line and use the SH1106 one.
U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, U8X8_PIN_NONE);
// U8G2_SH1106_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, U8X8_PIN_NONE);

bool oledFound = false;

void scanI2C() {
  Wire.begin(OLED_SDA, OLED_SCL);
  Serial.println("\n--- 1. OLED (I2C scan) ---");
  int found = 0;
  for (byte addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      Serial.printf("Found device at 0x%02X\n", addr);
      if (addr == 0x3C || addr == 0x3D) oledFound = true;
      found++;
    }
  }
  if (found == 0) {
    Serial.println("NOTHING found. Check: VCC->3V3, GND->GND, SDA->21, SCL->22 (try swapping SDA/SCL).");
  } else if (oledFound) {
    Serial.println("OLED OK at I2C. If the screen stays black, try the SH1106 line in the code.");
  }
}

void showText(const char *line1, const char *line2) {
  u8g2.clearBuffer();
  u8g2.setFont(u8g2_font_ncenB14_tr);
  u8g2.drawStr(0, 24, line1);
  u8g2.setFont(u8g2_font_6x12_tr);
  u8g2.drawStr(0, 50, line2);
  u8g2.sendBuffer();
}

void startAmp() {
  Serial.println("\n--- 2. Amplifier (I2S) ---");
  i2s_config_t cfg = {};
  cfg.mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX);
  cfg.sample_rate = SAMPLE_RATE;
  cfg.bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT;
  cfg.channel_format = I2S_CHANNEL_FMT_ONLY_LEFT;
  cfg.communication_format = I2S_COMM_FORMAT_STAND_I2S;
  cfg.dma_buf_count = 8;
  cfg.dma_buf_len = 256;
  cfg.tx_desc_auto_clear = true;

  i2s_pin_config_t pins = {};
  pins.bck_io_num = AMP_BCLK;
  pins.ws_io_num = AMP_LRC;
  pins.data_out_num = AMP_DIN;
  pins.data_in_num = I2S_PIN_NO_CHANGE;

  if (i2s_driver_install(I2S_NUM_0, &cfg, 0, NULL) != ESP_OK || i2s_set_pin(I2S_NUM_0, &pins) != ESP_OK) {
    Serial.println("I2S start FAILED.");
    return;
  }
  Serial.println("I2S started. You should hear beeps now.");
}

void beep(int freq, int ms) {
  const int n = 256;
  int16_t buf[n];
  int total = SAMPLE_RATE * ms / 1000;
  static float phase = 0;
  for (int done = 0; done < total; done += n) {
    for (int i = 0; i < n; i++) {
      buf[i] = (int16_t)(6000 * sinf(phase));  // about 20% volume
      phase += 2 * PI * freq / SAMPLE_RATE;
      if (phase > 2 * PI) phase -= 2 * PI;
    }
    size_t written;
    i2s_write(I2S_NUM_0, buf, sizeof(buf), &written, portMAX_DELAY);
  }
  i2s_zero_dma_buffer(I2S_NUM_0);
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n=== Zirek hardware test ===");

  scanI2C();
  u8g2.begin();
  showText("Silav!", oledFound ? "OLED OK" : "OLED not found");

  startAmp();
}

void loop() {
  showText("Beep...", "Speaker test");
  Serial.println("beep");
  beep(440, 300);
  delay(100);
  beep(660, 300);
  delay(100);
  beep(880, 300);
  showText("Silav!", "Did you hear 3 beeps?");
  delay(3000);
}

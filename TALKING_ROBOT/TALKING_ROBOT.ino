// Talking robot: OLED eyes + INMP441 mic + MAX98357A speaker on ESP32.
// It listens, records what you say (2 s) and repeats it in a higher voice
// while the mouth on the OLED moves with the sound.
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <driver/i2s.h>

// INMP441 microphone
#define MIC_SCK 33
#define MIC_WS  25
#define MIC_SD  32
// MAX98357A amplifier
#define AMP_BCLK 27
#define AMP_LRC  14
#define AMP_DIN  26
// OLED uses the default I2C pins: SDA 21, SCL 22

#define RATE      16000
#define REC_SEC   2
#define REC_LEN   (RATE * REC_SEC)
#define PITCH     1.35      // >1 = higher, funnier voice
#define TRIGGER   2500      // loudness that starts recording
#define CHUNK     256

Adafruit_SSD1306 oled(128, 64, &Wire, -1);
int16_t *rec;
int32_t raw[CHUNK];
float dc = 0;

void micInit() {
  i2s_config_t c = {};
  c.mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX);
  c.sample_rate = RATE;
  c.bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT;
  c.channel_format = I2S_CHANNEL_FMT_ONLY_LEFT;   // L/R pin -> GND
  c.communication_format = I2S_COMM_FORMAT_STAND_I2S;
  c.dma_buf_count = 8;
  c.dma_buf_len = CHUNK;
  i2s_pin_config_t p = {};
  p.mck_io_num = I2S_PIN_NO_CHANGE;
  p.bck_io_num = MIC_SCK;
  p.ws_io_num = MIC_WS;
  p.data_out_num = I2S_PIN_NO_CHANGE;
  p.data_in_num = MIC_SD;
  i2s_driver_install(I2S_NUM_0, &c, 0, NULL);
  i2s_set_pin(I2S_NUM_0, &p);
}

void ampInit() {
  i2s_config_t c = {};
  c.mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX);
  c.sample_rate = RATE * PITCH;
  c.bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT;
  c.channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT;
  c.communication_format = I2S_COMM_FORMAT_STAND_I2S;
  c.dma_buf_count = 8;
  c.dma_buf_len = CHUNK;
  c.tx_desc_auto_clear = true;
  i2s_pin_config_t p = {};
  p.mck_io_num = I2S_PIN_NO_CHANGE;
  p.bck_io_num = AMP_BCLK;
  p.ws_io_num = AMP_LRC;
  p.data_out_num = AMP_DIN;
  p.data_in_num = I2S_PIN_NO_CHANGE;
  i2s_driver_install(I2S_NUM_1, &c, 0, NULL);
  i2s_set_pin(I2S_NUM_1, &p);
}

// Reads one chunk from the mic into out (16-bit), returns the peak level.
int readMic(int16_t *out) {
  size_t bytes;
  i2s_read(I2S_NUM_0, raw, sizeof(raw), &bytes, portMAX_DELAY);
  int n = bytes / 4, peak = 0;
  for (int i = 0; i < n; i++) {
    float v = raw[i] >> 14;
    dc += (v - dc) * 0.001;
    int s = constrain((int)(v - dc), -32767, 32767);
    if (out) out[i] = s;
    peak = max(peak, abs(s));
  }
  return peak;
}

void face(int eyeH, int mouth) {
  oled.clearDisplay();
  oled.fillRoundRect(20, 24 - eyeH / 2, 32, eyeH, 9, SSD1306_WHITE);
  oled.fillRoundRect(76, 24 - eyeH / 2, 32, eyeH, 9, SSD1306_WHITE);
  if (mouth > 0) oled.fillRoundRect(52, 48, 24, mouth, 4, SSD1306_WHITE);
  oled.display();
}

void listenAndRecord() {
  face(30, 0);                       // big eyes: listening
  int len = 0;
  while (len + CHUNK <= REC_LEN) {
    readMic(rec + len);
    len += CHUNK;
  }
  speak(len);
}

void speak(int len) {
  int16_t stereo[CHUNK * 2];
  size_t bytes;
  int peak = 0;
  for (int i = 0; i < len; i += CHUNK) {
    for (int j = 0; j < CHUNK; j++) {
      int16_t s = rec[i + j];
      stereo[2 * j] = stereo[2 * j + 1] = s;
      peak = max(peak, abs((int)s));
    }
    i2s_write(I2S_NUM_1, stereo, sizeof(stereo), &bytes, portMAX_DELAY);
    if ((i / CHUNK) % 4 == 3) {       // redraw every 4 chunks so audio keeps flowing
      face(20, map(min(peak, 12000), 0, 12000, 2, 14));
      peak = 0;
    }
  }
  i2s_zero_dma_buffer(I2S_NUM_1);
  // ignore the mic for a moment so the robot does not hear itself
  unsigned long t = millis();
  while (millis() - t < 400) readMic(NULL);
}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  Wire.setClock(400000);
  oled.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  rec = (int16_t *)malloc(REC_LEN * sizeof(int16_t));
  micInit();
  ampInit();
  face(24, 0);
}

void loop() {
  static unsigned long nextBlink = 3000;
  int level = readMic(NULL);
  if (level > TRIGGER) {
    listenAndRecord();
    face(24, 0);
    return;
  }
  if (millis() > nextBlink) {          // idle blink
    face(3, 0);
    delay(120);
    face(24, 0);
    nextBlink = millis() + random(2000, 5000);
  }
}

#include <SPI.h>

/* ================= KONFIGURASI ================= */
#define NUM_IC          3
#define LATCH_PIN       5

#define SPI_MOSI        23
#define SPI_SCLK        18

#define ANIM_DELAY_MS  150

/* ================= BUFFER DATA ================= */
/*
  sr_data[0] -> IC 1 (dekat ESP32)
  sr_data[1] -> IC 2
  sr_data[2] -> IC 3
*/
uint8_t sr_data[NUM_IC];

/* ================= POLA RING ================= */
// 2 LED aktif, circular
uint8_t ring_pattern[NUM_IC] = {
  0b00000011,
  0b00000011,
  0b00000011
};

/* ================= MODE AKTIF ================= */
enum Mode {
  IC1_ONLY,
  IC2_ONLY,
  IC3_ONLY,
  ALL_IC
};

Mode currentMode = IC1_ONLY;

/* ================= SHIFT REGISTER WRITE ================= */
void shiftRegisterWrite() {
  digitalWrite(LATCH_PIN, LOW);

  // Kirim data dari IC terakhir ke IC pertama
  for (int i = NUM_IC - 1; i >= 0; i--) {
    SPI.transfer(sr_data[i]);
  }

  digitalWrite(LATCH_PIN, HIGH);
}

/* ================= RING UPDATE ================= */
uint8_t ringShift(uint8_t value) {
  uint8_t msb = (value & 0b10000000) >> 7;
  value <<= 1;
  value |= msb;     // Q7 kembali ke Q0
  return value;
}

/* ================= UPDATE BUFFER ================= */
void updateSRBuffer() {
  // Clear semua
  for (int i = 0; i < NUM_IC; i++) {
    sr_data[i] = 0x00;
  }

  switch (currentMode) {
    case IC1_ONLY:
      sr_data[0] = ring_pattern[0];
      break;

    case IC2_ONLY:
      sr_data[1] = ring_pattern[1];
      break;

    case IC3_ONLY:
      sr_data[2] = ring_pattern[2];
      break;

    case ALL_IC:
      for (int i = 0; i < NUM_IC; i++) {
        sr_data[i] = ring_pattern[i];
      }
      break;
  }
}

/* ================= SETUP ================= */
void setup() {
  pinMode(LATCH_PIN, OUTPUT);
  digitalWrite(LATCH_PIN, HIGH);

  SPI.begin(SPI_SCLK, -1, SPI_MOSI, -1);
  SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0));

  // Pastikan semua LED mati saat boot
  for (int i = 0; i < NUM_IC; i++) {
    sr_data[i] = 0x00;
  }
  shiftRegisterWrite();
}

/* ================= LOOP ================= */
void loop() {

  /* === GANTI MODE SETIAP 5 DETIK === */
  static uint32_t lastModeChange = 0;
  static uint8_t modeIndex = 0;

  if (millis() - lastModeChange >= 5000) {
    modeIndex = (modeIndex + 1) % 4;
    currentMode = (Mode)modeIndex;
    lastModeChange = millis();
  }

  /* === UPDATE RING TIAP IC === */
  for (int i = 0; i < NUM_IC; i++) {
    ring_pattern[i] = ringShift(ring_pattern[i]);
  }

  updateSRBuffer();
  shiftRegisterWrite();

  delay(ANIM_DELAY_MS);
}

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
// #include <ArduinoJson.h> // Tidak digunakan dalam versi ini, bisa dihapus jika tidak ada rencana pakai JSON

// --- Definisi Hardware ---
#define I2C_SDA_PIN 21
#define I2C_SCL_PIN 22
#define PCA9548A_ADDRESS 0x70

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 32

#define OLED_ADDRESS 0x3C // Jika OLED tidak muncul, coba ubah ke 0x3D

// UART2 Pins for ESP32 (TX connected to RX of ESP B, RX connected to TX of ESP B)
#define UART2_TX_PIN 17
#define UART2_RX_PIN 16

// Tambahkan marker untuk komunikasi UART
const char START_MARKER = '<';
const char END_MARKER = '>';

// Inisialisasi objek display untuk setiap OLED
// Pastikan pointer ke Wire digunakan (&Wire)
Adafruit_SSD1306 display0(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
Adafruit_SSD1306 display1(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
Adafruit_SSD1306 display2(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
Adafruit_SSD1306 display3(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// --- Definisi Pin Tombol ---
#define BTN_PRES_UP_PIN 13
#define BTN_PRES_DOWN_PIN 14

#define BTN_PUMP_PRIM_ON_PIN 25
#define BTN_PUMP_PRIM_OFF_PIN 26
#define BTN_PUMP_SEC_ON_PIN 27
#define BTN_PUMP_SEC_OFF_PIN 32
#define BTN_PUMP_TER_ON_PIN 33
#define BTN_PUMP_TER_OFF_PIN 4

// --- Definisi Pin Buzzer ---
#define BUZZER_PIN 5

// --- Definisi Pin Motor Driver L298N (Hanya PWM) ---
#define MOTOR_PRIM_PWM_PIN 12
#define MOTOR_SEC_PWM_PIN 18
#define MOTOR_TER_PWM_PIN 19


// --- Variabel Status Sistem ---
float pressurizerPressure = 0.0;
const float PRESS_MIN_ACTIVATE_PUMP1 = 40.0;
const float PRESS_NORMAL_OPERATION = 150.0;
const float PRESS_INCREMENT_FAST = 5.0;
const float PRESS_INCREMENT_SLOW = 1.0;

// Batas peringatan tekanan yang Diperbarui
const float PRESS_WARNING_ABOVE = 160.0; // Peringatan (kedip & buzzer jeda) jika di atas 160 bar
const float PRESS_CRITICAL_HIGH = 180.0; // Kritis (buzzer bunyi panjang) jika di atas 180 bar

// Enum untuk status pompa (nilai numerik akan dikirim via UART)
enum PumpStatus {
  PUMP_OFF = 0,
  PUMP_STARTING = 1,
  PUMP_ON = 2,
  PUMP_SHUTTING_DOWN = 3
};

PumpStatus pumpPrimaryStatus = PUMP_OFF;
PumpStatus pumpSecondaryStatus = PUMP_OFF;
PumpStatus pumpTertiaryStatus = PUMP_OFF;

int pumpPrimaryPWM = 0;
int pumpSecondaryPWM = 0;
int pumpTertiaryPWM = 0;

const int PWM_STARTUP_STEP = 10;
const int PWM_SHUTDOWN_STEP = 1;
const long PWM_UPDATE_INTERVAL = 100; // Interval untuk memperbarui PWM pompa

unsigned long lastPWMUpdateTime = 0;

bool oledBlinkState = false;
unsigned long lastBlinkTime = 0;
const long BLINK_INTERVAL = 250; // Interval kedip OLED/buzzer

const long UART_SEND_INTERVAL = 200; // Interval pengiriman data via UART
unsigned long lastUartSendTime = 0;

// --- Debouncing Tombol dan Mapping Pin ---
const long DEBOUNCE_DELAY = 100;

// Enum untuk mengidentifikasi indeks tombol
enum ButtonIndex {
  BTN_PRES_UP_IDX = 0,
  BTN_PRES_DOWN_IDX,
  BTN_PUMP_PRIM_ON_IDX,
  BTN_PUMP_PRIM_OFF_IDX,
  BTN_PUMP_SEC_ON_IDX,
  BTN_PUMP_SEC_OFF_IDX,
  BTN_PUMP_TER_ON_IDX,
  BTN_PUMP_TER_OFF_IDX,
  NUM_BUTTONS // Ini akan otomatis menjadi jumlah tombol
};

unsigned long lastButtonPressTime[NUM_BUTTONS]; // Array untuk waktu penekanan terakhir setiap tombol
int buttonPinMap[NUM_BUTTONS] = {
  BTN_PRES_UP_PIN, BTN_PRES_DOWN_PIN,
  BTN_PUMP_PRIM_ON_PIN, BTN_PUMP_PRIM_OFF_PIN,
  BTN_PUMP_SEC_ON_PIN, BTN_PUMP_SEC_OFF_PIN,
  BTN_PUMP_TER_ON_PIN, BTN_PUMP_TER_OFF_PIN
};

// --- Fungsi untuk memilih channel pada PCA9548A ---
void pca9548a_select_channel(uint8_t channel) {
  Wire.beginTransmission(PCA9548A_ADDRESS);
  Wire.write(1 << channel);
  Wire.endTransmission();
}

// --- Fungsi untuk memperbarui tampilan OLED ---
void updateOLED(int oledIndex, Adafruit_SSD1306* display, String title, String value1, bool inverted = false) {
  pca9548a_select_channel(oledIndex);
  display->clearDisplay();

  if (inverted) {
    display->setTextColor(SSD1306_BLACK, SSD1306_WHITE);
  } else {
    display->setTextColor(SSD1306_WHITE);
  }

  display->setTextSize(1);
  int16_t x1, y1;
  uint16_t w, h;
  display->getTextBounds(title, 0, 0, &x1, &y1, &w, &h);
  display->setCursor((SCREEN_WIDTH - w) / 2, 0);
  display->println(title);

  display->setTextSize(2);
  display->getTextBounds(value1, 0, 0, &x1, &y1, &w, &h);
  display->setCursor((SCREEN_WIDTH - w) / 2, 16);
  display->println(value1);

  display->display();
}

// --- Fungsi Kontrol Buzzer ---
void controlBuzzer(bool on) {
  digitalWrite(BUZZER_PIN, on ? HIGH : LOW);
}

// --- Fungsi Pembantu untuk mendapatkan String dari PumpStatus Enum ---
String getPumpStatusString(PumpStatus status) {
  switch (status) {
    case PUMP_OFF: return "OFF";
    case PUMP_STARTING: return "STARTING";
    case PUMP_ON: return "ON";
    case PUMP_SHUTTING_DOWN: return "SHUTTING";
    default: return "UNKNOWN";
  }
}

// --- Fungsi untuk mengirim data via UART ---
void sendDataViaUART() {
  Serial2.print(START_MARKER); // Mengirim START_MARKER

  Serial2.print("tekanan:");
  Serial2.print(String(pressurizerPressure, 1)); // Format tekanan dengan 1 angka di belakang koma

  Serial2.print(";pump1:");
  Serial2.print(pumpPrimaryStatus); // Kirim nilai numerik dari enum

  Serial2.print(";pump2:");
  Serial2.print(pumpSecondaryStatus); // Kirim nilai numerik dari enum

  Serial2.print(";pump3:");
  Serial2.print(pumpTertiaryStatus); // Kirim nilai numerik dari enum

  Serial2.print(END_MARKER); // Mengirim END_MARKER
  Serial2.print('\n');       // Tambahkan newline secara eksplisit untuk menandai akhir baris.

  // --- Untuk debugging di Serial Monitor ESP A ---
  Serial.print("Data Sent via UART (Numeric Status): ");
  Serial.print(START_MARKER);
  Serial.print("tekanan:"); Serial.print(String(pressurizerPressure, 1));
  Serial.print(";pump1:"); Serial.print(pumpPrimaryStatus);
  Serial.print(";pump2:"); Serial.print(pumpSecondaryStatus);
  Serial.print(";pump3:"); Serial.print(pumpTertiaryStatus);
  Serial.println(END_MARKER);
}


// --- Fungsi Setup ---
void setup() {
  Serial.begin(115200);
  Serial.println("Starting Reactor Control System (PWR Simulation) - ESP A (Sender)...");

  // Inisialisasi UART2 untuk komunikasi antar-ESP
  Serial2.begin(115200, SERIAL_8N1, UART2_RX_PIN, UART2_TX_PIN);
  Serial.println("UART2 Initialized for inter-ESP communication.");

  // Inisialisasi I2C Bus
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
  Serial.println("I2C Bus initialized.");

  // Scan I2C devices (debugging)
  Serial.println("\n--- Scanning I2C addresses on main bus (GPIO 21, 22) ---");
  byte error, address;
  int nDevices = 0;
  for (address = 1; address < 127; address++ ) {
    Wire.beginTransmission(address);
    error = Wire.endTransmission();
    if (error == 0) {
      Serial.print("I2C device found at address 0x");
      if (address < 16) Serial.print("0");
      Serial.print(address, HEX);
      Serial.println("    !");
      nDevices++;
    } else if (error == 4) {
      Serial.print("Unknow error at address 0x");
      if (address < 16) Serial.print("0");
      Serial.println(address, HEX);
    }
  }
  if (nDevices == 0) {
    Serial.println("No I2C devices found on main bus (0x70 for PCA9548A expected). Check wiring.");
  } else {
    Serial.println("I2C scanning complete for main bus.\n");
  }

  // Inisialisasi pin tombol sebagai INPUT_PULLUP
  for (int i = 0; i < NUM_BUTTONS; i++) {
    pinMode(buttonPinMap[i], INPUT_PULLUP);
    lastButtonPressTime[i] = 0; // Inisialisasi waktu penekanan terakhir
  }

  // Inisialisasi pin buzzer dan motor driver
  pinMode(BUZZER_PIN, OUTPUT);
  controlBuzzer(false); // Pastikan buzzer mati saat startup

  pinMode(MOTOR_PRIM_PWM_PIN, OUTPUT);
  pinMode(MOTOR_SEC_PWM_PIN, OUTPUT);
  pinMode(MOTOR_TER_PWM_PIN, OUTPUT);

  analogWrite(MOTOR_PRIM_PWM_PIN, 0);
  analogWrite(MOTOR_SEC_PWM_PIN, 0);
  analogWrite(MOTOR_TER_PWM_PIN, 0);

  // Inisialisasi OLED display melalui PCA9548A
  Serial.println("\n--- Attempting to initialize OLEDs via PCA9548A ---");
  for (uint8_t i = 0; i < 4; i++) {
    pca9548a_select_channel(i);

    Adafruit_SSD1306* currentDisplay;
    switch (i) {
      case 0: currentDisplay = &display0; break;
      case 1: currentDisplay = &display1; break;
      case 2: currentDisplay = &display2; break;
      case 3: currentDisplay = &display3; break;
      default: continue;
    }

    Serial.print("    > Attempting OLED init on channel ");
    Serial.print(i);
    Serial.print(" (OLED I2C Address 0x"); Serial.print(OLED_ADDRESS, HEX); Serial.println(")");

    if (!currentDisplay->begin(SSD1306_SWITCHCAPVCC, OLED_ADDRESS)) {
      Serial.print("    ERROR: SSD1306 allocation failed for OLED on channel ");
      Serial.println(i);
      Serial.println("       (Possible causes: OLED not connected, incorrect OLED address, or power issue)");
    } else {
      Serial.print("    OLED on channel ");
      Serial.print(i);
      Serial.println(" initialized successfully!");

      currentDisplay->clearDisplay();
      currentDisplay->setTextSize(2);
      currentDisplay->setTextColor(SSD1306_WHITE);

      int16_t x1, y1;
      uint16_t w, h;
      String welcomeText = "PLTN";
      currentDisplay->getTextBounds(welcomeText, 0, 0, &x1, &y1, &w, &h);
      currentDisplay->setCursor((SCREEN_WIDTH - w) / 2, (SCREEN_HEIGHT - h) / 2);
      currentDisplay->println(welcomeText);
      currentDisplay->display();

      delay(1500);
      currentDisplay->clearDisplay();
    }
  }
  Serial.println("\n--- OLED initialization attempts complete ---");
  Serial.println("If some OLEDs failed, re-check their wiring and power.");
  Serial.println("If no OLEDs work, try changing OLED_ADDRESS to 0x3D and re-upload.");

  // ========== PERUBAHAN DIMULAI DI SINI (setup) ==========
  // Update initial OLED displays sesuai permintaan
  // display 0: pump tersier
  // display 1: pump second
  // display 2: presurizer
  // display 3: pump primer
  updateOLED(0, &display0, "Pump Tertiary", getPumpStatusString(pumpTertiaryStatus));
  updateOLED(1, &display1, "Pump Secondary", getPumpStatusString(pumpSecondaryStatus));
  updateOLED(2, &display2, "Pressurizer", String(pressurizerPressure, 1) + " bar");
  updateOLED(3, &display3, "Pump Primary", getPumpStatusString(pumpPrimaryStatus));
  // ========== PERUBAHAN SELESAI DI SINI (setup) ==========
}

// --- Fungsi Loop ---
void loop() {
  unsigned long currentTime = millis();

  // Kirim data via UART secara periodik
  if (currentTime - lastUartSendTime >= UART_SEND_INTERVAL) {
    lastUartSendTime = currentTime;
    sendDataViaUART();
  }

  // --- Pembacaan Tombol Pressurizer (UP) ---
  if (digitalRead(BTN_PRES_UP_PIN) == LOW) {
    if (currentTime - lastButtonPressTime[BTN_PRES_UP_IDX] > DEBOUNCE_DELAY) {
      // Jika tombol ditahan lebih dari 500ms, gunakan INCREMENT_FAST
      if (lastButtonPressTime[BTN_PRES_UP_IDX] == 0 || (currentTime - lastButtonPressTime[BTN_PRES_UP_IDX] > 500)) {
        pressurizerPressure += PRESS_INCREMENT_FAST;
      } else {
        pressurizerPressure += PRESS_INCREMENT_SLOW;
      }
      if (pressurizerPressure > PRESS_CRITICAL_HIGH + 10.0) pressurizerPressure = PRESS_CRITICAL_HIGH + 10.0; // Batas atas
      // ========== PERUBAHAN DI SINI: Update OLED Pressurizer di channel 2 ==========
      updateOLED(2, &display2, "Pressurizer", String(pressurizerPressure, 1) + " bar"); // Update OLED saat tombol ditekan
      Serial.print("Pressurizer Pressure: ");
      Serial.println(pressurizerPressure, 1);
      lastButtonPressTime[BTN_PRES_UP_IDX] = currentTime; // Update waktu penekanan
    }
  } else {
    // Reset waktu penekanan saat tombol dilepas agar bisa mendeteksi penekanan singkat berikutnya
    if (lastButtonPressTime[BTN_PRES_UP_IDX] != 0 && (currentTime - lastButtonPressTime[BTN_PRES_UP_IDX] > DEBOUNCE_DELAY)) {
        lastButtonPressTime[BTN_PRES_UP_IDX] = 0;
    }
  }

  // --- Pembacaan Tombol Pressurizer (DOWN) ---
  if (digitalRead(BTN_PRES_DOWN_PIN) == LOW) {
    if (currentTime - lastButtonPressTime[BTN_PRES_DOWN_IDX] > DEBOUNCE_DELAY) {
      // Jika tombol ditahan lebih dari 500ms, gunakan INCREMENT_FAST
      if (lastButtonPressTime[BTN_PRES_DOWN_IDX] == 0 || (currentTime - lastButtonPressTime[BTN_PRES_DOWN_IDX] > 500)) {
        pressurizerPressure -= PRESS_INCREMENT_FAST;
      } else {
        pressurizerPressure -= PRESS_INCREMENT_SLOW;
      }
      if (pressurizerPressure < 0.0) pressurizerPressure = 0.0; // Batas bawah
      // ========== PERUBAHAN DI SINI: Update OLED Pressurizer di channel 2 ==========
      updateOLED(2, &display2, "Pressurizer", String(pressurizerPressure, 1) + " bar"); // Update OLED
      Serial.print("Pressurizer Pressure: ");
      Serial.println(pressurizerPressure, 1);
      lastButtonPressTime[BTN_PRES_DOWN_IDX] = currentTime; // Update waktu penekanan
    }
  } else {
    // Reset waktu penekanan saat tombol dilepas
    if (lastButtonPressTime[BTN_PRES_DOWN_IDX] != 0 && (currentTime - lastButtonPressTime[BTN_PRES_DOWN_IDX] > DEBOUNCE_DELAY)) {
      lastButtonPressTime[BTN_PRES_DOWN_IDX] = 0;
    }
  }

  // --- Logika Kontrol Buzzer dan Kedipan OLED Pressurizer ---
  bool warningActive = false;
  bool criticalActive = false;

  if (pressurizerPressure > PRESS_WARNING_ABOVE && pressurizerPressure <= PRESS_CRITICAL_HIGH) {
    warningActive = true;
  }
  if (pressurizerPressure > PRESS_CRITICAL_HIGH) {
    criticalActive = true;
  }

  if (criticalActive) {
    controlBuzzer(true); // Buzzer ON terus
    if (currentTime - lastBlinkTime >= BLINK_INTERVAL) {
      oledBlinkState = !oledBlinkState; // OLED kedip
      lastBlinkTime = currentTime;
    }
    // ========== PERUBAHAN DI SINI: Update OLED Pressurizer di channel 2 ==========
    updateOLED(2, &display2, "CRITICAL PRESSURE!", String(pressurizerPressure, 1) + " bar", oledBlinkState);
  } else if (warningActive) {
    if (currentTime - lastBlinkTime >= BLINK_INTERVAL) {
      oledBlinkState = !oledBlinkState; // OLED dan Buzzer kedip
      controlBuzzer(oledBlinkState);
      lastBlinkTime = currentTime;
    }
    // ========== PERUBAHAN DI SINI: Update OLED Pressurizer di channel 2 ==========
    updateOLED(2, &display2, "PRESSURE WARNING!", String(pressurizerPressure, 1) + " bar", oledBlinkState);
  } else {
    controlBuzzer(false); // Buzzer OFF
    if (oledBlinkState) {
      oledBlinkState = false; // Pastikan OLED tidak inverted jika tidak ada peringatan
    }
    // ========== PERUBAHAN DI SINI: Update OLED Pressurizer di channel 2 ==========
    updateOLED(2, &display2, "Pressurizer", String(pressurizerPressure, 1) + " bar");
  }


  // --- Logika Kontrol Pompa (Perbarui PWM dan Status) ---
  if (currentTime - lastPWMUpdateTime >= PWM_UPDATE_INTERVAL) {
    lastPWMUpdateTime = currentTime;

    // Pompa Primer
    if (pumpPrimaryStatus == PUMP_STARTING) {
      pumpPrimaryPWM += PWM_STARTUP_STEP;
      if (pumpPrimaryPWM >= 255) {
        pumpPrimaryPWM = 255;
        pumpPrimaryStatus = PUMP_ON;
        Serial.println("Pump Primary: ON (Full Speed)");
      }
    } else if (pumpPrimaryStatus == PUMP_SHUTTING_DOWN) {
      pumpPrimaryPWM -= PWM_SHUTDOWN_STEP;
      if (pumpPrimaryPWM <= 0) {
        pumpPrimaryPWM = 0;
        pumpPrimaryStatus = PUMP_OFF;
        Serial.println("Pump Primary: OFF");
      }
    }
    analogWrite(MOTOR_PRIM_PWM_PIN, pumpPrimaryPWM);
    // ========== PERUBAHAN DI SINI: Update OLED Pompa Primer di channel 3 ==========
    updateOLED(3, &display3, "Pump Primary", getPumpStatusString(pumpPrimaryStatus));


    // Pompa Sekunder
    if (pumpSecondaryStatus == PUMP_STARTING) {
      pumpSecondaryPWM += PWM_STARTUP_STEP;
      if (pumpSecondaryPWM >= 255) {
        pumpSecondaryPWM = 255;
        pumpSecondaryStatus = PUMP_ON;
        Serial.println("Pump Secondary: ON (Full Speed)");
      }
    } else if (pumpSecondaryStatus == PUMP_SHUTTING_DOWN) {
      pumpSecondaryPWM -= PWM_SHUTDOWN_STEP;
      if (pumpSecondaryPWM <= 0) {
        pumpSecondaryPWM = 0;
        pumpSecondaryStatus = PUMP_OFF;
        Serial.println("Pump Secondary: OFF");
      }
    }
    analogWrite(MOTOR_SEC_PWM_PIN, pumpSecondaryPWM);
    // ========== PERUBAHAN DI SINI: Update OLED Pompa Sekunder di channel 1 ==========
    updateOLED(1, &display1, "Pump Secondary", getPumpStatusString(pumpSecondaryStatus));


    // Pompa Tersier
    if (pumpTertiaryStatus == PUMP_STARTING) {
      pumpTertiaryPWM += PWM_STARTUP_STEP;
      if (pumpTertiaryPWM >= 255) {
        pumpTertiaryPWM = 255;
        pumpTertiaryStatus = PUMP_ON;
        Serial.println("Pump Tertiary: ON (Full Speed)");
      }
    } else if (pumpTertiaryStatus == PUMP_SHUTTING_DOWN) {
      pumpTertiaryPWM -= PWM_SHUTDOWN_STEP;
      if (pumpTertiaryPWM <= 0) {
        pumpTertiaryPWM = 0;
        pumpTertiaryStatus = PUMP_OFF;
        Serial.println("Pump Tertiary: OFF");
      }
    }
    analogWrite(MOTOR_TER_PWM_PIN, pumpTertiaryPWM);
    // ========== PERUBAHAN DI SINI: Update OLED Pompa Tersier di channel 0 ==========
    updateOLED(0, &display0, "Pump Tertiary", getPumpStatusString(pumpTertiaryStatus));
  }


  // --- Pembacaan Tombol Pompa Primer ON ---
  if (digitalRead(BTN_PUMP_PRIM_ON_PIN) == LOW) {
    if (currentTime - lastButtonPressTime[BTN_PUMP_PRIM_ON_IDX] > DEBOUNCE_DELAY) {
      if (pumpPrimaryStatus == PUMP_OFF || pumpPrimaryStatus == PUMP_SHUTTING_DOWN) {
        if (pressurizerPressure >= PRESS_MIN_ACTIVATE_PUMP1) {
          pumpPrimaryStatus = PUMP_STARTING;
          Serial.println("Initiating Pump Primary Startup...");
        } else {
          Serial.println("ERROR: Pressurizer pressure too low to start Pump Primary! (Min " + String(PRESS_MIN_ACTIVATE_PUMP1) + " bar)");
        }
      }
      lastButtonPressTime[BTN_PUMP_PRIM_ON_IDX] = currentTime;
    }
  } else {
    if (lastButtonPressTime[BTN_PUMP_PRIM_ON_IDX] != 0 && (currentTime - lastButtonPressTime[BTN_PUMP_PRIM_ON_IDX] > DEBOUNCE_DELAY)) {
      lastButtonPressTime[BTN_PUMP_PRIM_ON_IDX] = 0;
    }
  }

  // --- Pembacaan Tombol Pompa Primer OFF ---
  if (digitalRead(BTN_PUMP_PRIM_OFF_PIN) == LOW) {
    if (currentTime - lastButtonPressTime[BTN_PUMP_PRIM_OFF_IDX] > DEBOUNCE_DELAY) {
      if (pumpPrimaryStatus == PUMP_ON || pumpPrimaryStatus == PUMP_STARTING) {
        pumpPrimaryStatus = PUMP_SHUTTING_DOWN;
        Serial.println("Initiating Pump Primary Shutdown...");
      }
      lastButtonPressTime[BTN_PUMP_PRIM_OFF_IDX] = currentTime;
    }
  } else {
    if (lastButtonPressTime[BTN_PUMP_PRIM_OFF_IDX] != 0 && (currentTime - lastButtonPressTime[BTN_PUMP_PRIM_OFF_IDX] > DEBOUNCE_DELAY)) {
      lastButtonPressTime[BTN_PUMP_PRIM_OFF_IDX] = 0;
    }
  }

  // --- Pembacaan Tombol Pompa Sekunder ON ---
  if (digitalRead(BTN_PUMP_SEC_ON_PIN) == LOW) {
    if (currentTime - lastButtonPressTime[BTN_PUMP_SEC_ON_IDX] > DEBOUNCE_DELAY) {
      if (pumpSecondaryStatus == PUMP_OFF || pumpSecondaryStatus == PUMP_SHUTTING_DOWN) {
        pumpSecondaryStatus = PUMP_STARTING;
        Serial.println("Initiating Pump Secondary Startup...");
      }
      lastButtonPressTime[BTN_PUMP_SEC_ON_IDX] = currentTime;
    }
  } else {
    if (lastButtonPressTime[BTN_PUMP_SEC_ON_IDX] != 0 && (currentTime - lastButtonPressTime[BTN_PUMP_SEC_ON_IDX] > DEBOUNCE_DELAY)) {
      lastButtonPressTime[BTN_PUMP_SEC_ON_IDX] = 0;
    }
  }

  // --- Pembacaan Tombol Pompa Sekunder OFF ---
  if (digitalRead(BTN_PUMP_SEC_OFF_PIN) == LOW) {
    if (currentTime - lastButtonPressTime[BTN_PUMP_SEC_OFF_IDX] > DEBOUNCE_DELAY) {
      if (pumpSecondaryStatus == PUMP_ON || pumpSecondaryStatus == PUMP_STARTING) {
        pumpSecondaryStatus = PUMP_SHUTTING_DOWN;
        Serial.println("Initiating Pump Secondary Shutdown...");
      }
      lastButtonPressTime[BTN_PUMP_SEC_OFF_IDX] = currentTime;
    }
  } else {
    if (lastButtonPressTime[BTN_PUMP_SEC_OFF_IDX] != 0 && (currentTime - lastButtonPressTime[BTN_PUMP_SEC_OFF_IDX] > DEBOUNCE_DELAY)) {
      lastButtonPressTime[BTN_PUMP_SEC_OFF_IDX] = 0;
    }
  }

  // --- Pembacaan Tombol Pompa Tersier ON ---
  if (digitalRead(BTN_PUMP_TER_ON_PIN) == LOW) {
    if (currentTime - lastButtonPressTime[BTN_PUMP_TER_ON_IDX] > DEBOUNCE_DELAY) {
      if (pumpTertiaryStatus == PUMP_OFF || pumpTertiaryStatus == PUMP_SHUTTING_DOWN) {
        pumpTertiaryStatus = PUMP_STARTING;
        Serial.println("Initiating Pump Tertiary Startup...");
      }
      lastButtonPressTime[BTN_PUMP_TER_ON_IDX] = currentTime;
    }
  } else {
    if (lastButtonPressTime[BTN_PUMP_TER_ON_IDX] != 0 && (currentTime - lastButtonPressTime[BTN_PUMP_TER_ON_IDX] > DEBOUNCE_DELAY)) {
      lastButtonPressTime[BTN_PUMP_TER_ON_IDX] = 0;
    }
  }

  // --- Pembacaan Tombol Pompa Tersier OFF ---
  if (digitalRead(BTN_PUMP_TER_OFF_PIN) == LOW) {
    if (currentTime - lastButtonPressTime[BTN_PUMP_TER_OFF_IDX] > DEBOUNCE_DELAY) {
      if (pumpTertiaryStatus == PUMP_ON || pumpTertiaryStatus == PUMP_STARTING) {
        pumpTertiaryStatus = PUMP_SHUTTING_DOWN;
        Serial.println("Initiating Pump Tertiary Shutdown...");
      }
      lastButtonPressTime[BTN_PUMP_TER_OFF_IDX] = currentTime;
    }
  } else {
    if (lastButtonPressTime[BTN_PUMP_TER_OFF_IDX] != 0 && (currentTime - lastButtonPressTime[BTN_PUMP_TER_OFF_IDX] > DEBOUNCE_DELAY)) {
      lastButtonPressTime[BTN_PUMP_TER_OFF_IDX] = 0;
    }
  }

  // --- Cek Kondisi Penuh ---
  if (pumpPrimaryStatus == PUMP_ON && pumpSecondaryStatus == PUMP_ON &&
      pumpTertiaryStatus == PUMP_ON && pressurizerPressure >= PRESS_NORMAL_OPERATION) {
    // Pesan ini hanya akan muncul sekali saat kondisi terpenuhi
    static bool systemFullyOperational = false;
    if (!systemFullyOperational) {
      Serial.println("SYSTEM STATUS: All Pumps ON and Pressurizer at Normal Operation Pressure (150 bar).");
      systemFullyOperational = true;
    }
  } else {
    // Reset flag jika kondisi tidak lagi terpenuhi
    static bool systemFullyOperational = false; // Pindahkan deklarasi ke sini agar tidak konflik
    if (systemFullyOperational) {
        systemFullyOperational = false;
        Serial.println("SYSTEM STATUS: Not all conditions met for full operation.");
    }
  }

  delay(5); // Delay kecil untuk stabilitas loop
}
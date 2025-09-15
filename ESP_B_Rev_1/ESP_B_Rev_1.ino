#include <ESP32Servo.h> // Library Servo yang kompatibel dengan ESP32
#include <Wire.h>
#include <Adafruit_SSD1306.h>
#include <HardwareSerial.h> // Diperlukan untuk Serial2 pada ESP32

// --- Definisi Global Hardware ---
// --- Definisi UART untuk Komunikasi Antar-ESP ---
// RX_PIN ESP-B (pin 16) terhubung ke TX_PIN ESP-A (pin 17)
// TX_PIN ESP-B (pin 17) terhubung ke RX_PIN ESP-A (pin 16) - jika komunikasi dua arah
#define UART2_TX_PIN 17
#define UART2_RX_PIN 16

// --- Definisi Hardware I2C (untuk OLED dan PCA9548A) ---
#define I2C_SDA_PIN_B 21 // Pin SDA untuk I2C di ESP-B
#define I2C_SCL_PIN_B 22 // Pin SCL untuk I2C di ESP-B
#define PCA9548A_ADDRESS_B 0x70 // Alamat PCA9548A

// --- OLED config ---
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 32 // Untuk OLED 128x32
#define OLED_091_WIDTH 96
#define OLED_091_HEIGHT 32 // Untuk OLED 0.91 inci (96x32)
#define OLED_ADDRESS 0x3C // Alamat default OLED

// --- Definisi Pin Motor Servo Batang Kendali ---
#define ROD1_SERVO_PIN 13 // Sesuaikan pin PWM ESP32
#define ROD2_SERVO_PIN 14 // Sesuaikan pin PWM ESP32
#define ROD3_SERVO_PIN 15 // Sesuaikan pin PWM ESP32

// --- Definisi Pin Tombol (SUDAH DIPERBAIKI KONFLIK DENGAN UART2) ---
// Pin yang umum digunakan untuk tombol di ESP32. HATI-HATI dengan GPIO0,2,4,5,12
// karena punya fungsi booting khusus, tapi biasanya aman setelah booting.
// Jika ada masalah boot, ganti pin ini.
const int btnUp1 = 0;   // GPIO0
const int btnDown1 = 5; // GPIO2
const int btnUp2 = 4;   // GPIO4
const int btnDown2 = 2; // GPIO5
const int btnUp3 = 12;  // GPIO12

// Pin yang diubah untuk menghindari konflik UART2 (16 dan 17)
const int btnDown3 = 23;      // Pindah dari GPIO16 (UART2_RX_PIN) ke GPIO23
const int btnEmergency = 19; // Pindah dari GPIO17 (UART2_TX_PIN) ke GPIO19

const int buzzerPin = 18; // GPIO18

// --- Definisi Marker Komunikasi UART ---
const char START_MARKER = '<';
const char END_MARKER = '>';


// --- Inisialisasi Objek Global ---
// Inisialisasi objek display untuk setiap OLED di ESP-B
Adafruit_SSD1306 oled1(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1); // Channel 0 (Rod 1)
Adafruit_SSD1306 oled2(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1); // Channel 1 (Rod 2)
Adafruit_SSD1306 oled3(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1); // Channel 2 (Rod 3)
Adafruit_SSD1306 oledKwThermal(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1); // Channel 3 (KwThermal)

// Array untuk menyimpan status inisialisasi setiap OLED
bool oledInitialized[4] = {false, false, false, false};

// Objek Servo
Servo servo1, servo2, servo3;

// --- Variabel Global Status Sistem ---
int pos1 = 0, pos2 = 0, pos3 = 0; // Posisi batang kendali dalam persentase (0-100%)
const int stepSize = 1; // Langkah perubahan posisi per tombol tekan

// Emergency & Buzzer
bool emergencyTriggered = false;
bool buzzerActive = false;
unsigned long buzzerStartTime = 0;
const unsigned long buzzerDuration = 1000; // Durasi buzzer untuk emergency (1 detik)

// Debounce Tombol & Interval Update
unsigned long lastMoveTime = 0;
const unsigned long initialMoveDelay = 0; // Delay awal setelah tombol pertama ditekan
const unsigned long continuousMoveDelay = 150; // Delay untuk gerakan berkelanjutan saat ditahan

unsigned long lastOLEDUpdate = 0; // Interval update OLED
const unsigned long OLEDRate = 200; // Update OLED setiap 200ms

// Variabel untuk menyimpan status tombol sebelumnya (untuk debouncing yang lebih baik)
bool prevBtnUp1State = HIGH;
bool prevBtnDown1State = HIGH;
bool prevBtnUp2State = HIGH;
bool prevBtnDown2State = HIGH;
bool prevBtnUp3State = HIGH;
bool prevBtnDown3State = HIGH;
bool prevBtnEmergencyState = HIGH; // Tambahkan untuk tombol emergency

const int MAX_DATA_LENGTH = 100; // Ukuran maksimum pesan yang diharapkan
char receivedChars[MAX_DATA_LENGTH];
boolean newData = false; // Flag untuk menandai data baru telah diterima

// Variabel untuk Menyimpan Data yang Telah di-Parsing dari ESP-A
float receivedPressure = 0.0;
int receivedPumpPrimaryStatus = 0; // 0=OFF, 1=STARTING, 2=ON, 3=SHUTTING_DOWN
int receivedPumpSecondaryStatus = 0;
int receivedPumpTertiaryStatus = 0;

// Enum yang SAMA PERSIS dengan di ESP-A untuk memetakan nilai numerik status pompa
enum PumpStatus {
  PUMP_OFF = 0,
  PUMP_STARTING = 1,
  PUMP_ON = 2,
  PUMP_SHUTTING_DOWN = 3
};

// --- Variabel untuk Perhitungan KwTermal ---
float kwThermal = 0.0;
// Daya termal maksimal saat semua batang naik penuh (100%)
const float MAX_KW_THERMAL_VALUE = 2000.0;
// Daya termal minimal saat semua batang turun penuh (0%)
const float MIN_KW_THERMAL_VALUE = 0.0; // Diatur ke 0.0 untuk memulai dari 0 kW

// Kondisi Aktivasi Batang Kendali
const float MIN_PRESSURE_TO_OPERATE_RODS = 130.0; // Minimal tekanan untuk mengoperasikan batang kendali

// Pengaturan Interval Pengiriman Data ke ESP-C
unsigned long lastUartSendToC = 0;
const long UART_SEND_TO_C_INTERVAL = 250; // Kirim data ke ESP-C setiap 250ms


// --- Fungsi Pembantu (Prototipe) ---
void selectMultiplexerChannel(uint8_t channel);
void updateOLED_B(int oledChannel, Adafruit_SSD1306* display, String title, String value1);
String getPumpStatusString(PumpStatus status);
void recvDataFromESP_A();
void parseDataFromESP_A();
void setServoPosition(Servo& servo, int positionPercent);
float calculateKwThermal();
void sendDataToESP_C();


// --- Fungsi untuk memilih channel pada PCA9548A ---
void selectMultiplexerChannel(uint8_t channel) {
  if (channel > 7) return; // PCA9548A memiliki 8 channel (0-7)
  Wire.beginTransmission(PCA9548A_ADDRESS_B);
  Wire.write(1 << channel);
  Wire.endTransmission();
}

// --- Fungsi untuk memperbarui tampilan OLED ---
void updateOLED_B(int oledChannel, Adafruit_SSD1306* display, String title, String value1) {
  // Hanya update jika OLED berhasil diinisialisasi
  if (oledChannel >= 0 && oledChannel < 4 && oledInitialized[oledChannel]) {
    selectMultiplexerChannel(oledChannel);
    display->clearDisplay();
    display->setTextColor(SSD1306_WHITE);

    // Teks judul (Rod Pos / KwThermal)
    display->setTextSize(1);
    display->setCursor(0, 0);
    display->print(title);

    // Nilai posisi/KwThermal
    display->setTextSize(2);
    int16_t x1, y1; uint16_t w1, h1;
    display->getTextBounds(value1, 0, 0, &x1, &y1, &w1, &h1);
    // Atur posisi Y agar nilai di tengah atau di bawah
    display->setCursor((display->width() - w1) / 2, (display->height() - h1) / 2);
    display->print(value1);
    display->display();
  }
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

// --- Fungsi untuk Menerima Data via UART dari ESP-A ---
void recvDataFromESP_A() {
  static boolean recvInProgress = false;
  static int ndx = 0;
  char rc;

  while (Serial2.available() > 0 && newData == false) {
    rc = Serial2.read();

    if (recvInProgress == true) {
      if (rc != END_MARKER) {
        if (ndx < MAX_DATA_LENGTH - 1) {
          receivedChars[ndx] = rc;
          ndx++;
        } else {
          Serial.println("Error: Buffer overflow. Resetting receiver.");
          recvInProgress = false;
          ndx = 0;
        }
      } else {
        receivedChars[ndx] = '\0';
        recvInProgress = false;
        ndx = 0;
        newData = true;
      }
    } else if (rc == START_MARKER) {
      recvInProgress = true;
    }
  }
}

// --- Fungsi untuk Mem-parsing Data yang Diterima dari ESP-A ---
void parseDataFromESP_A() {
  if (newData == true) {
    Serial.print("Received Raw Data from ESP-A: ");
    Serial.println(receivedChars);

    char tempChars[MAX_DATA_LENGTH];
    strcpy(tempChars, receivedChars);

    char *token;
    token = strtok(tempChars, ";");

    while (token != NULL) {
      String dataPair = String(token);
      int colonIndex = dataPair.indexOf(':');

      if (colonIndex != -1) {
        String key = dataPair.substring(0, colonIndex);
        String value = dataPair.substring(colonIndex + 1);

        key.trim();
        value.trim();

        if (key == "tekanan") {
          receivedPressure = value.toFloat();
        } else if (key == "pump1") {
          receivedPumpPrimaryStatus = value.toInt();
        } else if (key == "pump2") {
          receivedPumpSecondaryStatus = value.toInt();
        } else if (key == "pump3") {
          receivedPumpTertiaryStatus = value.toInt();
        }
      }
      token = strtok(NULL, ";");
    }

    Serial.println("\n--- Parsed Data from ESP-A ---");
    Serial.print("Pressure: "); Serial.print(receivedPressure, 1); Serial.println(" bar");
    Serial.print("Pump Primary Status: "); Serial.println(getPumpStatusString((PumpStatus)receivedPumpPrimaryStatus));
    Serial.print("Pump Secondary Status: "); Serial.println(getPumpStatusString((PumpStatus)receivedPumpSecondaryStatus));
    Serial.print("Pump Tertiary Status: "); Serial.println(getPumpStatusString((PumpStatus)receivedPumpTertiaryStatus));
    Serial.println("------------------------------\n");

    newData = false; // Reset flag setelah data di-parsing
  }
}

// --- Fungsi untuk Mengatur Posisi Servo Berdasarkan Persentase ---
void setServoPosition(Servo& servo, int positionPercent) {
  // Map posisi persentase (0-100) ke sudut servo (0-180 derajat)
  int angle = map(positionPercent, 0, 100, 0, 180);
  servo.write(angle);
}

// --- Fungsi untuk Menghitung KwTermal (Daya Termal) ---
float calculateKwThermal() {
  // Asumsi: Daya termal 0 kW saat batang di 0% (turun penuh),
  // dan mencapai MAX_KW_THERMAL_VALUE saat batang di 100% (naik penuh).
  // Artinya, daya termal MENINGKAT saat batang kendali naik (posisi% meningkat).

  // Kontribusi masing-masing batang kendali terhadap daya termal
  // Ketika batang di 0%, kontribusinya 0
  // Ketika batang di 100%, kontribusinya 1/3 dari MAX_KW_THERMAL_VALUE
  float rod1Contribution = map(pos1, 0, 100, MIN_KW_THERMAL_VALUE / 3.0, MAX_KW_THERMAL_VALUE / 3.0);
  float rod2Contribution = map(pos2, 0, 100, MIN_KW_THERMAL_VALUE / 3.0, MAX_KW_THERMAL_VALUE / 3.0);
  float rod3Contribution = map(pos3, 0, 100, MIN_KW_THERMAL_VALUE / 3.0, MAX_KW_THERMAL_VALUE / 3.0);

  // Total KwTermal adalah jumlah kontribusi ketiga batang kendali
  kwThermal = rod1Contribution + rod2Contribution + rod3Contribution;

  // Pastikan nilai tidak di luar batas yang diinginkan
  if (kwThermal < MIN_KW_THERMAL_VALUE) kwThermal = MIN_KW_THERMAL_VALUE;
  if (kwThermal > MAX_KW_THERMAL_VALUE) kwThermal = MAX_KW_THERMAL_VALUE;

  return kwThermal;
}

// --- Fungsi untuk Mengirim Data Posisi Batang Kendali ke ESP-C via UART ---
void sendDataToESP_C() {
  // Format: <rod1:XX;rod2:YY;rod3:ZZ>\n
  Serial1.print(START_MARKER);              // DIUBAH
  Serial1.print("rod1:"); Serial1.print(pos1); // DIUBAH
  Serial1.print(";rod2:"); Serial1.print(pos2); // DIUBAH
  Serial1.print(";rod3:"); Serial1.print(pos3); // DIUBAH
  Serial1.print(END_MARKER);                // DIUBAH
  Serial1.print('\n');                      // DIUBAH

  // Untuk debugging di Serial Monitor ESP-B (ini tetap)
  Serial.print("Data Sent to ESP-C (via UART1): "); // Pesan debug bisa diperjelas
  Serial.print(START_MARKER);
  Serial.print("rod1:"); Serial.print(pos1);
  Serial.print(";rod2:"); Serial.print(pos2);
  Serial.print(";rod3:"); Serial.print(pos3);
  Serial.println(END_MARKER);
}


// --- Setup ESP-B ---
void setup() {
  Serial.begin(115200); // Serial Monitor untuk debugging (pastikan baud rate sama dengan ESP A)
  Serial.println("Starting Reactor Control System - ESP B (Control Rods)...");

  // Inisialisasi UART2 untuk komunikasi DARI ESP-A
  Serial2.begin(115200, SERIAL_8N1, UART2_RX_PIN, UART2_TX_PIN);
  Serial.println("UART2 Initialized to RECEIVE data from ESP-A.");
  
  // Inisialisasi UART1 untuk komunikasi KE ESP-C menggunakan pin yang aman
  // TX1 (mengirim) diatur ke GPIO 25. RX1 diatur ke GPIO 26.
  Serial1.begin(115200, SERIAL_8N1, 26, 25); // (baud, config, RX, TX)
  Serial.println("UART1 Initialized on safe pins (TX=25, RX=26) to SEND data to ESP-C.");

  // Inisialisasi Servo
  servo1.attach(ROD1_SERVO_PIN); // Gunakan definisi pin
  servo2.attach(ROD2_SERVO_PIN); // Gunakan definisi pin
  servo3.attach(ROD3_SERVO_PIN); // Gunakan definisi pin

  // Set posisi awal servo (turun penuh / 0%)
  setServoPosition(servo1, pos1);
  setServoPosition(servo2, pos2);
  setServoPosition(servo3, pos3);

  // Inisialisasi pin tombol sebagai INPUT_PULLUP
  pinMode(btnUp1, INPUT_PULLUP);
  pinMode(btnDown1, INPUT_PULLUP);
  pinMode(btnUp2, INPUT_PULLUP);
  pinMode(btnDown2, INPUT_PULLUP);
  pinMode(btnUp3, INPUT_PULLUP);
  pinMode(btnDown3, INPUT_PULLUP);
  pinMode(btnEmergency, INPUT_PULLUP);
  pinMode(buzzerPin, OUTPUT);
  digitalWrite(buzzerPin, LOW); // Pastikan buzzer mati saat startup

  Wire.begin(I2C_SDA_PIN_B, I2C_SCL_PIN_B); // Inisialisasi Wire dengan pin yang ditentukan
  Serial.println("I2C Bus initialized.");

  // Inisialisasi OLED display melalui PCA9548A
  Serial.println("\n--- Attempting to initialize OLEDs via PCA9548A ---");
  // Array untuk semua objek OLED
  Adafruit_SSD1306* displays[] = {&oled1, &oled2, &oled3, &oledKwThermal};
  // Array untuk judul awal OLED
  String oledTitles[] = {"PLTN", "PLTN", "PLTN", "PLTN"};

  for (uint8_t i = 0; i < 4; i++) {
    selectMultiplexerChannel(i);
    Serial.print("     > Attempting OLED init on channel "); Serial.print(i);
    Serial.print(" (OLED I2C Address 0x"); Serial.print(OLED_ADDRESS, HEX); Serial.println(")");

    if (!displays[i]->begin(SSD1306_SWITCHCAPVCC, OLED_ADDRESS)) {
      Serial.print("     ERROR: SSD1306 allocation failed for OLED on channel "); Serial.println(i);
      Serial.println("        (Check wiring, address, or power)");
      oledInitialized[i] = false;
    } else {
      Serial.print("     OLED on channel "); Serial.print(i); Serial.println(" initialized successfully!");
      oledInitialized[i] = true;

      // Tampilkan pesan startup di OLED
      displays[i]->clearDisplay();
      displays[i]->setTextSize(2);
      displays[i]->setTextColor(SSD1306_WHITE);
      int16_t x1, y1; uint16_t w, h;
      displays[i]->getTextBounds(oledTitles[i], 0, 0, &x1, &y1, &w, &h);
      displays[i]->setCursor((displays[i]->width() - w) / 2, (displays[i]->height() - h) / 2);
      displays[i]->println(oledTitles[i]);
      displays[i]->display();
      delay(500);
      displays[i]->clearDisplay();
    }
  }
  Serial.println("\n--- OLED initialization attempts complete ---");

  // Perbarui tampilan OLED awal dengan posisi default dan KwThermal
  updateOLED_B(0, &oled1, "Rod 1 Pos", String(pos1) + "%");
  updateOLED_B(1, &oled2, "Rod 2 Pos", String(pos2) + "%");
  updateOLED_B(2, &oled3, "Rod 3 Pos", String(pos3) + "%");
  updateOLED_B(3, &oledKwThermal, "KwThermal", String(calculateKwThermal(), 2) + " kW");
}

// --- Loop ESP-B ---
void loop() {
  unsigned long currentTime = millis();

  // --- Menerima dan Mem-parsing Data dari ESP-A ---
  recvDataFromESP_A();
  if (newData == true) {
    parseDataFromESP_A();
    // Setelah parsing, newData akan menjadi false di dalam parseDataFromESP_A()
  }

  // --- Cek Kondisi Aktivasi Batang Kendali ---
  // Batang kendali bisa dioperasikan jika semua pompa ON dan tekanan di atas 130 bar
  bool rodsCanBeOperated = false;
  if (receivedPumpPrimaryStatus == PUMP_ON &&
      receivedPumpSecondaryStatus == PUMP_ON &&
      receivedPumpTertiaryStatus == PUMP_ON &&
      receivedPressure >= MIN_PRESSURE_TO_OPERATE_RODS) {
    rodsCanBeOperated = true;
  }

  // --- Tombol Emergency ---
  bool currentBtnEmergencyState = digitalRead(btnEmergency);
  if (currentBtnEmergencyState == LOW && prevBtnEmergencyState == HIGH) { // Tombol baru ditekan
    if (!emergencyTriggered) { // Hanya picu jika belum dalam mode emergency
      pos1 = pos2 = pos3 = 0; // Turunkan semua batang kendali
      setServoPosition(servo1, pos1);
      setServoPosition(servo2, pos2);
      setServoPosition(servo3, pos3);
      emergencyTriggered = true;
      buzzerActive = true;
      buzzerStartTime = millis();
      digitalWrite(buzzerPin, HIGH);
      Serial.println("EMERGENCY BUTTON PRESSED! All rods lowered.");
    }
  }
  prevBtnEmergencyState = currentBtnEmergencyState; // Simpan status tombol saat ini

  // Kontrol durasi buzzer emergency
  if (buzzerActive && millis() - buzzerStartTime >= buzzerDuration) {
    digitalWrite(buzzerPin, LOW);
    buzzerActive = false;
    emergencyTriggered = false; // <-- Solusi: Reset emergencyTriggered di sini
    Serial.println("Emergency mode deactivated (buzzer stopped)."); // Feedback
  }

  // Jika mode emergency aktif, kontrol batang kendali lainnya non-aktif
  if (emergencyTriggered) {
    // Tidak melakukan apa-apa di sini, tombol lain sudah dinonaktifkan di bawah
  } else {
    // --- Kontrol Batang Kendali (Hanya jika kondisi terpenuhi) ---
    if (rodsCanBeOperated) {
      // --- Logika Tombol Rod 1 UP ---
      bool currentBtnUp1State = digitalRead(btnUp1);
      if (currentBtnUp1State == LOW && prevBtnUp1State == HIGH) { // Tombol baru ditekan
        lastMoveTime = currentTime; // Reset waktu untuk gerakan awal
        if (pos1 < 100) {
          pos1 += stepSize;
          setServoPosition(servo1, pos1);
          Serial.print("Rod 1 Pos: "); Serial.println(pos1);
        }
      } else if (currentBtnUp1State == LOW && (currentTime - lastMoveTime > continuousMoveDelay)) { // Tombol ditahan
        lastMoveTime = currentTime; // Update waktu untuk gerakan berkelanjutan
        if (pos1 < 100) {
          pos1 += stepSize;
          setServoPosition(servo1, pos1);
          Serial.print("Rod 1 Pos: "); Serial.println(pos1);
        }
      }
      prevBtnUp1State = currentBtnUp1State;

      // --- Logika Tombol Rod 1 DOWN ---
      bool currentBtnDown1State = digitalRead(btnDown1);
      if (currentBtnDown1State == LOW && prevBtnDown1State == HIGH) { // Tombol baru ditekan
        lastMoveTime = currentTime;
        if (pos1 > 0) {
          if (pos2 == 0 && pos3 == 0) pos1 -= stepSize;
          else {
            digitalWrite(buzzerPin, HIGH); delay(200); digitalWrite(buzzerPin, LOW);
          }
          setServoPosition(servo1, pos1);
          Serial.print("Rod 1 Pos: "); Serial.println(pos1);
        }
      } else if (currentBtnDown1State == LOW && (currentTime - lastMoveTime > continuousMoveDelay)) { // Tombol ditahan
        lastMoveTime = currentTime;
        if (pos1 > 0) {
          if (pos2 == 0 && pos3 == 0) pos1 -= stepSize;
          else {
            digitalWrite(buzzerPin, HIGH); delay(200); digitalWrite(buzzerPin, LOW);
          }
          setServoPosition(servo1, pos1);
          Serial.print("Rod 1 Pos: "); Serial.println(pos1);
        }
      }
      prevBtnDown1State = currentBtnDown1State;

      // Tombol Rod 2 & 3 hanya berfungsi jika Rod 1 sudah di 100%
      if (pos1 == 100) {
        // --- Logika Tombol Rod 2 UP ---
        bool currentBtnUp2State = digitalRead(btnUp2);
        if (currentBtnUp2State == LOW && prevBtnUp2State == HIGH) {
          lastMoveTime = currentTime;
          if (pos2 < 100) { pos2 += stepSize; setServoPosition(servo2, pos2); Serial.print("Rod 2 Pos: "); Serial.println(pos2); }
        } else if (currentBtnUp2State == LOW && (currentTime - lastMoveTime > continuousMoveDelay)) {
          lastMoveTime = currentTime;
          if (pos2 < 100) { pos2 += stepSize; setServoPosition(servo2, pos2); Serial.print("Rod 2 Pos: "); Serial.println(pos2); }
        }
        prevBtnUp2State = currentBtnUp2State;

        // --- Logika Tombol Rod 2 DOWN ---
        bool currentBtnDown2State = digitalRead(btnDown2);
        if (currentBtnDown2State == LOW && prevBtnDown2State == HIGH) {
          lastMoveTime = currentTime;
          if (pos2 > 0) { pos2 -= stepSize; setServoPosition(servo2, pos2); Serial.print("Rod 2 Pos: "); Serial.println(pos2); }
        } else if (currentBtnDown2State == LOW && (currentTime - lastMoveTime > continuousMoveDelay)) {
          lastMoveTime = currentTime;
          if (pos2 > 0) { pos2 -= stepSize; setServoPosition(servo2, pos2); Serial.print("Rod 2 Pos: "); Serial.println(pos2); }
        }
        prevBtnDown2State = currentBtnDown2State;

        // --- Logika Tombol Rod 3 UP ---
        bool currentBtnUp3State = digitalRead(btnUp3);
        if (currentBtnUp3State == LOW && prevBtnUp3State == HIGH) {
          lastMoveTime = currentTime;
          if (pos3 < 100) { pos3 += stepSize; setServoPosition(servo3, pos3); Serial.print("Rod 3 Pos: "); Serial.println(pos3); }
        } else if (currentBtnUp3State == LOW && (currentTime - lastMoveTime > continuousMoveDelay)) {
          lastMoveTime = currentTime;
          if (pos3 < 100) { pos3 += stepSize; setServoPosition(servo3, pos3); Serial.print("Rod 3 Pos: "); Serial.println(pos3); }
        }
        prevBtnUp3State = currentBtnUp3State;

        // --- Logika Tombol Rod 3 DOWN ---
        bool currentBtnDown3State = digitalRead(btnDown3);
        if (currentBtnDown3State == LOW && prevBtnDown3State == HIGH) {
          lastMoveTime = currentTime;
          if (pos3 > 0) { pos3 -= stepSize; setServoPosition(servo3, pos3); Serial.print("Rod 3 Pos: "); Serial.println(pos3); }
        } else if (currentBtnDown3State == LOW && (currentTime - lastMoveTime > continuousMoveDelay)) {
          lastMoveTime = currentTime;
          if (pos3 > 0) { pos3 -= stepSize; setServoPosition(servo3, pos3); Serial.print("Rod 3 Pos: "); Serial.println(pos3); }
        }
        prevBtnDown3State = currentBtnDown3State;
      }
    } else {
      // Ini adalah kondisi di mana rodsCanBeOperated == false
      // Serial.println("Rods inactive: Pumps OFF or Pressure < 130 bar.");
    }
  }

  // --- Update Posisi Servo (Ini akan dipanggil setiap loop untuk menjaga posisi) ---
  setServoPosition(servo1, pos1);
  setServoPosition(servo2, pos2);
  setServoPosition(servo3, pos3);

  // --- Perbarui OLED secara periodik ---
  if (currentTime - lastOLEDUpdate >= OLEDRate) {
    lastOLEDUpdate = currentTime;

    // Hitung ulang KwThermal
    kwThermal = calculateKwThermal();

    // Update OLEDs
    updateOLED_B(0, &oled1, "Rod 1 Pos", String(pos1) + "%");
    updateOLED_B(1, &oled2, "Rod 2 Pos", String(pos2) + "%");
    updateOLED_B(2, &oled3, "Rod 3 Pos", String(pos3) + "%");
    updateOLED_B(3, &oledKwThermal, "KwThermal", String(kwThermal, 2) + " kW");
  }

  // --- Kirim data posisi batang kendali ke ESP-C secara periodik ---
  if (currentTime - lastUartSendToC >= UART_SEND_TO_C_INTERVAL) {
    lastUartSendToC = currentTime;
    sendDataToESP_C();
  }

  delay(5); // Cooldown untuk loop
}
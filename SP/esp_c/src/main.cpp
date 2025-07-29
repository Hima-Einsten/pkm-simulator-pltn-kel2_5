/*
 * =================================================================
 * KODE LENGKAP & DITINGKATKAN UNTUK ESP-C (POWER GENERATION)
 * =================================================================
 * Versi: 2.1 - Ditambahkan pengiriman data ke ESP-D
 * Deskripsi:
 * - Menggunakan state machine yang lebih efisien dan andal.
 * - Motor dan relay hanya diatur saat ada perubahan power level.
 * - Menerima data dari ESP-B via Serial2.
 * - Mengirim data Power Level ke ESP-D via Serial1.
 */

#include <Arduino.h>
#include <HardwareSerial.h>

// --- (1) DEFINISI PIN PERANGKAT KERAS ---
// Dari ESP-B
#define UART2_RX_PIN 16
#define UART2_TX_PIN 17
#define BUZZER_PIN 21

#define RELAY_ON LOW
#define RELAY_OFF HIGH

#define STEAM_HUMID_1_PIN     19
#define STEAM_HUMID_2_PIN     18
#define CONDENSOR_HUMID_PIN   5
#define COOLTOWER_HUMID_1_PIN 2
#define COOLTOWER_HUMID_2_PIN 27

#define STEAM_FAN_PWM_PIN     26
#define TURBINE_MOTOR_PWM_PIN 25
#define CONDENSOR_PUMP_PWM_PIN 13
#define COOLTOWER_FAN_PWM_PIN 23

// --- (2) PENGATURAN GLOBAL ---
const int PWM_FREQ = 5000;
const int PWM_RESOLUTION = 8;
const int PWM_CH_STEAM_FAN = 0;
const int PWM_CH_TURBINE = 1;
const int PWM_CH_CONDENSOR = 2;
const int PWM_CH_COOLTOWER = 3;

enum SystemState { STATE_IDLE, STATE_STARTING_UP, STATE_RUNNING, STATE_SHUTTING_DOWN };
SystemState currentState = STATE_IDLE;

int currentPowerLevel = 0;
int previousPowerLevel = 0;

int rod2_pos = 0;
int rod3_pos = 0;
unsigned long stateTimer = 0;
unsigned long buzzerTimer = 0;
int sequence_step = 0;

const long SEQUENCE_DELAY = 5000;
const long BUZZER_INTERVAL = 500;
bool isBuzzerOn = false;

const char START_MARKER = '<';
const char END_MARKER = '>';
const int MAX_DATA_LENGTH = 50;
char receivedChars[MAX_DATA_LENGTH];
boolean newData = false;

// === TAMBAHAN: Variabel untuk pengiriman data ke ESP-D ===
unsigned long lastUartSendToD = 0;
const long UART_SEND_TO_D_INTERVAL = 500; // Kirim data setiap 500ms

// --- (3) FUNGSI-FUNGSI BANTUAN (Prototipe) ---
void setMotorPwm(int channel, int speed);
void updateSystemOutputs();
void runStartupSequence();
void runShutdownSequence();
void turnEverythingOff();
void sendDataToEspD(); // === TAMBAHAN: Prototipe fungsi baru ===

// --- FUNGSI KONTROL MOTOR ---
void setMotorPwm(int channel, int speed) {
  int pwmValue = map(speed, 0, 100, 0, 255);
  ledcWrite(channel, pwmValue);
}

// --- FUNGSI UNTUK MENERIMA DAN PARSING DATA (Tidak berubah) ---
void recvDataFromESP_B() {
  static boolean recvInProgress = false; static byte ndx = 0; char rc;
  while (Serial2.available() > 0 && newData == false) {
    rc = Serial2.read();
    if (recvInProgress) {
      if (rc != END_MARKER) { if (ndx < MAX_DATA_LENGTH - 1) receivedChars[ndx++] = rc; }
      else { receivedChars[ndx] = '\0'; recvInProgress = false; ndx = 0; newData = true; }
    } else if (rc == START_MARKER) { recvInProgress = true; }
  }
}

void parseDataFromESP_B() {
  if (newData) {
    char tempChars[MAX_DATA_LENGTH]; strcpy(tempChars, receivedChars);
    char *token = strtok(tempChars, ";");
    while (token != NULL) {
      String dataPair = String(token); int colonIndex = dataPair.indexOf(':');
      if (colonIndex != -1) {
        String key = dataPair.substring(0, colonIndex);
        String value = dataPair.substring(colonIndex + 1);
        if (key == "rod2") rod2_pos = value.toInt();
        else if (key == "rod3") rod3_pos = value.toInt();
      }
      token = strtok(NULL, ";");
    }
    newData = false;
  }
}

// --- (4) SETUP ---
void setup() {
  Serial.begin(115200);
  Serial.println("\n--- ESP-C Power Generation Control Initializing (v2.1) ---");
  
  // Komunikasi DARI ESP-B (Tidak berubah)
  Serial2.begin(115200, SERIAL_8N1, UART2_RX_PIN, UART2_TX_PIN);
  
  // Komunikasi KE ESP-D (Sudah benar)
  Serial1.begin(115200, SERIAL_8N1, 26, 25); // TX di GPIO 25
  Serial.println("Serial1 initialized to send data to ESP-D on TX=25");

  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(STEAM_HUMID_1_PIN, OUTPUT); pinMode(STEAM_HUMID_2_PIN, OUTPUT);
  pinMode(CONDENSOR_HUMID_PIN, OUTPUT); pinMode(COOLTOWER_HUMID_1_PIN, OUTPUT);
  pinMode(COOLTOWER_HUMID_2_PIN, OUTPUT);

  ledcSetup(PWM_CH_STEAM_FAN, PWM_FREQ, PWM_RESOLUTION); ledcAttachPin(STEAM_FAN_PWM_PIN, PWM_CH_STEAM_FAN);
  ledcSetup(PWM_CH_TURBINE, PWM_FREQ, PWM_RESOLUTION); ledcAttachPin(TURBINE_MOTOR_PWM_PIN, PWM_CH_TURBINE);
  ledcSetup(PWM_CH_CONDENSOR, PWM_FREQ, PWM_RESOLUTION); ledcAttachPin(CONDENSOR_PUMP_PWM_PIN, PWM_CH_CONDENSOR);
  ledcSetup(PWM_CH_COOLTOWER, PWM_FREQ, PWM_RESOLUTION); ledcAttachPin(COOLTOWER_FAN_PWM_PIN, PWM_CH_COOLTOWER);

  turnEverythingOff();
  Serial.println("System Initialized. Current State: IDLE.");
}


// --- (5) LOOP UTAMA ---
void loop() {
  recvDataFromESP_B();
  parseDataFromESP_B();

  previousPowerLevel = currentPowerLevel;
  if (rod2_pos < 21 || rod3_pos < 16) {
    currentPowerLevel = 0;
  } else if (rod2_pos >= 41 && rod3_pos >= 31) {
    currentPowerLevel = 2;
  } else {
    currentPowerLevel = 1;
  }

  // --- State Machine Utama (tidak berubah) ---
  switch (currentState) {
    case STATE_IDLE:
      if (currentPowerLevel > 0) {
        currentState = STATE_STARTING_UP;
        sequence_step = 1;
        stateTimer = millis();
        runStartupSequence();
      }
      break;

    case STATE_STARTING_UP:
      if (currentPowerLevel == 0) {
        currentState = STATE_SHUTTING_DOWN;
        sequence_step = 1;
        stateTimer = millis();
        turnEverythingOff();
        runShutdownSequence();
        break;
      }
      if (millis() - stateTimer > SEQUENCE_DELAY) {
        sequence_step++;
        stateTimer = millis();
        runStartupSequence();
      }
      break;

    case STATE_RUNNING:
      if (currentPowerLevel == 0) {
        currentState = STATE_SHUTTING_DOWN;
        sequence_step = 1;
        stateTimer = millis();
        turnEverythingOff();
        runShutdownSequence();
        break;
      }
      if (currentPowerLevel != previousPowerLevel) {
        Serial.print("Power Level changed to: "); Serial.println(currentPowerLevel);
        updateSystemOutputs();
      }
      if (currentPowerLevel == 2 && rod2_pos >= 70 && rod3_pos >= 55) {
        if (millis() - buzzerTimer > BUZZER_INTERVAL) {
          buzzerTimer = millis();
          isBuzzerOn = !isBuzzerOn;
          digitalWrite(BUZZER_PIN, isBuzzerOn);
        }
      } else {
        if (isBuzzerOn) {
          isBuzzerOn = false;
          digitalWrite(BUZZER_PIN, LOW);
        }
      }
      break;

    case STATE_SHUTTING_DOWN:
      if (millis() - stateTimer > SEQUENCE_DELAY) {
        sequence_step++;
        stateTimer = millis();
        runShutdownSequence();
      }
      break;
  }

  // === TAMBAHAN: Kirim data ke ESP-D secara berkala ===
  if (millis() - lastUartSendToD > UART_SEND_TO_D_INTERVAL) {
    lastUartSendToD = millis();
    sendDataToEspD();
  }

  delay(10);
}

// === TAMBAHAN: Fungsi baru untuk mengirim data ke ESP-D ===
void sendDataToEspD() {
  // Format: <pwr:LEVEL>
  Serial1.print(START_MARKER);
  Serial1.print("pwr:");
  Serial1.print(currentPowerLevel);
  Serial1.print(END_MARKER);
  Serial1.print('\n');
}

// --- (6) FUNGSI-FUNGSI LOGIKA (Tidak berubah) ---

void runStartupSequence() {
  switch (sequence_step) {
    case 1:
      Serial.println("STARTUP (1/4): Steam Generator ON");
      digitalWrite(STEAM_HUMID_1_PIN, RELAY_ON);
      setMotorPwm(PWM_CH_STEAM_FAN, 50);
      break;
    case 2:
      Serial.println("STARTUP (2/4): Turbine ON");
      setMotorPwm(PWM_CH_TURBINE, 40);
      break;
    case 3:
      Serial.println("STARTUP (3/4): Condensor ON");
      digitalWrite(CONDENSOR_HUMID_PIN, RELAY_ON);
      setMotorPwm(PWM_CH_CONDENSOR, 60);
      break;
    case 4:
      Serial.println("STARTUP (4/4): Cooling Tower ON");
      digitalWrite(COOLTOWER_HUMID_1_PIN, RELAY_ON);
      setMotorPwm(PWM_CH_COOLTOWER, 60);
      currentState = STATE_RUNNING;
      Serial.println("STARTUP SEQUENCE COMPLETE! -> Entering RUNNING State");
      updateSystemOutputs();
      break;
  }
}

void runShutdownSequence() {
  switch (sequence_step) {
    case 1:
      Serial.println("SHUTDOWN (1/4): Steam Generator OFF");
      break;
    case 2:
      Serial.println("SHUTDOWN (2/4): Turbine OFF");
      setMotorPwm(PWM_CH_TURBINE, 0);
      break;
    case 3:
      Serial.println("SHUTDOWN (3/4): Condensor OFF");
      setMotorPwm(PWM_CH_CONDENSOR, 0);
      break;
    case 4:
      Serial.println("SHUTDOWN (4/4): Cooling Tower OFF");
      setMotorPwm(PWM_CH_COOLTOWER, 0);
      currentState = STATE_IDLE;
      Serial.println("SHUTDOWN SEQUENCE COMPLETE! -> Entering IDLE State");
      break;
  }
}

void updateSystemOutputs() {
  if (currentState != STATE_RUNNING) return;

  if (currentPowerLevel == 1) { // Mode NORMAL
    digitalWrite(STEAM_HUMID_1_PIN, RELAY_ON);
    digitalWrite(STEAM_HUMID_2_PIN, RELAY_OFF);
    digitalWrite(CONDENSOR_HUMID_PIN, RELAY_ON);
    digitalWrite(COOLTOWER_HUMID_1_PIN, RELAY_ON);
    digitalWrite(COOLTOWER_HUMID_2_PIN, RELAY_OFF);
    setMotorPwm(PWM_CH_STEAM_FAN, 50);
    setMotorPwm(PWM_CH_TURBINE, 40);
    setMotorPwm(PWM_CH_CONDENSOR, 60);
    setMotorPwm(PWM_CH_COOLTOWER, 60);
  } else if (currentPowerLevel == 2) { // Mode MAKSIMAL
    digitalWrite(STEAM_HUMID_1_PIN, RELAY_ON);
    digitalWrite(STEAM_HUMID_2_PIN, RELAY_ON);
    digitalWrite(CONDENSOR_HUMID_PIN, RELAY_ON);
    digitalWrite(COOLTOWER_HUMID_1_PIN, RELAY_ON);
    digitalWrite(COOLTOWER_HUMID_2_PIN, RELAY_ON);
    setMotorPwm(PWM_CH_STEAM_FAN, 100);
    setMotorPwm(PWM_CH_TURBINE, 100);
    setMotorPwm(PWM_CH_CONDENSOR, 100);
    setMotorPwm(PWM_CH_COOLTOWER, 100);
  }
}

void turnEverythingOff() {
  digitalWrite(STEAM_HUMID_1_PIN, RELAY_OFF);
  digitalWrite(STEAM_HUMID_2_PIN, RELAY_OFF);
  digitalWrite(CONDENSOR_HUMID_PIN, RELAY_OFF);
  digitalWrite(COOLTOWER_HUMID_1_PIN, RELAY_OFF);
  digitalWrite(COOLTOWER_HUMID_2_PIN, RELAY_OFF);
  digitalWrite(BUZZER_PIN, LOW);
  isBuzzerOn = false;
  
  setMotorPwm(PWM_CH_STEAM_FAN, 0);
  setMotorPwm(PWM_CH_TURBINE, 0);
  setMotorPwm(PWM_CH_CONDENSOR, 0);
  setMotorPwm(PWM_CH_COOLTOWER, 0);
}

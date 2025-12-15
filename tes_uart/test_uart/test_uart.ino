/*
 * ESP32 UART Test - Simple Echo & Response Test
 * Upload this to ESP-BC to test UART communication
 * 
 * Connections:
 * - GPIO 16 (RX2) ← RasPi GPIO 14 (TX)
 * - GPIO 17 (TX2) → RasPi GPIO 15 (RX)
 * - GND ← GND
 */

#define UART_BAUD 115200
HardwareSerial UartComm(2);  // UART2

void setup() {
  // USB Serial for debugging
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n\n=================================");
  Serial.println("ESP32 UART Test - Simple Echo");
  Serial.println("=================================");
  
  // Initialize UART2 on GPIO 16/17
  UartComm.begin(UART_BAUD, SERIAL_8N1, 16, 17);
  Serial.println("✅ UART2 initialized on GPIO 16(RX) / 17(TX)");
  Serial.println("   Baudrate: 115200");
  Serial.println("   Waiting for commands...");
  Serial.println("=================================\n");
  
  // Send initial message via UART
  UartComm.println("{\"status\":\"ready\",\"device\":\"ESP-BC\"}");
  Serial.println("TX → {\"status\":\"ready\",\"device\":\"ESP-BC\"}");
}

void loop() {
  // Echo test: Read from UART and echo back
  if (UartComm.available()) {
    String received = UartComm.readStringUntil('\n');
    received.trim();
    
    if (received.length() > 0) {
      // Log to USB Serial
      Serial.print("RX ← ");
      Serial.println(received);
      
      // Check command
      if (received.indexOf("ping") >= 0) {
        // Respond to ping
        String response = "{\"status\":\"ok\",\"message\":\"pong\",\"device\":\"ESP-BC\"}";
        UartComm.println(response);
        Serial.print("TX → ");
        Serial.println(response);
      } else {
        // Echo back
        String echo = "{\"status\":\"ok\",\"echo\":\"" + received + "\"}";
        UartComm.println(echo);
        Serial.print("TX → ");
        Serial.println(echo);
      }
    }
  }
  
  // Send periodic heartbeat every 5 seconds
  static unsigned long lastHeartbeat = 0;
  if (millis() - lastHeartbeat > 5000) {
    UartComm.println("{\"status\":\"alive\",\"uptime\":" + String(millis()/1000) + "}");
    Serial.println("TX → Heartbeat");
    lastHeartbeat = millis();
  }
  
  delay(10);
}

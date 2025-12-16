#include <Arduino.h>
#include <Encoder.h>

// Pin definition (matches p2-1.cpp and kp.cpp)
// Arduino Mega 2560 Interrupt Pins: 2, 3, 18, 19, 20, 21
const int PIN_ENC_A = 20;
const int PIN_ENC_B = 21;

Encoder myEncoder(PIN_ENC_A, PIN_ENC_B);

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }
  Serial.println("--- ENCODER DEBUG MODE ---");
  Serial.print("Checking Encoder on Pins: ");
  Serial.print(PIN_ENC_A);
  Serial.print(" and ");
  Serial.println(PIN_ENC_B);
  Serial.println("Please manually rotate the motor shaft.");
}

long oldPosition  = -999;

void loop() {
  long newPosition = myEncoder.read();
  
  // Print only on change to avoid flooding
  if (newPosition != oldPosition) {
    oldPosition = newPosition;
    Serial.print("Count: ");
    Serial.println(newPosition);
  }
  
  // Heartbeat every 1s to show board is alive
  static unsigned long lastHeartbeat = 0;
  if (millis() - lastHeartbeat > 1000) {
    lastHeartbeat = millis();
    // Optional: Blink LED or minimal output
    // Serial.println("."); 
  }
}

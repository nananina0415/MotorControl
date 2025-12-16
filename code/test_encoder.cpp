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
  Serial.println("Please manually rotate the motor shaft.");
  
  // Explicitly ensure Pullups are active (just in case)
  pinMode(PIN_ENC_A, INPUT_PULLUP);
  pinMode(PIN_ENC_B, INPUT_PULLUP);
}

long oldPosition  = -999;

void loop() {
  // 1. Library Count Check
  long newPosition = myEncoder.read();
  if (newPosition != oldPosition) {
    oldPosition = newPosition;
    Serial.print("Count: ");
    Serial.println(newPosition);
  }
  
  // 2. Raw Pin State Monitor (Polling every 50ms)
  // This helps see if the pins are stuck HIGH or LOW even if count doesn't change
  static unsigned long lastCheck = 0;
  if (millis() - lastCheck > 100) {
    lastCheck = millis();
    int a = digitalRead(PIN_ENC_A);
    int b = digitalRead(PIN_ENC_B);
    Serial.print("[Raw State] A: ");
    Serial.print(a);
    Serial.print(" | B: ");
    Serial.println(b);
  }
}

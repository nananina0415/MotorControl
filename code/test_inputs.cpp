/*
  Input Test Firmware
  
  Purpose: Verify Pin Functionality without external circuit.
  
  Setup:
    - Disconnect all encoder/motor wires.
    - Pins 20 and 21 are configured as INPUT_PULLUP.
    
  Behavior:
    - Default State (Nothing connected): Should read 1 (HIGH) due to pullup.
    - Test: Use a jumper wire to connect Pin 20 or 21 to GND.
    - Active State (Grounded): Should read 0 (LOW).
    
  This verifies that the Arduino Mega's processor pins are not damaged.
*/

#include <Arduino.h>

const int PIN_A = 20;
const int PIN_B = 21;

void setup() {
  Serial.begin(115200);
  
  // Use Internal Pullup resistors
  // Default state will be HIGH (1) if floating.
  // Connect to GND to make it LOW (0).
  pinMode(PIN_A, INPUT_PULLUP);
  pinMode(PIN_B, INPUT_PULLUP);
  
  Serial.println("--- INPUT TEST MODE ---");
  Serial.println("Pins 20 & 21 set to INPUT_PULLUP.");
  Serial.println("Expected Behavior:");
  Serial.println("  - OPEN (No wire): 1");
  Serial.println("  - GND (Connected): 0");
  Serial.println("-----------------------");
}

void loop() {
  int valA = digitalRead(PIN_A);
  int valB = digitalRead(PIN_B);
  
  Serial.print("Pin 20: ");
  Serial.print(valA);
  Serial.print("  |  Pin 21: ");
  Serial.println(valB);
  
  delay(100); // 10Hz update rate
}

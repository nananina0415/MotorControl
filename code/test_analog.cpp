/*
  Analog Signal Test Firmware
  
  Purpose: View raw voltage levels from the Encoder.
  
  Setup:
    - Move Encoder Signal wires from Pin 20/21 to **A0 and A1**.
    - Keep VCC (5V) and GND connected.
    
  Behavior:
    - Prints values from 0 (0V) to 1023 (5V).
    - As you slowly turn the encoder, you should see these values swing:
      Low (near 0) <--> High (near 1023).
      
  If values stay near 1023 (5V) or 0 (0V) without changing, the encoder is not outputting a signal.
*/

#include <Arduino.h>

const int PIN_ANA_A = A0;
const int PIN_ANA_B = A1;

void setup() {
  Serial.begin(115200);
  
  // No internal pullup on analog read usually, but we can try to enable it on the digital side if needed.
  // Generally encoders are Open Collector (need pullup) or Push-Pull (don't need).
  // Let's enable pullup on the digital function of these pins just in case, typical for simple encoders.
  pinMode(PIN_ANA_A, INPUT_PULLUP);
  pinMode(PIN_ANA_B, INPUT_PULLUP);
  
  Serial.println("--- ANALOG SCOPE MODE ---");
  Serial.println("Please Connect Encoder to pins A0 and A1.");
}

void loop() {
  int valA = analogRead(PIN_ANA_A);
  int valB = analogRead(PIN_ANA_B);
  
  // CSV format for Serial Plotter
  Serial.print("A0:");
  Serial.print(valA);
  Serial.print(",A1:");
  Serial.println(valB);
  
  delay(20); // 50Hz sample rate
}

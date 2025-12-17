#include <Arduino.h>

// Custom Encoder Test - Analog A0
// Displays analog voltage values from the encoder sensor

const int ENCODER_PIN = A0;
const int THRESHOLD = 512;  // Current threshold setting

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    ; // wait for serial port to connect
  }
  Serial.println("--- CUSTOM ENCODER DEBUG MODE (ANALOG A0) ---");
  Serial.println("Reading analog values from A0 pin");
  Serial.print("Current threshold: ");
  Serial.println(THRESHOLD);
  Serial.println("Manually rotate the motor shaft to see values.");
  Serial.println();
}

void loop() {
  // Read analog value from A0 (0-1023)
  int analogValue = analogRead(ENCODER_PIN);
  
  // Convert to voltage (5V reference)
  float voltage = analogValue * (5.0 / 1023.0);
  
  // Determine HIGH/LOW state based on threshold
  int state = (analogValue >= THRESHOLD) ? HIGH : LOW;
  const char* stateStr = (state == HIGH) ? "HIGH" : "LOW ";
  
  // Print formatted output
  Serial.print("Analog: ");
  Serial.print(analogValue);
  Serial.print("\t");
  
  Serial.print("Voltage: ");
  Serial.print(voltage, 2);
  Serial.print("V\t");
  
  Serial.print("State: ");
  Serial.print(stateStr);
  Serial.print("\t");
  
  // Visual bar graph (0-1023 mapped to 0-50 chars)
  Serial.print("[");
  int barLength = map(analogValue, 0, 1023, 0, 50);
  for (int i = 0; i < barLength; i++) {
    Serial.print("=");
  }
  for (int i = barLength; i < 50; i++) {
    Serial.print(" ");
  }
  Serial.print("]");
  
  Serial.println();
  
  delay(100);  // Update every 100ms
}

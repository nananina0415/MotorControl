// P #1 - 2
// This program controls a motor's PWM duty cycle based on commands received via serial communication.
// It continuously reads the motor's encoder and sends the angle back to the host.

#include <Arduino.h>
#include <Encoder.h> 

// Pin definitions
const int ENA_PIN = 6;
const int IN1_PIN = 7;
const int IN2_PIN = 8;

// Encoder setup
Encoder myEncoder(20, 21);
const float PPR = 374.0; // Pulses Per Revolution

// Timing for sending data
unsigned long prevTime = 0;
const long interval = 10; // Send data every 10 ms

void setup() {
  // Pin modes
  pinMode(ENA_PIN, OUTPUT);
  pinMode(IN1_PIN, OUTPUT);
  pinMode(IN2_PIN, OUTPUT);

  // Start with motor off
  digitalWrite(IN1_PIN, LOW);
  digitalWrite(IN2_PIN, LOW);
  analogWrite(ENA_PIN, 0);

  // Initialize Serial communication
  Serial.begin(115200);
}

void loop() {
  // --- 1. Check for incoming commands from Python ---
  if (Serial.available() > 0) {
    // Read the integer value for the PWM duty cycle 'd'
    int d = Serial.parseInt();

    if (d >= 0 && d <= 255) { // Validate PWM value
      if (d > 0) {
        // Set direction and apply power
        digitalWrite(IN1_PIN, HIGH);
        digitalWrite(IN2_PIN, LOW);
        analogWrite(ENA_PIN, d);
      } else {
        // Stop the motor
        analogWrite(ENA_PIN, 0);
      }
    }
    // Clear any remaining characters in the buffer
    while(Serial.available() > 0) {
      Serial.read();
    }
  }

  // --- 2. Periodically send angle data back to Python ---
  unsigned long currentTime = millis();
  if (currentTime - prevTime >= interval) {
    prevTime = currentTime;

    long newPosition = myEncoder.read();
    
    // Calculate angle and wrap it to 0-360 degrees
    float rawAngle = (newPosition / PPR) * 360.0;
    float currentAngle = fmod(rawAngle, 360.0);
    if (currentAngle < 0) {
      currentAngle += 360.0;
    }

    // Send angle data
    Serial.print("Angle:");
    Serial.println(currentAngle);
  }
}

// P #1 - 1 (Custom Encoder Version)
// Calculate & plot angular velocity along time with the encoder reading of an open-loop response
// for a sufficient PWM duty step input, d = 200. (Be sure to get a smooth plot.)
// 
// Custom Encoder: 12 slits + 12 wings = 24 segments, 15 degrees each
// Using pin 3 for encoder input

#include <Arduino.h>

const int ENA_PIN = 6;
const int IN1_PIN = 7;
const int IN2_PIN = 8;

// Custom encoder on pin 3
const int ENCODER_PIN = 3;
const int STEPS_PER_REV = 24;  // 12 slits + 12 wings
const float DEGREES_PER_STEP = 15.0;  // 360 / 24

long encoderCount = 0;
int lastEncoderState = LOW;  // Track previous encoder state

unsigned long prevTime = 0;
float lastAngle = 0;
bool isFirstReading = true;

void setup() {
  pinMode(ENA_PIN, OUTPUT);
  pinMode(IN1_PIN, OUTPUT);
  pinMode(IN2_PIN, OUTPUT);

  // Setup encoder pin (threshold-based polling)
  pinMode(ENCODER_PIN, INPUT_PULLUP);

  Serial.begin(115200);
  delay(2000);

  // Send task identifier
  Serial.println("TASK:1-1");

  // Start with motor off, wait for command
  digitalWrite(IN1_PIN, LOW);
  digitalWrite(IN2_PIN, LOW);
  analogWrite(ENA_PIN, 0);

  prevTime = millis();
}

void loop() {
  // Threshold-based encoder counting (polling method)
  int currentEncoderState = digitalRead(ENCODER_PIN);
  if (lastEncoderState == LOW && currentEncoderState == HIGH) {
    // LOW -> HIGH transition detected (rising edge)
    encoderCount++;
  }
  lastEncoderState = currentEncoderState;

  unsigned long currentTime = millis();

  if (currentTime - prevTime >= 50) {  // 50ms interval for stable measurements
    float dt = (currentTime - prevTime) / 1000.0; // Convert to seconds
    prevTime = currentTime;

    // Read encoder count
    long count = encoderCount;

    // Calculate current angle
    float rawAngle = (count % STEPS_PER_REV) * DEGREES_PER_STEP;
    float currentAngle = fmod(rawAngle, 360.0);
    if (currentAngle < 0) {
      currentAngle += 360.0;
    }

    if (!isFirstReading) {
      // Calculate angular velocity
      float deltaAngle = currentAngle - lastAngle;

      // Handle wraparound (e.g., 359 -> 1 degrees)
      if (deltaAngle > 180) {
        deltaAngle -= 360;
      } else if (deltaAngle < -180) {
        deltaAngle += 360;
      }

      float angularVelocity = deltaAngle / dt; // deg/s

      // Send data in format: Duty,Time,Velocity
      Serial.print("Data:");
      Serial.print(200);
      Serial.print(",");
      Serial.print(currentTime / 1000.0, 3);
      Serial.print(",");
      Serial.println(angularVelocity);
    } else {
      isFirstReading = false;
      // Start motor after first reading
      digitalWrite(IN1_PIN, LOW);
      digitalWrite(IN2_PIN, HIGH);
      analogWrite(ENA_PIN, 200);
    }

    lastAngle = currentAngle;
  }
}

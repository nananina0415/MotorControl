// P #1 - 1
// Calculate & plot angular velocity along time with the encoder reading of an open-loop response
// for a sufficient PWM duty step input, d = 200. (Be sure to get a smooth plot.)

#include <Arduino.h>
#include <Encoder.h>

const int ENA_PIN = 6;
const int IN1_PIN = 7;
const int IN2_PIN = 8;

Encoder myEncoder(20, 21);
const float PPR = 374.0;

unsigned long prevTime = 0;
float lastAngle = 0;
bool isFirstReading = true;

void setup() {
  pinMode(ENA_PIN, OUTPUT);
  pinMode(IN1_PIN, OUTPUT);
  pinMode(IN2_PIN, OUTPUT);

  Serial.begin(115200);

  // Start with motor off, wait for command
  digitalWrite(IN1_PIN, LOW);
  digitalWrite(IN2_PIN, LOW);
  analogWrite(ENA_PIN, 0);

  prevTime = millis();
}

void loop() {
  unsigned long currentTime = millis();

  if (currentTime - prevTime >= 50) {  // 50ms interval for stable measurements
    float dt = (currentTime - prevTime) / 1000.0; // Convert to seconds
    prevTime = currentTime;

    long newPosition = myEncoder.read();

    // Calculate current angle
    float rawAngle = (newPosition / PPR) * 360.0;
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

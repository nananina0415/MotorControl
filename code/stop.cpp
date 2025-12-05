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
}

void loop() {
}

#include <Arduino.h>
#include <Encoder.h> 

const int ENA_PIN = 6;
const int IN1_PIN = 7;
const int IN2_PIN = 8;

Encoder myEncoder(20, 21);
const float PPR = 374.0; 

unsigned long prevTime = 0;

void setup() {
  pinMode(ENA_PIN, OUTPUT);
  pinMode(IN1_PIN, OUTPUT);
  pinMode(IN2_PIN, OUTPUT);

  Serial.begin(115200);

  // 모터 구동
  digitalWrite(IN1_PIN, HIGH);
  digitalWrite(IN2_PIN, LOW);
  analogWrite(ENA_PIN, 50);
}

void loop() {
  unsigned long currentTime = millis();

  if (currentTime - prevTime >= 10) {
    prevTime = currentTime;

    long newPosition = myEncoder.read();
    
    // 1. 전체 누적 각도 계산
    float rawAngle = (newPosition / PPR) * 360.0;

    // 2. 360도로 나눈 나머지 계산 (fmod 함수 사용)
    float currentAngle = fmod(rawAngle, 360.0);

    // 3. 음수일 경우 360을 더해서 0~360 범위의 양수로 보정
    // (예: -10도 -> 350도로 표현)
    if (currentAngle < 0) {
      currentAngle += 360.0;
    }

    Serial.print("Angle:");
    Serial.println(currentAngle);
  }
}
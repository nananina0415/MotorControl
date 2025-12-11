// KP Tuning Firmware
// Based on p2-1.cpp
// Usage: Upload via python run.py kp

#include <Arduino.h>
#include <Encoder.h>

// Pin definitions
const int ENA_PIN = 6;
const int IN1_PIN = 7;
const int IN2_PIN = 8;

// Encoder setup
Encoder myEncoder(20, 21);
const float PPR = 374.0;

// PID Gains (Initially 0, set by Python script)
float Kp = 0.0;
float Ki = 0.0;
float Kd = 0.0;

// PID Controller state
float reference = 0.0;        // Target position (degrees)
float position = 0.0;         // Current position (degrees)
float error = 0.0;
float error_prev = 0.0;
float error_integral = 0.0;
float control_signal = 0.0;

// Anti-windup
const float INTEGRAL_MAX = 100.0;
const float INTEGRAL_MIN = -100.0;

// PWM limits
const int PWM_MAX = 255;
const int PWM_MIN = 0;
const int PWM_DEADZONE = 50;

// Timing
unsigned long prevTime = 0;
const long interval = 10;  // 10ms control loop (100 Hz)

// Filtering
float derivative_filtered = 0.0;
const float alpha = 0.2;

// Serial
String inputString = "";
bool stringComplete = false;

void setup() {
  pinMode(ENA_PIN, OUTPUT);
  pinMode(IN1_PIN, OUTPUT);
  pinMode(IN2_PIN, OUTPUT);

  digitalWrite(IN1_PIN, LOW);
  digitalWrite(IN2_PIN, LOW);
  analogWrite(ENA_PIN, 0);

  Serial.begin(115200);
  delay(1000);

  Serial.println("TASK:KP_TUNING");
  myEncoder.write(0);
  prevTime = millis();
}

void processSerialCommand() {
  inputString.trim();

  if (inputString.startsWith("R:")) {
    reference = inputString.substring(2).toFloat();
    error_integral = 0;
    // Don't print debug info to keep serial clean for parser
  } 
  else if (inputString.startsWith("G:")) {
    // Format: G:Kp,Ki,Kd
    int c1 = inputString.indexOf(',');
    int c2 = inputString.indexOf(',', c1 + 1);
    if (c1 > 0 && c2 > 0) {
      Kp = inputString.substring(2, c1).toFloat();
      Ki = inputString.substring(c1 + 1, c2).toFloat();
      Kd = inputString.substring(c2 + 1).toFloat();
      error_integral = 0;
    }
  }
  else if (inputString.equals("S")) {
    digitalWrite(IN1_PIN, LOW);
    digitalWrite(IN2_PIN, LOW);
    analogWrite(ENA_PIN, 0);
    error_integral = 0;
  }
  else if (inputString.equals("Z")) {
    // Zeroing command
    myEncoder.write(0);
    position = 0;
    reference = 0;
    error_integral = 0;
    Serial.println("ZEROED");
  }
}

void loop() {
  if (stringComplete) {
    processSerialCommand();
    inputString = "";
    stringComplete = false;
  }

  unsigned long currentTime = millis();
  if (currentTime - prevTime >= interval) {
    float dt = (currentTime - prevTime) / 1000.0;
    prevTime = currentTime;

    long encoderCount = myEncoder.read();
    float rawAngle = (encoderCount / PPR) * 360.0;
    position = rawAngle; // No modulo for tuning, usually small range

    error = reference - position;

    float P = Kp * error;
    
    error_integral += error * dt;
    error_integral = constrain(error_integral, INTEGRAL_MIN, INTEGRAL_MAX);
    float I = Ki * error_integral;

    float derivative_raw = (error - error_prev) / dt;
    derivative_filtered = alpha * derivative_raw + (1 - alpha) * derivative_filtered;
    float D = Kd * derivative_filtered;

    control_signal = P + I + D;

    int pwm = 0;
    if (abs(control_signal) > PWM_DEADZONE) {
      pwm = (int)constrain(control_signal, -PWM_MAX, PWM_MAX);
    }

    if (pwm > 0) {
      digitalWrite(IN1_PIN, LOW);
      digitalWrite(IN2_PIN, HIGH);
      analogWrite(ENA_PIN, abs(pwm));
    } else if (pwm < 0) {
      digitalWrite(IN1_PIN, HIGH);
      digitalWrite(IN2_PIN, LOW);
      analogWrite(ENA_PIN, abs(pwm));
    } else {
      digitalWrite(IN1_PIN, LOW);
      digitalWrite(IN2_PIN, LOW);
      analogWrite(ENA_PIN, 0);
    }
    
    // Output for Python script
    // Format: Data:Time,Position,Reference
    Serial.print("Data:");
    Serial.print(currentTime / 1000.0, 3);
    Serial.print(",");
    Serial.print(position, 2);
    Serial.print(",");
    Serial.println(reference, 2);

    error_prev = error;
  }
}

void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    inputString += inChar;
    if (inChar == '\n') {
      stringComplete = true;
    }
  }
}

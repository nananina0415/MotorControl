// P #2 - 1
// PID Position Controller Implementation
// Controls motor position (angle) using PID feedback
//
// Requirements:
//   - overshoot < 15%
//   - settling time ts <= 0.5s
//   - no steady-state error
//
// Usage:
//   - Upload this code with: python run.py 2-1
//   - Set reference angle via Serial: "R:200" (for 200 degrees)
//   - Monitor position, error, and control signal via plotter

#include <Arduino.h>
#include <Encoder.h>

// Pin definitions
const int ENA_PIN = 6;
const int IN1_PIN = 7;
const int IN2_PIN = 8;

// Encoder setup
Encoder myEncoder(20, 21);
const float PPR = 374.0;

// PID Gains (optimized from Python simulation)
// From p2-1_pid_simulation.py with tau=3.009s, K=5.233
// Performance: Overshoot=1.29%, ts=0.519s, ess=-2.58deg
float Kp = 0.0;   // Proportional gain
float Ki = 1.663; // Integral gain
float Kd = 7.117; // Derivative gain

// PID Controller state
float reference = 200.0;      // Target position (degrees)
float position = 0.0;         // Current position (degrees)
float error = 0.0;            // Current error
float error_prev = 0.0;       // Previous error (for derivative)
float error_integral = 0.0;   // Accumulated error (for integral)
float control_signal = 0.0;   // PID output

// Anti-windup
const float INTEGRAL_MAX = 100.0;  // Prevent integral windup
const float INTEGRAL_MIN = -100.0;

// PWM limits
const int PWM_MAX = 255;
const int PWM_MIN = 0;
const int PWM_DEADZONE = 50;  // Minimum PWM to overcome friction

// Timing
unsigned long prevTime = 0;
const long interval = 10;  // 10ms control loop (100 Hz)

// Low-pass filter for derivative (reduce noise)
float derivative_filtered = 0.0;
const float alpha = 0.2;  // Filter coefficient (0 = no new data, 1 = no filtering)

// Serial command parsing
String inputString = "";
bool stringComplete = false;

// Function declarations
void processSerialCommand();

void setup() {
  pinMode(ENA_PIN, OUTPUT);
  pinMode(IN1_PIN, OUTPUT);
  pinMode(IN2_PIN, OUTPUT);

  // Start with motor off
  digitalWrite(IN1_PIN, LOW);
  digitalWrite(IN2_PIN, LOW);
  analogWrite(ENA_PIN, 0);

  Serial.begin(115200);
  delay(2000);

  // Send task identifier
  Serial.println("TASK:2-1");

  Serial.println("PID Position Controller Started");
  Serial.println("Commands:");
  Serial.println("  R:<value>  - Set reference position (e.g., R:200)");
  Serial.println("  G:<Kp>,<Ki>,<Kd> - Set PID gains (e.g., G:10.5,5.2,2.1)");
  Serial.println("  S - Stop motor");
  Serial.println("");

  Serial.print("Initial reference: ");
  Serial.print(reference);
  Serial.println(" deg");

  Serial.print("PID gains: Kp=");
  Serial.print(Kp, 3);
  Serial.print(", Ki=");
  Serial.print(Ki, 3);
  Serial.print(", Kd=");
  Serial.println(Kd, 3);
  Serial.println("");

  // Reset encoder
  myEncoder.write(0);

  prevTime = millis();

  // Reserve space for serial input
  inputString.reserve(50);
}

void loop() {
  unsigned long currentTime = millis();

  // Check for serial commands
  if (stringComplete) {
    processSerialCommand();
    inputString = "";
    stringComplete = false;
  }

  // PID control loop
  if (currentTime - prevTime >= interval) {
    float dt = (currentTime - prevTime) / 1000.0;  // Convert to seconds
    prevTime = currentTime;

    // Read encoder
    long encoderCount = myEncoder.read();
    float rawAngle = (encoderCount / PPR) * 360.0;

    // Convert to 0-360 range
    position = fmod(rawAngle, 360.0);
    if (position < 0) {
      position += 360.0;
    }

    // Calculate error
    error = reference - position;

    // Handle wraparound for shortest path
    if (error > 180) {
      error -= 360;
    } else if (error < -180) {
      error += 360;
    }

    // Proportional term
    float P = Kp * error;

    // Integral term (with anti-windup)
    error_integral += error * dt;
    error_integral = constrain(error_integral, INTEGRAL_MIN, INTEGRAL_MAX);
    float I = Ki * error_integral;

    // Derivative term (with low-pass filter to reduce noise)
    float derivative_raw = (error - error_prev) / dt;
    derivative_filtered = alpha * derivative_raw + (1 - alpha) * derivative_filtered;
    float D = Kd * derivative_filtered;

    // PID output
    control_signal = P + I + D;

    // Apply deadzone and saturation
    int pwm = 0;
    if (abs(control_signal) > PWM_DEADZONE) {
      pwm = (int)constrain(control_signal, -PWM_MAX, PWM_MAX);
    }

    // Set motor direction and speed
    if (pwm > 0) {
      // Forward (increase angle)
      digitalWrite(IN1_PIN, LOW);
      digitalWrite(IN2_PIN, HIGH);
      analogWrite(ENA_PIN, abs(pwm));
    } else if (pwm < 0) {
      // Reverse (decrease angle)
      digitalWrite(IN1_PIN, HIGH);
      digitalWrite(IN2_PIN, LOW);
      analogWrite(ENA_PIN, abs(pwm));
    } else {
      // Stop
      digitalWrite(IN1_PIN, LOW);
      digitalWrite(IN2_PIN, LOW);
      analogWrite(ENA_PIN, 0);
    }

    // Send data for plotting
    // Format: Data:Time,Position,Reference,Error,ControlSignal
    Serial.print("Data:");
    Serial.print(currentTime / 1000.0, 3);
    Serial.print(",");
    Serial.print(position, 2);
    Serial.print(",");
    Serial.print(reference, 2);
    Serial.print(",");
    Serial.print(error, 2);
    Serial.print(",");
    Serial.println(control_signal, 2);

    // Update previous error
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

void processSerialCommand() {
  inputString.trim();

  if (inputString.startsWith("R:")) {
    // Set reference
    float newRef = inputString.substring(2).toFloat();
    reference = newRef;

    // Reset integral term when reference changes
    error_integral = 0;

    Serial.print("Reference set to: ");
    Serial.print(reference);
    Serial.println(" deg");

  } else if (inputString.startsWith("G:")) {
    // Set PID gains
    String gainStr = inputString.substring(2);
    int comma1 = gainStr.indexOf(',');
    int comma2 = gainStr.indexOf(',', comma1 + 1);

    if (comma1 > 0 && comma2 > 0) {
      Kp = gainStr.substring(0, comma1).toFloat();
      Ki = gainStr.substring(comma1 + 1, comma2).toFloat();
      Kd = gainStr.substring(comma2 + 1).toFloat();

      // Reset integral when gains change
      error_integral = 0;

      Serial.print("Gains updated: Kp=");
      Serial.print(Kp, 3);
      Serial.print(", Ki=");
      Serial.print(Ki, 3);
      Serial.print(", Kd=");
      Serial.println(Kd, 3);
    } else {
      Serial.println("Error: Invalid gain format. Use G:<Kp>,<Ki>,<Kd>");
    }

  } else if (inputString.equals("S")) {
    // Stop motor
    digitalWrite(IN1_PIN, LOW);
    digitalWrite(IN2_PIN, LOW);
    analogWrite(ENA_PIN, 0);
    error_integral = 0;
    Serial.println("Motor stopped");

  } else {
    Serial.println("Unknown command");
  }
}

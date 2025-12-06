// P #1 - 2
// Automatically cycles through different PWM duty values (150, 175, 200, 225, 250)
// Measures motor response and outputs velocity data independently

#include <Arduino.h>
#include <Encoder.h>

// Pin definitions
const int ENA_PIN = 6;
const int IN1_PIN = 7;
const int IN2_PIN = 8;

// Encoder setup
Encoder myEncoder(20, 21);
const float PPR = 374.0;

// Duty cycle values to test
const int D_VALUES[] = {150, 175, 200, 225, 250};
const int NUM_D_VALUES = 5;

// Timing variables
unsigned long prevTime = 0;
unsigned long stateStartTime = 0;
const long interval = 50; // Send data every 50 ms for stable measurements

// State machine variables
enum State {
  START_MOTOR,
  WAIT_STEADY,
  WAIT_STOPPED
};

State currentState = START_MOTOR;
int currentDIndex = 0;
int currentDuty = 0;

// Velocity calculation
float lastAngle = 0;
bool isFirstReading = true;
float currentVelocity = 0;

// Tau calculation
float startVelocity = 0;
float steadyStateVelocity = 0;
float riseStartTime = 0;
float tauValue = 0;
bool tauCalculated = false;
int tauDuty = 0;

// Timing thresholds
const unsigned long STEADY_TIME = 5000;  // Run for 5 seconds
const unsigned long STOP_TIME = 2000;    // Wait 2 seconds for stop

void setup() {
  pinMode(ENA_PIN, OUTPUT);
  pinMode(IN1_PIN, OUTPUT);
  pinMode(IN2_PIN, OUTPUT);

  // Start with motor off
  digitalWrite(IN1_PIN, LOW);
  digitalWrite(IN2_PIN, LOW);
  analogWrite(ENA_PIN, 0);

  Serial.begin(115200);

  // Wait for serial connection
  delay(2000);

  // Send task identifier
  Serial.println("TASK:1-2");

  Serial.println("Starting automatic duty cycle test...");

  stateStartTime = millis();
}

void loop() {
  unsigned long currentTime = millis();

  // State machine for automatic duty cycling
  switch (currentState) {
    case START_MOTOR:
      if (currentDIndex < NUM_D_VALUES) {
        currentDuty = D_VALUES[currentDIndex];
        Serial.print("Test ");
        Serial.print(currentDIndex + 1);
        Serial.print("/");
        Serial.print(NUM_D_VALUES);
        Serial.print(": d=");
        Serial.println(currentDuty);

        // Save starting velocity (should be near 0)
        startVelocity = abs(currentVelocity);
        riseStartTime = currentTime / 1000.0;
        steadyStateVelocity = 0;
        tauCalculated = false;
        tauDuty = currentDuty;

        // Start motor (reversed direction)
        digitalWrite(IN1_PIN, LOW);
        digitalWrite(IN2_PIN, HIGH);
        analogWrite(ENA_PIN, currentDuty);

        stateStartTime = currentTime;
        currentState = WAIT_STEADY;
      } else {
        // All tests complete, restart from beginning
        currentDIndex = 0;
        Serial.println("\nAll tests complete. Restarting cycle...\n");
        delay(3000);
        currentState = START_MOTOR;
      }
      break;

    case WAIT_STEADY:
      // Wait for steady state
      if (currentTime - stateStartTime >= STEADY_TIME) {
        Serial.println("  Steady state reached. Stopping motor...");

        // Stop motor
        analogWrite(ENA_PIN, 0);
        currentDuty = 0;

        stateStartTime = currentTime;
        currentState = WAIT_STOPPED;
      }
      break;

    case WAIT_STOPPED:
      // Wait for motor to stop
      if (currentTime - stateStartTime >= STOP_TIME) {
        Serial.println("  Motor stopped.\n");

        // Move to next duty value
        currentDIndex++;
        stateStartTime = currentTime;
        currentState = START_MOTOR;
      }
      break;
  }

  // Periodically calculate and send velocity data
  if (currentTime - prevTime >= interval) {
    float dt = (currentTime - prevTime) / 1000.0;
    prevTime = currentTime;

    long newPosition = myEncoder.read();

    // Calculate angle
    float rawAngle = (newPosition / PPR) * 360.0;
    float currentAngle = fmod(rawAngle, 360.0);
    if (currentAngle < 0) {
      currentAngle += 360.0;
    }

    if (!isFirstReading) {
      // Calculate angular velocity
      float deltaAngle = currentAngle - lastAngle;

      // Handle wraparound
      if (deltaAngle > 180) {
        deltaAngle -= 360;
      } else if (deltaAngle < -180) {
        deltaAngle += 360;
      }

      float velocity = deltaAngle / dt; // deg/s
      currentVelocity = velocity;

      // Calculate tau during rise (step-up response)
      if (currentState == WAIT_STEADY && !tauCalculated) {
        float absVelocity = abs(velocity);

        // Update steady state estimate (use values after 3 seconds)
        if (currentTime - stateStartTime >= 3000) {
          // Update steady state as moving average of recent velocities
          if (steadyStateVelocity == 0) {
            steadyStateVelocity = absVelocity;
          } else {
            // Exponential moving average
            steadyStateVelocity = 0.9 * steadyStateVelocity + 0.1 * absVelocity;
          }
        }

        // Check for 63.2% threshold (after we have steady state estimate)
        if (steadyStateVelocity > 50) {
          float threshold = startVelocity + (steadyStateVelocity - startVelocity) * 0.632;

          if (absVelocity >= threshold) {
            tauValue = (currentTime / 1000.0) - riseStartTime;
            tauCalculated = true;

            // Send tau label
            Serial.print("Tau:");
            Serial.print(tauDuty);
            Serial.print(",");
            Serial.print(currentTime / 1000.0, 3);
            Serial.print(",");
            Serial.println(tauValue, 3);

            Serial.print("  [Start: ");
            Serial.print(startVelocity, 1);
            Serial.print(" -> Steady: ");
            Serial.print(steadyStateVelocity, 1);
            Serial.print(" -> 63.2% at ");
            Serial.print(threshold, 1);
            Serial.println(" deg/s]");
          }
        }
      }

      // Send data in format: Duty,Time,Velocity
      Serial.print("Data:");
      Serial.print(currentDuty);
      Serial.print(",");
      Serial.print(currentTime / 1000.0, 3);
      Serial.print(",");
      Serial.println(velocity);
    } else {
      isFirstReading = false;
    }

    lastAngle = currentAngle;
  }
}

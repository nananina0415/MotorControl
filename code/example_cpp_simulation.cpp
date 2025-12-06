/**
 * Example C++ Simulation using data_loader.hpp
 *
 * This demonstrates how to use the header-only data_loader.hpp
 * in a PC-based C++ simulation (NOT for Arduino).
 *
 * Compilation:
 *   g++ -std=c++17 example_cpp_simulation.cpp -o example_sim
 *   ./example_sim
 *
 * Note: This will NOT compile on Arduino (and that's OK - it's not meant to)
 */

#include <iostream>
#include <cmath>
#include <vector>
#include "data_loader.hpp"

// Simple PID Controller
class PIDController {
public:
    PIDController(double Kp, double Ki, double Kd, double dt)
        : Kp_(Kp), Ki_(Ki), Kd_(Kd), dt_(dt),
          error_integral_(0.0), error_prev_(0.0) {}

    double update(double error) {
        // Proportional
        double P = Kp_ * error;

        // Integral
        error_integral_ += error * dt_;
        double I = Ki_ * error_integral_;

        // Derivative
        double D = Kd_ * (error - error_prev_) / dt_;

        error_prev_ = error;

        return P + I + D;
    }

    void reset() {
        error_integral_ = 0.0;
        error_prev_ = 0.0;
    }

private:
    double Kp_, Ki_, Kd_, dt_;
    double error_integral_;
    double error_prev_;
};

// Simple motor model
class MotorModel {
public:
    MotorModel(double tau, double K, double dt)
        : tau_(tau), K_(K), dt_(dt), velocity_(0.0), position_(0.0) {}

    void update(double control) {
        // Motor dynamics: dω/dt = (K*u - ω) / τ
        double dv = (K_ * control - velocity_) / tau_;
        velocity_ += dv * dt_;
        position_ += velocity_ * dt_;
    }

    double get_position() const { return position_; }
    double get_velocity() const { return velocity_; }

    void reset() {
        velocity_ = 0.0;
        position_ = 0.0;
    }

private:
    double tau_, K_, dt_;
    double velocity_, position_;
};

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "C++ PID Simulation Example" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << std::endl;

    try {
        // Load system parameters from data/1-3/
        auto [tau, K] = DataLoader::load_system_parameters("1-3");

        std::cout << "System Parameters:" << std::endl;
        std::cout << "  τ = " << tau << " s" << std::endl;
        std::cout << "  K = " << K << " (deg/s)/PWM" << std::endl;
        std::cout << std::endl;

        // Simulation parameters
        double dt = 0.001;  // 1ms
        double t_max = 2.0;  // 2 seconds
        double reference = 200.0;  // Target position

        // PID gains (example values - should be optimized)
        double Kp = 10.0;
        double Ki = 5.0;
        double Kd = 2.0;

        std::cout << "PID Gains:" << std::endl;
        std::cout << "  Kp = " << Kp << std::endl;
        std::cout << "  Ki = " << Ki << std::endl;
        std::cout << "  Kd = " << Kd << std::endl;
        std::cout << std::endl;

        // Create controller and plant
        PIDController pid(Kp, Ki, Kd, dt);
        MotorModel motor(tau, K, dt);

        // Simulate
        std::cout << "Running simulation..." << std::endl;

        int n_steps = static_cast<int>(t_max / dt);
        std::vector<double> time_vec;
        std::vector<double> position_vec;
        std::vector<double> error_vec;

        for (int i = 0; i < n_steps; ++i) {
            double t = i * dt;
            double position = motor.get_position();
            double error = reference - position;
            double control = pid.update(error);

            motor.update(control);

            // Save every 10ms for plotting
            if (i % 10 == 0) {
                time_vec.push_back(t);
                position_vec.push_back(position);
                error_vec.push_back(error);
            }
        }

        // Calculate performance metrics
        double final_position = motor.get_position();
        double steady_state_error = reference - final_position;

        double max_position = *std::max_element(position_vec.begin(), position_vec.end());
        double overshoot = (max_position - reference) / reference * 100.0;

        std::cout << "Simulation complete!" << std::endl;
        std::cout << std::endl;

        std::cout << "Performance Metrics:" << std::endl;
        std::cout << "  Final position: " << final_position << " deg" << std::endl;
        std::cout << "  Steady-state error: " << steady_state_error << " deg" << std::endl;
        std::cout << "  Overshoot: " << overshoot << " %" << std::endl;
        std::cout << std::endl;

        // Save results to CSV
        std::cout << "Saving results to cpp_simulation_results.csv..." << std::endl;
        std::ofstream outfile("cpp_simulation_results.csv");
        outfile << "Time(s),Position(deg),Error(deg)" << std::endl;
        for (size_t i = 0; i < time_vec.size(); ++i) {
            outfile << time_vec[i] << "," << position_vec[i] << "," << error_vec[i] << std::endl;
        }
        outfile.close();

        std::cout << "Results saved!" << std::endl;

    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        std::cerr << std::endl;
        std::cerr << "Please run: python run.py 1-3" << std::endl;
        std::cerr << "Then press 'p' to save data" << std::endl;
        return 1;
    }

    return 0;
}

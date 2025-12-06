/**
 * Data Loader - Header-Only C++ Version
 *
 * Provides functions to load the latest measurement data from data/ folder.
 *
 * IMPORTANT:
 * - This is a HEADER-ONLY library
 * - Only include this file when you need it (e.g., in PC-based C++ simulations)
 * - DO NOT include in Arduino code (Arduino has no file system)
 * - If not included, this file won't be compiled → no errors!
 *
 * Requirements:
 * - C++17 or higher (for std::filesystem)
 * - nlohmann/json library: https://github.com/nlohmann/json
 *   Download single header: https://raw.githubusercontent.com/nlohmann/json/develop/single_include/nlohmann/json.hpp
 *
 * Usage:
 *   #include "data_loader.hpp"
 *
 *   auto [tau, K, metadata] = DataLoader::load_latest_summary("1-3");
 *   std::cout << "τ = " << tau << ", K = " << K << std::endl;
 *
 * Compilation:
 *   g++ -std=c++17 my_simulation.cpp -o sim
 *
 * Note: This file is intended for PC-based C++ programs, not Arduino.
 */

#ifndef DATA_LOADER_HPP
#define DATA_LOADER_HPP

#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <filesystem>
#include <stdexcept>
#include <tuple>
#include <algorithm>

// You need to download nlohmann/json.hpp and place it in the include path
// Download: https://github.com/nlohmann/json/releases
// For this example, we'll provide a minimal JSON parser alternative below
// Or uncomment this line if you have nlohmann/json:
// #include <nlohmann/json.hpp>

namespace fs = std::filesystem;

namespace DataLoader {

/**
 * Simple JSON value extractor (minimal implementation)
 * For production use, consider nlohmann/json library instead
 */
inline double extract_json_number(const std::string& json, const std::string& key) {
    std::string search_key = "\"" + key + "\":";
    size_t pos = json.find(search_key);
    if (pos == std::string::npos) {
        throw std::runtime_error("Key not found: " + key);
    }

    pos += search_key.length();

    // Skip whitespace
    while (pos < json.length() && std::isspace(json[pos])) {
        ++pos;
    }

    // Extract number
    size_t end_pos = pos;
    while (end_pos < json.length() &&
           (std::isdigit(json[end_pos]) || json[end_pos] == '.' ||
            json[end_pos] == '-' || json[end_pos] == 'e' || json[end_pos] == 'E')) {
        ++end_pos;
    }

    std::string number_str = json.substr(pos, end_pos - pos);
    return std::stod(number_str);
}

inline std::string extract_json_string(const std::string& json, const std::string& key) {
    std::string search_key = "\"" + key + "\":";
    size_t pos = json.find(search_key);
    if (pos == std::string::npos) {
        return "";
    }

    pos += search_key.length();

    // Skip whitespace and opening quote
    while (pos < json.length() && (std::isspace(json[pos]) || json[pos] == '"')) {
        if (json[pos] == '"') {
            ++pos;
            break;
        }
        ++pos;
    }

    // Extract until closing quote
    size_t end_pos = pos;
    while (end_pos < json.length() && json[end_pos] != '"') {
        ++end_pos;
    }

    return json.substr(pos, end_pos - pos);
}

/**
 * Metadata structure for summary data
 */
struct SummaryMetadata {
    double tau_average;
    double K_average;
    double tau_std;
    double K_std;
    int data_points;
    std::string timestamp;
    std::string task;
};

/**
 * Get the project root directory
 */
inline fs::path get_project_root() {
    // Assume this file is in code/ directory
    // Project root is parent of code/
    fs::path current_file = fs::path(__FILE__);
    return current_file.parent_path().parent_path();
}

/**
 * Get data directory for a specific task
 */
inline fs::path get_task_data_dir(const std::string& task_name) {
    return get_project_root() / "data" / task_name;
}

/**
 * Find the most recent file matching a pattern
 */
inline fs::path find_latest_file(const fs::path& dir, const std::string& pattern) {
    if (!fs::exists(dir) || !fs::is_directory(dir)) {
        throw std::runtime_error("Directory not found: " + dir.string());
    }

    fs::path latest_file;
    fs::file_time_type latest_time;
    bool found = false;

    for (const auto& entry : fs::directory_iterator(dir)) {
        if (entry.is_regular_file()) {
            std::string filename = entry.path().filename().string();

            // Simple pattern matching (starts with pattern)
            if (filename.find(pattern) == 0) {
                auto ftime = fs::last_write_time(entry);
                if (!found || ftime > latest_time) {
                    latest_file = entry.path();
                    latest_time = ftime;
                    found = true;
                }
            }
        }
    }

    if (!found) {
        throw std::runtime_error("No files matching pattern: " + pattern);
    }

    return latest_file;
}

/**
 * Load the latest summary file for a task
 *
 * @param task_name Task identifier (e.g., "1-3")
 * @param verbose Print loading information
 * @return Tuple of (tau, K, metadata)
 */
inline std::tuple<double, double, SummaryMetadata>
load_latest_summary(const std::string& task_name, bool verbose = true) {
    fs::path data_dir = get_task_data_dir(task_name);

    // Find latest summary file
    fs::path latest_file = find_latest_file(data_dir, "summary_");

    // Read JSON file
    std::ifstream file(latest_file);
    if (!file.is_open()) {
        throw std::runtime_error("Failed to open file: " + latest_file.string());
    }

    std::string json_content((std::istreambuf_iterator<char>(file)),
                              std::istreambuf_iterator<char>());
    file.close();

    // Parse JSON (using simple extractor)
    SummaryMetadata metadata;
    metadata.tau_average = extract_json_number(json_content, "tau_average");
    metadata.K_average = extract_json_number(json_content, "K_average");
    metadata.tau_std = extract_json_number(json_content, "tau_std");
    metadata.K_std = extract_json_number(json_content, "K_std");
    metadata.data_points = static_cast<int>(extract_json_number(json_content, "data_points"));
    metadata.timestamp = extract_json_string(json_content, "timestamp");
    metadata.task = extract_json_string(json_content, "task");

    if (verbose) {
        std::cout << "=== Auto-loaded from " << latest_file.filename().string() << " ===" << std::endl;
        std::cout << "Time constant τ = " << metadata.tau_average
                  << " ± " << metadata.tau_std << " s" << std::endl;
        std::cout << "DC gain K = " << metadata.K_average
                  << " ± " << metadata.K_std << " (deg/s)/PWM" << std::endl;
        std::cout << "Data points: " << metadata.data_points << std::endl;
        std::cout << "Timestamp: " << metadata.timestamp << std::endl;
        std::cout << std::endl;
    }

    return {metadata.tau_average, metadata.K_average, metadata};
}

/**
 * Convenience function to load only tau and K
 */
inline std::pair<double, double> load_system_parameters(const std::string& task_name = "1-3",
                                                        bool verbose = true) {
    auto [tau, K, _] = load_latest_summary(task_name, verbose);
    return {tau, K};
}

/**
 * CSV data structure
 */
struct RawData {
    std::vector<double> time;
    std::vector<double> velocity;
    std::vector<double> duty;
};

/**
 * Load the latest raw data CSV file
 *
 * @param task_name Task identifier
 * @param verbose Print loading information
 * @return RawData structure with time, velocity, duty vectors
 */
inline RawData load_latest_raw_data(const std::string& task_name, bool verbose = true) {
    fs::path data_dir = get_task_data_dir(task_name);
    fs::path latest_file = find_latest_file(data_dir, "raw_data_");

    if (verbose) {
        std::cout << "=== Loading raw data from " << latest_file.filename().string()
                  << " ===" << std::endl;
    }

    std::ifstream file(latest_file);
    if (!file.is_open()) {
        throw std::runtime_error("Failed to open file: " + latest_file.string());
    }

    RawData data;
    std::string line;

    // Skip header
    std::getline(file, line);

    // Read data
    while (std::getline(file, line)) {
        double t, v, d;
        char comma;
        std::istringstream iss(line);

        if (iss >> t >> comma >> v >> comma >> d) {
            data.time.push_back(t);
            data.velocity.push_back(v);
            data.duty.push_back(d);
        }
    }

    file.close();

    if (verbose) {
        std::cout << "Loaded " << data.time.size() << " data points" << std::endl;
        std::cout << std::endl;
    }

    return data;
}

} // namespace DataLoader

#endif // DATA_LOADER_HPP

/**
 * Example usage (for testing - not compiled in Arduino):
 *
 * #include "data_loader.hpp"
 *
 * int main() {
 *     try {
 *         // Load system parameters
 *         auto [tau, K] = DataLoader::load_system_parameters("1-3");
 *         std::cout << "τ = " << tau << " s" << std::endl;
 *         std::cout << "K = " << K << " (deg/s)/PWM" << std::endl;
 *
 *         // Load full metadata
 *         auto [tau2, K2, meta] = DataLoader::load_latest_summary("1-3");
 *         std::cout << "Task: " << meta.task << std::endl;
 *
 *         // Load raw data
 *         auto data = DataLoader::load_latest_raw_data("1-3");
 *         std::cout << "First time point: " << data.time[0] << " s" << std::endl;
 *
 *     } catch (const std::exception& e) {
 *         std::cerr << "Error: " << e.what() << std::endl;
 *         return 1;
 *     }
 *
 *     return 0;
 * }
 */

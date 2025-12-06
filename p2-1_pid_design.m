% P#2-1: PID Controller Design
% Traditional Root Locus Method
%
% Requirements:
%   - overshoot < 15%
%   - settling time ts <= 0.5s
%   - no steady-state error

clear all;
close all;
clc;

%% 1. System Parameters (auto-load from P#1-3 measurements)

% Method 1: Use Python data_loader (recommended)
% Method 2: Use native Matlab JSON loading (fallback)

use_python_loader = true;  % Set to false to use Matlab-only method

if use_python_loader
    try
        % Add src directory to Python path
        src_path = fullfile(pwd, 'src');
        if count(py.sys.path, src_path) == 0
            insert(py.sys.path, int32(0), src_path);
        end

        % Load using Python data_loader
        result = py.data_loader.load_system_parameters('1-3', pyargs('verbose', true));
        tau = double(result{1});
        K = double(result{2});

    catch ME
        warning('Failed to load using Python data_loader: %s', ME.message);
        fprintf('Falling back to Matlab JSON loading...\n\n');
        use_python_loader = false;
    end
end

if ~use_python_loader
    % Fallback: Native Matlab JSON loading
    data_dir = fullfile(pwd, 'data', '1-3');
    summary_files = dir(fullfile(data_dir, 'summary_*.json'));

    if isempty(summary_files)
        % No data file found, use manual values
        warning('No summary file found in data/1-3/. Using manual values.');
        fprintf('Please run: python run.py 1-3\n');
        fprintf('Then press ''p'' to save data, and re-run this script.\n\n');

        tau = 0.4;      % Time constant (s) - PLACEHOLDER
        K = 12.4;       % DC gain (deg/s)/PWM - PLACEHOLDER

        fprintf('=== System Parameters (PLACEHOLDER) ===\n');
        fprintf('Time constant τ = %.3f s\n', tau);
        fprintf('DC gain K = %.3f (deg/s)/PWM\n', K);
        fprintf('\n');
    else
        % Load the most recent summary file
        [~, idx] = max([summary_files.datenum]);
        latest_file = fullfile(data_dir, summary_files(idx).name);

        % Read JSON file
        fid = fopen(latest_file, 'r');
        raw = fread(fid, inf);
        str = char(raw');
        fclose(fid);
        data = jsondecode(str);

        % Extract values
        tau = data.tau_average;
        K = data.K_average;

        fprintf('=== Auto-loaded from %s ===\n', summary_files(idx).name);
        fprintf('Time constant τ = %.4f ± %.4f s\n', tau, data.tau_std);
        fprintf('DC gain K = %.4f ± %.4f (deg/s)/PWM\n', K, data.K_std);
        fprintf('Data points: %d\n', data.data_points);
        fprintf('\n');
    end
end

%% 2. Motor Transfer Function (Approximated)
% G(s) = K / [s(τs + 1)]

% State space representation
A = [0 1; 0 -1/tau];
B = [0; K/tau];
C = [1 0];
D = [0];

motor_ss = ss(A, B, C, D);

% Transfer function
motor_tf = tf(K, [tau 1 0]);

fprintf('=== Motor Transfer Function ===\n');
fprintf('G(s) = K / [s(τs + 1)]\n');
display(motor_tf);

%% 3. Design Specifications
% overshoot < 15% → damping ratio ζ > 0.517
% ts <= 0.5s → settling time

Mp_max = 0.15;  % Maximum overshoot (15%)
ts_max = 0.5;   % Maximum settling time (0.5s)

% Calculate required damping ratio from overshoot
% Mp = exp(-ζπ / sqrt(1-ζ^2))
% Solving for ζ:
zeta_min = sqrt((log(Mp_max))^2 / (pi^2 + (log(Mp_max))^2));

% Calculate required natural frequency from settling time
% ts = 4.6 / (ζ*ωn) for 2% criterion
% Choose ζ slightly higher than minimum for safety
zeta_design = 0.6;  % Design damping ratio
wn_min = 4.6 / (zeta_design * ts_max);

fprintf('=== Design Specifications ===\n');
fprintf('Maximum overshoot: %.1f%%\n', Mp_max*100);
fprintf('Maximum settling time: %.2f s\n', ts_max);
fprintf('Minimum damping ratio: %.3f\n', zeta_min);
fprintf('Design damping ratio: %.3f\n', zeta_design);
fprintf('Minimum natural frequency: %.2f rad/s\n', wn_min);
fprintf('\n');

%% 4. PID Controller Design

% Method 1: Automatic PID Tuner
fprintf('=== Method 1: PID Tuner (Interactive) ===\n');
% Uncomment to use interactive tuner:
% pidTuner(motor_tf, 'pid');

% Method 2: Manual PID design based on desired poles
fprintf('=== Method 2: Pole Placement ===\n');

% Desired closed-loop poles
% For 2nd order system: s = -ζωn ± jωn√(1-ζ²)
sigma = zeta_design * wn_min;
wd = wn_min * sqrt(1 - zeta_design^2);
desired_poles = [-sigma + 1j*wd; -sigma - 1j*wd];

fprintf('Desired poles: %.2f ± j%.2f\n', real(desired_poles(1)), imag(desired_poles(1)));

% For PID + 1st order plant, we have 3rd order system
% Add additional pole (faster than dominant poles)
additional_pole = -4 * sigma;  % Make it 4x faster
desired_poles_3rd = [desired_poles; additional_pole];

fprintf('3rd order poles: [%.2f±j%.2f, %.2f]\n', ...
    real(desired_poles(1)), imag(desired_poles(1)), additional_pole);

% PID controller: C(s) = Kp + Ki/s + Kd*s = (Kd*s^2 + Kp*s + Ki)/s
% Closed loop: G_cl = C*G / (1 + C*G)

% Manual tuning starting point (trial and error)
% Start with rough estimates
Kp_init = 0.5 * wn_min^2 * tau / K;
Ki_init = 0.3 * wn_min^2 / K;
Kd_init = 0.5 * wn_min * tau / K;

fprintf('\nInitial PID gains (rough estimate):\n');
fprintf('Kp = %.3f\n', Kp_init);
fprintf('Ki = %.3f\n', Ki_init);
fprintf('Kd = %.3f\n', Kd_init);

% Method 3: Optimization-based tuning
fprintf('\n=== Method 3: Iterative Tuning ===\n');

% Define objective function
objective = @(gains) pid_objective(gains, motor_tf, Mp_max, ts_max);

% Initial guess
x0 = [Kp_init, Ki_init, Kd_init];

% Bounds (gains must be positive)
lb = [0, 0, 0];
ub = [100, 100, 20];

% Optimize
options = optimset('Display', 'iter', 'MaxIter', 100);
[gains_opt, fval] = fmincon(objective, x0, [], [], [], [], lb, ub, [], options);

Kp = gains_opt(1);
Ki = gains_opt(2);
Kd = gains_opt(3);

fprintf('\n=== Optimized PID Gains ===\n');
fprintf('Kp = %.3f\n', Kp);
fprintf('Ki = %.3f\n', Ki);
fprintf('Kd = %.3f\n', Kd);
fprintf('\n');

%% 5. Create PID Controller and Closed-Loop System

C = pid(Kp, Ki, Kd);
fprintf('PID Controller:\n');
display(C);

% Closed-loop system with unity feedback
sys_cl = feedback(C * motor_tf, 1);

fprintf('Closed-loop transfer function:\n');
display(sys_cl);

%% 6. Step Response Analysis for R = 200

R = 200;  % Reference input
t = 0:0.001:2;  % Time vector

fprintf('=== Step Response for R = %d ===\n', R);

figure('Name', 'Step Response R=200', 'Position', [100 100 1000 600]);

% Simulate
[y, t] = step(R * sys_cl, t);

% Calculate performance metrics
info = stepinfo(y, t);

overshoot = info.Overshoot;
ts_actual = info.SettlingTime;
ess = R - y(end);

fprintf('Overshoot: %.2f%% (spec: < 15%%)\n', overshoot);
fprintf('Settling time: %.3f s (spec: < 0.5s)\n', ts_actual);
fprintf('Steady-state error: %.4f deg (spec: = 0)\n', ess);
fprintf('Rise time: %.3f s\n', info.RiseTime);
fprintf('Peak time: %.3f s\n', info.PeakTime);

% Check if specs are met
specs_met = (overshoot < 15) && (ts_actual <= 0.5) && (abs(ess) < 0.01*R);
if specs_met
    fprintf('\n✓ All specifications MET!\n');
else
    fprintf('\n✗ Specifications NOT MET. Adjust gains.\n');
end
fprintf('\n');

% Plot
subplot(2,1,1);
plot(t, y, 'b-', 'LineWidth', 2);
hold on;
yline(R, 'r--', 'Reference', 'LineWidth', 1.5);
yline(R*1.15, 'g--', '+15% overshoot limit', 'LineWidth', 1);
yline(R*0.98, 'k:', '±2% settling band', 'LineWidth', 0.5);
yline(R*1.02, 'k:', '', 'LineWidth', 0.5);
xline(0.5, 'm--', 'ts = 0.5s limit', 'LineWidth', 1);
grid on;
xlabel('Time (s)');
ylabel('Position (deg)');
title(sprintf('Step Response for R=%d (Kp=%.2f, Ki=%.2f, Kd=%.2f)', R, Kp, Ki, Kd));
legend('Response', 'Reference', 'Overshoot Limit', 'Location', 'best');

% Plot error
subplot(2,1,2);
error = R - y;
plot(t, error, 'r-', 'LineWidth', 1.5);
grid on;
xlabel('Time (s)');
ylabel('Error (deg)');
title('Tracking Error');

%% 7. Test with Different Reference Values (R = 150, 250)

R_values = [150, 250];

figure('Name', 'Step Response Comparison', 'Position', [150 150 1200 800]);

colors = {'b', 'r', 'g'};
R_all = [200, R_values];

for idx = 1:length(R_all)
    R_test = R_all(idx);

    [y, t] = step(R_test * sys_cl, t);
    info = stepinfo(y, t);

    overshoot = info.Overshoot;
    ts_actual = info.SettlingTime;
    ess = R_test - y(end);

    fprintf('=== Step Response for R = %d ===\n', R_test);
    fprintf('Overshoot: %.2f%%\n', overshoot);
    fprintf('Settling time: %.3f s\n', ts_actual);
    fprintf('Steady-state error: %.4f deg\n', ess);
    fprintf('\n');

    % Plot
    subplot(2,1,1);
    plot(t, y, 'Color', colors{idx}, 'LineWidth', 2);
    hold on;

    subplot(2,1,2);
    error = R_test - y;
    plot(t, error, 'Color', colors{idx}, 'LineWidth', 1.5);
    hold on;
end

subplot(2,1,1);
grid on;
xlabel('Time (s)');
ylabel('Position (deg)');
title('Step Response for Different References');
legend('R=200', 'R=150', 'R=250', 'Location', 'best');

subplot(2,1,2);
grid on;
xlabel('Time (s)');
ylabel('Error (deg)');
title('Tracking Error');
legend('R=200', 'R=150', 'R=250', 'Location', 'best');

%% 8. Root Locus Plot

figure('Name', 'Root Locus', 'Position', [200 200 800 600]);
rlocus(C * motor_tf);
grid on;
title('Root Locus of C(s)G(s)');

% Mark desired pole locations
hold on;
plot(real(desired_poles), imag(desired_poles), 'rx', 'MarkerSize', 15, 'LineWidth', 2);
legend('Root Locus', 'Desired Poles', 'Location', 'best');

%% 9. Bode Plot

figure('Name', 'Bode Plot', 'Position', [250 250 800 600]);
bode(sys_cl);
grid on;
title('Bode Plot of Closed-Loop System');

%% 10. Save Results

% Save gains to file
results.tau = tau;
results.K = K;
results.Kp = Kp;
results.Ki = Ki;
results.Kd = Kd;
results.overshoot_200 = overshoot;
results.ts_200 = ts_actual;
results.ess_200 = ess;

save('p2-1_results.mat', 'results');
fprintf('Results saved to p2-1_results.mat\n');

%% Helper Function: Objective for PID optimization

function cost = pid_objective(gains, plant, Mp_max, ts_max)
    % Unpack gains
    Kp = gains(1);
    Ki = gains(2);
    Kd = gains(3);

    % Create controller
    C = pid(Kp, Ki, Kd);

    % Closed-loop
    sys_cl = feedback(C * plant, 1);

    % Check stability
    if ~isstable(sys_cl)
        cost = 1e10;
        return;
    end

    % Simulate step response
    [y, t] = step(sys_cl, 0:0.001:2);

    % Calculate metrics
    info = stepinfo(y, t);

    overshoot = info.Overshoot / 100;  % Convert to fraction
    ts = info.SettlingTime;
    ess = abs(1 - y(end));

    % Cost function (penalty for violating specs)
    cost = 0;

    % Overshoot penalty
    cost = cost + max(0, overshoot - Mp_max)^2 * 1000;

    % Settling time penalty
    cost = cost + max(0, ts - ts_max)^2 * 100;

    % Steady-state error penalty
    cost = cost + ess^2 * 500;

    % Control effort penalty (prefer smaller gains)
    cost = cost + (Kp^2 + Ki^2 + Kd^2) * 0.01;

    % Penalize overly large derivative gain (noise sensitivity)
    cost = cost + max(0, Kd - 10)^2 * 10;
end

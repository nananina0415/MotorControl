# P #1 - 2
# Obtain the time constant tau of your motor system.
# Check the variation of tau for different values of d.
# This script automates the process for d = [150, 175, 200, 225, 250].

import serial
import matplotlib.pyplot as plt
import numpy as np
import time
from collections import deque

# --- 실험 설정 ---
PORT = 'COM6'
BAUD_RATE = 115200
D_VALUES = [150, 175, 200, 225, 250]
MAX_POINTS_PER_RUN = 500 # 한 번의 실행에서 수집할 최대 데이터 포인트
STEADY_STATE_THRESHOLD = 2.0 # 각속도 표준편차가 이 값보다 작으면 안정 상태로 간주 (deg/s)
STEADY_STATE_POINTS = 25   # 안정 상태를 확인할 때 마지막 N개의 데이터 포인트를 사용
STOP_THRESHOLD = 1.0       # 각속도가 이 값보다 낮으면 정지 상태로 간주 (deg/s)
STOP_POINTS = 25           # 정지 상태를 확인할 때 마지막 N개의 데이터 포인트를 사용

# --- 상태 정의 ---
STATE = "IDLE" # 현재 상태
d_index = 0    # 현재 테스트 중인 D_VALUES의 인덱스

# --- 데이터 저장소 ---
# 각 d 값에 대한 결과를 저장_ {'d_value': {'time': [...], 'velocity': [...]}}
results = {} 
# 현재 실행(run)에 대한 임시 데이터
current_run_time = []
current_run_vel = []

# --- 시리얼 연결 ---
try:
    ser = serial.Serial(PORT, BAUD_RATE, timeout=0.1)
    time.sleep(2) # 시리얼 안정화를 위한 대기
    ser.reset_input_buffer()
    print(f"Connected to {PORT}. Arduino를 준비합니다...")
except Exception as e:
    print(f"Error: {PORT} 연결 실패. {e}")
    exit()

def send_d_to_arduino(d_value):
    """Arduino에 d 값을 전송"""
    print(f"Sending d = {d_value} to Arduino.")
    ser.write(f"{int(d_value)}\n".encode())

# --- 실시간 데이터 처리를 위한 변수 ---
start_time_current_run = 0
last_angle = 0
last_time = 0
is_first_point = True

def process_serial_data():
    """시리얼 데이터를 읽고 각속도를 계산하여 임시 버퍼에 저장"""
    global last_angle, last_time, is_first_point

    has_new_data = False
    while ser.in_waiting > 0:
        try:
            raw_data = ser.readline().decode('utf-8', errors='ignore').strip()
            if "Angle:" in raw_data:
                current_angle = float(raw_data.split(":")[1])
                current_time = time.time() - start_time_current_run
                has_new_data = True
                
                if not is_first_point:
                    dt = current_time - last_time
                    delta_angle = current_angle - last_angle
                    if delta_angle > 180: delta_angle -= 360
                    elif delta_angle < -180: delta_angle += 360
                    
                    if dt > 0:
                        velocity = delta_angle / dt
                        current_run_time.append(current_time)
                        current_run_vel.append(velocity)
                
                last_angle = current_angle
                last_time = current_time
                is_first_point = False
        except (ValueError, IndexError):
            continue # 데이터 파싱 오류 무시
    return has_new_data

def check_steady_state():
    """현재 각속도가 안정 상태에 도달했는지 확인"""
    if len(current_run_vel) < STEADY_STATE_POINTS:
        return False
    
    last_velocities = current_run_vel[-STEADY_STATE_POINTS:]
    std_dev = np.std(last_velocities)
    # print(f"Checking steady state: std_dev = {std_dev:.2f}") # 디버깅용
    return std_dev < STEADY_STATE_THRESHOLD

def check_stopped():
    """모터가 정지했는지 확인"""
    if len(current_run_vel) < STOP_POINTS:
        # 데이터가 충분하지 않으면, 마지막 점만이라도 확인
        return len(current_run_vel) > 0 and abs(current_run_vel[-1]) < STOP_THRESHOLD
        
    last_velocities = current_run_vel[-STOP_POINTS:]
    avg_abs_vel = np.mean(np.abs(last_velocities))
    # print(f"Checking stop state: avg_abs_vel = {avg_abs_vel:.2f}") # 디버깅용
    return avg_abs_vel < STOP_THRESHOLD

def manage_experiment():
    """실험 상태를 관리하는 메인 상태 머신"""
    global STATE, d_index, start_time_current_run, is_first_point, current_run_time, current_run_vel

    process_serial_data()

    # --- 상태 전이 로직 ---
    if STATE == "IDLE":
        STATE = "START_MOTOR"

    elif STATE == "START_MOTOR":
        if d_index < len(D_VALUES):
            current_d = D_VALUES[d_index]
            # 새 실행을 위한 변수 초기화
            current_run_time = []
            current_run_vel = []
            is_first_point = True
            start_time_current_run = time.time()
            
            send_d_to_arduino(current_d)
            STATE = "WAIT_STEADY"
        else:
            STATE = "FINISHED" # 모든 d 값에 대한 실험 완료

    elif STATE == "WAIT_STEADY":
        if check_steady_state():
            print(f"d={D_VALUES[d_index]}에서 안정 상태 도달. 모터를 정지합니다.")
            send_d_to_arduino(0)
            STATE = "WAIT_STOP"
            
    elif STATE == "WAIT_STOP":
        # 모터가 멈출 때까지 기다림
        if check_stopped():
            print(f"모터 정지 확인. d={D_VALUES[d_index]} 데이터 저장.")
            # 현재 d 값에 대한 결과 저장
            results[D_VALUES[d_index]] = {
                'time': list(current_run_time),
                'velocity': list(current_run_vel)
            }
            d_index += 1
            STATE = "START_MOTOR" # 다음 d 값으로 실험 시작
            time.sleep(1) # 다음 실험 전 잠시 대기

    elif STATE == "FINISHED":
        print("모든 실험 완료. 결과 플로팅.")
        plot_final_results()
        # 상태를 IDLE로 되돌려 다시 실행할 수 없도록 함
        STATE = "PLOT_CLOSED" 
        
def plot_final_results():
    """모든 d 값에 대한 결과를 하나의 그래프에 플로팅"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    for d_value, data in results.items():
        ax.plot(data['time'], data['velocity'], label=f'd = {d_value}')

    ax.set_title('Motor Step Response for Different Duty Cycles')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Angular Velocity (deg/s)')
    ax.legend()
    ax.grid(True)
    plt.show()

# --- 메인 루프 ---
print("실험을 시작합니다. Ctrl+C를 눌러 종료할 수 있습니다.")
send_d_to_arduino(0) # 시작 전 모터가 확실히 정지하도록 함
STATE = "IDLE"

try:
    while STATE != "PLOT_CLOSED":
        manage_experiment()
        time.sleep(0.05) # CPU 사용량을 줄이기 위한 짧은 대기
finally:
    print("프로그램 종료. 모터를 정지합니다.")
    send_d_to_arduino(0)
    ser.close()


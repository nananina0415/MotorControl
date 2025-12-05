import serial
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque
import time

# --- 설정 ---
PORT = 'COM4'   # 포트 번호 확인!
BAUD_RATE = 115200

# 시리얼 연결
try:
    ser = serial.Serial(PORT, BAUD_RATE, timeout=0.1)
    # 버퍼 비우기 (시작 전 찌꺼기 데이터 제거)
    ser.reset_input_buffer()
    print(f"Connected to {PORT}")
except Exception as e:
    print(f"Error: {PORT} 연결 실패.")
    exit()

# 데이터 저장소
max_points = 200
y_vals = deque(maxlen=max_points)
x_vals = deque(maxlen=max_points)
index_count = 0 

fig, ax = plt.subplots()
line, = ax.plot([], [], 'b-') # 파란 실선

def update(frame):
    global index_count
    
    # 데이터가 들어와 있을 때만 실행 (중요!)
    if ser.in_waiting > 0:
        # 쌓여있는 데이터를 모두 읽어서 최신 상태로 만듦 (렉 제거 핵심)
        while ser.in_waiting:
            try:
                raw_data = ser.readline().decode('utf-8', errors='ignore').strip()
                
                if "Angle:" in raw_data:
                    val_str = raw_data.split(":")[1]
                    angle = float(val_str)
                    
                    # 리스트에 추가
                    y_vals.append(angle)
                    x_vals.append(index_count)
                    index_count += 1
                    
                    # 터미널 출력 확인
                    # print(f"Angle: {angle}") 
                    
            except ValueError:
                pass
        
        # 그래프 업데이트 (데이터가 갱신되었을 때만)
        line.set_data(x_vals, y_vals)
        
        # 축 범위 자동 조정
        if len(y_vals) > 0:
            ax.set_xlim(min(x_vals), max(x_vals) + 1)
            ax.set_ylim(min(y_vals) - 10, max(y_vals) + 10)
            ax.set_title(f"Real-time Angle: {y_vals[-1]:.1f} deg")

    return line,

# blit=False로 설정하여 안정성 확보
ani = FuncAnimation(fig, update, interval=10, blit=False, cache_frame_data=False)
plt.grid(True)
plt.show()

ser.close()
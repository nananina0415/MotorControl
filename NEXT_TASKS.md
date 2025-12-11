# 다음 세션 작업 계획

**우선순위 작업**: 플로터 데이터 저장 기능 추가

---

## 🎯 즉시 할 작업: 플로터 데이터 저장 기능

### 요구사항
사용자가 **'p' 키**를 누르면:
1. ✅ 그래프 업데이트 멈춤 (이미 구현됨)
2. ⬜ **그래프를 이미지로 저장**
3. ⬜ **측정값 원본을 CSV로 저장**
4. ⬜ **계산된 값(τ, K 등)을 JSON/TXT로 저장**

### 구현 위치
**파일**: `src/plotter.py`
**수정 함수**: `on_key(event)` (line 53-77)

---

## 📋 구현 계획

### 1. 파일 저장 경로 구조

**중요**: `data/` 폴더는 **src 밖**에 생성됩니다!

```
MotorControl/
├── src/              # 소스 코드
│   └── plotter.py
├── code/             # Arduino 코드
├── data/             # 📁 측정 데이터 저장 (src 밖!)
│   ├── 1-1/          # Task 1-1 데이터
│   │   ├── plot_YYYYMMDD_HHMMSS.png
│   │   ├── raw_data_YYYYMMDD_HHMMSS.csv
│   │   └── summary_YYYYMMDD_HHMMSS.json
│   ├── 1-2/          # Task 1-2 데이터
│   │   ├── plot_YYYYMMDD_HHMMSS.png
│   │   ├── raw_data_YYYYMMDD_HHMMSS.csv
│   │   ├── tau_values_YYYYMMDD_HHMMSS.json
│   │   └── summary_YYYYMMDD_HHMMSS.json
│   └── 1-3/          # Task 1-3 데이터
│       ├── plot_YYYYMMDD_HHMMSS.png
│       ├── raw_data_YYYYMMDD_HHMMSS.csv
│       ├── tau_values_YYYYMMDD_HHMMSS.json
│       ├── K_values_YYYYMMDD_HHMMSS.json
│       └── summary_YYYYMMDD_HHMMSS.json
└── p2-1_pid_design.m # 이 파일이 data/ 폴더에서 자동으로 읽음
```

**왜 `data/` 폴더가 src 밖에 있나요?**
- 다른 코드(Matlab, Python 분석 스크립트 등)에서 쉽게 접근
- 프로젝트 루트에서 데이터 관리가 명확
- Git에서 쉽게 제외 가능 (.gitignore)

### 2. 과제 자동 감지
**방법**: Arduino에서 첫 메시지로 과제 번호 전송

**수정 파일**: 각 Arduino 코드 (`code/p*.cpp`)

```cpp
// setup() 함수에서
Serial.println("TASK:1-1");  // 또는 1-2, 1-3
```

**plotter.py에서**:
```python
task_name = None  # 전역 변수

# update_plot()에서 첫 메시지 파싱
if raw_data.startswith("TASK:"):
    task_name = raw_data.split(":")[1]  # "1-1", "1-2", "1-3"
```

### 3. 이미지 저장
```python
def save_plot(task_name):
    """현재 플롯을 이미지로 저장"""
    from datetime import datetime
    import os

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 디렉토리 생성 (프로젝트 루트의 data/ 폴더)
    # plotter.py는 src/에 있으므로 상위 폴더로 이동
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / task_name
    data_dir.mkdir(parents=True, exist_ok=True)

    # 파일명
    filename = data_dir / f"plot_{timestamp}.png"

    # 저장
    fig.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Plot saved: {filename}")

    return filename
```

### 4. 원본 데이터 저장 (CSV)
```python
def save_raw_data(task_name, time_data, velocity_data, duty_data):
    """측정값 원본을 CSV로 저장"""
    from datetime import datetime
    import csv

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 프로젝트 루트/data/ 폴더
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / task_name
    data_dir.mkdir(parents=True, exist_ok=True)

    filename = data_dir / f"raw_data_{timestamp}.csv"

    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Time(s)', 'Velocity(deg/s)', 'Duty'])

        for t, v, d in zip(time_data, velocity_data, duty_data):
            writer.writerow([t, v, d/10])  # duty는 10배 스케일 복원

    print(f"Raw data saved: {filename}")
    return filename
```

### 5. 계산된 값 저장 (JSON)
```python
def save_calculated_values(task_name, tau_labels, K_labels):
    """τ, K 등 계산된 값을 JSON으로 저장"""
    from datetime import datetime
    import json

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 프로젝트 루트/data/ 폴더
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / task_name
    data_dir.mkdir(parents=True, exist_ok=True)

    # τ 값들 저장
    if tau_labels:
        tau_data = {
            'timestamp': timestamp,
            'task': task_name,
            'measurements': []
        }

        for time_val, tau_val, duty, _ in tau_labels:
            tau_data['measurements'].append({
                'duty': duty,
                'time': time_val,
                'tau': tau_val
            })

        tau_file = data_dir / f"tau_values_{timestamp}.json"
        with open(tau_file, 'w') as f:
            json.dump(tau_data, f, indent=2)
        print(f"Tau values saved: {tau_file}")

    # K 값들 저장
    if K_labels:
        K_data = {
            'timestamp': timestamp,
            'task': task_name,
            'measurements': []
        }

        for time_val, K_val, duty, _ in K_labels:
            K_data['measurements'].append({
                'duty': duty,
                'time': time_val,
                'K': K_val
            })

        K_file = data_dir / f"K_values_{timestamp}.json"
        with open(K_file, 'w') as f:
            json.dump(K_data, f, indent=2)
        print(f"K values saved: {K_file}")

    # 통합 요약 저장
    summary = {
        'timestamp': timestamp,
        'task': task_name,
        'tau_average': None,
        'K_average': None,
        'data_points': len(time_data)
    }

    if tau_labels:
        tau_values = [tau for _, tau, _, _ in tau_labels]
        summary['tau_average'] = sum(tau_values) / len(tau_values)
        summary['tau_std'] = (sum((x - summary['tau_average'])**2 for x in tau_values) / len(tau_values))**0.5

    if K_labels:
        K_values = [K for _, K, _, _ in K_labels]
        summary['K_average'] = sum(K_values) / len(K_values)
        summary['K_std'] = (sum((x - summary['K_average'])**2 for x in K_values) / len(K_values))**0.5

    summary_file = data_dir / f"summary_{timestamp}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"Summary saved: {summary_file}")
```

### 6. 'p' 키 이벤트 수정
```python
def on_key(event):
    """Handle keyboard events"""
    global paused

    if event.key == 'c':
        # ... (기존 코드 유지)

    elif event.key == 'p':
        if not paused:
            paused = True
            print("\n=== Plotter paused ===")

            # 과제 이름 확인
            if task_name is None:
                print("Warning: Task name not detected. Using 'unknown'")
                save_task = "unknown"
            else:
                save_task = task_name

            # 모든 데이터 저장
            print("\nSaving data...")

            # 1. 플롯 이미지 저장
            plot_file = save_plot(save_task)

            # 2. 원본 데이터 저장
            raw_file = save_raw_data(save_task, time_data, velocity_data, duty_data)

            # 3. 계산된 값 저장
            save_calculated_values(save_task, tau_labels, K_labels)

            print("\n=== All data saved successfully ===")
            print("Close window to exit.")

            ax.set_title('Motor Speed Response - PAUSED & SAVED (close window to exit)')
        else:
            print("Already paused")
```

---

## 📊 다른 코드에서 데이터 자동 로딩

### Matlab에서 data/ 폴더 자동 읽기

**목적**: P#2-1 Matlab 코드가 `data/1-3/summary_*.json`을 자동으로 읽어서 τ, K 값 사용

**구현** (`p2-1_pid_design.m` 파일 수정):

```matlab
%% 1. System Parameters (자동으로 data/1-3/ 폴더에서 읽기)

% data/1-3/ 폴더에서 가장 최근 summary 파일 찾기
data_dir = fullfile(pwd, 'data', '1-3');
summary_files = dir(fullfile(data_dir, 'summary_*.json'));

if isempty(summary_files)
    % 파일 없으면 수동 입력
    warning('No summary file found in data/1-3/. Using manual values.');
    tau = 0.4;  % TODO: Fill with measured value
    K = 12.4;   % TODO: Fill with measured value
else
    % 가장 최근 파일 선택
    [~, idx] = max([summary_files.datenum]);
    latest_file = fullfile(data_dir, summary_files(idx).name);

    % JSON 파일 읽기
    fid = fopen(latest_file, 'r');
    raw = fread(fid, inf);
    str = char(raw');
    fclose(fid);
    data = jsondecode(str);

    % 값 추출
    tau = data.tau_average;
    K = data.K_average;

    fprintf('=== Auto-loaded from %s ===\n', summary_files(idx).name);
    fprintf('τ = %.4f ± %.4f s\n', tau, data.tau_std);
    fprintf('K = %.4f ± %.4f (deg/s)/PWM\n', K, data.K_std);
    fprintf('\n');
end

% 나머지 코드는 동일...
```

### Python에서 data/ 폴더 자동 읽기

**예시**: 분석 스크립트에서 사용

```python
import json
from pathlib import Path

def load_latest_summary(task_name):
    """가장 최근 summary 파일 로드"""
    data_dir = Path("data") / task_name
    summary_files = list(data_dir.glob("summary_*.json"))

    if not summary_files:
        raise FileNotFoundError(f"No summary files in data/{task_name}/")

    # 가장 최근 파일 (파일명에 타임스탬프 포함)
    latest_file = max(summary_files, key=lambda p: p.stat().st_mtime)

    with open(latest_file, 'r') as f:
        data = json.load(f)

    return data

# 사용 예시
summary = load_latest_summary("1-3")
tau = summary['tau_average']
K = summary['K_average']

print(f"τ = {tau:.4f} s")
print(f"K = {K:.4f} (deg/s)/PWM")
```

---

## 🔧 Arduino 코드 수정

### p1-1.cpp
```cpp
void setup() {
    // ... 기존 코드 ...

    Serial.begin(115200);
    delay(2000);

    // 과제 식별자 전송
    Serial.println("TASK:1-1");

    Serial.println("Starting angular velocity measurement...");
    // ... 나머지 코드 ...
}
```

### p1-2.cpp
```cpp
void setup() {
    // ... 기존 코드 ...

    Serial.begin(115200);
    delay(2000);

    // 과제 식별자 전송
    Serial.println("TASK:1-2");

    Serial.println("Starting automatic duty cycle test...");
    // ... 나머지 코드 ...
}
```

### p1-3.cpp
```cpp
void setup() {
    // ... 기존 코드 ...

    Serial.begin(115200);
    delay(2000);

    // 과제 식별자 전송
    Serial.println("TASK:1-3");

    Serial.println("Starting K parameter measurement...");
    // ... 나머지 코드 ...
}
```

---

## 📊 저장 데이터 예시

### raw_data_20251206_143022.csv
```csv
Time(s),Velocity(deg/s),Duty
0.050,5.2,200
0.100,12.8,200
0.150,24.5,200
...
```

### tau_values_20251206_143022.json
```json
{
  "timestamp": "20251206_143022",
  "task": "1-2",
  "measurements": [
    {
      "duty": 150,
      "time": 3.456,
      "tau": 0.423
    },
    {
      "duty": 175,
      "time": 10.234,
      "tau": 0.418
    },
    ...
  ]
}
```

### K_values_20251206_143022.json
```json
{
  "timestamp": "20251206_143022",
  "task": "1-3",
  "measurements": [
    {
      "duty": 150,
      "time": 5.000,
      "K": 2.456
    },
    {
      "duty": 175,
      "time": 12.000,
      "K": 2.489
    },
    ...
  ]
}
```

### summary_20251206_143022.json
```json
{
  "timestamp": "20251206_143022",
  "task": "1-3",
  "tau_average": 0.420,
  "tau_std": 0.012,
  "K_average": 2.478,
  "K_std": 0.034,
  "data_points": 1523
}
```

---

## ✅ 구현 체크리스트

### plotter.py 수정
- [ ] `task_name` 전역 변수 추가
- [ ] `TASK:` 메시지 파싱 추가
- [ ] `save_plot()` 함수 구현
- [ ] `save_raw_data()` 함수 구현
- [ ] `save_calculated_values()` 함수 구현
- [ ] `on_key()` 함수에서 'p' 키 이벤트 수정
- [ ] `from datetime import datetime` import 추가
- [ ] `from pathlib import Path` 확인 (이미 있음)
- [ ] `import csv` 추가
- [ ] `import json` 추가

### Arduino 코드 수정
- [ ] p1-1.cpp에 `Serial.println("TASK:1-1");` 추가
- [ ] p1-2.cpp에 `Serial.println("TASK:1-2");` 추가
- [ ] p1-3.cpp에 `Serial.println("TASK:1-3");` 추가

### 테스트
- [ ] p1-1 실행 → 'p' 누르기 → 파일 확인
- [ ] p1-2 실행 → 'p' 누르기 → τ 값 저장 확인
- [ ] p1-3 실행 → 'p' 누르기 → τ, K 값 저장 확인
- [ ] results/ 폴더 구조 확인
- [ ] JSON 파일 형식 확인
- [ ] CSV 파일 형식 확인

---

## 🎯 다음 세션 시작 시

1. **이 파일(NEXT_TASKS.md) 읽기**
2. **SESSION_SUMMARY.md 확인** - 이전 작업 내용
3. **구현 시작**:
   ```
   "다음 세션 작업 계획(NEXT_TASKS.md)에 있는
    플로터 데이터 저장 기능을 구현해줘"
   ```

---

## 💡 추가 아이디어 (나중에)

### 자동 분석 기능
저장된 JSON 파일을 읽어서:
- τ, K 평균값 자동 계산
- Matlab 코드에 자동 입력
- 보고서용 표 자동 생성

### 실시간 통계
플로터 화면에 현재까지:
- 평균 τ 표시
- 평균 K 표시
- 데이터 포인트 개수

### 데이터 비교 도구
여러 측정 결과를 비교:
```python
python compare_results.py results/p1-3/*.json
```

---

## 📚 참고 코드 위치

- **plotter.py**: `src/plotter.py`
  - 현재 'p' 키: line 70-77
  - update_plot 함수: line 81-141

- **Arduino 코드**:
  - p1-1.cpp: line 54-71 (setup)
  - p1-2.cpp: line 54-71 (setup)
  - p1-3.cpp: line 60-78 (setup)

---

## 🚀 최종 목표

사용자가 **'p' 한 번**만 누르면:
1. ✅ 그래프 정지
2. ✅ 이미지 저장
3. ✅ CSV 저장
4. ✅ JSON 저장
5. ✅ 평균값 계산 및 저장

→ **완전 자동화된 실험 데이터 관리!**

# Data Loader Library

데이터 로딩 로직을 별도 파일로 분리하여 재사용성과 유지보수성을 향상시킨 라이브러리입니다.

## 📁 파일 구조

```
MotorControl/
├── src/
│   └── data_loader.py          # Python용 데이터 로더 ✅
├── code/
│   ├── data_loader.hpp         # C++ Header-only 데이터 로더 ✅
│   └── example_cpp_simulation.cpp  # C++ 사용 예제
└── DATA_LOADER_README.md       # 이 파일
```

---

## 🐍 Python 버전 (`src/data_loader.py`)

### 기능

- `load_latest_summary(task_name)` - 최신 summary JSON 파일 로드
- `load_latest_raw_data(task_name)` - 최신 raw CSV 파일 로드
- `load_latest_pid_data(task_name)` - 최신 PID CSV 파일 로드
- `load_system_parameters(task_name)` - τ, K만 간단히 로드
- `list_all_summaries(task_name)` - 모든 summary 파일 나열

### 사용법

#### 1. 기본 사용 (τ, K 로드)

```python
from data_loader import load_system_parameters

tau, K = load_system_parameters("1-3")
print(f"τ = {tau:.4f} s, K = {K:.4f}")
```

#### 2. 전체 메타데이터 포함

```python
from data_loader import load_latest_summary

tau, K, metadata = load_latest_summary("1-3")
print(f"Standard deviation: τ_std = {metadata['tau_std']:.4f}")
print(f"Data points: {metadata['data_points']}")
```

#### 3. Raw 데이터 로드

```python
from data_loader import load_latest_raw_data

time, velocity, duty = load_latest_raw_data("1-3")
print(f"Loaded {len(time)} data points")
```

#### 4. 모든 측정 데이터 나열

```python
from data_loader import list_all_summaries

summaries = list_all_summaries("1-3")
for s in summaries:
    print(f"{s['filename']}: τ={s['tau']:.3f}, K={s['K']:.3f}")
```

### Python 스크립트에 적용

**Before:**
```python
# 직접 JSON 로딩
with open('data/1-3/summary_xxx.json', 'r') as f:
    data = json.load(f)
tau = data['tau_average']
K = data['K_average']
```

**After:**
```python
from data_loader import load_system_parameters

tau, K = load_system_parameters("1-3")
```

✅ **간결하고 재사용 가능!**

---

## 🔧 C++ 버전 (`code/data_loader.hpp`)

### 특징

- **Header-only**: `#include`할 때만 컴파일됨
- **Arduino 비포함**: Arduino 코드에서 include 안 하면 에러 없음 ✅
- **PC용 시뮬레이션 전용**: 파일 시스템 필요 (std::filesystem)

### 요구사항

- C++17 이상
- `std::filesystem` 지원 컴파일러
- PC 환경 (Arduino 아님!)

### 사용법

#### 1. Header 포함

```cpp
#include "data_loader.hpp"
```

#### 2. 시스템 파라미터 로드

```cpp
auto [tau, K] = DataLoader::load_system_parameters("1-3");
std::cout << "τ = " << tau << " s" << std::endl;
std::cout << "K = " << K << std::endl;
```

#### 3. 전체 메타데이터 포함

```cpp
auto [tau, K, metadata] = DataLoader::load_latest_summary("1-3");
std::cout << "Data points: " << metadata.data_points << std::endl;
std::cout << "Timestamp: " << metadata.timestamp << std::endl;
```

#### 4. Raw 데이터 로드

```cpp
auto data = DataLoader::load_latest_raw_data("1-3");
std::cout << "First time point: " << data.time[0] << " s" << std::endl;
std::cout << "Loaded " << data.time.size() << " points" << std::endl;
```

### C++ 시뮬레이션 예제

`code/example_cpp_simulation.cpp` 참고:

```bash
# 컴파일 (Windows - MinGW)
g++ -std=c++17 code/example_cpp_simulation.cpp -o example_sim.exe

# 실행
./example_sim.exe
```

출력:
```
=== Auto-loaded from summary_20251206_163045.json ===
Time constant τ = 0.4123 ± 0.0052 s
DC gain K = 2.4567 ± 0.0234 (deg/s)/PWM

System Parameters:
  τ = 0.4123 s
  K = 2.4567 (deg/s)/PWM

Running simulation...
Simulation complete!

Performance Metrics:
  Final position: 199.9876 deg
  Steady-state error: 0.0124 deg
  Overshoot: 12.34 %

Results saved to cpp_simulation_results.csv
```

---

## 🎯 Arduino에서는?

### ❌ Arduino에서 data_loader.hpp 사용 불가

Arduino에는 파일 시스템이 없어서 `data/` 폴더를 읽을 수 없습니다.

### ✅ 대신 이렇게 하세요

#### 방법 1: 하드코딩 (간단)

```cpp
// code/p2-1.cpp
float Kp = 10.5;  // Matlab/Python에서 계산한 값 직접 입력
float Ki = 5.2;
float Kd = 2.8;
```

#### 방법 2: Serial 입력 (동적)

```cpp
// p2-1.cpp는 이미 Serial 명령어 지원
// Serial Monitor에서:
G:10.5,5.2,2.8  // 게인 업데이트
```

#### 방법 3: EEPROM 저장 (고급)

```cpp
#include <EEPROM.h>

// PC에서 계산 → Serial로 전송 → EEPROM 저장 → 재부팅 후 로드
```

---

## 🔄 통합 워크플로우

### 전체 흐름

```
1. 데이터 수집 (Arduino)
   python run.py 1-3
   → 'p' 키로 data/1-3/ 저장

2. PID 설계 (PC)

   Option A: Python
   python src/p2-1_pid_simulation.py
   → data_loader.py 사용 ✅

   Option B: Matlab
   p2-1_pid_design
   → py.data_loader.load_system_parameters() 호출 ✅

   Option C: C++
   g++ -std=c++17 code/example_cpp_simulation.cpp -o sim
   ./sim
   → data_loader.hpp 사용 ✅

3. Arduino 적용
   code/p2-1.cpp에 Kp, Ki, Kd 하드코딩
   또는 Serial 명령어 사용
```

---

## 📋 주요 함수 요약

### Python (`data_loader.py`)

| 함수 | 입력 | 출력 | 설명 |
|------|------|------|------|
| `load_system_parameters(task)` | task_name | (tau, K) | 간단히 τ, K만 로드 |
| `load_latest_summary(task)` | task_name | (tau, K, dict) | 전체 메타데이터 포함 |
| `load_latest_raw_data(task)` | task_name | (time, vel, duty) | Raw CSV 로드 |
| `load_latest_pid_data(task)` | task_name | (t, pos, ref, err, ctrl) | PID CSV 로드 |
| `list_all_summaries(task)` | task_name | List[dict] | 모든 summary 나열 |

### C++ (`data_loader.hpp`)

| 함수 | 입력 | 출력 | 설명 |
|------|------|------|------|
| `load_system_parameters(task)` | task_name | pair<tau, K> | 간단히 τ, K만 로드 |
| `load_latest_summary(task)` | task_name | tuple<tau, K, meta> | 전체 메타데이터 포함 |
| `load_latest_raw_data(task)` | task_name | RawData struct | Raw CSV 로드 |

---

## ✅ 장점

### 1. **코드 재사용**
- Python, Matlab, C++ 모두 동일한 로직 사용
- 한 번 작성, 여러 곳에서 사용

### 2. **유지보수 용이**
- 데이터 형식 변경 시 한 곳만 수정
- 버그 수정 시 모든 코드에 자동 반영

### 3. **안전한 컴파일**
- C++ Header-only: include 안 하면 컴파일 에러 없음 ✅
- Arduino 코드에 영향 없음

### 4. **명확한 인터페이스**
- 함수 이름이 직관적
- 타입 힌트와 문서화 제공

---

## 🛠️ 테스트

### Python 테스트

```bash
python src/data_loader.py
```

출력:
```
=== Auto-loaded from summary_20251206_163045.json ===
Time constant τ = 0.4123 ± 0.0052 s
DC gain K = 2.4567 ± 0.0234 (deg/s)/PWM
Data points: 1523
Timestamp: 20251206_163045

✓ Successfully loaded: τ=0.4123, K=2.4567

All available summaries for task 1-3:
  1. summary_20251206_163045.json: τ=0.4123, K=2.4567
  2. summary_20251206_143022.json: τ=0.4089, K=2.4501
```

### C++ 테스트

```bash
g++ -std=c++17 code/example_cpp_simulation.cpp -o test_loader
./test_loader
```

---

## ❓ FAQ

### Q1: Matlab에서 Python 함수를 어떻게 호출하나요?

```matlab
% Python path 추가
src_path = fullfile(pwd, 'src');
insert(py.sys.path, int32(0), src_path);

% Python 함수 호출
result = py.data_loader.load_system_parameters('1-3');
tau = double(result{1});
K = double(result{2});
```

### Q2: Arduino에서는 왜 사용 못하나요?

Arduino에는 파일 시스템이 없어서 `data/` 폴더를 읽을 수 없습니다.
대신 PC에서 계산한 값을 하드코딩하거나 Serial로 전송하세요.

### Q3: C++ 컴파일 에러가 나요!

- C++17 이상인지 확인: `g++ --version`
- `std::filesystem` 지원 확인
- Windows MinGW의 경우 최신 버전 필요

### Q4: 이전 데이터도 보존되나요?

네! 항상 **최신 파일**만 로드하지만, 이전 파일은 삭제되지 않습니다.
`list_all_summaries()`로 모든 측정 데이터를 확인할 수 있습니다.

---

## 📝 추가 개선 아이디어

- [ ] 특정 timestamp 파일 선택 기능
- [ ] 여러 측정 데이터 비교 함수
- [ ] 통계 분석 함수 (평균, 표준편차, 신뢰구간)
- [ ] 자동 플롯 생성 함수
- [ ] Matlab Native JSON 파서 최적화

---

**Created by**: Claude Code
**Date**: 2025-12-06
**Version**: 1.0

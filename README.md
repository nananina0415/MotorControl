# Motor Control Project

## 프로젝트 구조

```
MotorControl/
├── code/                   # Arduino 코드 모음
│   ├── p1-1.cpp            # Task 1-1: 각속도 측정 (d=200)
│   ├── p1-2.cpp            # Task 1-2: 타우 측정 (자동 듀티 순환)
│   ├── p1-3.cpp            # Task 1-3: K 파라미터 측정 (DC 게인)
│   └── stop.cpp            # 모터 정지
├── src/
│   └── plotter.py          # 범용 플로터
├── run.py                  # 자동 업로드 스크립트
├── legacy/                 # 원본 파일 보관
└── platformio.ini          # PlatformIO 설정
```

## 사용 방법

### 0. 빠른 업로드 (자동화 스크립트)

```bash
python run.py <n-m>
```

예시:
```bash
python run.py 1-1  # code/p1-1.cpp를 업로드
python run.py 1-2  # code/p1-2.cpp를 업로드
python run.py 1-3  # code/p1-3.cpp를 업로드
python run.py stop # code/stop.cpp를 업로드 (모터 정지)
```

스크립트가 자동으로:
1. 실행 중인 플로터 자동 종료 (psutil 설치 시)
2. code/pn-m.cpp를 src/main.cpp로 복사
3. PlatformIO로 빌드 및 업로드
4. src/ 폴더 정리
5. 플로터 자동 실행

**필수 패키지 설치:**
```bash
pip install psutil  # 플로터 자동 종료용 (선택사항)
```

### 1. 환경변수 설정

**Windows PowerShell:**
```powershell
$env:COM_MEGA2560="COM4"
```

**Windows CMD:**
```cmd
set COM_MEGA2560=COM4
```

**Linux/Mac:**
```bash
export COM_MEGA2560=/dev/ttyUSB0
```

### 2. Task 실행

#### Task 1-1 실행 (d=200, 각속도 측정)

```bash
python run.py 1-1
```
→ 자동으로 업로드 후 플로터 실행됨

#### Task 1-2 실행 (자동 듀티 순환, τ 측정)

```bash
python run.py 1-2
```
→ 자동으로 업로드 후 플로터 실행됨

#### Task 1-3 실행 (K 파라미터 측정)

```bash
python run.py 1-3
```
→ 자동으로 업로드 후 플로터 실행됨

#### 모터 정지

```bash
python run.py stop
```

### 플로터 사용법
- **'c' 키**: 현재 플롯 데이터 지우기 (새로운 측정 시작)
- **'p' 키**: 플로터 일시정지 + 데이터 자동 저장
  - 그래프 이미지 저장 (PNG, 300 DPI)
  - 측정값 원본 저장 (CSV)
  - 계산된 값 저장 (JSON: τ, K 평균/표준편차 등)
  - **저장 위치**: `data/{n-m}/` (예: `data/1-3/`)
  - **자동 사용**: Matlab/Python 코드가 `data/` 폴더에서 자동으로 읽어서 사용
- **플롯 창 닫기**: 플로터 종료
- **Ctrl+C**: 강제 종료

## Task 설명

### Task 1-1: 각속도 측정
- PWM duty d=200으로 모터 구동
- 실시간으로 각속도 측정 및 플롯
- 측정 주기: 50ms (필터 없는 원본 데이터)

### Task 1-2: 타임 상수 Tau 측정
- Arduino가 자동으로 d = [150, 175, 200, 225, 250]을 순환
- 각 d값에서 5초간 실행 → 모터 정지 → 2초 대기 → 다음 d값
- 모든 사이클 완료 후 자동 재시작
- 연속 타임라인으로 데이터 수집
- 측정 주기: 50ms (필터 없는 원본 데이터)
- 상승 응답 63.2% 기준으로 τ 계산

### Task 1-3: DC 게인 K 파라미터 측정
- Task 1-2와 동일하게 d = [150, 175, 200, 225, 250]을 순환
- 각 듀티값에서 정상상태 속도(ω_ss) 측정
- DC 게인 계산: K = ω_ss / d
- 각 듀티값에 대해 K값을 계산하여 변동 확인
- τ 측정도 함께 수행 (Task 1-2 기능 포함)
- 측정 주기: 50ms
- 플로터에 K 라벨(녹색)과 τ 라벨(노란색) 동시 표시

## 데이터 형식

Arduino는 다음 형식으로 데이터를 전송합니다:

### 기본 속도 데이터
```
Data:Duty,Time,Velocity
```

예시:
```
Data:200,1.234,567.8
```

### Tau 측정 데이터 (Task 1-2, 1-3)
```
Tau:Duty,Time,TauValue
```

예시:
```
Tau:200,3.456,0.423
```

### K 파라미터 데이터 (Task 1-3)
```
K:Duty,Time,K_value,SteadyVelocity
```

예시:
```
K:200,5.000,2.845,569.0
```

## 주의사항

- `src/` 폴더는 PlatformIO 업로드 전용
- 각 태스크 폴더의 .cpp 파일을 src/로 복사 후 업로드
- 범용 플로터 하나로 모든 실험 데이터 시각화 가능

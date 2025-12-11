# 작업 세션 요약

**날짜**: 2025-12-06
**프로젝트**: Motor Control - PID 제어 시스템

---

## ✅ 완료된 작업

### 1. P#1 시리즈 완료
- ✅ **P#1-1** (`code/p1-1.cpp`): d=200에서 각속도 측정
- ✅ **P#1-2** (`code/p1-2.cpp`): 자동 듀티 순환 + τ(타우) 측정
  - 상승 응답 63.2% 기준으로 τ 계산
  - D_VALUES = [150, 175, 200, 225, 250]
  - STEADY_TIME = 5초, STOP_TIME = 2초
- ✅ **P#1-3** (`code/p1-3.cpp`): K 파라미터 측정
  - K = ω_ss / d (DC 게인)
  - τ 측정도 포함 (P#1-2 기능 유지)

### 2. 플로터 시스템 (`src/plotter.py`)
- ✅ 범용 플로터 구현
- ✅ 데이터 형식:
  - `Data:duty,time,velocity` - 기본 속도 데이터
  - `Tau:duty,time,tau_value` - τ 라벨 (노란색 박스)
  - `K:duty,time,K_value,steady_velocity` - K 라벨 (녹색 박스)
- ✅ 키 기능:
  - **'c' 키**: 데이터 지우기
  - **'p' 키**: 일시정지 (업데이트 중단, 창 유지)
  - **창 닫기**: 플로터 종료

### 3. 자동 업로드 스크립트 (`run.py`)
- ✅ 사용법: `python run.py n-m` (예: `python run.py 1-3`)
- ✅ 자동 기능:
  - 실행 중인 plotter 종료 (psutil)
  - PlatformIO로 빌드 및 업로드
  - src/ 폴더 정리
  - 플로터 자동 실행
- ✅ Stop 명령: `python run.py stop`

### 4. P#2-1 준비
- ✅ PID 설계 이론 정리 (`P2_PID_Design_Ideas.md`)
  - Root Locus 방법 (전통적)
  - Gradient Descent 최적화 (현대적)
  - Multi-objective Optimization
- ✅ Matlab 코드 작성 (`p2-1_pid_design.m`)
  - Pole placement 기반 PID 설계
  - fmincon 최적화
  - R=200, 150, 250 테스트
  - 성능 지표 자동 계산

### 5. 프로젝트 구조

```
MotorControl/
├── code/
│   ├── p1-1.cpp          ✅ 각속도 측정 (d=200)
│   ├── p1-2.cpp          ✅ τ 측정 (자동 듀티 순환)
│   ├── p1-3.cpp          ✅ K 파라미터 측정
│   └── stop.cpp          ✅ 모터 정지
├── src/
│   └── plotter.py        ✅ 범용 플로터 (⬜ 저장 기능 추가 예정)
├── data/                 ⬜ 측정 데이터 저장소 (다음 세션에서 생성)
│   ├── 1-1/              ⬜ Task 1-1 데이터
│   ├── 1-2/              ⬜ Task 1-2 데이터 (τ)
│   └── 1-3/              ⬜ Task 1-3 데이터 (τ, K)
├── run.py                ✅ 자동 업로드 스크립트
├── p2-1_pid_design.m     ✅ Matlab PID 설계 (⬜ 자동 로딩 추가 예정)
├── P2_PID_Design_Ideas.md  ✅ 이론 및 계획
├── SESSION_SUMMARY.md    ✅ 이전 작업 요약
├── NEXT_TASKS.md         ✅ 다음 작업 계획 (저장 기능)
├── START_HERE.md         ✅ 빠른 시작 가이드
├── README.md             ✅ 전체 문서
└── platformio.ini        ✅ PlatformIO 설정
```

---

## 📊 현재 상태

### 측정 필요:
- **P#1-3 실행 대기**: `python run.py 1-3`
  - d=150, 175, 200, 225, 250 각각에 대한 τ, K 측정 필요
  - 플로터에서 수동으로 값 기록 중

### 다음 단계:
1. P#1-3 실행하여 τ, K 측정
2. 측정값을 Matlab 코드에 입력
3. P#2-1 PID 설계 실행
4. 보고서 작성

---

## 🔧 기술적 결정 사항

### 1. τ 측정 알고리즘 (p1-2.cpp, p1-3.cpp)
- **상승 응답 63.2% 기준** (step-up response)
- EMA로 정상상태 추정 (3초 이후부터)
  ```cpp
  steadyStateVelocity = 0.9 * prev + 0.1 * current
  threshold = startVel + (steadyVel - startVel) * 0.632
  ```
- 이유: PDF 15-16페이지에서 명시

### 2. K 계산 (p1-3.cpp:128)
```cpp
K_value = steadyStateVelocity / K_duty;
```
- 조건: `steadyStateVelocity > 50 && K_duty > 0`
- 문제 가능성: d=150에서 속도 < 50이면 계산 안 됨
- 해결책: 필요시 임계값 낮추기

### 3. 플로터 pause 기능
- 'p' 누르면 `paused = True`
- 시리얼 버퍼는 계속 비움 (오버플로우 방지)
- 'q'는 matplotlib 기본 단축키라 사용 안 함

### 4. run.py 형식 변경
- 기존: `python run.py 1 1` (2개 인자)
- 변경: `python run.py 1-1` (1개 인자, 하이픈 구분)

---

## 📝 주요 파라미터

### Arduino 설정
- **보드**: Arduino Mega 2560
- **모터 핀**: ENA=6, IN1=7, IN2=8
- **엔코더 핀**: 20, 21
- **PPR**: 374.0
- **시리얼 보드레이트**: 115200
- **측정 주기**: 50ms

### P#1-2, P#1-3 공통
- **듀티 값**: [150, 175, 200, 225, 250]
- **각 듀티 실행 시간**: 5초
- **정지 대기 시간**: 2초
- **자동 재시작**: 모든 사이클 완료 후

### 성능 조건 (P#2-1)
- overshoot < 15%
- settling time ≤ 0.5s
- steady-state error = 0

---

## 🐛 알려진 이슈

1. **K 계산 임계값 (50 deg/s)**
   - 낮은 듀티에서 문제 가능
   - 위치: `p1-3.cpp:127`
   - 해결: 필요시 20-30으로 낮추기

2. **플로터 시리얼 버퍼**
   - pause 시에도 버퍼 비우기 구현됨
   - 위치: `plotter.py:84-91`

---

## 💡 설계 철학

### "기존 코드 수정 금지" 원칙
- P#1-1, P#1-2는 수정 안 함
- P#1-3는 P#1-2를 **복사**하여 K 계산 추가
- 이유: 각 과제의 독립성 유지

### 범용 플로터
- 하나의 플로터로 모든 과제 지원
- 데이터 형식만 다르게 전송
- 확장 가능한 구조

---

## 🎯 목표

- [x] P#1-1: 각속도 측정
- [x] P#1-2: τ 측정
- [x] P#1-3: K 측정 (코드 완료, 실행 대기)
- [ ] P#2-1: PID 설계 (Matlab 코드 완료, τ/K 측정 필요)
- [ ] P#2-2: 실제 PID 구현 (Arduino)
- [ ] P#3: Full-State Feedback Controller

---

## 📚 참고 자료

- **PDF**: `2025_TermProject-MatlabArduino_MotorPIDControl.pdf`
- **전달함수**: G(s) = K / [s(τs+1)]
- **State Space**: 4페이지 참조
- **Root Locus**: 10페이지 참조

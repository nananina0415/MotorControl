# P#2: PID Controller Design - 두 가지 접근법 비교

## 목표

- overshoot < 15%
- settling time (ts) ≤ 0.5s
- no steady-state error

## 방법 1: Root Locus (전통적 제어 이론)

### 원리

폐루프 특성방정식의 극점 위치로 시스템 성능 예측:

- 실수부 (σ): settling time 결정 (ts ≈ 4.6/|σ|)
- 허수부 (ω): 진동 주파수
- 감쇠비 (ζ): overshoot 결정

### 설계 절차

```matlab
% 1. P#1-3에서 측정한 파라미터 사용
tau = (측정값);  % 예: 0.4
K = (측정값);    % 예: 2.5

% 2. 성능 조건 → 극점 위치 계산
overshoot < 15% → ζ > 0.52
ts ≤ 0.5s → σ = 4.6/ts = 9.2

% 3. 목표 극점 설정
zeta = 0.52;
wn = sqrt(sigma^2 / zeta^2);
desired_poles = [-sigma + j*wn*sqrt(1-zeta^2),
                 -sigma - j*wn*sqrt(1-zeta^2)];

% 4. State-space 표현
A = [0 1; 0 -1/tau];
B = [0; K/tau];
C = [1 0];
D = [0];

% 5. PID 게인 계산
% (pole placement 또는 PID tuner 사용)
```

### 장점

- ✅ 분석적/확정적 방법
- ✅ 시각적 직관 (극점 궤적)
- ✅ 수학적 보장 (극점 = 성능)
- ✅ 빠른 계산

### 단점

- ❌ 복잡한 제약 조건 처리 어려움
- ❌ 비선형 시스템에 적용 제한적

---

## 방법 2: Gradient Descent Optimization (현대적 접근)

### 원리

손실 함수를 정의하고 gradient를 따라 최적 게인 탐색

### 손실 함수 설계

```python
def loss_function(Kp, Ki, Kd, tau, K):
    """
    PID 게인 조합의 성능을 평가하는 손실 함수
    """
    # 1. 폐루프 시스템 구성
    # G(s) = K / (s(τs+1))
    # C(s) = Kp + Ki/s + Kd*s

    # 2. 스텝 응답 시뮬레이션
    sys_cl = feedback(C * G, 1)
    t, y = step_response(sys_cl)

    # 3. 성능 지표 계산
    overshoot = (max(y) - 1.0) * 100  # %
    settling_time = get_settling_time(t, y, threshold=0.02)
    steady_state_error = abs(1.0 - y[-1])

    # 4. Penalty 기반 손실 함수
    loss = 0

    # 조건 위반 시 큰 페널티
    loss += max(0, overshoot - 15)**2 * 1000
    loss += max(0, settling_time - 0.5)**2 * 100
    loss += steady_state_error**2 * 500

    # 5. 추가 목적: 제어 노력 최소화 (게인 크기 제한)
    loss += (Kp**2 + Ki**2 + Kd**2) * 0.01

    # 6. 추가 목적: 노이즈 민감도 (Kd 너무 크면 페널티)
    loss += max(0, Kd - 5)**2 * 10

    return loss
```

### 최적화 알고리즘

```python
import numpy as np
from scipy.optimize import minimize

# P#1-3에서 측정한 값
tau = 0.4
K = 2.5

# 손실 함수 래핑
def objective(params):
    Kp, Ki, Kd = params
    return loss_function(Kp, Ki, Kd, tau, K)

# 초기값
x0 = [10.0, 5.0, 2.0]  # [Kp, Ki, Kd]

# 경계 조건
bounds = [
    (0, 50),   # Kp 범위
    (0, 50),   # Ki 범위
    (0, 10)    # Kd 범위
]

# 최적화 실행
result = minimize(
    objective,
    x0=x0,
    method='L-BFGS-B',  # 또는 'SLSQP', 'trust-constr'
    bounds=bounds,
    options={'maxiter': 1000}
)

Kp_opt, Ki_opt, Kd_opt = result.x
print(f"Optimal gains: Kp={Kp_opt:.3f}, Ki={Ki_opt:.3f}, Kd={Kd_opt:.3f}")
```

### Numerical Gradient (유한차분법)

```python
def numerical_gradient(f, x, eps=1e-6):
    """
    수치적 기울기 계산
    """
    grad = np.zeros_like(x)
    for i in range(len(x)):
        x_plus = x.copy()
        x_minus = x.copy()
        x_plus[i] += eps
        x_minus[i] -= eps
        grad[i] = (f(x_plus) - f(x_minus)) / (2 * eps)
    return grad

# Gradient Descent 직접 구현
def gradient_descent(f, x0, lr=0.01, max_iter=1000):
    x = x0.copy()
    history = [x.copy()]

    for i in range(max_iter):
        grad = numerical_gradient(f, x)
        x = x - lr * grad

        # 경계 조건 적용
        x = np.clip(x, [0, 0, 0], [50, 50, 10])

        history.append(x.copy())

        if i % 100 == 0:
            print(f"Iter {i}: Loss={f(x):.4f}, Kp={x[0]:.2f}, Ki={x[1]:.2f}, Kd={x[2]:.2f}")

    return x, history
```

### 장점

- ✅ 복잡한 제약 조건 쉽게 추가
- ✅ 다목적 최적화 자연스럽게 처리
- ✅ 비선형 시스템에도 적용 가능
- ✅ 실측 데이터 기반 최적화 가능

### 단점

- ❌ 국소 최적해에 빠질 수 있음 (초기값 의존)
- ❌ 계산 시간 오래 걸림
- ❌ 수학적 보장 없음

---

## 방법 3: Multi-Objective Optimization (Pareto Front)

### 개념

여러 목표를 동시에 최적화하여 **최적해 범위** 도출

```python
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import Problem

class PIDOptimizationProblem(Problem):
    def __init__(self, tau, K):
        super().__init__(
            n_var=3,  # Kp, Ki, Kd
            n_obj=3,  # overshoot, ts, control_effort
            n_constr=0,
            xl=[0, 0, 0],
            xu=[50, 50, 10]
        )
        self.tau = tau
        self.K = K

    def _evaluate(self, X, out, *args, **kwargs):
        """
        X: (N, 3) array of [Kp, Ki, Kd]
        """
        f1 = []  # overshoot
        f2 = []  # settling time
        f3 = []  # control effort (Kp^2 + Ki^2 + Kd^2)

        for params in X:
            Kp, Ki, Kd = params
            # 시뮬레이션
            overshoot, ts = simulate_pid(Kp, Ki, Kd, self.tau, self.K)
            control_effort = Kp**2 + Ki**2 + Kd**2

            f1.append(overshoot)
            f2.append(ts)
            f3.append(control_effort)

        out["F"] = np.column_stack([f1, f2, f3])

# NSGA-II 실행
algorithm = NSGA2(pop_size=100)
res = minimize(
    PIDOptimizationProblem(tau, K),
    algorithm,
    termination=('n_gen', 200)
)

# Pareto front 시각화
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(res.F[:, 0], res.F[:, 1], res.F[:, 2])
ax.set_xlabel('Overshoot (%)')
ax.set_ylabel('Settling Time (s)')
ax.set_zlabel('Control Effort')
plt.show()
```

---

## 비교 실험 계획

### 1. 구현

- **Matlab**: Root Locus 방법
- **Python**: Gradient Descent + Multi-objective

### 2. 측정 지표

| 방법       | Kp  | Ki  | Kd  | Overshoot | ts  | ess | 계산시간 |
| ---------- | --- | --- | --- | --------- | --- | --- | -------- |
| Root Locus | ?   | ?   | ?   | ?         | ?   | ?   | ?        |
| L-BFGS-B   | ?   | ?   | ?   | ?         | ?   | ?   | ?        |
| NSGA-II    | ?   | ?   | ?   | ?         | ?   | ?   | ?        |

### 3. 분석 포인트

- 성능 비교: 모든 방법이 조건 만족하는가?
- 게인 차이: 왜 다른 조합이 나오는가?
- Trade-off: Pareto front로 시각화
- Robustness: 파라미터 변화(τ, K)에 대한 민감도

### 4. Discussion

- Root Locus: 이론적 명확성, 교육적 가치
- GD: 실용성, 확장성
- Multi-obj: 의사결정 지원

---

## 구현 파일 구조

```
MotorControl/
├── p2-1_root_locus.m          # Matlab: Root Locus 설계
├── p2-1_gradient_descent.py   # Python: GD 최적화
├── p2-1_pareto.py              # Python: Multi-objective
├── p2_comparison.py            # 결과 비교 스크립트
└── results/
    ├── root_locus_response.png
    ├── gd_response.png
    ├── pareto_front.png
    └── comparison_table.csv
```

---

## 참고 문헌

- Åström, K. J., & Hägglund, T. (2006). Advanced PID control.
- Ziegler, J. G., & Nichols, N. B. (1942). Optimum settings for automatic controllers.
- Deb, K., et al. (2002). A fast and elitist multiobjective genetic algorithm: NSGA-II.

---

## 결론

전통적 방법(Root Locus)과 현대적 방법(Optimization)을 모두 적용하여:

1. 각 방법의 장단점 이해
2. 최적해의 비유일성(non-uniqueness) 확인
3. 다양한 설계 관점 습득

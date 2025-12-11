# 문제 2-1 풀이: 전통적 방법(극점 배치법)을 이용한 PID 설계

이 문서는 `P2_PID_Design_Ideas.md`에 기술된 **전통적 방법(Traditional Method)**, 즉 **극점 배치법(Pole Placement)**을 사용하여 **문제 2-1**을 해결하는 단계별 계산 과정을 상세히 설명합니다.

> **업데이트 (2025.12.11): 요청하신 새 파라미터($\tau=3.0, K=5.7$)를 반영하여 계산했습니다.**

## 1. 시스템 파라미터 선정

사용자 지정 파라미터:
*   **시상수 ($\tau$)**: **$3.0$ s**
*   **DC 이득 ($K$)**: **$5.7$ (deg/s)/PWM**

---

## 2. 설계 요구사항

1.  **초과 (Overshoot, $M_p$)**: $< 15\%$
2.  **정착 시간 (Settling Time, $t_s$)**: $\le 0.5s$ (2% 기준)
3.  **정상 상태 오차 (Steady-State Error, $e_{ss}$)**: $0$

---

## 3. 이론적 유도 및 계산

### 1단계: 목표 폐루프 극점(Desired Closed-Loop Poles) 결정

**1. 감쇠비 ($\zeta$) 결정:**
오버슈트 15% 조건에서 $\zeta > 0.517$. 안전하게 **$\zeta = 0.6$** 선정.

**2. 실수부 ($\sigma$) 및 고유 진동수 ($\omega_n$) 결정:**
정착 시간 $0.5s$ 조건에서:
$$ \sigma \ge \frac{4.6}{0.5} = 9.2 \implies \text{선정: } \sigma = 9.2 $$
$$ \omega_n = \frac{\sigma}{\zeta} = \frac{9.2}{0.6} \approx 15.33 \text{ rad/s} $$

**지배 극점 위치:** $s_{1,2} = -9.2 \pm j12.26$

### 2단계: 추가 극점 배치

3차 시스템이므로 추가 극점 $s_3 = -\alpha$가 필요합니다.
지배 극점보다 5배 빠르게 설정: **$\alpha = 5\sigma = 46$**

### 3단계: 게인($K_p, K_i, K_d$) 계산

전통적 방법(극점 배치법)의 공식에 파라미터를 대입합니다.

**공통 항:**
*   $2\zeta\omega_n = 18.4$
*   $\omega_n^2 \approx 235.0$

**1. $K_d$ (미분 게인) 계산:**
$$ K_d = \frac{\tau(\alpha + 2\zeta\omega_n) - 1}{K} $$
$$ K_d = \frac{3.0(46 + 18.4) - 1}{5.7} = \frac{3.0(64.4) - 1}{5.7} = \frac{192.2}{5.7} \approx \mathbf{33.72} $$

**2. $K_p$ (비례 게인) 계산:**
$$ K_p = \frac{\tau(2\zeta\omega_n \alpha + \omega_n^2)}{K} $$
$$ K_p = \frac{3.0(18.4 \times 46 + 235.0)}{5.7} = \frac{3.0(846.4 + 235)}{5.7} = \frac{3244.2}{5.7} \approx \mathbf{569.16} $$

**3. $K_i$ (적분 게인) 계산:**
$$ K_i = \frac{\tau \alpha \omega_n^2}{K} $$
$$ K_i = \frac{3.0(46 \times 235.0)}{5.7} = \frac{3.0(10810)}{5.7} = \frac{32430}{5.7} \approx \mathbf{5689.47} $$

---

## 4. 최종 결과

$$ \mathbf{K_p = 569.16}, \quad \mathbf{K_i = 5689.47}, \quad \mathbf{K_d = 33.72} $$

> **주의**: 여전히 게인 값이 매우 커서 PWM 포화가 예상됩니다.

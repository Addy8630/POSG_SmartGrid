# POSG SmartGrid Payoff Functions Presentation

## Slide 1: Title
**POSG SmartGrid: Payoff Functions Analysis**

- Defender Payoff Matrices for Each Game Stage
- Strategic Decision Framework
- Cost-Benefit Analysis for Cyber Defense

*Presenter: AI Assistant*

---

## Slide 2: Payoff Formula Overview
**General Defender Payoff Formula:**

```
U_D(aA, aD) = w1 × Prevention(stage, aD)
            - w2 × P_success(stage, aA, aD) × Damage(stage, aA)
            - w3 × DefenseCost(stage, aD)
            - w4 × OperationalDisruption(stage, aD)
```

**Weights:**
- w1 = 1.0 (Prevention benefit multiplier)
- w2 = 1.0 (Damage cost multiplier)
- w3 = 0.5 (Defense cost multiplier)
- w4 = 0.3 (Operational disruption multiplier)

**Note:** Execute stage caps disruption: max(1, OperationalDisruption)

---

## Slide 3: NORMAL Stage Payoff Matrix
**Stage: NORMAL**
- Attacker: NoAttack only
- Defender: Monitor, LightScan

**Payoff Matrix (U_D):**

| Attacker \ Defender | Monitor | LightScan |
|---------------------|---------|-----------|
| NoAttack           | 0.85   | 0.35     |

**Calculation Example:**
- Monitor: U = 1.0×1.0 - 0×0 - 0.5×0.5 - 0.3×0.0 = 0.85
- LightScan: U = 1.0×2.0 - 0×0 - 0.5×1.0 - 0.3×1.0 = 0.35

---

## Slide 4: RECON Stage Payoff Matrix
**Stage: RECON**
- Attacker: PingSweep, PortScan, ServiceProbe
- Defender: Monitor, Honeypot, RateLimit, IDS+Honey

**Payoff Matrix (U_D):**

| Attacker \ Defender | Monitor | Honeypot | RateLimit | IDS+Honey |
|---------------------|---------|----------|-----------|-----------|
| PingSweep          | -0.45  | 1.55    | 0.60     | 2.65     |
| PortScan           | -1.20  | 0.80    | -0.15    | 1.90     |
| ServiceProbe       | -1.95  | 0.05    | -0.90    | 1.15     |

**Key Insight:** IDS+Honey provides highest payoff across all attacker actions.

---

## Slide 5: COMPROMISE Stage Payoff Matrix
**Stage: COMPROMISE**
- Attacker: ModbusRead, SSHBrute, CVEExploit
- Defender: Monitor, MFA, IPWhitelist, PatchCVE

**Payoff Matrix (U_D):**

| Attacker \ Defender | Monitor | MFA    | IPWhitelist | PatchCVE |
|---------------------|---------|--------|-------------|----------|
| ModbusRead         | -0.95  | 1.05  | 1.60       | 2.65    |
| SSHBrute           | -1.45  | 0.55  | 1.10       | 2.15    |
| CVEExploit         | -2.45  | -0.45 | 0.10       | 1.15    |

**Key Insight:** PatchCVE is most effective against CVEExploit, but costly.

---

## Slide 6: WEAPONIZE Stage Payoff Matrix
**Stage: WEAPONIZE**
- Attacker: FDIPrep, ModbusWrite, Backdoor
- Defender: Monitor, PhysicsCheck, IsolateIBR, Sandbox

**Payoff Matrix (U_D):**

| Attacker \ Defender | Monitor | PhysicsCheck | IsolateIBR | Sandbox |
|---------------------|---------|--------------|------------|---------|
| FDIPrep            | -1.45  | 1.55        | 2.60      | 2.05   |
| ModbusWrite        | -2.20  | 0.80        | 1.85      | 1.30   |
| Backdoor           | -2.45  | 0.55        | 1.60      | 1.05   |

**Key Insight:** IsolateIBR provides strong protection against all weaponization actions.

---

## Slide 7: EXECUTE Stage Payoff Matrix
**Stage: EXECUTE**
- Attacker: DNP3Trip, FDICascade, Ransomware
- Defender: Monitor, EmergBlock, Rollback, Block+Rollback

**Payoff Matrix (U_D):**

| Attacker \ Defender | Monitor | EmergBlock | Rollback | Block+Rollback |
|---------------------|---------|------------|----------|----------------|
| DNP3Trip           | -3.45  | 0.55      | 1.60    | 3.65          |
| FDICascade         | -3.70  | 0.30      | 1.35    | 3.40          |
| Ransomware         | -3.20  | 0.80      | 1.85    | 3.90          |

**Key Insight:** Block+Rollback maximizes payoff but has highest operational disruption.

---

## Slide 8: Payoff Analysis Summary
**Stage Comparison:**

| Stage       | Best Defender Action | Avg Payoff | Risk Level |
|-------------|----------------------|------------|------------|
| NORMAL     | Monitor             | 0.60     | Low       |
| RECON      | IDS+Honey          | 1.63     | Medium    |
| COMPROMISE | PatchCVE            | 1.49     | High      |
| WEAPONIZE  | IsolateIBR          | 1.78     | High      |
| EXECUTE    | Block+Rollback      | 2.33     | Critical  |

**Trends:**
- Payoff increases with stage severity
- Advanced defenses needed for later stages
- Operational disruption costs rise significantly

---

## Slide 9: Strategic Implications
**Defender Strategy:**
- Early stages: Balance monitoring with light defenses
- Mid stages: Invest in targeted protections (MFA, patching)
- Late stages: Accept high disruption for damage prevention

**Attacker Strategy:**
- Recon: Use low-risk probes first
- Compromise: Target unpatched vulnerabilities
- Execute: Choose actions with highest expected payoff

**Nash Equilibrium Considerations:**
- Mixed strategies may be optimal
- Belief uncertainty affects decisions

---

## Slide 10: Implementation in Code
**Key Functions:**
- `compute_payoff_matrix(stage)` in `posg_models.py`
- Returns np.ndarray shape [n_aA, n_aD]
- Pre-computed in PAYOFF dict

**Usage:**
```python
from posg_models import get_payoff
payoff_matrix = get_payoff(S.RECON)  # Shape: [3, 4]
```

**EU Maximization:**
```python
expected_utility = payoff_matrix.mean(axis=0)  # Average over attacker actions
best_action_idx = np.argmax(expected_utility)
```

---

## Slide 11: Conclusion
**Key Takeaways:**
- Payoff functions quantify cyber defense trade-offs
- Stage-specific matrices guide tactical decisions
- Prevention vs cost balance critical for optimal strategy
- Game theory enables proactive security posture

**Applications:**
- Automated defense policy selection
- Risk assessment for security investments
- Training for cybersecurity decision-making

*Questions?*
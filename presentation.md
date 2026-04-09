# POSG SmartGrid Game Stages Presentation

## Slide 1: Title
**POSG SmartGrid: Game Theory for Smart Grid Security**

- Partially Observable Stochastic Game (POSG) Model
- Attacker vs Defender in Smart Grid Context
- Stages: Normal → Recon → Compromise → Weaponize → Execute

*Presenter: AI Assistant*

---

## Slide 2: Game Overview
**What is POSG?**
- Partially Observable: Defender doesn't see attacker's exact state
- Stochastic: Random transitions and success probabilities
- Game Theory: Attacker and Defender make strategic decisions

**Objective:**
- Defender maximizes security payoff
- Attacker maximizes damage payoff
- Bayesian belief updates for defender uncertainty

---

## Slide 3: Payoff Formula
**Defender Payoff Formula:**

```
U_D = w1 × Prevention(aD)
    - w2 × P_success(aA, aD) × Damage(aA)
    - w3 × DefenseCost(aD)
    - w4 × OperationalDisruption(aD)
```

**Weights:**
- w1 = 1.0 (Prevention benefit)
- w2 = 1.0 (Damage cost)
- w3 = 0.5 (Defense cost)
- w4 = 0.3 (Disruption cost)

---

## Slide 4: Stage 1 - NORMAL
**Initial State**
- No active attack
- Baseline network activity
- Defender monitors for anomalies

**Attacker Actions:**
- NoAttack (only action)

**Defender Actions:**
- Monitor (cost: 0.5)
- LightScan (cost: 1.0)

**Transition:**
- Low probability to Recon (0.05-0.10 depending on defense)

---

## Slide 5: Stage 2 - RECON (Reconnaissance)
**Attacker Goal:** Gather intelligence
- Network scanning and probing
- Identify vulnerabilities

**Attacker Actions:**
- PingSweep (damage: 1.0)
- PortScan (damage: 2.5)
- ServiceProbe (damage: 4.0)

**Defender Actions:**
- Monitor (prevention: 1.0, cost: 0.5)
- Honeypot (prevention: 3.0, cost: 2.0)
- RateLimit (prevention: 2.5, cost: 1.5)
- IDS+Honey (prevention: 4.0, cost: 3.0)

---

## Slide 6: Stage 3 - COMPROMISE
**Attacker Goal:** Gain foothold
- Exploit vulnerabilities
- Establish persistence

**Attacker Actions:**
- ModbusRead (damage: 3.0)
- SSHBrute (damage: 4.0)
- CVEExploit (damage: 6.0)

**Defender Actions:**
- Monitor (prevention: 1.0, cost: 0.5)
- MFA (prevention: 3.0, cost: 2.0)
- IPWhitelist (prevention: 3.5, cost: 1.5)
- PatchCVE (prevention: 4.5, cost: 3.5)

---

## Slide 7: Stage 4 - WEAPONIZE
**Attacker Goal:** Prepare attack payload
- Stage malicious tools
- Configure FDI/backdoors

**Attacker Actions:**
- FDIPrep (damage: 5.0)
- ModbusWrite (damage: 7.0)
- Backdoor (damage: 8.0)

**Defender Actions:**
- Monitor (prevention: 1.0, cost: 0.5)
- PhysicsCheck (prevention: 4.0, cost: 2.5)
- IsolateIBR (prevention: 5.0, cost: 3.0)
- Sandbox (prevention: 4.5, cost: 2.5)

---

## Slide 8: Stage 5 - EXECUTE
**Attacker Goal:** Launch attack
- Execute malicious actions
- Cause system damage

**Attacker Actions:**
- DNP3Trip (damage: 10.0)
- FDICascade (damage: 12.0)
- Ransomware (damage: 9.0)

**Defender Actions:**
- Monitor (prevention: 0.0, cost: 0.5)
- EmergBlock (prevention: 5.0, cost: 4.0)
- Rollback (prevention: 6.0, cost: 3.5)
- Block+Rollback (prevention: 8.0, cost: 5.0)

---

## Slide 9: Transition Model
**Key Features:**
- Every state can return to Normal (de-escalation)
- Attack progression: Normal → Recon → Compromise → Weaponize → Execute
- Defender actions reduce advancement probability
- EPS floor (0.005) prevents belief collapse

**Example Transition (Recon):**
- Monitor: 10% to Normal, 55% stay Recon, 30% to Compromise
- IDS+Honey: 35% to Normal, 60% stay Recon, 4% to Compromise

---

## Slide 10: Observation Model
**Observation Types:**
- Network layer: Normal Traffic, High SYN, Service Probe, Suspicious Login
- OT Protocol layer: Modbus Write, Phasor Anomaly, DNP3 Operate, Freq Deviation

**Mapping:**
- Recon: High probability of network anomalies
- Execute: High probability of OT protocol anomalies
- Normal: Mostly normal traffic

---

## Slide 11: Simulation & UI
**Files:**
- `posg_engine.py`: Core game logic
- `posg_models.py`: Payoff, transition, observation models
- `posg_types.py`: Enums and data structures
- `app.py`: Streamlit web interface
- `run_simulation.py`: Command-line simulation

**Run the UI:**
```bash
pip install streamlit
streamlit run app.py
```

---

## Slide 12: Conclusion
**Key Insights:**
- Game theory provides framework for cyber defense
- Bayesian belief updates handle uncertainty
- Stage-specific actions reflect real APT tactics
- Payoff formula balances security vs operational costs

**Future Work:**
- Multi-agent extensions
- Real-time integration with SIEM
- Machine learning for optimal policies

*Questions?*
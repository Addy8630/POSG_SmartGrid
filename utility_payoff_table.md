# Smart-Grid POSG Utility Payoff Tables

## Defender utility definition

For stage \(s\), attacker action \(a_A\), and defender action \(a_D\), the implemented defender utility is:

$$
U_D(s,a_A,a_D) =
P(s,a_D)
- p_{\mathrm{success}}(s,a_A,a_D)D(s,a_A)
- 0.5C_D(s,a_D)
- 0.3L(s,a_D).
$$

For the Execute stage, the final term is \(0.3\max(1,L(s,a_D))\). Higher values are better for the defender.

| Symbol | Meaning |
|---|---|
| \(P\) | Prevention benefit of the defender action |
| \(p_{\mathrm{success}}\) | Probability that the attacker action succeeds |
| \(D\) | Damage caused by a successful attacker action |
| \(C_D\) | Direct cost of the defender action |
| \(L\) | Operational disruption caused by the defender action |

## Utility payoff matrices

### 1. Normal stage — \(s=\mathrm{NORMAL}\)

| \(U_D(\mathrm{NORMAL},a_A,a_D)\) | Monitor | LightScan |
|---|---:|---:|
| NoAttack | 0.75 | **1.20** |

### 2. Recon stage — \(s=\mathrm{RECON}\)

| \(U_D(\mathrm{RECON},a_A,a_D)\) | Monitor | Honeypot | RateLimit | IDS+Honeypot |
|---|---:|---:|---:|---:|
| PingSweep | -0.10 | 1.40 | 0.90 | **1.65** |
| PortScan | -1.65 | 1.07 | 0.40 | **1.38** |
| ServiceProbe | -2.80 | 0.90 | -0.25 | **1.27** |

### 3. Infection stage — \(s=\mathrm{INFECTION}\)

| \(U_D(\mathrm{INFECTION},a_A,a_D)\) | Monitor | MFA | IPWhitelist | PatchCVE |
|---|---:|---:|---:|---:|
| ModbusRead | -1.95 | 0.20 | 0.80 | **1.10** |
| SSHBrute | -2.95 | 0.60 | 0.25 | **1.00** |
| CVEExploit | -4.95 | -0.40 | -0.85 | **1.40** |

### 4. Installation stage — \(s=\mathrm{INSTALLATION}\)

| \(U_D(\mathrm{INSTALLATION},a_A,a_D)\) | Monitor | PhysicsCheck | IsolateIBR | Sandbox |
|---|---:|---:|---:|---:|
| FDIPrep | -3.70 | 0.65 | **1.30** | 1.10 |
| ModbusWrite | -5.65 | -0.65 | **1.25** | 0.25 |
| Backdoor | -6.90 | -0.65 | 0.30 | **1.15** |

### 5. Execute stage — \(s=\mathrm{EXECUTE}\)

| \(U_D(\mathrm{EXECUTE},a_A,a_D)\) | Monitor | EmergBlock | Rollback | Block+Rollback |
|---|---:|---:|---:|---:|
| DNP3Trip | -10.05 | -1.30 | 0.95 | **4.20** |
| FDICascade | -11.95 | -2.70 | -0.25 | **3.76** |
| Ransomware | -8.65 | -0.45 | 1.70 | **4.48** |

> Bold values identify the best defender response for that attacker action. Values are computed directly from `posg_models.py` using \(w_1=1.0\), \(w_2=1.0\), \(w_3=0.5\), and \(w_4=0.3\).

# Markov Equilibrium Analysis for the Smart-Grid POSG

## 1. Markov equilibrium model

This analysis uses **only a stationary Markov equilibrium**. A strategy depends on the current game information, not on the full path of earlier actions.

Because the defender does not directly observe the attack stage, its Markov information state is its current belief \(b\). Thus:

$$
\pi_D^*(a_D\mid b)
\quad\text{and}\quad
\pi_A^*(a_A\mid s)
$$

are stationary defender and attacker policies. The defender maps its current belief to an action distribution; the attacker maps the current true stage to an action distribution.

For the numerical results below, the defender utility from `posg_models.py` is treated as a zero-sum security game:

$$
U_A(s,a_A,a_D)=-U_D(s,a_A,a_D).
$$

This assumption is required because the current implementation defines \(U_D\) only.

## 2. Markov value equation

With discount factor \(\gamma=0.9\) (the project default), define the state-action value:

$$
Q_s(a_A,a_D)=U_D(s,a_A,a_D)
+\gamma\sum_{s'\in\mathcal S}
T(s'\mid s,a_D)V(s').
$$

The stationary Markov equilibrium value is the minimax value of this matrix game:

$$
V(s)=
\max_{\pi_D\in\Delta(\mathcal A_D(s))}
\min_{\pi_A\in\Delta(\mathcal A_A(s))}
\pi_A^\top Q_s\pi_D.
$$

For the partially observed defender, the current state is replaced by the current belief:

$$
V(b)=
\max_{\pi_D}
\min_{\pi_A}
\sum_s b(s)
\sum_{a_A,a_D}\pi_A(a_A\mid s)\pi_D(a_D\mid b)
\left[U_D+\gamma\mathbb E_{o'}V(b')\right].
$$

The next belief \(b'\) is produced by the project’s existing transition and observation models:

$$
\bar b(s')=\sum_s b(s)\sum_{a_D}\pi_D(a_D\mid b)T(s'\mid s,a_D),
\qquad
b'(s')=\frac{O(o'\mid s')\bar b(s')}
{\sum_jO(o'\mid j)\bar b(j)}.
$$

## 3. Computed stationary Markov equilibrium

The following values were computed by repeatedly applying the Markov value equation until the maximum change in \(V\) was below \(10^{-10}\). The transition model in this project depends on defender action \(a_D\), as implemented in `TRANSITION_MODEL`.

| Current stage \(s\) | Attacker policy \(\pi_A^*(\cdot\mid s)\) | Defender policy \(\pi_D^*(\cdot\mid s)\) | Discounted defender value \(V(s)\) |
|---|---|---|---:|
| Normal | NoAttack: 1.000 | LightScan: 1.000 | 12.264 |
| Recon | ServiceProbe: 1.000 | IDS+Honeypot: 1.000 | 12.380 |
| Infection | SSHBrute: 1.000 | PatchCVE: 1.000 | 11.933 |
| Installation | ModbusWrite: 0.455; Backdoor: 0.545 | IsolateIBR: 0.486; Sandbox: 0.514 | 11.972 |
| Execute | FDICascade: 1.000 | Block+Rollback: 1.000 | 17.694 |

The values are discounted infinite-horizon values, not one-step payoffs. For example, \(V(\text{Execute})\) includes the immediate payoff under Block+Rollback and the expected value of transitions to future stages.

## 4. Equilibrium policy statement

The stationary Markov defender policy is:

$$
\pi_D^*(s)=
\begin{cases}
\text{LightScan}, & s=\text{Normal},\\
\text{IDS+Honeypot}, & s=\text{Recon},\\
\text{PatchCVE}, & s=\text{Infection},\\
0.486\,\text{IsolateIBR}+0.514\,\text{Sandbox}, & s=\text{Installation},\\
\text{Block+Rollback}, & s=\text{Execute}.
\end{cases}
$$

Only Installation requires randomization. The defender should choose IsolateIBR with probability \(0.486\) and Sandbox with probability \(0.514\). This prevents the attacker from exploiting a predictable fixed response.

## 5. Using the policy with partial observations

In operation, the defender should not assume it knows \(s\). After each observation:

1. update \(b\) using `OBSERVATION_MODEL` and `TRANSITION_MODEL`;
2. use the policy corresponding to the dominant stage when a single belief component is clearly largest;
3. when the belief is diffuse, calculate the belief-weighted matrix \(Q(b)=\sum_s b(s)Q_s\) and solve its minimax policy;
4. sample the defender action from that policy and apply the corresponding ONOS rule.

## 6. Difference from the current engine

`posg_engine.py` currently averages over attacker actions uniformly and chooses the defender action with largest expected utility. The Markov equilibrium policy above instead assumes a strategic attacker that minimizes defender utility. Replacing uniform averaging with the minimax policy in Section 2 makes the controller Markov-equilibrium based.

## 7. Assumptions

- Discount factor: \(\gamma=0.9\).
- Zero-sum proxy: \(U_A=-U_D\).
- Stationary policies: neither player conditions on full history.
- Defender transitions: \(T(s'\mid s,a_D)\), matching the existing code.
- The policy table is exact for the present matrices and parameters; changing payoffs, transition probabilities, or \(\gamma\) requires recomputation.

## 8. Stage-specific Markov equilibrium equations

Let \(V_N,V_R,V_I,V_W,V_E\) denote the stationary defender values for Normal, Recon, Infection, Installation, and Execute, respectively. Substituting the Markov-equilibrium policies from Section 3 into the value equation gives the following simultaneous system. These equations are the POSG counterpart of stage-by-stage equilibrium equations, but remain purely Markov: each term is the current payoff plus the discounted expected value of the next state.

### Normal

At equilibrium, the attacker chooses NoAttack and the defender chooses LightScan. Its immediate payoff is \(1.20\):

$$
V_N = 1.20 + 0.9\bigl(
0.935961V_N + 0.049261V_R + 0.004926V_I
+0.004926V_W + 0.004926V_E
\bigr).
$$

### Recon

At equilibrium, the attacker chooses ServiceProbe and the defender chooses IDS+Honeypot. Its immediate payoff is \(1.27\):

$$
V_R = 1.27 + 0.9\bigl(
0.348259V_N + 0.597015V_R + 0.039801V_I
+0.009950V_W + 0.004975V_E
\bigr).
$$

### Infection

At equilibrium, the attacker chooses SSHBrute and the defender chooses PatchCVE. Its immediate payoff is \(1.00\):

$$
V_I = 1.00 + 0.9\bigl(
0.20V_N + 0.20V_R + 0.55V_I + 0.04V_W + 0.01V_E
\bigr).
$$

### Installation

Installation is the mixed Markov state. The attacker uses ModbusWrite with probability \(0.455004\) and Backdoor with probability \(0.544996\); the defender uses IsolateIBR with probability \(0.486486\) and Sandbox with probability \(0.513514\). The immediate equilibrium payoff is \(0.736486\). The mixed defender transition row is

$$
\bar T_W=0.486486T(\cdot\mid W,\text{IsolateIBR})
+0.513514T(\cdot\mid W,\text{Sandbox})
=(0.069730,0.094865,0.129730,0.625676,0.080000).
$$

Therefore,

$$
V_W = 0.736486 + 0.9\bigl(
0.069730V_N + 0.094865V_R + 0.129730V_I
+0.625676V_W + 0.080000V_E
\bigr).
$$

### Execute

At equilibrium, the attacker chooses FDICascade and the defender chooses Block+Rollback. Its immediate payoff is \(3.76\):

$$
V_E = 3.76 + 0.9\bigl(
0.20V_N + 0.05V_R + 0.05V_I + 0.10V_W + 0.60V_E
\bigr).
$$

### Markov-equilibrium solution

Solving the five equations together gives:

$$
(V_N,V_R,V_I,V_W,V_E)
= (12.264,\ 12.380,\ 11.933,\ 11.972,\ 17.694).
$$

The values are not one-step utilities. Each contains the infinite discounted stream of expected future defender utility under the stationary Markov policies.

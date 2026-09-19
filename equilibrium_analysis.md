# Equilibrium Analysis for the Smart-Grid POSG

## 1. Equilibrium concept

The guiding ransomware-deception paper solves a fully observable extensive-form game by **Subgame-Perfect Nash Equilibrium (SPNE)** and backward induction. This Smart-Grid model is instead a **partially observable stochastic game (POSG)**: the defender observes telemetry and maintains a belief over the hidden attack stage. Therefore, the corresponding equilibrium is a **belief-state Markov perfect Bayesian equilibrium** (MPBE); under the zero-sum surrogate below, it is equivalently a **minimax Markov equilibrium**.

The game state is

$$
s\in\mathcal S=\{\text{Normal, Recon, Infection, Installation, Execute}\},
$$

and the defender maintains \(b(s)=\Pr(s\mid o_{1:t},a^D_{1:t-1})\). Its policy is \(\pi_D(a_D\mid b)\); the attacker policy is \(\pi_A(a_A\mid s)\).

> **Modeling assumption for the numerical equilibrium below.** `posg_models.py` defines only defender utility \(U_D\). To obtain a two-player equilibrium, use the standard zero-sum security-game proxy \(U_A=-U_D\). If a separately calibrated attacker utility is later introduced, recompute the analysis as a general-sum MPBE; the numerical values below will not necessarily remain valid.

## 2. Stage utility and belief update

The immediate defender utility implemented by the project is

$$
U_D(s,a_A,a_D)=P(s,a_D)-p_{\mathrm{success}}(s,a_A,a_D)D(s,a_A)
-0.5C_D(s,a_D)-0.3L(s,a_D).
$$

For Execute, the disruption term is \(0.3\max\{1,L(s,a_D)\}\). The posterior belief is the project's predict–correct update:

$$
\bar b(s')=\sum_s b(s)\sum_{a_D}\pi_D(a_D\mid b)T(s'\mid s,a_D),
\qquad
b'(s')=\frac{O(o'\mid s')\bar b(s')}{\sum_j O(o'\mid j)\bar b(j)}.
$$

Here \(T\) is `TRANSITION_MODEL` and \(O\) is `OBSERVATION_MODEL`.

## 3. Backward-recursive POSG equilibrium

Following the paper’s backward-induction logic, replace each terminal-stage calculation by a belief-state continuation value. For discount factor \(\gamma\), define

$$
Q_s(a_A,a_D)=U_D(s,a_A,a_D)+
\gamma\sum_{s'}T(s'\mid s,a_D)V(s').
$$

The state-game recursion is

$$
V(s)=\max_{\pi_D\in\Delta(\mathcal A_D(s))}
\min_{\pi_A\in\Delta(\mathcal A_A(s))}
\pi_A^\top Q_s\pi_D.
$$

For the actual partially observed controller, use the belief-state form:

$$
V(b)=\max_{\pi_D}\min_{\pi_A}
\sum_s b(s)\sum_{a_A,a_D}
\pi_A(a_A\mid s)\pi_D(a_D\mid b)
\left[U_D+\gamma\mathbb E_{o'}V\bigl(b'(b,a_D,o')\bigr)\right].
$$

This is the POSG analogue of the paper’s “solve the last decision first, substitute its value into the previous decision, and continue backward” procedure. A finite-horizon version starts with \(V_H=0\) and evaluates \(t=H-1,\ldots,0\); an infinite-horizon version iterates the Bellman–Shapley operator to convergence.

## 4. One-stage equilibrium characterization

The table below is the closed-form **immediate-payoff** equilibrium obtained from the current payoff matrices. It is the base case for the recursion above, i.e. \(\gamma=0\), or the terminal-stage policy in a finite-horizon analysis.

| State | Attacker equilibrium policy \(\pi_A^*\) | Defender equilibrium policy \(\pi_D^*\) | Defender value \(V_D^*\) |
|---|---|---|---:|
| Normal | NoAttack (1.000) | LightScan (1.000) | 1.200 |
| Recon | ServiceProbe (1.000) | IDS+Honeypot (1.000) | 1.270 |
| Infection | SSHBrute (1.000) | PatchCVE (1.000) | 1.000 |
| Installation | ModbusWrite (0.459), Backdoor (0.541) | IsolateIBR (0.486), Sandbox (0.514) | 0.736 |
| Execute | FDICascade (1.000) | Block+Rollback (1.000) | 3.760 |

### Proposition 1 — Pure-strategy stage equilibria

Normal, Recon, Infection, and Execute each have a saddle point in the current payoff matrix:

$$
\begin{aligned}
\text{Normal:}&\quad(\text{NoAttack},\ \text{LightScan}), &V_D&=1.20,\\
\text{Recon:}&\quad(\text{ServiceProbe},\ \text{IDS+Honeypot}), &V_D&=1.27,\\
\text{Infection:}&\quad(\text{SSHBrute},\ \text{PatchCVE}), &V_D&=1.00,\\
\text{Execute:}&\quad(\text{FDICascade},\ \text{Block+Rollback}), &V_D&=3.76.
\end{aligned}
$$

**Justification.** In each listed pair, the defender action maximizes its worst-case column payoff and the attacker action minimizes the corresponding row payoff. For example, in Recon, IDS+Honeypot has column minimum \(1.27\), attained by ServiceProbe; ServiceProbe’s best defender response is also IDS+Honeypot, with payoff \(1.27\).

### Proposition 2 — Installation mixed-strategy equilibrium

Installation has no pure saddle point. Let \(q\) be the probability that the defender chooses IsolateIBR, with Sandbox chosen with probability \(1-q\). The relevant attacker payoffs to the defender are

$$
\begin{aligned}
U_D(\text{ModbusWrite}) &=0.25+q,\\
U_D(\text{Backdoor}) &=1.15-0.85q.
\end{aligned}
$$

Equating them gives

$$
q^*=\frac{0.90}{1.85}=0.4865,
\qquad
V_D^*=0.25+q^*=0.7365.
$$

Let \(p\) be the probability that the attacker chooses ModbusWrite, with Backdoor chosen with probability \(1-p\). Defender indifference between IsolateIBR and Sandbox requires

$$
0.30+0.95p=1.15-0.90p,
$$

so

$$
p^*=\frac{0.85}{1.85}=0.4595.
$$

Thus:

$$
\pi_D^*=(0,0,0.4865,0.5135),\qquad
\pi_A^*=(0,0.4595,0.5405).
$$

The entries are ordered according to the action order in `posg_types.py`.

## 5. Operational policy implied by the equilibrium

At a belief concentrated on a particular state, the defender should use the stage policy in Table 1. For uncertain beliefs, select the equilibrium policy from the belief-state recursion rather than simply taking the most probable stage. In particular:

- strong Recon belief supports IDS+Honeypot;
- strong Infection belief supports PatchCVE;
- strong Installation belief requires randomized IsolateIBR/Sandbox deployment;
- strong Execute belief supports Block+Rollback.

Randomization in Installation is important: a fixed IsolateIBR policy invites the attacker’s Sandbox-favored response, while a fixed Sandbox policy invites ModbusWrite. The equilibrium mixture removes that predictable advantage.

## 6. Relationship to the current implementation

`posg_engine.py` currently performs **belief-weighted expected-utility maximization using a uniform average over attacker actions**; its own documentation states that Nash mixing is deferred. It therefore does not yet implement the equilibrium policies above. The analysis supplies the required replacement:

1. construct \(Q_s\) using immediate utility plus continuation value;
2. solve each zero-sum state game for \((\pi_A^*,\pi_D^*)\);
3. update the defender belief with observations;
4. dispatch a defender action sampled from \(\pi_D^*(\cdot\mid b)\).

## 7. Scope and limitation

The reference paper’s SPNE is appropriate because its decision tree is complete-information and sequential. This project has hidden stages, noisy observations, and simultaneous attacker/defender actions. Calling its result an SPNE would be inaccurate. The belief-state minimax/MPBE formulation above preserves the paper’s backward-recursive equilibrium reasoning while respecting the POSG structure.

Reference guide: Neupane et al., *On Countering Ransomware Attacks Using Strategic Deception*, GameSec 2024. The paper performs closed-form SPNE analysis via backward induction for its extensive-form ransomware game.

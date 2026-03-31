"""
run_simulation_v2.py — POSG Engine v2 full simulation
======================================================
Tests:
  1. Main 4-stage attack (Recon→Compromise→Weaponize→Execute)
  2. False alarm test  (quiet traffic must stay in Normal)
  3. De-escalation test (belief returns toward Normal after attack stops)
  4. Backward induction SPE + VED table
  5. v1 vs v2 diff summary
"""

import numpy as np
from posg_engine import POSGEngine, backward_induction
from posg_types import (
    S, STATE_NAMES, DEFENDER_ACTION_NAMES, OBS_NAMES, RawObs,
)

# ── terminal colours ──────────────────────────────────────────
R="\033[91m"; G="\033[92m"; Y="\033[93m"; C="\033[96m"
M="\033[95m"; BO="\033[1m"; RE="\033[0m"
DIV = f"{C}{'─'*72}{RE}"


def sep(title):
    print(f"\n{DIV}\n{BO}{Y}  {title}{RE}\n{DIV}")


def belief_bar(v, width=28, color=C):
    n = int(v * width)
    return f"{color}{'█'*n}{'░'*(width-n)}{RE}"


def print_belief(label, b):
    colors = [G, C, Y, M, R]
    best   = int(np.argmax(b))
    print(f"\n  {BO}{label}{RE}")
    for i, (name, v) in enumerate(zip(STATE_NAMES.values(), b)):
        c   = colors[i]
        mrk = f"  ← most likely" if i == best else ""
        print(f"  {name:<14} {belief_bar(v,28,c)}  {c}{v:.4f}  {v*100:5.1f}%{RE}{mrk}")


def print_eu(all_eu, best_idx, stage, action_names):
    print(f"\n  {BO}Expected utility per defender action  [{STATE_NAMES[stage]}]:{RE}")
    for i, (n, eu) in enumerate(zip(action_names, all_eu)):
        c   = G if i == best_idx else (R if eu < 0 else Y)
        mrk = f"  {G}← BEST{RE}" if i == best_idx else ""
        print(f"    D{i} {n:<20}  {c}{eu:+.4f}{RE}{mrk}")


def action_names_for(stage_name):
    for s, name in STATE_NAMES.items():
        if name == stage_name:
            return list(DEFENDER_ACTION_NAMES[s].values())
    return []


# ════════════════════════════════════════════════════════════
# SCENARIO 1 — 4-stage attack
# ════════════════════════════════════════════════════════════

def run_attack_scenario():
    scenario = [
        {
            "title": "t=1  PortScan  (nmap -sV -p 20000,502,4712)",
            "obs":   RawObs(syn_count=80, unique_ports=22),
            "llm":   np.array([0.05, 0.82, 0.08, 0.03, 0.02]),
        },
        {
            "title": "t=2  SSH BruteForce + Modbus read_holding_registers",
            "obs":   RawObs(ssh_attempts=12, modbus_anomaly=True),
            "llm":   np.array([0.03, 0.08, 0.76, 0.10, 0.03]),
        },
        {
            "title": "t=3  write_register(100,0) — IBR voltage corruption",
            "obs":   RawObs(modbus_anomaly=True, phasor_mismatch=5.5),
            "llm":   np.array([0.02, 0.05, 0.10, 0.76, 0.07]),
        },
        {
            "title": "t=4  DNP3 OPERATE group=12 idx=5 TRIP",
            "obs":   RawObs(dnp3_operate=True, freq_deviation=1.4),
            "llm":   np.array([0.01, 0.02, 0.04, 0.08, 0.85]),
        },
    ]

    print(f"\n{BO}{M}{'='*72}")
    print("  POSG ENGINE v2  |  Smart Grid CKC Attack Simulation")
    print(f"  5-state model  |  EU maximization  |  Predict-Correct belief")
    print(f"{'='*72}{RE}")

    engine  = POSGEngine(alpha=0.6, gamma=0.9, dry_run=True)
    results = []
    print_belief("Initial belief b₀", engine.belief.tolist())

    for step in scenario:
        sep(step["title"])
        obs     = step["obs"]
        obs_sym = obs.to_obs()
        print(f"  {BO}Observation symbol:{RE}  {G}{OBS_NAMES[obs_sym]}{RE}")

        print(f"  {BO}Active signals:{RE}")
        for f in ["syn_count","unique_ports","ssh_attempts","cve_alert",
                  "modbus_anomaly","phasor_mismatch","dnp3_operate","freq_deviation"]:
            v = getattr(obs, f)
            if v:
                print(f"    {Y}{f}{RE} = {v}")

        llm = step.get("llm")
        if llm is not None:
            print(f"  {BO}LLM belief (5-state, α=0.6):{RE}  {C}{[f'{x:.2f}' for x in llm]}{RE}")

        r = engine.step(obs, llm_belief=llm)
        results.append(r)
        
        print_belief(
            "Bayesian belief (predict → correct)",
            r.belief_bayes
        )

        print_belief(
            f"b' after predict→correct→hybrid  (Bayes×40% + LLM×60%)",
            r.belief_updated
        )
        print_eu(r.all_utilities, r.best_action_idx,
                 S(list(STATE_NAMES.values()).index(r.most_likely_stage)),
                 action_names_for(r.most_likely_stage))

        print(f"\n  {BO}Decision:{RE}  {G}{r.best_action_name}{RE}"
              f"  EU={G}{r.expected_utility:+.4f}{RE}"
              f"  H={Y}{r.belief_entropy:.3f}{RE} bits")
        print(f"  {BO}ONOS:{RE}  rule={Y}{r.onos_payload['rule']}{RE}"
              f"  target={r.onos_payload['target']}")

    return engine, results


# ════════════════════════════════════════════════════════════
# SCENARIO 2 — False alarm test
# ════════════════════════════════════════════════════════════

def run_false_alarm_test():
    sep("FALSE ALARM TEST — 4 quiet timesteps should stay in Normal")
    engine = POSGEngine(alpha=0.0, dry_run=True)   # pure Bayes
    print_belief("b₀", engine.belief.tolist())

    r = None
    for i in range(4):
        r = engine.step(RawObs())
        norm = r.belief_updated[S.NORMAL]
        print(f"  t={i+1}  Normal={norm:.4f}  stage={r.most_likely_stage:<12}"
              f"  action={r.best_action_name}")

    assert r.belief_updated[S.NORMAL] > 0.70, \
        f"Normal dropped too low: {r.belief_updated[S.NORMAL]:.4f}"
    print(f"\n  {G}✓ PASS — Normal belief {r.belief_updated[S.NORMAL]:.4f} > 0.70{RE}")


# ════════════════════════════════════════════════════════════
# SCENARIO 3 — De-escalation test
# ════════════════════════════════════════════════════════════

def run_deescalation_test():
    sep("DE-ESCALATION TEST — belief must return toward Normal after attack stops")
    engine = POSGEngine(alpha=0.0, dry_run=True)

    # Force belief deep into Execute
    engine.belief = np.array([0.01, 0.02, 0.04, 0.08, 0.85])
    print_belief("Forced belief (Execute dominated)", engine.belief.tolist())

    r = None
    for i in range(6):
        r = engine.step(RawObs())  # all quiet
        norm = r.belief_updated[S.NORMAL]
        exe  = r.belief_updated[S.EXECUTE]
        print(f"  t={i+1}  Normal={norm:.4f}  Execute={exe:.4f}"
              f"  action={r.best_action_name}  H={r.belief_entropy:.3f}")

    assert r.belief_updated[S.NORMAL] > 0.05, \
        f"Normal never recovered: {r.belief_updated[S.NORMAL]:.4f}"
    print(f"\n  {G}✓ PASS — Normal recovered to {r.belief_updated[S.NORMAL]:.4f}{RE}")


# ════════════════════════════════════════════════════════════
# SPE + VED
# ════════════════════════════════════════════════════════════

def run_spe(engine):
    sep("SUBGAME PERFECT EQUILIBRIUM — EU Backward Induction")
    spe = engine.run_backward_induction()

    print(f"\n  {BO}Stage values V(s)  (defender perspective):{RE}")
    for s_name, v in spe["stage_values"].items():
        c = G if v > 0 else R
        print(f"    {s_name:<14}  V = {c}{v:+.4f}{RE}  "
              f"→ best action = {Y}{spe['best_actions'][s_name]}{RE}")

    print(f"\n  {BO}Value of Early Detection (VED):{RE}")
    print(f"  {'Stage':<14} {'Block Cost':>11} {'Damage Saved':>13} {'VED':>8}")
    print(f"  {'─'*52}")
    for s_name, v in spe["ved"].items():
        ved = v["VED"]
        c   = G if ved > 0 else (Y if ved == 0 else R)
        print(f"  {s_name:<14}  {v['block_cost']:>10}  {v['damage_saved']:>12}  "
              f"{c}{ved:>+7}{RE}")
    print(f"\n  {BO}Interpretation:{RE}  Block early (Recon/Compromise) = {G}positive VED{RE}")
    print(f"  Blocking at Execute = {R}negative VED{RE} (disruption > benefit)")


# ════════════════════════════════════════════════════════════
# SUMMARY TABLE
# ════════════════════════════════════════════════════════════

def print_summary(results):
    sep("SIMULATION SUMMARY")
    print(f"\n  {'t':>3}  {'Observation':<33} {'Stage':<14}"
          f" {'Conf':>6}  {'Action':<22} {'EU':>8}  {'H':>6}")
    print(f"  {'─'*96}")
    for r in results:
        c = G if r.stage_confidence > 0.55 else Y
        print(f"  {r.timestep:>3}  {r.observation:<33} "
              f"{c}{r.most_likely_stage:<14}{RE}"
              f" {r.stage_confidence:>6.1%}  {r.best_action_name:<22}"
              f" {r.expected_utility:>+8.4f}  {r.belief_entropy:>6.3f}")

# ════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    engine, results = run_attack_scenario()
    run_false_alarm_test()
    run_deescalation_test()
    run_spe(engine)
    print_summary(results)
    print(f"\n{DIV}\n")

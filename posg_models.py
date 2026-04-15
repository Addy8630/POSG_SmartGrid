"""
posg_models.py — Observation, Transition, and Payoff models
============================================================
Three probability/utility models that define the game:

  1. ObservationModel  P(o | s)           shape [5 × 8]
  2. TransitionModel   P(s'| s, aD)       shape [5 × max_aD × 5]
  3. PayoffModel       U_D(s, aA, aD)     stage-specific 2D matrices

All models are validated at construction time.
Zero-smoothing (ε = 0.005) prevents belief collapse.
"""

import numpy as np
import random
from posg_types import (
    S, O, NUM_STATES, NUM_OBS,
    NormalA, ReconA, CompA, WeapA, ExecA,
    NormalD, ReconD, CompD, WeapD, ExecD,
    NUM_DEF_ACTIONS, AttackerAction, DefenderAction,
)

EPS = 0.005   # minimum probability — prevents belief collapse
W1, W2, W3, W4 = 1.0, 1.0, 0.5, 0.3   # payoff formula weights


# ════════════════════════════════════════════════════════════
# 1.  OBSERVATION MODEL   P[s, o]
# ════════════════════════════════════════════════════════════

def _build_observation_model() -> np.ndarray:
    """
    Expert-designed P(o|s) table, then:
      1. Replace all values below EPS with EPS
      2. Renormalize each row so it sums exactly to 1

    Row order  : S.NORMAL, S.RECON, S.INFECTION, S.INSTALLATION, S.EXECUTE
    Column order: O.NORMAL_TRAFFIC, HIGH_SYN, SERVICE_PROBE, SUSPICIOUS_LOGIN,
                  MODBUS_WRITE, PHASOR_ANOMALY, DNP3_OPERATE, FREQ_DEVIATION
    """
    #                  norm   syn   probe  login  modbus phasor dnp3   freq
    raw = np.array([
        # Normal     — mostly quiet; tiny chance of OT noise
        [0.860,  0.050, 0.040, 0.020, 0.010, 0.005, 0.005, 0.005],

        # Recon      — nmap / service fingerprinting dominates
        [0.050,  0.580, 0.270, 0.040, 0.020, 0.010, 0.005, 0.005],

        # Compromise — login attempts + Modbus reads
        [0.050,  0.095, 0.095, 0.340, 0.290, 0.055, 0.030, 0.020],

        # Weaponize  — Modbus writes, IBR anomalies, FDI prep
        [0.050,  0.030, 0.020, 0.050, 0.330, 0.285, 0.100, 0.100],

        # Execute    — DNP3 OPERATE / frequency cascade dominate
        [0.020,  0.010, 0.010, 0.010, 0.050, 0.145, 0.540, 0.195],
    ], dtype=float)

    # Apply EPS floor then renormalize
    raw = np.maximum(raw, EPS)
    raw = raw / raw.sum(axis=1, keepdims=True)

    # Validate
    assert raw.shape == (NUM_STATES, NUM_OBS), \
        f"Observation model shape mismatch: {raw.shape}"
    assert np.allclose(raw.sum(axis=1), 1.0, atol=1e-9), \
        "Observation model rows do not sum to 1"
    assert (raw > 0).all(), "Observation model contains non-positive entry"

    return raw


OBSERVATION_MODEL = _build_observation_model()


# ════════════════════════════════════════════════════════════
# 2.  TRANSITION MODEL   P[s, aD_idx, s']
# ════════════════════════════════════════════════════════════

def _build_transition_model() -> dict:
    """
    Returns: T[s][aD_idx] = np.array of shape (NUM_STATES,)
             representing P(s'| s, aD).

    Design constraints enforced:
      • Every (s, aD) row sums to 1
      • Every state can return to Normal (false alarm / attack abort)
      • Attack persistence: nonzero self-loop at each stage
      • Defender actions reduce advance probability
      • EPS floor applied before normalization
      • Assertion check at the end
    """
    T = {}

    # ── S.NORMAL ─────────────────────────────────────────────
    # Normal state: attacker may begin probing (→ Recon)
    # Defender can reduce that probability
    #
    #                       →Norm  →Recon →Comp  →Weap  →Exec
    T[S.NORMAL] = {
        NormalD.MONITOR:    [0.90,  0.10,  0.00,  0.00,  0.00],
        NormalD.LIGHT_SCAN: [0.95,  0.05,  0.00,  0.00,  0.00],
    }

    # ── S.RECON ──────────────────────────────────────────────
    # Recon: attacker may advance to Compromise or abort
    # IDS+Honeypot gives strongest protection
    #
    #                       →Norm  →Recon →Comp  →Weap  →Exec
    T[S.RECON] = {
        ReconD.MONITOR:    [0.10,  0.55,  0.30,  0.05,  0.00],
        ReconD.HONEYPOT:   [0.20,  0.60,  0.15,  0.05,  0.00],
        ReconD.RATE_LIMIT: [0.25,  0.65,  0.08,  0.02,  0.00],
        ReconD.IDS_HONEY:  [0.35,  0.60,  0.04,  0.01,  0.00],
    }

    # ── S.INFECTION ─────────────────────────────────────────
    # Compromise: attacker tries to establish foothold
    # Patching CVE stops advance most effectively
    #
    #                        →Norm  →Recon →Comp  →Weap  →Exec
    T[S.INFECTION] = {
        CompD.MONITOR:      [0.05,  0.10,  0.50,  0.30,  0.05],
        CompD.MFA:          [0.10,  0.15,  0.55,  0.15,  0.05],
        CompD.IP_WHITELIST: [0.15,  0.15,  0.60,  0.08,  0.02],
        CompD.PATCH_CVE:    [0.20,  0.20,  0.55,  0.04,  0.01],
    }

    # ── S.INSTALLATION ──────────────────────────────────────────
    # Weaponize: attacker stages FDI / backdoors
    # Isolating IBR is most effective; return to Normal is harder now
    #
    #                          →Norm  →Recon →Comp  →Weap  →Exec
    T[S.INSTALLATION] = {
        WeapD.MONITOR:        [0.03,  0.05,  0.10,  0.47,  0.35],
        WeapD.PHYSICS_CHECK:  [0.05,  0.08,  0.12,  0.55,  0.20],
        WeapD.ISOLATE_IBR:    [0.08,  0.10,  0.14,  0.60,  0.08],
        WeapD.SANDBOX:        [0.06,  0.09,  0.12,  0.65,  0.08],
    }

    # ── S.EXECUTE ────────────────────────────────────────────
    # Execute: near-absorbing but not fully absorbing
    # Return to Normal = 0.01 (attack completes or is fully blocked)
    # Block+Rollback gives best chance of recovery
    #
    #                           →Norm  →Recon →Comp  →Weap  →Exec
    T[S.EXECUTE] = {
        ExecD.MONITOR:         [0.01,  0.01,  0.02,  0.06,  0.90],
        ExecD.EMERG_BLOCK:     [0.05,  0.05,  0.05,  0.05,  0.80],
        ExecD.ROLLBACK:        [0.10,  0.05,  0.05,  0.10,  0.70],
        ExecD.BLOCK_ROLLBACK:  [0.20,  0.05,  0.05,  0.10,  0.60],
    }

    # ── Apply EPS floor and normalize; then assert rows sum to 1 ─
    for s in S:
        for aD_idx, row in T[s].items():
            arr = np.array(row, dtype=float)
            arr = np.maximum(arr, EPS)
            arr = arr / arr.sum()
            T[s][aD_idx] = arr
            assert np.isclose(arr.sum(), 1.0, atol=1e-9), \
                f"Transition row ({s},{aD_idx}) does not sum to 1: {arr.sum()}"
            assert (arr > 0).all(), \
                f"Transition row ({s},{aD_idx}) has non-positive entry"

    return T


TRANSITION_MODEL = _build_transition_model()


# ════════════════════════════════════════════════════════════
# 3.  PAYOFF MODEL   U_D(s, aA, aD)
# ════════════════════════════════════════════════════════════

# ── Component tables ─────────────────────────────────────────

# Prevention benefit: how much damage does this defense prevent?
# Indexed by (stage, defender_action_idx)
PREVENTION = {
    S.NORMAL:     [1.0, 2.0],                 # Monitor, LightScan
    S.RECON:      [1.0, 3.0, 2.5, 4.0],      # Monitor, Honeypot, RateLimit, IDS+Honey
    S.INFECTION: [1.0, 3.0, 3.5, 4.5],
    S.INSTALLATION:  [1.0, 4.0, 5.0, 4.5],
    S.EXECUTE:    [0.0, 5.0, 6.0, 8.0],      # Monitor=0 during Execute (too late)
}

# Damage cost if attack action succeeds (indexed by attacker_action_idx per stage)
DAMAGE = {
    S.NORMAL:     [0.0],                      # no attack
    S.RECON:      [1.0, 2.5, 4.0],           # Ping, PortScan, ServiceProbe
    S.INFECTION: [3.0, 4.0, 6.0],           # ModbusRead, SSHBrute, CVEExploit
    S.INSTALLATION:  [5.0, 7.0, 8.0],           # FDIPrep, ModbusWrite, Backdoor
    S.EXECUTE:    [10.0, 12.0, 9.0],         # DNP3Trip, FDICascade, Ransomware
}

# Defense cost (indexed by defender_action_idx per stage)
DEFENSE_COST = {
    S.NORMAL:     [0.5, 1.0],
    S.RECON:      [0.5, 2.0, 1.5, 3.0],
    S.INFECTION: [0.5, 2.0, 1.5, 3.5],
    S.INSTALLATION:  [0.5, 2.5, 3.0, 2.5],
    S.EXECUTE:    [0.5, 4.0, 3.5, 5.0],
}

# Operational disruption: cost of blocking legitimate OT traffic
# HIGH in Normal (false positives), LOW in Execute (attack already happening)
# cap: max(1, value) applied in Execute per spec
OPERATIONAL_DISRUPTION = {
    S.NORMAL:     [0.0, 1.0],                 # Monitor=0, LightScan=1
    S.RECON:      [0.5, 1.0, 2.0, 2.5],
    S.INFECTION: [1.0, 2.0, 3.0, 2.5],
    S.INSTALLATION:  [1.5, 2.0, 4.0, 3.0],
    S.EXECUTE:    [0.5, 1.0, 1.0, 1.0],      # already under attack → low disruption
}

# P_success(s, aA, aD): probability attack succeeds given defender response
# Shape: [num_aA × num_aD] per stage
P_SUCCESS = {
    S.NORMAL: np.array([
        # aA=NoAttack:  defender can't really "stop" nothing
        #            Monitor  LightScan
        [0.00,       0.00],
    ]),

    S.RECON: np.array([
        #            Monitor  Honeypot  RateLimit  IDS+Honey
        [0.70,       0.30,    0.25,     0.10],   # PingSweep
        [0.90,       0.25,    0.30,     0.15],   # PortScan
        [0.85,       0.20,    0.35,     0.12],   # ServiceProbe
    ]),

    S.INFECTION: np.array([
        #            Monitor  MFA    IPWhitelist  PatchCVE
        [0.80,       0.40,    0.35,  0.30],      # ModbusRead
        [0.85,       0.20,    0.40,  0.25],      # SSHBrute
        [0.90,       0.30,    0.45,  0.10],      # CVEExploit
    ]),

    S.INSTALLATION: np.array([
        #            Monitor  Physics  IsolateIBR  Sandbox
        [0.80,       0.30,    0.20,    0.25],     # FDIPrep
        [0.85,       0.40,    0.15,    0.30],     # ModbusWrite
        [0.90,       0.35,    0.25,    0.15],     # Backdoor
    ]),

    S.EXECUTE: np.array([
        #            Monitor  EmergBlock  Rollback  Block+Rollback
        [0.95,       0.40,    0.30,       0.10],   # DNP3Trip
        [0.95,       0.45,    0.35,       0.12],   # FDICascade
        [0.90,       0.35,    0.25,       0.08],   # Ransomware
    ]),
}


def compute_payoff_matrix(stage: S) -> np.ndarray:
    """
    Compute defender payoff matrix for a given stage.

    U_D(aA, aD) = w1 × Prevention(stage, aD)
                − w2 × P_success(stage, aA, aD) × Damage(stage, aA)
                − w3 × DefenseCost(stage, aD)
                − w4 × max(1, OperationalDisruption(stage, aD))  [Execute]
                  OR
                − w4 × OperationalDisruption(stage, aD)          [other stages]

    Returns np.ndarray shape [num_aA, num_aD]
    """
    ps      = P_SUCCESS[stage]          # [n_aA × n_aD]
    n_aA, n_aD = ps.shape

    prevention = np.array(PREVENTION[stage],              dtype=float)  # [n_aD]
    damage     = np.array(DAMAGE[stage],                  dtype=float)  # [n_aA]
    def_cost   = np.array(DEFENSE_COST[stage],            dtype=float)  # [n_aD]
    disrupt    = np.array(OPERATIONAL_DISRUPTION[stage],  dtype=float)  # [n_aD]

    # Cap disruption in Execute state
    if stage == S.EXECUTE:
        disrupt = np.maximum(1.0, disrupt)

    # Broadcast: damage [n_aA] × P_success [n_aA × n_aD] → [n_aA × n_aD]
    expected_damage = ps * damage[:, np.newaxis]       # [n_aA × n_aD]

    # U_D: [n_aA × n_aD]
    U = (W1 * prevention[np.newaxis, :]
       - W2 * expected_damage
       - W3 * def_cost[np.newaxis, :]
       - W4 * disrupt[np.newaxis, :])

    return U


# Pre-compute all payoff matrices at import time
PAYOFF = {s: compute_payoff_matrix(s) for s in S}


def get_payoff(stage: S) -> np.ndarray:
    """Return pre-computed defender payoff matrix for stage."""
    return PAYOFF[stage]


# ════════════════════════════════════════════════════════════
# RANDOM ACTION UTILITIES
# ════════════════════════════════════════════════════════════

def random_attacker():
    """Return random attacker action from AttackerAction enum."""
    return random.choice(list(AttackerAction))


def random_defender():
    """Return random defender action from DefenderAction enum."""
    return random.choice(list(DefenderAction))

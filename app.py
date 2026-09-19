import streamlit as st
from posg_engine import POSGEnvironment
from posg_types import (
    Stage, S, AttackerAction, DefenderAction,
    ATTACKER_ACTION_NAMES, DEFENDER_ACTION_NAMES,
)
from posg_models import get_payoff

st.set_page_config(page_title="Smart Grid POSG", layout="wide")


def generate_stage_insight(stage: Stage, attacker_label: str, defender_label: str) -> str:
    stage_text = {
        Stage.NORMAL: "Everything is normal: no active attack has been detected yet.",
        Stage.RECON: "The attacker is in Reconnaissance, gathering intel on the network and probing targets.",
        Stage.INFECTION: "The attacker is in Infection, trying to penetrate defenses and gain foothold.",
        Stage.INSTALLATION: "The attacker is in Installation, preparing the payload or malicious tool for the attack.",
        Stage.EXECUTION: "The attacker is in Execution, attempting to carry out the attack and impact systems.",
    }.get(stage, "The game is in an unknown stage.")

    return (
        f"Stage: {stage.name}. {stage_text} "
        f"Selected attacker action: {attacker_label}. "
        f"Selected defender action: {defender_label}. "
        "This helps you understand whether the chosen actions match the current APT phase."
    )


# =============================
# SESSION STATE
# =============================
if "env" not in st.session_state:
    st.session_state.env = POSGEnvironment()
    st.session_state.state = st.session_state.env.reset()
    st.session_state.score_a = 0
    st.session_state.score_d = 0
    st.session_state.log = []
    st.session_state.selected_action = None

env = st.session_state.env
state = st.session_state.state

# =============================
# HEADER
# =============================
st.markdown(
    """
    <div style='background:#07121b; padding:20px; border-radius:12px;'>
      <h1 style='color:#00e5ff; margin:0;'>⚡ SMART GRID POSG — LIVE GAME SIMULATOR</h1>
      <p style='color:#8fb8d3; margin:4px 0 0;'>CRC • Partial Observability • Bayesian Belief • Payoff Matrix</p>
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns([6, 1, 1])
col2.metric("Attacker", st.session_state.score_a)
col3.metric("Defender", st.session_state.score_d)

# =============================
# KILL CHAIN NAV BAR
# =============================
st.markdown("### Cyber Kill Chain")

stage_map = {
    Stage.NORMAL:     ("NORMAL",     "#39a9dc"),
    Stage.RECON:      ("RECON",      "#0f6cff"),
    Stage.INFECTION: ("INFECTION",       "#e14c4c"),
    Stage.INSTALLATION:  ("INSTALLATION",  "#f5a623"),
    Stage.EXECUTION:    ("EXECUTION",  "#ffcc00"),
}

chain_parts = []
for idx, (stage, (label, color)) in enumerate(stage_map.items()):
    background = color if state.stage == stage else "#11233c"
    chain_parts.append(
        f"<div style='flex:1; background:{background}; padding:12px; border-radius:10px; "
        f"color:#fff; text-align:center; white-space:nowrap;'><strong>{label}</strong></div>"
    )
    if idx < len(stage_map) - 1:
        chain_parts.append(
            "<div style='color:#8fb8d3; font-size:26px; font-weight:bold; padding:0 10px;'>&rarr;</div>"
        )

st.markdown(
    "<div style='display:flex; align-items:center; width:100%;'>" + "".join(chain_parts) + "</div>",
    unsafe_allow_html=True,
)

progress_value = {
    Stage.NORMAL:     0.0,
    Stage.RECON:      0.2,
    Stage.INFECTION: 0.45,
    Stage.INSTALLATION:  0.7,
    Stage.EXECUTION:    0.95,
}.get(state.stage, 0.0)
st.progress(progress_value)

# =============================
# MAIN LAYOUT
# =============================
left, middle, right = st.columns([3, 4, 3])

# =============================
# LEFT: NETWORK SIGNALS
# =============================
with left:
    st.markdown("## 📡 Network Signals")

    signals = {
        "ICMP Flood": (0.9, 0.05),
        "Port Scan": (0.85, 0.02),
        "DNP3 Query": (0.7, 0.01),
        "No anomaly": (0.1, 0.95),
    }

    selected_signals = []
    for sig, probs in signals.items():
        if st.checkbox(sig):
            selected_signals.append(probs)

    if selected_signals:
        belief = 1.0
        for p_attack, p_normal in selected_signals:
            belief *= p_attack / (p_attack + p_normal)
        env.belief.threat_level = min(1.0, belief)

    st.markdown("---")
    st.write("**Selected Signals:**")
    if selected_signals:
        for sig in signals:
            if sig in [k for k, v in signals.items() if v in selected_signals]:
                st.write(f"- {sig}")
    else:
        st.write("No signals selected.")

# =============================
# MIDDLE: BELIEF + PAYOFF MATRIX
# =============================
with middle:
    st.markdown("## 🧠 Defender Belief")
    st.progress(env.belief.threat_level)
    threat = env.belief.threat_level
    severity = (
        "Critical" if threat >= 0.90 else
        "High" if threat >= 0.70 else
        "Medium" if threat >= 0.40 else
        "Low"
    )
    st.write(f"Threat Level: {threat:.0%} ({severity})")

    st.markdown("---")
    st.markdown("## 🎯 Payoff Matrix")

    stage_map = {
        Stage.NORMAL: S.NORMAL,
        Stage.RECON: S.RECON,
        Stage.INFECTION: S.INFECTION,
        Stage.INSTALLATION: S.INSTALLATION,
        Stage.EXECUTION: S.EXECUTE,
    }
    stage_key = stage_map.get(state.stage)

    if stage_key is not None:
        attacker_labels = list(ATTACKER_ACTION_NAMES[stage_key].values())
        defender_labels = list(DEFENDER_ACTION_NAMES[stage_key].values())
    else:
        attacker_labels = []
        defender_labels = []

    if not attacker_labels or not defender_labels:
        st.write("No actions available for this stage.")
    else:
        payoff_matrix = get_payoff(stage_key)
        payoff_table = {"Attacker action": attacker_labels}
        for defender_idx, defender_label in enumerate(defender_labels):
            payoff_table[defender_label] = [
                f"{payoff:+.2f}" for payoff in payoff_matrix[:, defender_idx]
            ]
        st.dataframe(
            payoff_table,
            hide_index=True,
            use_container_width=True,
            height=36 + 35 * len(attacker_labels),
        )
        st.caption("Defender payoff: higher values are better for the defender.")

    st.markdown("---")
    action_buttons = st.container()
    cols = action_buttons.columns(max(1, len(attacker_labels)))
    combos = [f"{a} vs {d}" for a in attacker_labels for d in defender_labels]
    for i, btn_label in enumerate(combos):
        if cols[i % len(cols)].button(btn_label):
            st.session_state.selected_action = btn_label

    if st.session_state.selected_action is not None:
        st.success(f"Selected scenario: {st.session_state.selected_action}")

# =============================
# RIGHT: ACTIONS
# =============================
with right:
    st.markdown("## ⚔️ Actions")

    if state.stage == Stage.NORMAL:
        attacker_options = ["Scan", "Idle"]
        defender_options = ["Monitor", "LightScan"]
    elif state.stage != Stage.DONE and state.stage.value in [s.value for s in S]:
        stage_key = S(state.stage.value)
        attacker_options = list(ATTACKER_ACTION_NAMES[stage_key].values())
        defender_options = list(DEFENDER_ACTION_NAMES[stage_key].values())
    else:
        attacker_options = ["Idle"]
        defender_options = ["Monitor"]

    attacker_action_label = st.selectbox("Attacker", attacker_options)
    defender_action_label = st.selectbox("Defender", defender_options)

    def _map_attacker_action(label, stage):
        if stage in (Stage.NORMAL, Stage.RECON):
            return AttackerAction.SCAN
        if stage == Stage.INSTALLATION:
            return AttackerAction.PREPARE_PAYLOAD
        if stage == Stage.INFECTION:
            return AttackerAction.EXPLOIT
        if stage == Stage.EXECUTION:
            return AttackerAction.EXECUTE_ATTACK
        return AttackerAction.IDLE

    def _map_defender_action(label):
        if label in {"Monitor", "LightScan"}:
            return DefenderAction.MONITOR
        if "Patch" in label or label == "MFA":
            return DefenderAction.PATCH
        if "Block" in label or "Rollback" in label or "Isolate" in label:
            return DefenderAction.BLOCK
        return DefenderAction.IGNORE

    st.markdown("### 🤖 AI Stage Insight")
    insight_text = generate_stage_insight(state.stage, attacker_action_label, defender_action_label)
    st.info(insight_text)

    if st.button("▶ EXECUTE STEP"):
        mapped_attacker = _map_attacker_action(attacker_action_label, state.stage)
        mapped_defender = _map_defender_action(defender_action_label)

        new_state, rewards, done = env.step(
            mapped_attacker,
            mapped_defender,
        )
        st.session_state.state = new_state
        st.session_state.score_a += rewards[0]
        st.session_state.score_d += rewards[1]
        st.session_state.log.append(
            f"Step {new_state.step}: {new_state.stage.name} | A:{attacker_action_label} D:{defender_action_label} | R:A{rewards[0]} D{rewards[1]}"
        )
        st.success(f"Rewards → Attacker: {rewards[0]}, Defender: {rewards[1]}")
        if done:
            st.error("💥 GAME OVER")

    if st.button("🔄 Reset Game"):
        st.session_state.env = POSGEnvironment()
        st.session_state.state = st.session_state.env.reset()
        st.session_state.score_a = 0
        st.session_state.score_d = 0
        st.session_state.log = []
        st.session_state.selected_action = None

# =============================
# BOTTOM: EVENT LOG
# =============================
st.markdown("## 📜 Event Log")
for entry in st.session_state.log[-10:]:
    st.write(entry)

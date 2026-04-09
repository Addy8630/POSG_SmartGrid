import streamlit as st
from posg_engine import POSGEnvironment
from posg_types import (
    Stage, AttackerAction, DefenderAction,
    ATTACKER_ACTION_NAMES, DEFENDER_ACTION_NAMES,
)

st.set_page_config(page_title="Smart Grid POSG", layout="wide")


def generate_stage_insight(stage: Stage, attacker_label: str, defender_label: str) -> str:
    stage_text = {
        Stage.RECON: "The attacker is in Reconnaissance, gathering intel on the network and probing targets.",
        Stage.COMPROMISE: "The attacker is in Compromise, trying to penetrate defenses and gain foothold.",
        Stage.WEAPONIZE: "The attacker is in Weaponization, preparing the payload or malicious tool for the attack.",
        Stage.EXECUTE: "The attacker is in Execution, attempting to carry out the attack and impact systems.",
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
st.markdown("### Kill Chain")

stage_map = {
    Stage.RECON:      ("RECON",      "#0f6cff"),
    Stage.COMPROMISE: ("COMP",       "#e14c4c"),
    Stage.WEAPONIZE:  ("WEAPONIZE",  "#f5a623"),
    Stage.EXECUTE:    ("EXEC",       "#ffcc00"),
}

stage_cols = st.columns(4)
for idx, (stage, (label, color)) in enumerate(stage_map.items()):
    style = f"background:{'#11233c' if state.stage != stage else color}; padding:12px; border-radius:10px; color:#fff; text-align:center;"
    stage_cols[idx].markdown(f"<div style='{style}'><strong>{label}</strong></div>", unsafe_allow_html=True)

progress_value = {
    Stage.RECON:      0.2,
    Stage.COMPROMISE: 0.45,
    Stage.WEAPONIZE:  0.7,
    Stage.EXECUTE:    0.95,
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
    st.write(f"Threat Level: {env.belief.threat_level:.2f}")

    st.markdown("---")
    st.markdown("## 🎯 Payoff Matrix")

    attacker_labels = list(ATTACKER_ACTION_NAMES[state.stage].values())
    defender_labels = list(DEFENDER_ACTION_NAMES[state.stage].values())

    if not attacker_labels or not defender_labels:
        st.write("No actions available for this stage.")
    else:
        header = "| Action | " + " | ".join(defender_labels) + " |"
        separator = "|---" + "|---" * len(defender_labels) + "|"
        st.write(header)
        st.write(separator)

        for row_idx, a_label in enumerate(attacker_labels):
            row_values = [f"A{row_idx + 1}/D{col_idx + 1}" for col_idx in range(len(defender_labels))]
            st.write("| " + a_label + " | " + " | ".join(row_values) + " |")

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

    attacker_options = [name for name in ATTACKER_ACTION_NAMES[state.stage].values()]
    defender_options = [name for name in DEFENDER_ACTION_NAMES[state.stage].values()]

    attacker_action_label = st.selectbox("Attacker", attacker_options)
    defender_action_label = st.selectbox("Defender", defender_options)

    def _map_attacker_action(label, stage):
        if stage == Stage.RECON:
            return AttackerAction.RECON
        if stage in (Stage.COMPROMISE, Stage.WEAPONIZE, Stage.EXECUTE):
            return AttackerAction.ATTACK
        return AttackerAction.IDLE

    def _map_defender_action(label):
        return DefenderAction.MONITOR if label == "Monitor" else DefenderAction.PATCH

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

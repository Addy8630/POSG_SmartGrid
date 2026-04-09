"""
run_simulation.py — Interactive POSG Game
===========================================
Simple attacker vs defender game with user input.
Two players take turns choosing actions:
  - Attacker: Recon, Attack, Idle
  - Defender: Monitor, Patch, Ignore
"""

from posg_engine import POSGEnvironment
from posg_types import AttackerAction, DefenderAction


def get_attacker_action():
    """Prompt attacker for action choice."""
    print("\n[Attacker Turn]")
    print("0: Recon | 1: Attack | 2: Idle")
    return AttackerAction(int(input("Choose action: ")))


def get_defender_action():
    """Prompt defender for action choice."""
    print("\n[Defender Turn]")
    print("0: Monitor | 1: Patch | 2: Ignore")
    return DefenderAction(int(input("Choose action: ")))


def print_state(state, belief):
    """Print current game state."""
    print("\n===== GAME STATE =====")
    print(f"Step: {state.step}")
    print(f"Compromised: {state.compromised}")
    print(f"Detected: {state.detected}")
    print(f"Belief (attack probability): {belief.attack_prob:.2f}")
    print("======================")


def main():
    """Main game loop."""
    env = POSGEnvironment()
    state = env.reset()

    print("\n⚡ SMART GRID CYBER GAME ⚡")

    while True:
        print_state(state, env.belief)

        attacker_action = get_attacker_action()
        defender_action = get_defender_action()

        state, rewards, done = env.step(attacker_action, defender_action)

        print(f"\n🎯 Rewards -> Attacker: {rewards[0]}, Defender: {rewards[1]}")

        if done:
            print("\n💥 GAME OVER")
            if state.compromised:
                print("🔥 Attacker Wins!")
            else:
                print("🛡️ Defender Survived!")
            break


if __name__ == "__main__":
    main()

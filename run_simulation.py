from engine import POSGEnvironment
from posg_types import *

def print_state(state, belief):
    print("\n==============================")
    print(f"Stage: {state.stage.name}")
    print(f"Step: {state.step}")
    print(f"Compromised: {state.compromised}")
    print(f"Detected: {state.detected}")
    print(f"Threat Level: {belief.threat_level:.2f}")
    print("==============================")

def get_attacker_action(stage):
    print(f"\n[Attacker Stage: {stage.name}]")

    actions = {
        Stage.NORMAL: [AttackerAction.SCAN, AttackerAction.IDLE],
        Stage.RECON: [AttackerAction.SCAN],
        Stage.INSTALLATION: [AttackerAction.PREPARE_PAYLOAD],
        Stage.INFECTION: [AttackerAction.EXPLOIT],
        Stage.EXECUTION: [AttackerAction.EXECUTE_ATTACK]
    }

    valid_actions = actions.get(stage, [AttackerAction.IDLE])

    for i, act in enumerate(valid_actions):
        print(f"{i}: {act.name}")

    choice = int(input("Choose action: "))
    return valid_actions[choice]

def get_defender_action():
    print("\n[Defender Actions]")
    for i, act in enumerate(DefenderAction):
        print(f"{i}: {act.name}")

    choice = int(input("Choose action: "))
    return DefenderAction(choice)

def main():
    env = POSGEnvironment()
    state = env.reset()

    print("\n⚡ CYBER KILL CHAIN GAME ⚡")

    while True:
        print_state(state, env.belief)

        attacker_action = get_attacker_action(state.stage)
        defender_action = get_defender_action()

        state, rewards, done = env.step(attacker_action, defender_action)

        print(f"\n🎯 Rewards → Attacker: {rewards[0]}, Defender: {rewards[1]}")

        if done:
            print("\n💥 GAME OVER")
            if state.stage == Stage.DONE:
                print("🔥 Attack Fully Executed!")
            else:
                print("🛡️ Defender Successfully Delayed Attack!")
            break

if __name__ == "__main__":
    main()

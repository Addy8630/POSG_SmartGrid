import random
from posg_types import *

from enum import Enum
from dataclasses import dataclass

class Stage(Enum):
    NORMAL = 0
    RECON = 1
    INSTALLATION = 2
    INFECTION = 3
    EXECUTION = 4
    DONE = 5

class AttackerAction(Enum):
    SCAN = 0
    PREPARE_PAYLOAD = 1
    EXPLOIT = 2
    EXECUTE_ATTACK = 3
    IDLE = 4

class DefenderAction(Enum):
    MONITOR = 0
    PATCH = 1
    BLOCK = 2
    IGNORE = 3

@dataclass
class GameState:
    stage: Stage = Stage.NORMAL
    compromised: bool = False
    detected: bool = False
    step: int = 0

@dataclass
class BeliefState:
    threat_level: float = 0.3

class POSGEnvironment:

    def __init__(self):
        self.state = GameState()
        self.belief = BeliefState()

    def reset(self):
        self.state = GameState()
        self.belief = BeliefState()
        return self.state

    def step(self, attacker_action, defender_action):

        reward_attacker = 0
        reward_defender = 0

        current_stage = self.state.stage
        success = False

        # =========================
        # 🔴 STAGE TRANSITIONS
        # =========================

        # --- NORMAL ---
        if current_stage == Stage.NORMAL:
            if attacker_action == AttackerAction.SCAN:
                success = random.random() < 0.9
                if success:
                    self.state.stage = Stage.RECON
                    reward_attacker += 1

        # --- RECON ---
        elif current_stage == Stage.RECON:
            if attacker_action == AttackerAction.SCAN:
                success = random.random() < 0.8
                if success:
                    self.state.stage = Stage.INSTALLATION
                    reward_attacker += 2

        # --- INSTALLATION ---
        elif current_stage == Stage.INSTALLATION:
            if attacker_action == AttackerAction.PREPARE_PAYLOAD:
                success = random.random() < 0.7
                if success:
                    self.state.stage = Stage.INFECTION
                    reward_attacker += 3

        # --- INFECTION ---
        elif current_stage == Stage.INFECTION:
            if attacker_action == AttackerAction.EXPLOIT:
                if defender_action == DefenderAction.PATCH:
                    success = random.random() < 0.2
                else:
                    success = random.random() < 0.7

                if success:
                    self.state.stage = Stage.EXECUTION
                    self.state.compromised = True
                    reward_attacker += 5
                else:
                    reward_defender += 3

        # --- EXECUTION ---
        elif current_stage == Stage.EXECUTION:
            if attacker_action == AttackerAction.EXECUTE_ATTACK:
                success = random.random() < 0.9

                if success:
                    reward_attacker += 10
                    reward_defender -= 10
                    self.state.stage = Stage.DONE

        # =========================
        # 🔵 DEFENDER DETECTION
        # =========================
        if defender_action == DefenderAction.MONITOR:
            detected = random.random() < 0.6
            self.state.detected = detected

            if detected:
                reward_defender += 5
                reward_attacker -= 2

        # =========================
        # 🧠 BELIEF UPDATE
        # =========================
        if attacker_action != AttackerAction.IDLE:
            self.belief.threat_level = min(1.0, self.belief.threat_level + 0.15)
        else:
            self.belief.threat_level = max(0.0, self.belief.threat_level - 0.05)

        # =========================
        # STEP + TERMINATION
        # =========================
        self.state.step += 1

        done = (
            self.state.stage == Stage.DONE
            or self.state.step >= 15
        )

        return self.state, (reward_attacker, reward_defender), done
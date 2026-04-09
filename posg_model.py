import random
from posg_types import *

from enum import Enum
from dataclasses import dataclass

class Stage(Enum):
    RECON = 0
    WEAPONIZATION = 1
    COMPROMISE = 2
    EXECUTION = 3
    DONE = 4

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
    stage: Stage = Stage.RECON
    compromised: bool = False
    detected: bool = False
    step: int = 0

@dataclass
class BeliefState:
    threat_level: float = 0.3

def attacker_policy(stage):
    if stage == Stage.RECON:
        return AttackerAction.SCAN
    elif stage == Stage.WEAPONIZATION:
        return AttackerAction.PREPARE_PAYLOAD
    elif stage == Stage.COMPROMISE:
        return AttackerAction.EXPLOIT
    elif stage == Stage.EXECUTION:
        return AttackerAction.EXECUTE_ATTACK
    return AttackerAction.IDLE


def defender_policy():
    return random.choice(list(DefenderAction))
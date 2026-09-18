import math

from config.models import EnergyProfile, Radio
from position import Position
from enum import Enum, auto

class NodeState(Enum):
    SLEEP = auto()
    CAD_DETECT = auto()
    CAD_PROCESSING = auto()
    TX_PAYLOAD = auto()
    TX_PREAMBLE = auto()
    RX = auto()

def state_power(e: EnergyProfile, state: NodeState):
    match state:
        case NodeState.SLEEP:
            return e.sleep_power
        case NodeState.CAD_DETECT:
            return e.cad_process_power
        case NodeState.TX_PAYLOAD | NodeState.TX_PREAMBLE:
            return e.tx_power
        case NodeState.RX | NodeState.CAD_DETECT:
            return e.rx_power

class Node:
    def __init__(self, uid: int, pos: Position, radio: Radio, coverage: float):
        self.uid = uid
        self.position = pos
        self.radio = radio
        self.coverage = coverage
        self.state = NodeState.SLEEP

    def wakeup(self):
        while True:
            self._change_state(NodeState.SLEEP)
            
    def in_range(self, path_loss: float, rx_sensitivity: float) -> bool:
        return (self.radio.tx_power - path_loss) > rx_sensitivity

    def distance_to(self, other: Position):
        return math.dist(
            (self.position.x, self.position.y), (other.x, other.y)
        )

    def _change_state(self, to_state: NodeState):
        self.state = to_state


    def __str__(self):
        return f"Node {self.uid} at {self.position}"

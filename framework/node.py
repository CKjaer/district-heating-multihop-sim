import math
from collections import defaultdict
from typing import TYPE_CHECKING

from config.models import EnergyProfile, Mac

if TYPE_CHECKING:
    from network import LinearNetwork

from enum import Enum, auto

import simpy as sp
from position import Position


class NodeState(Enum):
    SLEEP = auto()
    CAD_DETECT = auto()
    CAD_PROCESSING = auto()
    TX_PAYLOAD = auto()
    TX_PREAMBLE = auto()
    RX = auto()


def _state_power(e: EnergyProfile, state: NodeState):
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
    def __init__(
        self,
        env: sp.Environment,
        uid: int,
        pos: Position,
        mac: Mac,
        nw: LinearNetwork,
        e: EnergyProfile,
        coverage: float,
    ):
        self.env = env
        self.uid = uid
        self.position = pos
        self.mac = mac
        self.network = nw
        self.coverage = coverage

        self.energy = e
        self._last_change_time = 0.0 # s
        self.energy_consumed = 0.0 # J
        self.time_spent_in: defaultdict[NodeState, float] = defaultdict(float)
        self.state = NodeState.SLEEP

    def wakeup(self):
        while True:
            self._change_state(NodeState.SLEEP)
            yield self.env.timeout(self.mac.cad_interval)

            is_neighbors_active = yield from self.cad()
            if is_neighbors_active:
                yield from self.rx()
            else:
                yield from self.tx()

    def cad(self):
        self._change_state(NodeState.CAD_DETECT)
        yield self.env.timeout(self.mac.cad_det_time)

        neighbors_detected = self.network.get_neighbors_in_state(self, NodeState.TX_PREAMBLE)
        if any(neighbors_detected):
            yield self._change_state(NodeState.CAD_PROCESSING)
            yield self.env.timeout(self.mac.cad_proc_time)
        
        return neighbors_detected
    
    def rx(self):
        self.env.timeout(1.0) # Placeholder

    def tx(self):
        self.env.timeout(1.0) # Placeholder

    def distance_to(self, other: Position):
        return math.dist((self.position.x, self.position.y), (other.x, other.y))

    def _change_state(self, to_state: NodeState):       
        if to_state is self.state:
            return
        
        dt = self.env.now - self._last_change_time
        if dt > 0:
            self.energy = dt * _state_power(self.energy, self.state)
            self.time_spent_in[self.state] += dt 
        self.state = to_state
        self._last_change_time = self.env.now

    def __str__(self):
        return f"Node {self.uid} at {self.position}"

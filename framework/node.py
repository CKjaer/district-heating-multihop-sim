import math
from collections import defaultdict
from typing import TYPE_CHECKING

from .config.models import EnergyProfile, Mac, Packet, Radio
from .position import Position

if TYPE_CHECKING:
    from .network import LinearNetwork
from enum import Enum, auto

import simpy as sp
from numpy import random


class NodeState(Enum):
    SLEEP = auto()
    CAD_DETECT = auto()
    CAD_PROCESSING = auto()
    TX_PAYLOAD = auto()
    TX_PREAMBLE = auto()
    RX = auto()


class Node:
    def __init__(
        self,
        env: sp.Environment,
        uid: int,
        pos: Position,
        mac: Mac,
        radio: Radio,
        nw: LinearNetwork,
        e: EnergyProfile,
        coverage: float,
    ):
        self.env = env
        self.uid = uid
        self.position = pos
        self.mac = mac
        self.radio = radio
        self.network = nw
        self.coverage = coverage
        self.energy = e

        self.buffer = self.energy.buffer.capacity  # J
        self.time_spent_in: defaultdict[NodeState, float] = defaultdict(float)
        self.state = NodeState.SLEEP
        self._last_change_time = 0.0  # s
        self._is_init = True

    def wakeup(self):
        while True:
            if self._is_init:
                yield self.env.timeout(random.uniform(0.0, self.mac.max_start_delay))
                self._is_init = False
            
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

        neighbors_detected = self.network.get_neighbors_in_state(
            self, NodeState.TX_PREAMBLE
        )
        if any(neighbors_detected):
            yield self._change_state(NodeState.CAD_PROCESSING)
            yield self.env.timeout(self.mac.cad_proc_time)

        return neighbors_detected

    def rx(self):
        self.env.timeout(1.0)  # Placeholder

    def tx(self, pkt: Packet):
        preamb_t, payload_t = self.mac.calculate_packet_toa(
            pkt, self.radio.spreading_factor, self.radio.bandwidth
        )
        self._change_state(NodeState.TX_PREAMBLE)
        yield self.env.timeout(preamb_t)

        self._change_state(NodeState.TX_PAYLOAD)
        yield self.env.timeout(payload_t)

        self._change_state(NodeState.SLEEP)

    def distance_to(self, other: Position):
        return math.dist((self.position.x, self.position.y), (other.x, other.y))

    def _change_state(self, to_state: NodeState):
        if to_state is self.state:
            return

        dt = self.env.now - self._last_change_time
        if dt <= 0:
            return

        self.buffer = min(
            self.energy.buffer.capacity,
            max(
                0.0,
                self.buffer
                + dt * (self.energy.harvest_power - self._state_power(self.state)),
            ),
        )

        self.time_spent_in[self.state] += dt
        self.state = to_state
        self._last_change_time = self.env.now

    def _state_power(self, state: NodeState):
        match state:
            case NodeState.SLEEP:
                return self.energy.sleep_power
            case NodeState.TX_PAYLOAD | NodeState.TX_PREAMBLE:
                return self.energy.tx_power
            case NodeState.RX | NodeState.CAD_DETECT:
                return self.energy.rx_power
            case NodeState.CAD_PROCESSING:
                return self.energy.cad_process_power

    def __str__(self):
        return f"Node {self.uid} at {self.position}"

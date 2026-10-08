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

TX_STATES = frozenset({NodeState.TX_PREAMBLE, NodeState.TX_PAYLOAD})

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
        self._radio_state_changed = self.env.event()
        self._last_change_time = 0.0

        self.collisions = []
        self.received = []
        self.preamb_end = 0.0
        
    def distance_to(self, other: Position):
        return math.dist((self.position.x, self.position.y), (other.x, other.y))

    def run(self):
        yield self.env.timeout(random.uniform(0.0, self.mac.max_start_delay))        
        yield from self._periodic_wakeup()

    def _periodic_wakeup(self):
        while True:            
            self._change_state(NodeState.SLEEP)
            yield self.env.timeout(self.mac.cad_interval)

            self._change_state(NodeState.CAD_DETECT)
            yield self.env.timeout(self.mac.cad_det_time)
            
            preambles = [
                n for n in self.network.nodes
                if n in NodeState.TX_PREAMBLE
                and n is not self 
                and self.network.is_node_in_range(self, n)
            ] 
            
            if any(preambles):
                self._change_state(NodeState.CAD_PROCESSING)
                yield self.env.timeout(self.mac.cad_proc_time)
                yield from self._rx()
            else:
                pass # TODO: Check for sensing cycle before tx

    def _rx(self):
        """Listen to in-range transmissions, return the node whose frame was received or None"""
        self._change_state(NodeState.RX)
        sync_time = self.radio.sym_time * self.radio.N_SYNC_SYM
        locked: Node | None = None
        neighbors = [
            n for n in self.network.nodes
            if n is not self and self.network.is_node_in_range(self, n)
        ]
        while True:
            active = [n for n in neighbors if n.state in TX_STATES]
            
            # Locked sender finished its frame without being disrupted
            if locked is not None and locked not in active:
                self.received.append((self.env.now, locked.uid))
                return locked

            # No nodes are transmitting
            if not active: 
                return None
            
            # Resolve overlapping transmissions accounting for the capture effect
            strongest = self._resolve_capture(active)
            is_collided = strongest is None
            is_lock_lost = locked is not None and strongest is not locked
            if is_collided or is_lock_lost:
                self.collisions.append(self.env.now)
                return None
                       
            # Check whether enough preamble is left to sync to candidate
            if locked is None:
                remaining_preamb_t = strongest.preamb_end - self.env.now
                if (
                    strongest.state is not NodeState.TX_PREAMBLE
                    or remaining_preamb_t < sync_time 
                ):
                    return None
                locked = strongest

            yield self.env.any_of([n._radio_state_changed for n in neighbors])

    def _tx(self, pkt: Packet):
        preamb_t, payload_t = self.mac.calculate_packet_toa(
            pkt, self.radio.spreading_factor, self.radio.sym_time
        )
        self.preamb_end = self.env.now + preamb_t
        self._change_state(NodeState.TX_PREAMBLE)
        yield self.env.timeout(preamb_t)

        self._change_state(NodeState.TX_PAYLOAD)
        yield self.env.timeout(payload_t)

        self._change_state(NodeState.SLEEP)

    def _resolve_capture(self, active: list[Node]):
        """Return the node that survives interference using the capture effect, or None on a collision"""
        if len(active) == 1:
            return active[0]
        
        rx_powers = sorted(
            ((n, self.network.rss(n, self)) for n in active),
            key=lambda p: p[1],
            reverse=True,
            )
        
        (node1, p1), (_, p2) = rx_powers[:2]

        if p1 >= p2 + self.radio.CAPTURE_THRESHOLD:
            return node1
        return None

    def _change_state(self, to_state: NodeState):
        if to_state is self.state:
            return

        from_state = self.state
        self._track_spend_energy(from_state)
        self.state = to_state
        self._last_change_time = self.env.now

        if from_state in TX_STATES or to_state in TX_STATES:
            previous_event, self._radio_state_changed = self._radio_state_changed, self.env.event()
            previous_event.succeed(to_state)       

    def _track_spend_energy(self, to_state: NodeState):
        dt = self.env.now - self._last_change_time
        self.buffer = min(
            self.energy.buffer.capacity,
            max(
                0.0,
                self.buffer
                + dt * (self.energy.harvest_power - self._state_power(self.state)),
            ),
        )
        self.time_spent_in[to_state] += dt
        
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

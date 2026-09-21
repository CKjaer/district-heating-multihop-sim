import math
from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class NetworkGeometry:
    burial_depth: float
    num_nodes: int
    spacing: float


@dataclass
class Radio:
    frequency: float
    tx_power: float
    tx_gain: float
    rx_gain: float
    rx_sensitivity: float
    bandwidth: float
    spreading_factor: int


@dataclass
class UndergroundToUnderground:
    ref_dist: float
    rel_permeability: float
    loss_tan: float
    rel_permittivity: float


@dataclass
class UndergroundToAboveground:
    std_shadowing: float
    cell_coverage_prob: float
    coverage_case: str
    path_loss_exponent: float


@dataclass
class Packet:
    payload: bytes = bytes(1)
    crc: int = 0
    code_rate: int = 1
    implicit_header: int = 0
    data_rate_optimize: int = 0
    n_preamble: int = 8


@dataclass
class Mac:
    packet_rate: float
    cad_time: float = field(init=False)
    _SYNCWORD: ClassVar[float] = 4.25  # symbols

    def calculate_cad_timings(self, sf: int, bw: float):
        """Compute the CAD and processing times in seconds"""
        chips = 2**sf
        t_cad = (chips + 32) / bw
        t_processing = (chips * sf) / 1.75e6

        return t_cad, t_processing

    def calculate_packet_toa(self, pkt: Packet, sf: int, bw: float):
        t_sym = (2**sf) / bw

        n_preamble_sym = pkt.n_preamble + self._SYNCWORD
        n_payload_sym = self._n_payload_sym(pkt, sf)

        return (n_payload_sym + n_preamble_sym) * t_sym

    def _n_payload_sym(self, pkt: Packet, sf: int):
        n_bytes = len(pkt.payload)
        nom = 8.0 * n_bytes - 4.0 * sf + 28 + 16 * pkt.crc - 20 * pkt.implicit_header
        denom = 4.0 * (sf - 2 * pkt.data_rate_optimize)
        n_payload_sym = 8 + max(math.ceil((nom / denom) * (pkt.code_rate + 4)), 0)

        return n_payload_sym


@dataclass(frozen=True)
class Transceiver:
    name: str
    sleep_current: float
    tx_current: float
    rx_current: float
    cad_process_current: float


# TODO: move this to config instead
_SX1276 = Transceiver(
    name="SX1276",
    sleep_current=1e-6,
    tx_current=20e-3,
    rx_current=13.8e-3,
    cad_process_current=13.0,
)


@dataclass
class EnergyProfile:
    vcc: float
    tcvr: Transceiver = _SX1276
    sleep_power: float = field(init=False)
    tx_power: float = field(init=False)
    rx_power: float = field(init=False)
    cad_process_power: float = field(init=False)

    def __post_init__(self):
        self.sleep_power = self.tcvr.sleep_current * self.vcc
        self.tx_power = self.tcvr.tx_current * self.vcc
        self.rx_power = self.tcvr.rx_current * self.vcc
        self.cad_process_power = self.tcvr.cad_process_current * self.vcc


@dataclass
class Config:
    network: NetworkGeometry
    u2u: UndergroundToUnderground
    u2g: UndergroundToAboveground
    mac: Mac
    radio: Radio
    energy: EnergyProfile

    def __post_init__(self):
        cad_time, process_time = self.mac.calculate_cad_timings(
            self.radio.spreading_factor, self.radio.bandwidth
        )

        self.mac.cad_time = cad_time + process_time

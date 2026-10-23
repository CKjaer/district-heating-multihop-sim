import math
import warnings
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
    sym_limit: int
    sym_time: float = field(init=False)
    CAPTURE_THRESHOLD: ClassVar[float] = 6.0 # dB
    N_SYNC_SYM: ClassVar[int] = 4 # symbols
    
    def __post_init__(self):
        self.sym_time = (2**self.spreading_factor) / self.bandwidth


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
    n_preamble_sym: int = 8
    payload: bytes = bytes(1)
    crc: int = 0
    code_rate: int = 1
    implicit_header: int = 1
    data_rate_optimize: int = 0


@dataclass
class Mac:
    cad_interval: float
    max_start_delay: float
    measure_interval: float
    anycast: bool 
    excess_path_loss: float
    n_preamble_sym: int = field(init=False)
    cad_det_time: float = field(init=False) 
    cad_proc_time: float = field(init=False)  
    _SYNCWORD: ClassVar[float] = 4.25 # LoRa symbols

    @staticmethod
    def calculate_cad_timings(sf: int, bw: float):
        """Compute the CAD and processing times in seconds"""
        chips = 2**sf
        t_cad = (chips + 32) / bw
        t_processing = (chips * sf) / 1.75e6

        return t_cad, t_processing

    def calculate_packet_toa(self, pkt: Packet, sf: int, t_sym: float):
        n_preamble_sym = pkt.n_preamble_sym + self._SYNCWORD
        n_payload_sym = self.n_payload_sym(pkt, sf)

        return (n_preamble_sym * t_sym, n_payload_sym * t_sym)

    @staticmethod
    def n_payload_sym(pkt: Packet, sf: int):
        n_bytes = len(pkt.payload)
        nom = 8.0 * n_bytes - 4.0 * sf + 28 + 16 * pkt.crc - 20 * pkt.implicit_header
        denom = 4.0 * (sf - 2 * pkt.data_rate_optimize)
        n_payload_sym = 8 + max(math.ceil((nom / denom) * (pkt.code_rate + 4)), 0)

        return n_payload_sym
    
    def calculate_bmac_preamb(self, radio: Radio):
        n_sym = math.ceil(
            self.cad_interval / radio.sym_time
        )
        if n_sym > radio.sym_limit:
            warnings.warn(f"Required preamble length {n_sym} exceeds transceiver limit {radio.sym_limit}")
        return n_sym


@dataclass
class EnergyProfile:
    vcc: float
    harvest_power: float  
    sleep_current: float   
    tx_current: float     
    rx_current: float     
    cad_process_current: float
    buffer: float         

    sleep_power: float = field(init=False)
    tx_power: float = field(init=False)
    rx_power: float = field(init=False)   
    cad_process_power: float = field(init=False)

    def __post_init__(self):
        self.sleep_power = self.sleep_current * self.vcc
        self.tx_power = self.tx_current * self.vcc
        self.rx_power = self.rx_current * self.vcc
        self.cad_process_power = self.cad_process_current * self.vcc


@dataclass
class Config:
    network: NetworkGeometry
    u2u: UndergroundToUnderground
    u2g: UndergroundToAboveground
    mac: Mac
    radio: Radio
    energy: EnergyProfile

    def __post_init__(self):
        self.mac.cad_det_time, self.mac.cad_proc_time  = self.mac.calculate_cad_timings(
            self.radio.spreading_factor, self.radio.bandwidth
        )
        
        if self.mac.anycast:
            raise NotImplementedError
        else:
            self.mac.n_preamble_sym = self.mac.calculate_bmac_preamb(self.radio)
            

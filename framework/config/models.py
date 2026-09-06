from dataclasses import dataclass


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


@dataclass
class UndergroundPropagation:
    ref_dist: float
    rel_permeability: float
    loss_tan: float
    rel_permittivity: float


@dataclass
class Config:
    network: NetworkGeometry
    radio: Radio
    u2u: UndergroundPropagation

import math

from config.models import Radio
from position import Position


class Node:
    def __init__(self, uid: int, pos: Position, radio: Radio, is_gateway=False):
        self.uid = uid
        self.position = pos
        self.is_gateway = is_gateway
        self.radio = radio

    def in_range(self, path_loss: float, rx_sensitivity: float) -> bool:
        return (self.radio.tx_power - path_loss) > rx_sensitivity

    def distance_to(self, other: Position):
        return math.dist(
            (self.position.x, self.position.y), (other.x, other.y)
        )

    def __str__(self):
        role = "gateway" if self.is_gateway else "sensor"
        return f"Node {self.uid} ({role}) at {self.position}"

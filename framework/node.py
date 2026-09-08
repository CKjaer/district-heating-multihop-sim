import math
import numpy as np

from config.models import Radio
from position import Position


class Node:
    def __init__(self, uid: int, pos: Position, radio: Radio):
        self.uid = uid
        self.position = pos
        self.radio = radio

    def in_range(self, path_loss: float, rx_sensitivity: float) -> bool:
        return (self.radio.tx_power - path_loss) > rx_sensitivity

    def distance_to(self, other: Position):
        return math.dist(
            (self.position.x, self.position.y), (other.x, other.y)
        )
    
    def __str__(self):
        return f"Node {self.uid} at {self.position}"

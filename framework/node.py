from position import Position


class Node:
    def __init__(self, uid: int, position: Position, is_gateway=False):
        self.uid = uid
        self.position = position
        self.is_gateway = is_gateway

    def __str__(self):
        role = "gateway" if self.is_gateway else "sensor"
        return f"Node {self.uid} ({role}) at {self.position}"
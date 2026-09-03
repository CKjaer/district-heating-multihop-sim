import math

class Position:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def distance_to(self, other: Position):
        return math.dist((self.x, self.y), (other.x, other.y))

    def __str__(self):
        return f"({self.x}, {self.y})"
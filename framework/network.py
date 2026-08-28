from node import Node
from position import Position
import simpy 


class LinearNetwork:
    """Chain of nodes on a line, equally spaced, gateway at the origin."""

    def __init__(self, num_nodes: int, spacing: float, env=None):
        if num_nodes < 2:
            raise ValueError("Need at least 2 nodes (gateway + one sensor)")
        if spacing <= 0:
            raise ValueError("Spacing must be > 0")

        self.env = env
        self.num_nodes = num_nodes 
        self.spacing = spacing
        self.nodes = []

        for uid in range(num_nodes):
            self.nodes.append(
                Node(
                    uid=uid,
                    position=Position(uid * spacing, 0.0),
                    is_gateway=(uid == 0),
                )
            )

    def update(self):
        pass

    def run(self):
        pass

    def __str__(self):
        lines = [f"LinearNetwork: {self.n} nodes, spacing={self.spacing} m"]
        lines.extend(str(node) for node in self.nodes)
        return "\n".join(lines)


if __name__ == "__main__":
    NUM_NODES = 3
    SPACING = 2.5 # m
    env = simpy.Environment()
    network = LinearNetwork(NUM_NODES, SPACING, env)
    print(network)
    
    

import simpy
from config_loader import Settings, settings
from node import Node
from position import Position


class LinearNetwork:
    """Chain of nodes on a line, equally spaced, gateway at the origin"""

    def __init__(self, settings: Settings, env: simpy.Environment):
        if settings.num_nodes < 2:
            raise ValueError("Need at least 2 nodes (gateway + one sensor)")
        if settings.spacing <= 0:
            raise ValueError("Spacing must be > 0")

        self.nodes = []
        self.env = env

        for uid in range(settings.num_nodes):
            self.nodes.append(
                Node(
                    uid=uid,
                    position=Position(uid * settings.spacing, settings.burial_depth),
                    is_gateway=(uid == 0),
                )
            )

    def update(self):
        pass

    def run(self):
        pass

    def __str__(self):
        lines = [f"LinearNetwork: {settings.num_nodes} nodes, spacing = {settings.spacing} m"]
        lines.extend(str(node) for node in self.nodes)
        return "\n".join(lines)


if __name__ == "__main__":
    env = simpy.Environment()
    network = LinearNetwork(settings, env)
    print(network)

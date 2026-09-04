import itertools

import networkx as nx
from config.loader import load_config
from config.models import Config
from node import Node
from position import Position
from propagation_models import LogDistance, MaterialAttenuation


class LinearNetwork:
    """Chain of nodes on a line, equidistant spacing with gateway at the origin"""

    def __init__(self, config: Config):
        if config.network.num_nodes < 2:
            raise ValueError("Need at least 2 nodes (gateway + one sensor)")
        if config.network.spacing <= 0:
            raise ValueError("Spacing must be > 0")

        self.config = config
        self.nodes = []
        self.graph = nx.Graph()

        # Calculate the path loss for node-to-node link in the underground pipe
        self._fspl = LogDistance(config.radio)
        self._insulation_attenuation = MaterialAttenuation(config.radio, config.u2u)
        self.u2u_path_loss = self._calculate_u2u_path_loss(config.network.spacing)

        # Create nodes instances and attach them to networkx graph
        for uid in range(config.network.num_nodes):
            node = Node(
                uid=uid,
                pos=Position(uid * config.network.spacing, config.network.burial_depth),
                radio=self.config.radio,
                is_gateway=(uid == 0),
            )
            self.nodes.append(node)

            self.graph.add_node(
                uid,
                node=node,
                name=f"{uid:02d}",
                pos=(node.position.x, node.position.y),
            )

        # Add edges between nodes within range
        for node1, node2 in itertools.combinations(self.nodes, 2):
            distance = node1.distance_to(node2.position)
            path_loss = self._calculate_u2u_path_loss(distance)
            
            if node1.in_range(path_loss, node2.radio.rx_sensitivity):
                self.graph.add_edge(
                    node1.uid,
                    node2.uid,
                    weight=distance,
                )

    def print_adjacency(self):
        for uid in sorted(self.graph.nodes()):
            neighbors = sorted(self.graph.neighbors(uid))
            print(f"Node {uid:02d} -> {neighbors}")

    def plot(self):
        import matplotlib.pyplot as plt
        from matplotlib import patches
        from matplotlib.collections import PatchCollection

        pos = nx.get_node_attributes(self.graph, "pos")
        labels = nx.get_node_attributes(self.graph, "name")

        _, ax = plt.subplots()
        nx.draw_networkx_nodes(self.graph, pos, node_size=1000)
        nx.draw_networkx_labels(self.graph, pos, labels=labels)
        ax.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)
        ax.axis("on")
        ax.set_aspect("equal", adjustable="datalim")
        
        # Range is the number of connected neighbors and is identical since
        # the nodes are equidistant in LinearNetwork
        neighbor_range = self.graph.degree(0) * self.config.network.spacing

        circles = [
            patches.Circle((n.position.x, n.position.y), neighbor_range)
            for n in self.nodes
        ]
        ax.add_collection(
            PatchCollection(
                circles,
                facecolors="none",
                edgecolors="black",
                linestyles="--",
            )
        )

        plt.show()

    def _calculate_u2u_path_loss(self, dist):
        return self._fspl(dist) + self._insulation_attenuation(dist)
    

if __name__ == "__main__":
    config = load_config()
    network = LinearNetwork(config)
    network.print_adjacency()
    network.plot()
    
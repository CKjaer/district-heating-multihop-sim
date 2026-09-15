import itertools

import networkx as nx
import numpy as np
from config.loader import load_config
from config.models import Config
from node import Node
from position import Position
from propagation_models import LogDistance, MaterialAttenuation
from scipy import stats


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

        # Calculate the log-distance path loss at the coverage radius
        self._edge_path_loss = stats.norm.isf(config.u2g.edge_prob)
        self._max_node_dist = config.network.num_nodes * config.network.spacing

        # Create nodes instances and attach them to networkx graph
        for uid in range(config.network.num_nodes):
            position = Position(
                uid * config.network.spacing + config.network.spacing,
                config.network.burial_depth,
            )

            coverage = self._assign_coverage_prob(position.x)

            node = Node(
                uid=uid, pos=position, radio=self.config.radio, coverage=coverage
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

    def print_coverage(self):
        for node in self.nodes:
            print(f"Node {node.uid} coverage probability {node.coverage:.4f}")

    def _calculate_u2u_path_loss(self, dist):
        return self._fspl(dist) + self._insulation_attenuation(dist)

    def _assign_coverage_prob(self, x_pos):
        match self.config.u2g.coverage:
            case "radial":  # Coverage probability increases with uid
                loss_diff = (
                    10
                    * self.config.u2g.path_loss_exponent
                    * np.log10(self._max_node_dist / x_pos)
                )
                coverage_prob = stats.norm.sf(
                    self._edge_path_loss - loss_diff / self.config.u2g.std_shadowing
                )
                return coverage_prob
            case "edge":  # Coverage probability is identical for all uid
                return self.config.u2g.edge_prob
            case _:
                raise ValueError("Unknown coverage case:", self.config.u2g.coverage)


if __name__ == "__main__":
    from pathlib import Path

    _ROOT = Path(__file__).resolve().parents[1]  
    config = load_config(_ROOT / "configuration.yml")
    network = LinearNetwork(config) 
    print(config.mac.cad_time)
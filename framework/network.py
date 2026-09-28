import itertools

import networkx as nx
import simpy as sp
from config.loader import load_config
from config.models import Config
from coverage import find_cell_edge_margin, compute_coverage_prob
from node import Node

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from node import NodeState

from position import Position
from propagation_models import LogDistance, MaterialAttenuation


class LinearNetwork:
    """Chain of nodes on a line, equidistant spacing with gateway at the origin"""

    def __init__(self, config: Config, env: sp.Environment):
        if config.network.num_nodes < 2:
            raise ValueError("Need at least 2 nodes (gateway + one sensor)")
        if config.network.spacing <= 0:
            raise ValueError("Spacing must be > 0")

        self.config = config
        self.env = env

        # Calculate the path loss for node-to-node link in the underground pipe
        self._fspl = LogDistance(config.radio)
        self._insulation_attenuation = MaterialAttenuation(config.radio, config.u2u)
        self.u2u_path_loss = self._calculate_u2u_path_loss(config.network.spacing)

        # Calculate cell edge link margin for the node coverage probabilities
        self._cell_margin = find_cell_edge_margin(config.u2g)
        self._max_radius = (self.config.network.num_nodes + 1) * config.network.spacing
        
        self.graph = nx.Graph()
        self.nodes = [
            self._create_node(uid) for uid in range(self.config.network.num_nodes)
        ]
        self._connect_graph_edges(self.nodes)

    def is_node_in_range(self, node: Node, other: Node):
        r = self.config.radio
        dist = node.distance_to(other.position)
        path_loss = self._calculate_u2u_path_loss(dist)

        return (r.tx_power - path_loss) > r.rx_sensitivity

    def get_neighbors_in_state(self, node: Node, state: NodeState):
        return [
            other
            for other in self.nodes
            if other is not node
            and other.state is state
            and self.is_node_in_range(node, other)
        ]

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

    def _create_node(self, uid: int) -> Node:
        position = Position(
            (uid + 1) * self.config.network.spacing,
            self.config.network.burial_depth,
        )

        coverage = self._assign_coverage_prob(position.x)

        node = Node(
            self.env,
            uid,
            position,
            self.config.mac,
            self.config.radio,
            self.config.energy,
            self,
            coverage,
        )

        self.graph.add_node(
            uid,
            node=node,
            name=f"{uid:02d}",
            pos=(node.position.x, node.position.y),
        )

        return node

    def _connect_graph_edges(self, nodes: list[Node]):
        for node1, node2 in itertools.combinations(nodes, 2):
            if self.is_node_in_range(node1, node2):
                self.graph.add_edge(
                    node1.uid,
                    node2.uid,
                    weight=node1.distance_to(node2.position),
                )

    def _calculate_u2u_path_loss(self, dist):
        return self._fspl(dist) + self._insulation_attenuation(dist)

    def _assign_coverage_prob(self, x_pos):

        match self.config.u2g.coverage_case:
            case "radial":  # Coverage probability increases with uid
                return compute_coverage_prob(
                    self.config.u2g, self._cell_margin, self._max_radius, x_pos
                )
            case "edge":  # Coverage probability is identical for all uid
                return self._cell_margin
            case _:
                raise ValueError("Unknown coverage case:", self.config.u2g.coverage)


if __name__ == "__main__":
    from pathlib import Path

    _ROOT = Path(__file__).resolve().parents[1]
    config = load_config(_ROOT / "configuration.yml")
    env = sp.Environment()
    network = LinearNetwork(config, env)
    print(config.mac.cad_det_time)

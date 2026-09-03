import simpy
from config_loader import Settings, settings
from node import Node
from position import Position
import networkx as nx
import itertools

class LinearNetwork:
    """Chain of nodes on a line, equally spaced, gateway at the origin"""

    def __init__(self, settings: Settings, env: simpy.Environment):
        if settings.num_nodes < 2:
            raise ValueError("Need at least 2 nodes (gateway + one sensor)")
        if settings.spacing <= 0:
            raise ValueError("Spacing must be > 0")

        self.settings = settings
        self.env = env
        self.nodes = []
        self.graph = nx.Graph() 

        # Create nodes instances and attach them to networkx graph 
        for uid in range(settings.num_nodes):
            node = Node(
                    uid=uid,
                    position=Position(uid * settings.spacing, settings.burial_depth),
                    is_gateway=(uid == 0),
            )
            self.nodes.append(node)
            self.graph.add_node(
                uid,
                node=node,
                name=f"{uid:02d}",
                pos=(node.position.x, node.position.y),
            )
        
        #TODO: This is a placeholder for the topology
        for node1, node2 in itertools.combinations(self.nodes, 2):
            self.graph.add_edge(
                node1.uid,
                node2.uid,
                weight=node1.position.distance_to(node2.position),
            )

    def plot(self):
        import matplotlib.pyplot as plt

        pos = nx.get_node_attributes(self.graph, "pos")
        labels = nx.get_node_attributes(self.graph, "name")
        options = {"node_size": 1000}
        _, ax = plt.subplots()
        nx.draw(self.graph, pos, labels=labels, with_labels=True, **options)
        ax.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)
        ax.axis("on")
        plt.show()

    def __str__(self):
        lines = [f"LinearNetwork: {self.settings.num_nodes} nodes, spacing = {self.settings.spacing} m"]
        lines.extend(str(node) for node in self.nodes)
        return "\n".join(lines)


if __name__ == "__main__":
    env = simpy.Environment()
    network = LinearNetwork(settings, env)
    print(network)
    network.plot()
    

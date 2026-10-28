from pathlib import Path

import simpy as sp

from framework.config.loader import load_config
from framework.network import LinearNetwork
from framework.statistics import delivery_ratio, plot_delay_cdf
from framework.timeline import plot_timeline

_ROOT = Path(__file__).resolve().parents[1] 
_SIM_TIME = 20_000.0

def main():
    config = load_config(_ROOT / "configuration.yml")
    env = sp.Environment()
    network = LinearNetwork(config, env)

    network.nodes[-1].coverage = 0.95 # For testing

    for n in network.nodes:
        print(f"Node {n.uid} with coverage probability {n.coverage:.2f}")
        print(f"Node {n.uid} is sink {n.is_sink}")
    
    network.run(until=_SIM_TIME)

    plot_delay_cdf(network.nodes)
    n_sent, pdr = delivery_ratio(network.nodes)
    n_pkt_relayed = [n.n_relayed for n in network.nodes]
    print(f"PDR: {pdr:.2f}")
    print(f"Packets sent: {n_sent}")
    print(f"Packets relayed: {n_pkt_relayed}")
    
    print("Range", network.overhearing_range)
    print("Neighbors", network.n_overhearing_neigbors)
    # for node in network.nodes:
    #     node.print_history()
    # plot_timeline(network.nodes, env.now)

if __name__ == "__main__":
    main()
from pathlib import Path

import simpy as sp

from framework.config.loader import load_config
from framework.network import LinearNetwork

_ROOT = Path(__file__).resolve().parents[1] 

def main():
    config = load_config(_ROOT / "configuration.yml")
    env = sp.Environment()
    network = LinearNetwork(config, env)

    for n in network.nodes:
        print(f"Node {n.uid} with coverage probability {n.coverage:.2f}")
    
    network.run(until=100.0)
    for node in network.nodes:
        node.print_history()

if __name__ == "__main__":
    main()
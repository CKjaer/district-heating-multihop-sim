import warnings

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

from .node import Node


def delivery_ratio(nodes: list[Node]):
    sent = sum(n.n_sent for n in nodes)
    delivered = sum(n.n_delivered for n in nodes)

    return sent, delivered / sent if sent > 0 else 0.0

def plot_delay_cdf(nodes: list[Node]):
    all_delays = np.concatenate([node.delays for node in nodes])
    if len(all_delays) == 0:
        warnings.warn("No packets reached the gateway, nothing to plot")
        return

    ecdf = stats.ecdf(all_delays)
    _, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(ecdf.cdf.quantiles, ecdf.cdf.probabilities)
    ax.set_xlabel("Delay [s]")
    ax.set_ylabel("CDF")
    ax.set_ylim(0, 1.02)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

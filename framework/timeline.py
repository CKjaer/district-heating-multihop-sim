from collections.abc import Sequence

import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from .node import Node, NodeState

STATE_COLORS = {
    NodeState.INIT: "lightgrey",
    NodeState.SLEEP: "lightsteelblue",
    NodeState.CAD_DETECT: "tab:orange",
    NodeState.CAD_PROCESSING: "gold",
    NodeState.RX: "tab:green",
    NodeState.TX_PREAMBLE: "tab:red",
    NodeState.TX_PAYLOAD: "tab:purple",
}


def state_segments(node: Node, t_end: float):
    """Return (start, duration, state) for every state the node has been in"""
    segments = []
    t_prev, state = 0.0, NodeState.INIT
    for change in node.history:
        segments.append((t_prev, change.t - t_prev, state))
        t_prev, state = change.t, change.to_state
    segments.append((t_prev, t_end - t_prev, state))
    return segments


def plot_timeline(
    nodes: Sequence[Node],
    t_end: float,
    window: tuple[float, float] | None = None,
):
    """Gantt chart of node states. Hover a bar to read its exact start and duration"""
    _, ax = plt.subplots(figsize=(12, 1 + 0.6 * len(nodes)))
    all_segments = [state_segments(node, t_end) for node in nodes]

    for row, (node, segments) in enumerate(zip(nodes, all_segments)):
        for state, color in STATE_COLORS.items():
            bars = [(t, dt) for t, dt, s in segments if s is state]
            if bars:
                ax.broken_barh(bars, (row - 0.4, 0.8), facecolors=color)

        # Sub-millisecond states are invisible when zoomed out, so mark every wake-up
        wakeups = [c.t for c in node.history if c.from_state is NodeState.SLEEP]
        ax.vlines(wakeups, row - 0.45, row + 0.45, colors="black", linewidth=0.5)

    def format_coord(x, y):
        row = round(y)
        if 0 <= row < len(nodes):
            for t, dt, state in all_segments[row]:
                if t <= x < t + dt:
                    return (
                        f"t={x:.6f} s | node {nodes[row].uid}: {state} "
                        f"start={t:.6f} s, duration={dt * 1e3:.6f} ms"
                    )
        return f"t={x:.6f} s"

    ax.format_coord = format_coord
    ax.set_yticks(range(len(nodes)), [f"Node {n.uid}" for n in nodes])
    ax.set_xlabel("Time [s]")
    ax.set_xlim(window or (0.0, t_end))
    ax.legend(
        handles=[Patch(color=c, label=str(s)) for s, c in STATE_COLORS.items()],
        loc="lower center",
        bbox_to_anchor=(0.5, 1.0),
        ncol=len(STATE_COLORS),
        fontsize="small",
    )
    plt.tight_layout()
    plt.show()

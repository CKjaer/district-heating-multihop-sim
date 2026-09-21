import numpy as np
from config.models import UndergroundToAboveground
from scipy import optimize
from scipy.stats import norm


# Goldsmith, Wireless Communications, Eq. 2.60
def _compute_cell_coverage(a, path_loss_exp, std):
    """Computes the cell coverage probability for the log-normal channel"""
    b = (10 * path_loss_exp * np.log10(np.e)) / std

    return norm.sf(a) + np.exp((2 - 2 * a * b) / b**2) * norm.sf((2 - a * b) / b)


def find_cell_edge_margin(u2g: UndergroundToAboveground):
    """Returns the coverage probability for the cell edge given a cell coverage probability"""
    objective = lambda a: (
        _compute_cell_coverage(a, u2g.path_loss_exponent, u2g.std_shadowing)
        - u2g.cell_coverage_prob
    )

    result = optimize.root_scalar(objective, bracket=[-10, 10])

    return result.root


def compute_coverage_prob(
    u2g: UndergroundToAboveground,
    edge_margin: float,
    max_radius: float,
    node_radius: float,
):
    """Updates the coverage probabilitiy for nodes relative to the cell edge probability"""
    offset = (
        10 * u2g.path_loss_exponent * np.log10(max_radius / node_radius)
    ) / u2g.std_shadowing

    return edge_margin - offset

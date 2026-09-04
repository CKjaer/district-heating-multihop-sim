def enable_latex_rendering():
    """Enable LaTeX rendering for matplotlib."""
    import matplotlib.pyplot as plt
    plt.rcParams['text.usetex'] = True
    plt.rcParams['font.family'] = 'serif'



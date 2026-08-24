import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

sns.set_theme(style="whitegrid")

# Render LaTex in plots
# plt.rcParams.update({
#     "text.usetex": True,
#     "font.family": "serif",
# })


x = np.linspace(0, 2 * np.pi, 200)
y = np.sin(x)

ax = sns.lineplot(x=x, y=y)
ax.set_xlabel(r"$x$")
ax.set_ylabel(r"$\sin(x)$")
ax.set_title(r"Simple $x$–$y$ plot: $y = \sin(x)$")

plt.tight_layout()
# plt.savefig("plot.png", dpi=300, bbox_inches="tight")
plt.show()

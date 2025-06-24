import os
from typing import List

import matplotlib.pyplot as plt


def plot_timeseries(
    name: str, values: List[float], output_dir: str = "./plots", file_format: str = "png"
):
    """
    Plots a line chart for a time series and saves it to a file.

    Parameters:
    - name: Label for y-axis and filename (e.g. 'reward')
    - values: List of y-values (y-axis); x-axis is timestep (0, 1, 2, ...)
    - output_dir: Folder where the plot is saved
    - file_format: File format to save as (e.g. 'png', 'pdf', 'svg')
    """

    os.makedirs(output_dir, exist_ok=True)
    plt.figure()
    plt.plot(values)
    plt.title(f"{name} over time")
    plt.xlabel("Timestep")
    plt.ylabel(name)
    plt.grid(True)
    plt.tight_layout()

    file_path = os.path.join(output_dir, f"{name}.{file_format}")
    plt.savefig(file_path)
    plt.close()

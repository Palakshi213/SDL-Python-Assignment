#!/usr/bin/env python3
# exercicse-4-apollo.py
# Author: Martin CLOTUCHE

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Map visualization
from matplotlib.collections import LineCollection


def read_apollo_txt(filepath):
    """
    Load the Apollo 10 ascent-phase telemetry data from a text file.

    Parameters
    ----------
    filepath : str
        Path to the .txt data file.

    Returns
    -------
    dict
        Dictionary containing the time evolution of all measured parameters.
        Keys are parameter names and values are arrays/lists of values over time.
    """

    txt_file = Path(filepath)
    apollo_dic = {}

    with txt_file.open("r", encoding="utf-8") as f:
        # Create array containing lines
        lines_arr = f.readlines()

        # Discard all lines with comments (start with '$')
        data_lines = [line for line in lines_arr if not line.lstrip().startswith("$")]

        # Remove all '\n' return to line characters
        data_lines = [line.replace("\n", "") for line in data_lines]

        # Construct a table where the line elements are separated by ','
        data_matrix = [
            [item.strip() for item in line.split(",")] for line in data_lines
        ]

        # Transform all elemens (except header = first line & units = second line) into floats
        # ASSIGMENT QUESTION: why would we store data as integers while everything is floating-point in the txt?
        # Would be a huge precision loss and there would be repetition (ex. 3 first time instances would be 0)
        header = [str(field) for field in data_matrix[0]]
        units = [str(field) for field in data_matrix[1]]
        data_matrix_int = [[(float(elem)) for elem in line] for line in data_matrix[2:]]

        # Create the dictionary
        for field in header:
            apollo_dic[field] = []

        # Fill the dictionary with data
        for line in data_matrix_int:
            for i, field in enumerate(header):
                apollo_dic[field].append(line[i])

        # Add a field containing the units
        apollo_dic["UNITS"] = units

    return apollo_dic


def plot_parameters_vs_time(dic, savepath):
    """
    Plot the time evolution of all Apollo-10 mission parameters.

    Parameters
    ----------
    dic : dict
        Dictionary mapping parameter names to their time-series values.
    savepath: str
        Path of the file where the pdf should be outputted

    Returns
    -------
    None
        Saves the plot to 'apollo_params_vs_t.pdf'.
    """
    # Create the figure
    fig, axes = plt.subplots(nrows=11, ncols=1, figsize=(7, 22))

    # Extract the time (x axis) and units (labels) from the dic
    time = dic.pop("TIME")
    units = dic.pop("UNITS")

    # Fancy colors
    colors = [
        "tab:blue",
        "tab:orange",
        "tab:green",
        "tab:red",
        "tab:purple",
        "tab:brown",
        "tab:pink",
        "tab:gray",
        "tab:olive",
        "tab:cyan",
        "tab:blue",
    ]

    # Plot each parameter vs. time
    i = 0
    for ax, (field_name, values) in zip(axes, dic.items()):
        axes[i].plot(time, values, color=colors[i], linewidth=1.5)
        axes[i].set_title(field_name)
        axes[i].set_ylabel(f"{field_name} [{units[i + 1]}]")
        axes[i].set_xlabel(f"Time [{units[0]}]")
        axes[i].grid(True)
        i += 1

    # Making the plot prettier
    fig.suptitle("Apollo-11 Mission parameters: evolution vs. time", fontsize=14)
    plt.tight_layout()
    plt.subplots_adjust(hspace=0.7)  # more space between subplots
    plt.subplots_adjust(top=0.95)  # leave room for the figure title

    plt.savefig(savepath)
    print(f"Apollo parameters evolution figure sucessfully saved in {savepath}")


def plot_groundtrack(dic, savepath="apollo_groundtrack.pdf"):
    """
    Plot the groundtrack & altitude of the Apollo-11 mission

    Parameters
    ----------
    dic : dict
        Dictionary mapping parameter names to their time-series values.
    savepath: str
        Path of the file where the pdf should be outputted

    Returns
    -------
    None
        Saves the plot to the savepath location.
    """
    # Get relevant data from dictionary
    lon = np.asarray(dic["LONG"], dtype=float)
    lat = np.asarray(dic["GC LAT"], dtype=float)
    alt = np.asarray(dic["ALTITUDE"], dtype=float)
    alt /= 1e3  # Convert in km

    # Map image (geographic projection): 120W to 30W, 15N to 60N
    lon_min, lon_max = -120, -30
    lat_min, lat_max = 15, 60
    im = plt.imread("maps/NE1_50M_SR_W_CROPPED_1080.png")

    # Create figure, plot the map
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.imshow(im, extent=[lon_min, lon_max, lat_min, lat_max])
    ax.set_aspect("equal")

    # Gridlines & labels
    ax.grid(True, color="white", alpha=0.5, linewidth=0.5, linestyle="--")
    ax.set_xlabel("Longitude [deg E]")
    ax.set_ylabel("Latitude [deg N]")

    points = np.column_stack([lon, lat]).reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    # Create the displacement line with colormap using LineCollection from plt
    norm = plt.Normalize(alt.min(), alt.max())
    lc = LineCollection(
        segments,
        cmap="seismic",
        norm=norm,
        linewidth=2,
    )
    lc.set_array(alt)
    ax.add_collection(lc)
    cbar = fig.colorbar(lc, ax=ax, orientation="vertical", shrink=0.7, pad=0.07)
    cbar.set_label("Altitude [km]")

    # Start / end markers
    ax.plot(
        lon[0],
        lat[0],
        "o",
        color="blue",
        markersize=8,
        label=f"Start: ({-lon[0]} W, {lat[0]} N, {alt[0]} km alt) ",
    )
    ax.plot(
        lon[-1],
        lat[-1],
        "*",
        color="red",
        markersize=8,
        label=f"End: ({-lon[-1]} W, {lat[-1]} N, {alt[-1]} km alt)",
    )
    ax.legend(loc="upper left")

    # Title & save
    ax.set_title("Ground track and altitude evolution of Apollo-11 mission")
    plt.savefig(savepath, bbox_inches="tight")
    plt.close(fig)
    print(f"Apollo groundtrack evolution successfully saved in {savepath}")


if __name__ == "__main__":
    apollo_dic = read_apollo_txt("as-505-ascent-phase-data.txt")
    plot_parameters_vs_time(apollo_dic, savepath="apollo_params_vs_t.pdf")
    plot_groundtrack(apollo_dic, savepath="apollo_groundtrack.pdf")

#!/usr/bin/env python 3
# exercicse-4-apollo.py
# Author: Martin CLOTUCHE

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


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


if __name__ == "__main__":
    apollo_dic = read_apollo_txt("as-505-ascent-phase-data.txt")
    plot_parameters_vs_time(apollo_dic, savepath="apollo_params_vs_t.pdf")

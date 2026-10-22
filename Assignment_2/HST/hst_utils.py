# !/usr/bin/env python 3
# hst_utils.py
# Author: Martin CLOTUCHE#

# Contains all helper functions for the Part 1 of the assignment$

# Packages import
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from pathlib import Path

photometry_tables = {
    "F336W": {
        "PHOTMODE": "WFPC2,1,A2D15,F336W,,CAL",
        "PHOTFLAM": 1.115396e-16,
        "PHOTZPT": -21.1,
        "PHOTPLAM": 3359.474,
        "PHOTBW": 204.4908,
        "ZP_CORR": -0.03288031
    },
    "F555W": {
        "PHOTMODE": "WFPC2,1,A2D15,F555W,,CAL",
        "PHOTFLAM": 6.920538e-18,
        "PHOTZPT": -21.1,
        "PHOTPLAM": 5442.934,
        "PHOTBW": 522.2513,
        "ZP_CORR": 0.02655506
    }
}

EXPTIME = 700


def open_fits_file(file_path, secondary_header=False):
    """
    Return the primary header and the image data of a FITS file.

    The data is either in extension 0 (most calibration files), in
    extension 1 (raw file), or split with one chip per extension (some
    BLEVFILEs). The returned data always has the shape (chip, y, x).
    If secondary_header is set to True, the 1st & 2nd header are returned: ((header1, header2), data)
    """
    with fits.open(file_path) as hdul:
        header = hdul[0].header.copy()
        header2 = hdul[1].header.copy()
        if hdul[0].data is not None:
            data = hdul[0].data
        elif len(hdul) == 2:
            data = hdul[1].data
        else:
            chips = []
            for i in range(1, len(hdul)):
                chips.append(hdul[i].data)
            data = np.array(chips)
    if secondary_header:
        return (header,header2), data 
    else:
        return header, data

def load_calibration_files(exposure_dir):
    """
    Load every FITS file of one exposure folder into a dict keyed by
    file type, e.g. 'raw', 'maskfile', 'blevfile', ...

    Each value is a (header, data) tuple from open_fits_file().
    For the raw file, 1st & 2nd header are returned: ((header1, header2), data)
    """
    exposure_dir = Path(exposure_dir)
    files = {}
    for file_path in sorted(exposure_dir.glob('*.fits')):
        file_type = file_path.stem.split('_')[-1]
        files[file_type] = open_fits_file(file_path, secondary_header=False)
    return files

def normalize_image(x, pmin=1, pmax=99, clip=False):
    """
    AUTHOR: Dr Andrew Kirwan
    Normalize data between 0 and 1, optionally clipping the original data
    between user-specified min/max values, or percentiles

    Parameters:
    -----------
    x: np.ndarray
        The data to normalize
    pmin: float or int
        the lower percentile to use for normalization
    pmax : float or int
        the upper percentile to use for normalization

    Returns:
    -----------
    norm: np.ndarray
        the normalized data in the interval [0, 1]
    """

    # copy and cast to float to be safe
    res = np.asarray(x, dtype=float)
    vmin, vmax = np.percentile(res, [pmin, pmax])

    # scale relative to vmin and vmax
    norm = (res - vmin) / (vmax - vmin)

    if clip:
        norm = np.clip(norm, 0, 1)

    return norm


def transform_by(func, x, pmin=1, pmax=99):
    """
    AUTHOR: Dr Andrew Kirwan
    Transform/stretch the data by a named function,
    normalizing the data using given percentiles

    For log stretches, we typically like to use a non-linear
    scaling parameter `a` to highlight contrast in the image:

        y = log10 (1 + a * x_norm) / log10(1 + a)

    Parameters:
    -----------
    func: str
        one of 'linear', 'sqrt' or 'log'
    x: np.ndarray
        data to transform
    pmin : float or int
        lower percentile
    pmax : float or int
        upper percentile
    Returns:
    ----------
    res : `np.array`
        the stretched data
    """

    x_norm = normalize_image(x, pmin=pmin, pmax=pmax, clip=True)

    if func == "sqrt":
        return np.sqrt(x_norm)
    elif func == "log":
        scale = 1000
        log_scaled = np.ma.log10(1 + scale * x_norm) / np.ma.log10(1 + scale)
        return log_scaled.filled(fill_value=0.0)
    elif func == "linear":
        return x_norm
    else:
        raise ValueError(f"Unsupported function: {func}")
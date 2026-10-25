# !/usr/bin/env python 3
# hst_utils.py
# Author: Martin CLOTUCHE and Palakshi RATTAN#

# Contains all helper functions for the Part 1 of the assignment $

""""
1. open_fits_file(file_path, secondary_header=False)
2. load_calibration_files(exposure_dir)
3. normalize_image(x, pmin, pmax)
4. transform_by(func, x, pmin, pmax)
5. plot_calibration_files(files, chip=0, title=None)
6. print_statistics(data, name="Data")
7. mask_invalid_data(raw_data, mask_data)
8. mask_statistics(files, exposure_name=None)
9. remove_bias_level(raw_data_masked, blev_data)
10. remove_bias_image(raw_data_blev_corrected, bias_data)
11. plot_correction(before, correction, after, titles, chip=0)
12. remove_dark(raw_data_bias_corrected, dark_data, dark_time)
13. correct_flatfield(raw_data_dark_corrected, flat_data)

"""

# Packages import
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from pathlib import Path
from matplotlib.colors import Normalize

photometry_tables = {
        "PHOTMODE": "WFPC2,1,A2D15,F336W,,CAL",
        "PHOTFLAM": 1.115396e-16,
        "PHOTZPT": -21.1,
        "PHOTPLAM": 3359.474,
        "PHOTBW": 204.4908,
        "ZP_CORR": -0.03288031
}

EXPTIME = 700
DPC = 16.4e3

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


def plot_calibration_files(files, chip=0, title=None):
    """
    Plot one chip of the raw and calibration images, two per row.
    """
    names = ["raw", "maskfile", "blevfile", "biasfile", "darkfile", "flatfile"]
    fig, axes = plt.subplots(3, 2, figsize=(10, 15))
    axes = axes.ravel()

    for i in range(len(names)):
        data = files[names[i]][1][chip]
        # The mask only has the values 0, 2 and 256, so no log stretch
        if names[i] == "maskfile":
            image = transform_by("linear", data, pmin=0, pmax=100)
        else:
            image = transform_by("log", data, pmin=1, pmax=99)
        im = axes[i].imshow(image, origin="lower", aspect="auto")
        axes[i].set_title(f"{names[i]} (chip {chip})")
        fig.colorbar(im, ax=axes[i])


    if title:
        fig.suptitle(title, fontsize=14)
    fig.tight_layout()
    return fig


def print_statistics(data, name="Data"):
    """
    Print the mean, median, standard deviation, min and max of each chip.
    NaN-safe functions are used because the masked pixels are NaN.
    """
    print(f"{name} statistics: ")
    for chip in range(data.shape[0]):
        print(
            f"Chip {chip}: mean = {np.nanmean(data[chip]):.2f}, "
            f"median = {np.nanmedian(data[chip]):.2f}, "
            f"std = {np.nanstd(data[chip]):.2f}, "
            f"min = {np.nanmin(data[chip]):.2f}, "
            f"max = {np.nanmax(data[chip]):.2f}"
        )
    print()


def mask_invalid_data(raw_data, mask_data):
    """
    Return a float copy of raw_data where the defective (2) and
    questionable (256) pixels of mask_data are set to NaN.
    """
    raw_data_masked = raw_data.astype(float)
    raw_data_masked[(mask_data == 2) | (mask_data == 256)] = np.nan
    return raw_data_masked

def mask_statistics(files, exposure_name=None):
    """
    Print and return the valid / defective / questionable pixel counts
    for every chip in an exposure's maskfile.

    files: dict from load_calibration_files (needs the 'maskfile' key)
    Returns {chip: {"total", "valid", "defective", "questionable"}}.
    """
    mask_header, mask_data = files["maskfile"]
    codes = {"valid": 0, "defective": 2, "questionable": 256}

    title = f"Mask statistics{f' for {exposure_name}' if exposure_name else ''}"
    print(title)

    stats = {}
    for chip in range(mask_data.shape[0]):
        total = mask_data[chip].size
        counts = {label: int(np.sum(mask_data[chip] == code)) for label, code in codes.items()}
        stats[chip] = {"total": total, **counts}

        parts = ", ".join(f"{label} = {n} ({100 * n / total:.2f}%)" for label, n in counts.items())
        print(f"Chip {chip}: total = {total}, {parts}")
    print()
    return stats

def remove_bias_level(raw_data_masked, blev_data):
    """
    Subtract the mean overscan level of the BLEVFILE from each chip.
    Even and odd columns are corrected with their own mean.
    """
    raw_data_blev_corrected = raw_data_masked.copy()

    for chip in range(raw_data_masked.shape[0]):
        # Divide the overscan in even and odd columns
        blev_overscan_even = blev_data[chip, :, 7:12:2]
        blev_overscan_odd = blev_data[chip, :, 8:13:2]

        # Get the mean values
        overscan_even_mean = np.mean(blev_overscan_even)
        overscan_odd_mean = np.mean(blev_overscan_odd)

        # Subtract
        for i in range(raw_data_masked.shape[2]):
            is_even_column = (i % 2 == 1)  # Don't forget python indexing
            if is_even_column:
                raw_data_blev_corrected[chip, :, i] -= overscan_even_mean
            else: # Odd column
                raw_data_blev_corrected[chip, :, i] -= overscan_odd_mean
    print()

    return raw_data_blev_corrected

def remove_bias_image(raw_data_blev_corrected, bias_data):
    """
    Subtract the bias data image from the blev corrected image
    """
    # Simply substract one from the other
    raw_data_bias_corrected = raw_data_blev_corrected - bias_data
    return raw_data_bias_corrected

def plot_correction(before, correction, after, titles, chip=0):
    """
    Plot one chip of the image before the correction, the correction
    that was subtracted and the image after the correction, side by side.
    The colour limits are the 1st and 99th percentiles of each image.
    """
    images = [before[chip], correction[chip], after[chip]]

    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    for i in range(3):
        vmin = np.nanpercentile(images[i], 1)
        vmax = np.nanpercentile(images[i], 99)
        im = axes[i].imshow(images[i], origin="lower", cmap="plasma", vmin=vmin, vmax=vmax)
        axes[i].set_title(f"{titles[i]} (chip {chip})")
        fig.colorbar(im, ax=axes[i], label="DN")

    fig.tight_layout()
    return fig                      # was: plt.show()

def remove_dark(raw_data_bias_corrected, dark_data, dark_time):
    """
    Subtract the dark image, considering dark time time, from the bias corrected data
    """
    raw_data_dark_corrected = raw_data_bias_corrected - dark_data * dark_time
    return raw_data_dark_corrected

def correct_flatfield(raw_data_dark_corrected, flat_data):
    """
    Multiply the image by the flat_data (inverse sensitivity)
    """
    raw_data_flat_corrected = raw_data_dark_corrected * flat_data
    return raw_data_flat_corrected

# def correct_sky(data, sigma=3, maxiters=5):
#     sky = np.empty(data.shape[0])
#     sky_bkg = np.empty(data.shape[0])
#
#     for chip in range(data.shape[0]):
#         values = data[chip][np.isfinite(data[chip])]
#         _, sky[chip], sky_bkg [chip] = sigma_clipped_stats(values, sigma=sigma, maxiters=maxiters,
#                                                             cenfunc='median', stdfunc='mad_std')
#
#     return data - sky[:, np.newaxis, np.newaxis], sky, sky_noise

def spectral_flux(data):
    """
        Calculate the spectral flux from calibrated data
    """
    counts_per_sec = data / EXPTIME
    flux = counts_per_sec * photometry_tables["PHOTFLAM"]
    return flux

def get_appmag(flux):
    """
    Converts the flux to the apparent magnitude
    """
    flux = np.asarray(flux, dtype=float)
    app_mag = np.full_like(flux, np.nan)
    good = np.isfinite(flux) & (flux > 0)
    app_mag[good] = -2.5 * np.log10(flux[good]) + photometry_tables["PHOTZPT"]
    return app_mag

def get_abs_mag(dpc, app_mag):
    """
    convert an apparent magnitude to absolute magnitude
    given a distance in parsec (pc)
    """
    return app_mag + 5 - 5 * np.log10(dpc)




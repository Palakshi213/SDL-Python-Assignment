# !/usr/bin/env python 3
# hst_utils.py
# Author: Martin CLOTUCHE and Palakshi RATTAN (also using functions used in the Lab Workbooks) #

# Contains all helper functions for the Part 1 of the assignment $

"""
hst_utils.py
============
Functions and constants for calibrating raw HST exposures
(F336W, ubai25xxm) and comparing them with the science-ready images .

Calibration order (stars + noise = (raw - bias - dark) * flat - sky):
    mask -> bias level (BLEVFILE) -> bias image -> dark -> flat -> remove sky
"""

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits

# Constants

DPC = 16.4e3  # distance in parsec

CAL_TYPES = ["raw", "maskfile", "blevfile", "biasfile", "darkfile", "flatfile"]
MASK_CODES = {"valid": 0, "defective": 2, "questionable": 256}

# Photometry tables used for the F336W Files
PHOTOMETRY = {
    "PHOTMODE": "WFPC2,1,A2D15,F336W,,CAL",
    "PHOTFLAM": 1.115396e-16,   # erg/cm2/s/A per (DN/s)
    "PHOTZPT": -21.1,           # STMAG zero point
    "PHOTPLAM": 3359.474,
    "PHOTBW": 204.4908,
    "ZP_CORR": -0.03288031,
}

# --------------------------------------------------------------------------
# Loading files

def open_fits_file(filename):
    """
    Return (primary_header, data) where data is a (4, y, x) float stack.

    Uses the first HDU holding a 3D array with first dimension 4. If none
    exists (some BLEVFILEs have one 2D chip per extension), the four 2D
    extensions are stacked instead.
    """
    with fits.open(filename) as hdul:
        header = hdul[0].header.copy()
        for hdu in hdul:
            if (isinstance(hdu.data, np.ndarray) and hdu.data.ndim == 3
                    and hdu.data.shape[0] == 4):
                return header, hdu.data.astype(float)

        chips = [hdu.data.astype(float) for hdu in hdul
                 if isinstance(hdu.data, np.ndarray) and hdu.data.ndim == 2]
        if len(chips) == 4:
            return header, np.array(chips)

    raise ValueError(f"No 4-chip image stack found in {filename}")


def load_calibration_files(exposure_name, root=".", verbose=True):
    """
    Find and load the raw file and all calibration files of one exposure.

    Parameters
    ----------
    exposure_name : str
         Files are named <exposure_name>_<type>.fits.
    root : str or Path
        Folder searched

    Returns
    -------
    dict keyed by CAL_TYPES, each value (primary_header, data (4, y, x)).
    """
    exposure = {}
    for name in CAL_TYPES:
        matches = sorted(Path(root).rglob(f"{exposure_name}_{name}.fits"))
        if not matches:
            raise FileNotFoundError(
                f"{exposure_name}_{name}.fits not found under {Path(root).resolve()}")
        exposure[name] = open_fits_file(matches[0])
        if verbose:
            print(f"{name:9s} {matches[0]}  shape {exposure[name][1].shape}")
    return exposure


def normalize_image(x, pmin=1, pmax=99, clip=False):
    """
    Normalize data to 0-1 using percentiles (NaN-safe).
    AUTHOR: Dr Andrew Kirwan (NaN-safe version)
    """
    res = np.asarray(x, dtype=float)
    vmin, vmax = np.nanpercentile(res, [pmin, pmax])
    if vmax == vmin:
        vmax = vmin + 1e-12
    norm = (res - vmin) / (vmax - vmin)
    if clip:
        norm = np.clip(norm, 0, 1)
    return norm


def transform_by(func, x, pmin=1, pmax=99):
    """
    Stretch the data by 'linear', 'sqrt' or 'log' after percentile normalization.
    AUTHOR: Dr Andrew Kirwan
    """
    x_norm = normalize_image(x, pmin=pmin, pmax=pmax, clip=True)
    if func == "sqrt":
        return np.sqrt(x_norm)
    if func == "log":
        scale = 1000
        return np.log10(1 + scale * x_norm) / np.log10(1 + scale)
    if func == "linear":
        return x_norm
    raise ValueError(f"Unsupported function: {func}")


def get_chip(filename):
    """
    Return the float stack of a FITS file.
    Uses the first HDU holding a 3D array with a dimension of 4.
    """
    with fits.open(filename) as hdul:
        for hdu in hdul:
            if (isinstance(hdu.data, np.ndarray) and hdu.data.ndim == 3
                    and hdu.data.shape[0] == 4):
                return hdu.data.astype(float)

        chips = [hdu.data.astype(float) for hdu in hdul
                 if isinstance(hdu.data, np.ndarray) and hdu.data.ndim == 2]
        if len(chips) == 4:
            return np.array(chips)

    raise ValueError(f"No 4-chip image stack found in {filename}")


def get_exposure(index, root="."):
    """
    Find and load every calibration file of one exposure by its index.

    Returns a dict keyed by 'raw', 'maskfile', 'blevfile', 'biasfile',
    'darkfile', 'flatfile'. Each value is (primary_header, data) with data
    of shape (4, y, x) as float.
    """
    exposure = {}
    for name in CAL_TYPES:
        matches = sorted(Path(root).rglob(f"ubai{index}m_{name}.fits"))
        if not matches:
            raise FileNotFoundError(
                f"ubai{index}m_{name}.fits not found under {Path(root).resolve()}")
        path = matches[0]
        with fits.open(path) as hdul:
            header = hdul[0].header.copy()
        exposure[name] = (header, get_chip(path))
        print(f"{name:9s} {path}  shape {exposure[name][1].shape}")
    return exposure

def plot_calibration_files(files, chip=0, title=None):
    """Plot one chip of the raw image and every calibration file, two per row."""

    fig, axes = plt.subplots(3, 2, figsize=(10, 15))
    for ax, name in zip(axes.ravel(), CAL_TYPES):
        data = files[name][1][chip]
        if name == "maskfile":  # only values 0, 2, 256: no log stretch
            image = transform_by("linear", data, pmin=0, pmax=100)
        else:
            image = transform_by("log", data, pmin=1, pmax=99)
        im = ax.imshow(image, origin="lower", aspect="auto")
        ax.set_title(f"{name} (chip {chip})")
        fig.colorbar(im, ax=ax)
    if title:
        fig.suptitle(title, fontsize=14)
    fig.tight_layout()
    return fig


def plot_correction(before, correction, after, titles, chip=0):
    """
    Plot one chip of the image before a correction, the correction itself,
    and the image after, side by side (colour limits = 1st/99th percentile).
    """
    images = [before[chip], correction[chip], after[chip]]
    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    for ax, img, t in zip(axes, images, titles):
        vmin, vmax = np.nanpercentile(img, [1, 99])
        im = ax.imshow(img, origin="lower", cmap="plasma", vmin=vmin, vmax=vmax)
        ax.set_title(f"{t} (chip {chip})")
        fig.colorbar(im, ax=ax, label="DN")
    fig.tight_layout()
    return fig


def print_statistics(data, name="Data"):
    """Print mean, median, std, min and max of each chip (NaN-safe)."""
    print("------------------------ ")
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

#
# def plot_masked_pixels(raw_data, mask_data, chip=0, zoom_x=(350, 500), zoom_y=(500, 650)):
#     """Raw image with defective (red) / questionable (cyan) pixels, plus a zoom."""
#     raw_image = transform_by("sqrt", raw_data[chip], pmin=1, pmax=99)
#     dy, dx = np.where(mask_data[chip] == MASK_CODES["defective"])
#     qy, qx = np.where(mask_data[chip] == MASK_CODES["questionable"])
#
#     fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))
#     for ax in (ax1, ax2):
#         ax.imshow(raw_image, origin="lower", cmap="gray")
#         ax.scatter(dx, dy, s=1, color="red", label="defective")
#         ax.scatter(qx, qy, s=1, color="cyan", label="questionable")
#     ax1.set_title(f"Raw image with masked pixels (chip {chip})")
#     ax1.legend(loc="lower left", markerscale=10, fontsize=16)
#     ax2.set_xlim(*zoom_x)
#     ax2.set_ylim(*zoom_y)
#     ax2.set_title("Zoom on the bad columns")
#     ax2.legend(loc="lower left", markerscale=10, fontsize=16)
#     fig.tight_layout()
#     return fig
#
#


#
def mask_statistics(files, exposure_name=None):
    """Print and return valid / defective / questionable counts per chip."""
    _, mask_data = files["maskfile"]
    print(f"Mask statistics{f' for {exposure_name}' if exposure_name else ''}")
    stats = {}
    for chip in range(mask_data.shape[0]):
        total = mask_data[chip].size
        counts = {k: int(np.sum(mask_data[chip] == c)) for k, c in MASK_CODES.items()}
        stats[chip] = {"total": total, **counts}
        parts = ", ".join(f"{k} = {n} ({100 * n / total:.2f}%)" for k, n in counts.items())
        print(f"Chip {chip}: total = {total}, {parts}")
    print()
    return stats
#
#
# # --------------------------------------------------------------------------
# # Calibration steps
#
def mask_invalid_data(raw_data, mask_data):
    """Float copy of raw_data with defective (2) and questionable (256) pixels = NaN."""
    masked = raw_data.astype(float)
    masked[(mask_data == 2) | (mask_data == 256)] = np.nan
    return masked

def remove_bias_level(raw_data_masked, blev_data):
    """
    Subtract the mean overscan level of the BLEVFILE from each chip.
    Even and odd columns are corrected with their own mean.
    """
    raw_data_blev_corrected = raw_data_masked.copy()

    for chip in range(raw_data_masked.shape[0]):
        blev_overscan_even = blev_data[chip, :, 7:12:2]
        blev_overscan_odd = blev_data[chip, :, 8:13:2]

        overscan_even_mean = np.mean(blev_overscan_even)
        overscan_odd_mean = np.mean(blev_overscan_odd)

        # python index 1, 3, 5... are the "even" (1-based) columns
        raw_data_blev_corrected[chip, :, 1::2] -= overscan_even_mean
        raw_data_blev_corrected[chip, :, 0::2] -= overscan_odd_mean
        print(f"Chip {chip}: even overscan = {overscan_even_mean:.3f}, odd overscan = {overscan_odd_mean:.3f}")

    return raw_data_blev_corrected

def remove_bias_image(raw_data_blev_corrected, bias_data):
    """
    Subtract the bias data image from the blev corrected image
    """
    return raw_data_blev_corrected - bias_data

def remove_dark(raw_data_bias_corrected, dark_data, dark_time):
    """
    Subtract the dark image, scaled by the dark time, from the bias corrected data
    """
    return raw_data_bias_corrected - dark_data * dark_time

#%%
def correct_flatfield(raw_data_dark_corrected, flat_data):
    """
    Multiply the image by the flat_data (inverse sensitivity)
    """
    return raw_data_dark_corrected * flat_data

def calibrate_total(exposure):
    raw_header, raw_data     = exposure["raw"]
    mask_header, mask_data   = exposure["maskfile"]
    blev_header, blev_data   = exposure["blevfile"]
    bias_header, bias_data   = exposure["biasfile"]
    dark_header, dark_data   = exposure["darkfile"]
    flat_header, flat_data   = exposure["flatfile"]
    dark_time = raw_header["DARKTIME"]

    raw_data_masked = mask_invalid_data(raw_data, mask_data)
    raw_data_blev_corrected = remove_bias_level(raw_data_masked, blev_data)
    raw_data_bias_corrected = remove_bias_image(raw_data_blev_corrected, bias_data)
    raw_data_dark_corrected = remove_dark(raw_data_bias_corrected, dark_data, dark_time)
    raw_data_flat_corrected = correct_flatfield(raw_data_dark_corrected, flat_data)

    sky = get_sky(raw_data_flat_corrected)

    # subtract on a copy so the flat-corrected image is kept
    calibrated_data = raw_data_flat_corrected.copy()
    for chip in range(calibrated_data.shape[0]):
        calibrated_data[chip] -= sky[chip]

    return calibrated_data

# Sky functions and logic were discussed with Thomas Collins and Andreu, we may have similar functions for this

def filter_mad(sample, threshold=3):
    """
    Flag values more than `threshold` MAD-based sigmas above the median.
    """
    median = np.nanmedian(sample)
    mad = np.nanmedian(np.abs(sample - median))
    stddev = 1.4826 * mad
    with np.errstate(invalid="ignore"):          # NaN pixels compare as False
        flag = (sample - median) / stddev > threshold
    return flag

def get_sky(corrected_data):
    """
    Sky level per chip: median of the pixels left after MAD clipping of
    the bright (star) pixels and the NaN (masked) pixels.
    """
    skies = []
    for chip in range(corrected_data.shape[0]):
        flag = filter_mad(corrected_data[chip], 3)
        masked = np.ma.masked_array(corrected_data[chip],
                                    mask=flag | np.isnan(corrected_data[chip]))
        skies.append(float(np.ma.median(masked)))
    return np.array(skies)

def spectral_flux(data):
    counts_per_sec = data / exptime
    flux = counts_per_sec * PHOTOMETRY["PHOTFLAM"]
    return flux

def get_appmag(flux):
    """
    Converts the flux to the apparent magnitude
    """
    flux = np.asarray(flux, dtype=float)
    app_mag = np.full_like(flux, np.nan)
    good = np.isfinite(flux) & (flux > 0)
    app_mag[good] = -2.5 * np.log10(flux[good]) + PHOTOMETRY["PHOTZPT"]
    return app_mag

def get_abs_mag(app_mag, dpc=DPC ):
    """
    convert an apparent magnitude to absolute magnitude
    given a distance in parsec (pc)
    """
    return app_mag + 5 - 5 * np.log10(dpc)

def histogram(ax, x, bins=100, xrange=None, density=False,
              normed=True, histtype='step', **kwargs):
    """
    compute and plot a histogram from some given data, correctly
    handling normalization
    # Author: Dr Andrew Kirwan

    Parameters:
    -----------
    ax: matplotlib.axes.Axes instance
        where to plot the data
    x: array
        input values
    bins: int
        number of bins to use
    range: tuple or None
        bin range
    density: bool (default False)
        if True, return a noramlised probability density
    normed: bool, default True
        if True, return a normalized histogram
    histtype: one of 'bar', 'stacked', 'step', 'stepfilled'; default 'step'
        what type of histogram to draw

    Returns:
    ----------
    n, bins, patches:
        see Axes.stairs for more information
    """
    counts, bin_edges = np.histogram(x, bins, range=xrange)
    widths = bin_edges[1:] - bin_edges[:-1]

    if density:
        counts = counts / (widths * x.size)
    elif normed:
        counts = counts / widths

    return ax.hist(
        bin_edges[:-1], bin_edges, weights=counts, histtype=histtype, **kwargs
    )

def convert_to_flux(data, header1, header2):
    """
    header1: science-extension header (PHOTFLAM, BUNIT)
    header2: primary header (EXPTIME)
    Returns flux in erg/cm2/s/A and an updated header.

    This function is form the workshop
    """
    photflam = header1['PHOTFLAM']
    bunit = str(header1['BUNIT']).strip().upper()   # header case varies: COUNTS/S, COUNTS/s...
    exposure_time = header2['EXPTIME']

    flux = np.array(data, dtype=float)
    if not bunit.endswith('/S'):                     # totals, not a rate
        flux = flux / exposure_time
    flux = flux * photflam

    new_header = header1.copy()
    new_header['BUNIT'] = 'erg/cm2/s/A'
    return flux, new_header

def compare_magnitudes(mine_dn, aligned_file, exptime, photflam,
                       add_sky=0.0, bright_percentile=90, plot=True):
    """
    Compare the magnitudes of my calibrated chip with the aligned HST file.

    Parameters
    ----------
    mine_dn :  My calibrated chip in DN (unstretched), e.g. calibrated_data[0].
    aligned_file : str or Path
        The *_c0m_aligned.fits file (science data in extension 1).
    exptime : Exposure time of my raw exposure (s).
    photflam : HOTFLAM for my chip (e.g. photometry_tables["PHOTFLAM"]).
    add_sky : Sky level to add back to my chip before converting (the STScI product
        is not sky-subtracted). Use sky[0] to add it back, 0 to leave it out.
    bright_percentile : float
        Statistics use only pixels above this percentile of the reference,
        because faint pixels are noise-dominated.
    plot : Draw the magnitude maps and the difference histogram.

    Returns
    -------
    dict with mag_mine, mag_ref, dmag_img, valid, bright, and the summary stats.
    """
    # Reference: read data and headers - from the workbook (modified)
    with fits.open(aligned_file) as hdul:
        ref_header_sci = hdul[1].header.copy()
        ref_header_prim = hdul[0].header.copy()
        ref_data = hdul[1].data.astype(float)

    print("Reference BUNIT:", ref_header_sci.get("BUNIT"),
          "| PHOTFLAM:", ref_header_sci.get("PHOTFLAM"),
          "| EXPTIME:", ref_header_prim.get("EXPTIME"))

    if mine_dn.shape != ref_data.shape:
        raise ValueError(f"Grids differ: {mine_dn.shape} vs {ref_data.shape}")

    # Calculate Flux for own and reference
    flux_ref, _ = convert_to_flux(ref_data, ref_header_sci, ref_header_prim)
    flux_mine, _ = convert_to_flux(mine_dn + add_sky,
                                   {"PHOTFLAM": photflam, "BUNIT": "COUNTS"},
                                   {"EXPTIME": exptime})
    print(f"Mean flux: mine {np.nanmean(flux_mine):.3e}, reference {np.nanmean(flux_ref):.3e}")

    # Magnitudes (get_appmag)
    mag_mine = get_appmag(flux_mine)
    mag_ref = get_appmag(flux_ref)

    valid = np.isfinite(mag_mine) & np.isfinite(mag_ref)
    bright = valid & (ref_data > np.nanpercentile(ref_data, bright_percentile))
    dmag_img = np.where(valid, mag_mine - mag_ref, np.nan)
    dmag = dmag_img[bright]

    stats = dict(median=np.median(dmag), mean=np.mean(dmag), std=np.std(dmag),
                 within_0p1=np.mean(np.abs(dmag) < 0.1),
                 n_valid=int(valid.sum()), n_bright=int(bright.sum()))

    print(f"Valid in both: {stats['n_valid']}, bright subset: {stats['n_bright']}")
    print(f"Median dm: {stats['median']:.4f} mag, std: {stats['std']:.4f} mag")
    print(f"{stats['within_0p1']:.1%} of bright pixels within 0.1 mag")

    #
    figs = {}
    if plot:
        cmap = plt.get_cmap("coolwarm").copy()
        cmap.set_bad("lightgrey")

        #  magnitude maps + difference map
        fig_maps, axes = plt.subplots(1, 3, figsize=(20, 6))
        vmin, vmax = np.nanpercentile(
            np.concatenate([mag_mine[valid], mag_ref[valid]]), [1, 99])
        for ax, m, t in [(axes[0], mag_mine, "My calibration"),
                         (axes[1], mag_ref, "Aligned reference")]:
            im = ax.imshow(m, origin="lower", cmap=cmap, vmin=vmin, vmax=vmax)
            ax.set_title(f"{t}: apparent magnitude")
            fig_maps.colorbar(im, ax=ax, label="m (STMAG)")

        lim = np.nanpercentile(np.abs(dmag_img[valid]), 95)
        im = axes[2].imshow(dmag_img, origin="lower", cmap=cmap, vmin=-lim, vmax=lim)
        axes[2].set_title("Δm = mine - reference")
        fig_maps.colorbar(im, ax=axes[2], label="Δm (mag)")
        fig_maps.tight_layout()

        # --- histogram of diff m ---
        fig_hist, ax = plt.subplots(figsize=(7, 5))
        ax.hist(dmag, bins=np.linspace(*np.percentile(dmag, [0.5, 99.5]), 150),
                histtype="step", lw=1.5, color="k")
        ax.axvline(0, color="r", ls="--")
        ax.axvline(stats["median"], color="C2", ls=":",
                   label=f"median = {stats['median']:.3f}")
        ax.set_xlabel("Δm (mag)")
        ax.set_ylabel("number of pixels")
        ax.set_title("Magnitude difference, bright pixels")
        ax.legend()
        fig_hist.tight_layout()

        figs = {"maps": fig_maps, "hist": fig_hist}

    return stats, figs

def get_stages(exposure):
    """
    Run the same steps as calibrate_total, but keep every intermediate image.
    """
    raw_header, raw_data   = exposure["raw"]
    _, mask_data           = exposure["maskfile"]
    _, blev_data           = exposure["blevfile"]
    _, bias_data           = exposure["biasfile"]
    _, dark_data           = exposure["darkfile"]
    _, flat_data           = exposure["flatfile"]
    dark_time = raw_header["DARKTIME"]

    masked = mask_invalid_data(raw_data, mask_data)
    blev   = remove_bias_level(masked, blev_data)
    bias   = remove_bias_image(blev, bias_data)
    dark   = remove_dark(bias, dark_data, dark_time)
    flat   = correct_flatfield(dark, flat_data)

    sky = get_sky(flat)
    sky_image = np.broadcast_to(sky[:, None, None], flat.shape)

    return {
        "dark_time":   dark_time,
        "masked":      masked,
        "bias_level":  masked - blev,          # the level that was subtracted
        "blev":        blev,
        "bias":        bias,
        "dark_scaled": dark_data * dark_time,  # the dark that was subtracted
        "dark":        dark,
        "flat":        flat,
        "sky":         sky,
        "sky_image":   sky_image,
        "calibrated":  flat - sky_image,
    }


def report_intermediate_results(exposure, exposure_name, calibrated=None,
                                out_dir=None, chip=0, show=False):
    """
    Print the statistics after every calibration step and plot each
    correction (before | correction | after).

    exposure   : dict from get_exposure()
    calibrated : output of calibrate_total(exposure)
    Figures are saved to out_dir

    """
    stages = get_stages(exposure)

    if calibrated is not None:
        if not np.allclose(calibrated, stages["calibrated"], equal_nan=True):
            print("WARNING: calibrate_total output differs from the recomputed stages")

    _, blev_data = exposure["blevfile"]
    _, flat_data = exposure["flatfile"]
    _, bias_data = exposure["biasfile"]
    dark_time = stages["dark_time"]

    print("\n" + "=" * 60)
    print(f"Intermediate results: {exposure_name}")
    print("=" * 60)
    print_statistics(blev_data[:, :, 7:12:2], name="Blev overscan even columns")
    print_statistics(blev_data[:, :, 8:13:2], name="Blev overscan odd columns")
    print_statistics(stages["masked"], name="Masked data")
    print_statistics(stages["blev"], name="Bias level corrected")
    print_statistics(bias_data, name="Bias image")
    print_statistics(stages["bias"], name="Bias image corrected")
    print_statistics(stages["dark_scaled"], name=f"Dark data * darktime ({dark_time}s)")
    print_statistics(stages["dark"], name="Dark corrected")
    print_statistics(flat_data, name="Flatfield data")
    print_statistics(stages["flat"], name="Flatfield corrected")
    print("Sky level per chip (DN):", np.round(stages["sky"], 3))
    print_statistics(stages["calibrated"], name="Final calibrated (sky subtracted)")

    plots = [
        ("BiasLevel", "Bias level corrected",
         (stages["masked"], stages["bias_level"], stages["blev"]),
         ["Masked data", "Bias level removed", "Bias level corrected"]),
        ("BiasImage", "Bias image corrected",
         (stages["blev"], bias_data, stages["bias"]),
         ["Bias level corrected", "Bias image", "Bias image corrected"]),
        ("Dark", "Dark corrected",
         (stages["bias"], stages["dark_scaled"], stages["dark"]),
         ["Bias corrected", f"Dark image x {dark_time:.0f} s", "Dark corrected"]),
        ("FlatField", "Flatfield correction",
         (stages["dark"], flat_data, stages["flat"]),
         ["Dark corrected", "Flatfield image", "Flatfield corrected"]),
        ("Sky", "Sky correction",
         (stages["flat"], stages["sky_image"], stages["calibrated"]),
         ["Flatfield corrected", "Sky contribution", "Sky corrected"]),
    ]
    for tag, title, (before, corr, after), titles in plots:
        fig = plot_correction(before, corr, after, titles, chip=chip)
        fig.suptitle(f"{title}: {exposure_name}")
        _finish_figure(fig, out_dir, f"{exposure_name}_{tag}.png", show)

    return stages

def _finish_figure(fig, out_dir, filename, show):
    """Save and show/close a figure."""
    if out_dir is not None:
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        fig.savefig(Path(out_dir) / filename, dpi=200, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)


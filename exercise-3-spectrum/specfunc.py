#!/usr/bin/env python 3
# specfunc.py
# Author: Palakshi Rattan

"""
This file contains the necessary functions for Exercise-3-Spectrum as part of the first Space Detector Lab Assignment
for running the script : 'spectrum.py'. Ensure these are in the same folder before running 'spectrum.py'

1. parse_textfile(filename)

    - Parses a text file, separates headers from data and returns a dictionary

2. get_spectrum(filename)

    - Extracts spectrum data (wavelength, flux) from a parsed text file, using specific headers

3. find_continuum(wave, flux)

    - Returns the baselines continuum fit of a spectrum by fitting a low-order polynomial to the background of the spectrum

4. find_continuum_masked(wave, flux, wv_width=10)

    - Returns the baselines continuum fit of a spectrum by fitting a low-order polynomial to the background of the spectrum
    - This continuum masks the emission line peak region at a width = 10 Å around the peak wavelength
    - This continuum is evaluated at all values of the wavelength range of the spectrum

5. gauss(x, A, mu, sigma)

    - Returns a Gaussian function

6. fit_gaussian(wave, flux, wv_width=10.0)

    - Fits a Gaussian function to the emission line peak
"""

from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit


def parse_textfile(filename):
    """
    A function which parses a text file, separates headers from data and returns a dictionary

    Parameters:
    -----------------
   filename: A string which contains the file to parse

    Return:
    -----------------
   result: A dictionary which contains the headers and data from a .txt file
   raises FileNotFoundError: If the file does not exist

    """

    # Set up for the dictionary which will contain the data from .txt file
    header = {}
    data_rows = []
    current_key = None

    path = Path(filename)
    if not path.exists():
        raise FileNotFoundError(f"Text file not found: {path}")

    # Open the file using 'read' mode, separate the header information and data values by filtering exact key values
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue

            if stripped.startswith("#"):
                current_key = stripped[1:].strip()
                if current_key != "DATA":
                    header[current_key] = []
            elif current_key == "DATA":
                data_rows.append(stripped)
            elif current_key is not None:
                header[current_key].append(stripped)

    # Join multi-line values (e.g. COMMENT) into single strings
    result = {key: " ".join(values) for key, values in header.items()}

    # First data row is the column header (WAVELENGTH,FLUX)
    if data_rows:
        columns = [c.strip() for c in data_rows[0].split(",")]
        data = {col: [] for col in columns}
        for row in data_rows[1:]:
            for col, value in zip(columns, row.split(",")):
                data[col].append(float(value))
        result["DATA"] = data  # Store the data separately from the header information

    return result

def get_spectrum(filename):
    """
    A function which extracts spectrum data (wavelength, flux) from a parsed text file, using specific headers

    Parameters:
    -----------------
    filename: A string which contains the file to parse

    Return:
    -----------------

    wavelength, flux : Lists of floats which contains wavelength and flux data, from the spectrum
    """
    # Use specific headers to extract the wavelength and flux data as lists of floats
    spectrum = parse_textfile(filename)
    wavelength = spectrum["DATA"]["WAVELENGTH"]
    flux = spectrum["DATA"]["FLUX"]

    return wavelength, flux

def find_continuum(wave, flux):
    """
    A function which returns the baselines continuum fit of a spectrum by fitting a low-order polynomial to the background of the spectrum
    This continuum does not mask the emission line peak
    This continuum is evaluated at all values of the wavelength range of the spectrum

    Parameters:
    -----------------
    wave: Wavelength data
    flux: Flux data

    Return:
    -----------------

    c0: The baseline continuum fit using polyfit
    slope: The slope of the linear continuum
    intercept: The intercept of the linear continuum
    slope_err: The uncertainity on the slope
    intercept_err: The uncertainity on the intercept

    """
    # Evaluate the coefficients of the polynomial to degree = 1, y = mx+c
    # This returns the coefficients (m, c)

    coeffs, covariance = np.polyfit(wave, flux, deg=1, cov=True)
    slope, intercept = coeffs
    slope_err, intercept_err = np.sqrt(np.diag(covariance))

    # Evaluates the polynomial at the values of the wave function
    c0 = np.polyval(coeffs, wave)

    return c0, slope, intercept, slope_err, intercept_err


def find_continuum_masked(wave, flux, wv_width=10):
    """
    A function which masks the region of the emission line peak before evaluating the continuum polynomial fit

    Parameters:
    -----------------
    wave: Wavelength data (Å)
    flux: Flux data (ADU)
    wv_width: Peak region width along the wavelength axis

    Return:
    -----------------
    The continuum masked region of the emission line
    slope: The slope of the linear continuum
    intercept: The intercept of the linear continuum
    mask: The region of the emission line peak
    peak_wave: The peak wavelength
    slope_err: The uncertainity on the slope
    intercept_err: The uncertainity on the intercept

    """
    # Ensure data type is correct
    wave = np.asarray(wave, dtype=float)
    flux = np.asarray(flux, dtype=float)

    # The wavelength at the max flux
    peak_wave = wave[np.argmax(flux)]

    # Creates a mask to remove the emission peak from being in polyfit (20 Å around the peak)
    mask = np.abs(wave - peak_wave) > wv_width

    # Evaluates the polynomial, ignoring the emission peak
    coeffs, covariance = np.polyfit(wave[mask], flux[mask], deg=1, cov=True)
    slope = coeffs[0]
    intercept = coeffs[1]

    # Error matrix from coveriance
    slope_err, intercept_err = np.sqrt(np.diag(covariance))

    # Evaluate continuum from masked spectrum
    continuum_masked = np.polyval(coeffs, wave)

    return continuum_masked, slope, intercept, mask, peak_wave, slope_err, intercept_err


def gauss(x, A, mu, sigma):
    """A function which calculates the Gaussian function of data:

     Parameters:
    -----------------
    x: the x dataset (wavelength) (Å)
    A: Amplitude
    mu: Gaussian mean (center)
    sigma: Gaussian standard deviation

    Return:
    -----------------
    Gaussian function evaluated at given parameters

    """
    return A * np.exp(-((x - mu) ** 2) / (2 * sigma**2))


def fit_gaussian(wave, flux, wv_width=10.0):
    """

    This function which fits a Gaussian function to the emission line peak

    Parameters:
    -----------------

    wave: The wavelength data (Å)
    flux: The flux data (ADU)
    wv_width: The region around peak wavelength considered as the emission line peak

    Return:
    -----------------
    gopt: Optimised parameters for the curve
    gcov: Convariance matrix
    line: The Gaussian fitted line over the emission line peak
    peak_wave: Wavelength at maximum flux value
    fwhm: Full-width at half maximum
    c0: The baseline continuum
    sigma_guess: The initial parameter used for sigma, i.e. the standard deviation
    peak_region_mask: Mask indicating the peak region
    """
    wave = np.asarray(wave, dtype=float)
    flux = np.asarray(flux, dtype=float)

    # Baseline (uses the continuum which removes the emission line peak)
    c0, slope, intercept, mask, peak_wave, slope_err, intercept_err = find_continuum_masked(wave, flux, wv_width)
    peak_wave = wave[np.argmax(flux)]
    sigma_guess = np.std(wave)

    # The Gaussian fit line = the flux array - the continuum, c0
    line_base = flux - c0

    # Fit only the region around the peak
    peak_region_mask = np.abs(wave - peak_wave) < wv_width
    wv_base, flux_base = wave[peak_region_mask], line_base[peak_region_mask]

    # Starting guesses: [A, mu, sigma]
    # The amplitude guess is the maximum flux value (A = flux_base.max() )
    # The mu (Gaussian center) guess is the peak wavelength
    # The sigma guess is the standard deviation of the wavelength data

    p0 = [flux_base.max(), peak_wave, sigma_guess]

    # Evaluate the Gaussian curve fitting using initial parameters, and errors from diagonal error matrix
    gopt, gcov = curve_fit(gauss, wv_base, flux_base, p0=p0)
    gerr = np.sqrt(np.diag(gcov))

    # Fitted line sitting on top of the baseline, at every wavelength
    line = c0 + gauss(wave, *gopt)
    line = line[peak_region_mask]

    # Calculate the Full-Width Half-Max
    fwhm = 2.355 * abs(gopt[2])

    return gopt, gerr, line, fwhm, c0, sigma_guess, peak_region_mask










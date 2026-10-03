import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.optimize import curve_fit


def parse_textfile(filename):
    """

    :param filename: A string which contains the file to parse
    :return: result: A dictionary which contains the headers and data from a .txt file
    """

    header = {}
    data_rows = []
    current_key = None

    with Path(filename).open("r", encoding="utf-8") as f:
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
        result["DATA"] = data # Separate the data from the header information

    return result

def get_spectrum(filename):
    """
    :param filename: A string which contains the file to parse
    :return: wavelength, flux : Lists of floats which contains wavelength and flux data, from the spectrum
    """

    spectrum = parse_textfile("spectrum.txt")
    wavelength = spectrum["DATA"]["WAVELENGTH"]
    flux = spectrum["DATA"]["FLUX"]
    return wavelength, flux

def find_continuum(wave, flux):
    """

    :param wave: Wavelength data
    :param flux: Flux data :
    :return: The baseline continuum fit using polyfit and the slope
    """
    coeffs = np.polyfit(wave, flux, deg=1) # Evaluate the coefficients of the polynomial to degree = 1, y = mx+c
    slope = coeffs[0]

    # Evaluates the polynomial at the values of the wave function
    c0 = np.polyval(coeffs, wave)

    return c0, slope

def find_continuum_masked(wave, flux, wv_width=10):
    wave = np.asarray(wave, dtype=float)
    flux = np.asarray(flux, dtype=float)

    peak_wave = wave[np.argmax(flux)]

    # Creates a mask to remove the emission peak from being in polyfit
    mask = np.abs(wave - peak_wave) > wv_width

    coeffs = np.polyfit(wave[mask], flux[mask], deg=1)
    continuum_masked = np.polyval(coeffs, wave)
    slope = coeffs[0]

    return continuum_masked, slope, mask, peak_wave

def gauss(x, A, mu, sigma):
    """Gaussian centred on zero baseline. Add c0 later"""
    return A * np.exp(-(x - mu)**2 / (2 * sigma**2))

def fit_gaussian(wave, flux, region_width=10.0):
    wave = np.asarray(wave, dtype=float)
    flux = np.asarray(flux, dtype=float)

    # Baseline (uses the continuum which does not remove the emission line peak)
    c0, slope = find_continuum(wave, flux)
    peak_wave = wave[np.argmax(flux)]
    sigma_guess = np.std(wave)
    # The flux line = the flux array - the continuum
    line_base = flux - c0

    # Fit only the region around the peak
    peak_region = np.abs(wave - peak_wave) < region_width
    wv_base, flux_base = wave[peak_region], line_base[peak_region]

    # Starting guesses: [A, mu, sigma]
    p0 = [flux_base.max(), peak_wave, sigma_guess]

    gopt, gcov = curve_fit(gauss, wv_base, flux_base, p0=p0)
    gerr = np.sqrt(np.diag(gcov))

    # Fitted line sitting on top of the baseline, at every wavelength
    line = c0 + gauss(wave, *gopt)
    fwhm = 2.355 * abs(gopt[2])

    return gopt, gerr, line, fwhm, c0, slope, sigma_guess





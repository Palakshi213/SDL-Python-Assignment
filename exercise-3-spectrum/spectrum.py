#!/usr/bin/env python 3
# spectrum.py
# Author: Palakshi Rattan

"""

This main script runs the functions necessary to fit the continuum and an emission-line Gaussian to a spectrum as part of
Exercise-3 for the Space Detector Lab assignement.

There are four plots:

1. The Wavelength v. Flux Spectrum
2. The Wavelength v. Flux Spectrum overlaid by the baseline continuum (no masking)
3. The Wavelength v. Flux Spectrum overlaid by the baseline continuum (ignoring emission line peak)
4. The Wavelength v. Flux Spectrum overlaid by the baseline continuum and a Gaussian fit of the emission line peak

"""
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from specfunc import *
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Fit the continuum and an emission-line Gaussian to a spectrum."
    )
    parser.add_argument("filename", help="Spectrum text file, e.g. spectrum.txt")
    args = parser.parse_args()
    filename = args.filename

    plt.close('all')
    wavelength, flux = get_spectrum(filename)

    # --- Part 1: Spectrum of Wavelength vs. Flux ---
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(wavelength, flux, c='#EB5959')
    ax.set_title("Wavelength v. Flux Spectrum")
    ax.set_xlabel("Wavelength (Å)")
    ax.set_ylabel("Flux (ADU)")
    ax.grid(True)

    # --- Part 2: Spectrum and Baseline Continuum  ---
    continuum, slope = find_continuum(wavelength, flux)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_title("Wavelength v. Flux Spectrum")
    ax.plot(wavelength, flux, c='#EB5959', label="Spectrum")
    ax.plot(wavelength, continuum, c='blue', lw=2, label="Continuum (Polynomial Fit)")
    ax.set_title("Wavelength v. Flux Spectrum")
    ax.set_xlabel("Wavelength (Å)")
    ax.set_ylabel("Flux (ADU)")
    ax.set_facecolor('lightgrey')
    ax.grid(True)
    ax.legend()
    print(f"Wave Range: {min(wavelength):.1f} to {max(wavelength):.1f} Å")
    print(f"Slope: {slope}")

    # --- Part 3: Spectrum and Continuum with the Emission Line Ignored ---
    continuum_masked, slope, mask, peak_wave = find_continuum_masked(wavelength, flux)
    print(f"Peak Wave: {peak_wave}")
    print(f"Slope (masked): {slope}")

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_title("Wavelength v. Flux Spectrum")
    ax.plot(wavelength, flux, c='#EB5959', lw=0.7, label="Spectrum")
    ax.plot(wavelength, continuum_masked, c='b', lw=2, label="Continuum")
    ax.set_xlabel("Wavelength (Å)")
    ax.set_ylabel("Flux (ADU)")
    ax.axvspan(peak_wave - 10, peak_wave + 10, color='gray', alpha=0.3, label="Masked")
    ax.set_facecolor('lightgrey')
    ax.legend()
    ax.grid(True)

    # --- Part 4: Gaussian Fit ---
    gopt, gerr, line, fwhm, c0, sigma_guess = fit_gaussian(wavelength, flux)
    A, mu, sigma = gopt
    A_err, mu_err, sigma_err = gerr
    fwhm_err = 2.355 * sigma_err

    print(f"Centre = {mu:.3f} ± {mu_err:.3f} Å, "
          f"FWHM = {fwhm:.6f} ± {fwhm_err:.3f} Å, "
          f"amplitude = {A:.2f} ± {A_err:.3f} ADU")

    print(f"Uncertainties (A, mu, sigma): {gerr}")

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_title("Wavelength v. Flux Spectrum")
    ax.plot(wavelength, flux, c='#EB5959', lw=0.7, label="Spectrum")
    ax.plot(wavelength, c0, c='b', lw=2, label="Continuum")
    ax.axvspan(peak_wave - 10, peak_wave + 10, color='gray', alpha=0.3, label="Peak Region")
    ax.plot(wavelength, line, c='k', lw=1.5, label="Gaussian Fit")
    ax.set_facecolor('lightgrey')
    ax.set_xlabel("Wavelength (Å)")
    ax.set_ylabel("Flux (ADU)")
    ax.legend()
    ax.grid(True)

    plt.show()


if __name__ == "__main__":
    main()
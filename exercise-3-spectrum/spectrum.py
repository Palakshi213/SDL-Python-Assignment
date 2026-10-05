#!/usr/bin/env python 3
# spectrum.py
# Author: Palakshi Rattan

"""

This main script runs the functions necessary to fit the continuum and an emission-line Gaussian to a spectrum as part of
Exercise-3 for the Space Detector Lab assignement.

There are four plots:

1. The Wavelength v. Flux Spectrum
2. The Wavelength v. Flux Spectrum overlaid by the baseline continuum (no masking)
3. The Wavelength v. Flux Spectrum overlaid by the baseline continuum (masking emission line peak in polynomial fit)
4. The Wavelength v. Flux Spectrum overlaid by the baseline continuum and a Gaussian fit of the emission line peak

"""

import argparse
#from pathlib import Path

# Import necessary packages, including specific functions written for this exercise
import matplotlib.pyplot as plt
import numpy as np
from specfunc import find_continuum, find_continuum_masked, fit_gaussian, get_spectrum


def main():
    """
    Parse the arguments and run the functions to investigate the wavelength vs. flux spectrum
    """

    parser = argparse.ArgumentParser(
        description="Fit a low-order polynomial and a Gaussian function to a spectrum."
    )
    parser.add_argument("filename", help="Spectrum text file, e.g. spectrum.txt")
    args = parser.parse_args()
    filename = args.filename

    plt.close("all")

    # --- Part 1: Spectrum of Wavelength vs. Flux ---
    wavelength, flux = get_spectrum(filename)

    # Plotting
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(wavelength, flux, c="#EB5959")
    ax.set_title("Wavelength v. Flux Spectrum")
    ax.set_xlabel("Wavelength (Å)")
    ax.set_ylabel("Flux (ADU)")
    ax.grid(True)

    # --- Part 2: Spectrum and Baseline Continuum  ---
    continuum, slope, intercept, slope_err, intercept_err = find_continuum(wavelength, flux)
    
    # Plotting
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_title("Wavelength v. Flux Spectrum")
    ax.plot(wavelength, flux, c="#EB5959", label="Spectrum")
    ax.plot(wavelength, continuum, c="blue", lw=2, label=f"Continuum (1st-order Polynomial Fit)\n \
    Slope={slope:.2f} ADU/Å - Uncertainty: {slope_err:.2f}\n\
    Intercept={intercept:.2f} ADU -  Uncertainty: {intercept_err:.2f}")
    ax.set_title("Wavelength v. Flux Spectrum - 1st order fit on whole spectrum")
    ax.set_xlabel("Wavelength (Å)")
    ax.set_ylabel("Flux (ADU)")
    ax.set_facecolor("lightgrey")
    ax.grid(True)
    ax.legend()

    # Logging
    print("1st order polynomial fit - without emission line masking\n------")
    print(f"Wave Range: {min(wavelength):.1f} to {max(wavelength):.1f} Å")
    print(f"Slope: {slope:.3f} ADU/Å; Uncertainity: {slope_err:.3f}")
    print(f"Intercept: {intercept:.3f} ADU ; Uncertainity: {intercept_err:.3f} \n")


    # --- Part 3: Spectrum and Continuum with the Emission Line Ignored ---
    wv_width = 10 # Chosen value for the wavelength width
    continuum_masked, slope_masked, intercept_masked, mask, peak_wave, slope_err_masked, intercept_err_masked = find_continuum_masked(wavelength, flux, wv_width)

    # Plotting
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(wavelength, flux, c="#EB5959", lw=0.7, label=f"Spectrum\nPeak wave at: {peak_wave:.2f} Å")
    ax.plot(wavelength, continuum_masked, c="b", lw=2, label=f"Continuum\n\
    Slope={slope_masked:.3f} ADU/Å - Uncertainty: {slope_err_masked:.3f}\n\
    Intercept={intercept_masked:.3f} ADU -  Uncertainty: {intercept_err_masked:.3f}")
    ax.set_title("Wavelength v. Flux Spectrum - 1st order fit ignoring emission line peak")
    ax.set_xlabel("Wavelength (Å)")
    ax.set_ylabel("Flux (ADU)")
    ax.axvspan(peak_wave - wv_width, peak_wave + wv_width, color="gray", alpha=0.3, label=f"Masked Region\n Chosen width: {wv_width*2}")
    ax.set_facecolor("lightgrey")
    ax.legend()
    ax.grid(True)

    # Logging Results
    print("1st order polynomial fit - with emission line masking\n------")
    print(f"Peak Wave: {peak_wave}")
    print(f"Chosen emission line width: {wv_width*2} \n")
    
    print(f"Slope (masked) ADU/Å: {slope_masked:.3f} ; Uncertainty: {slope_err_masked:.3f}")
    print(f"Intercept (masked) ADU: {intercept_masked:.3f} ; Uncertainty: {intercept_err_masked:.3f} \n")


    # --- Part 4: Gaussian Fit ---
    gopt, gerr, line, fwhm, c0, sigma_guess, peak_region_mask = fit_gaussian(wavelength, flux, wv_width)
    A, mu, sigma = gopt
    A_err, mu_err, sigma_err = gerr
    fwhm_err = 2.355 * sigma_err

    print("Gaussian fit\n------")
    print(
        f"Centre = {mu:.3f} ± {mu_err:.3f} Å\n"
        f"FWHM = {fwhm:.6f} ± {fwhm_err:.3f} Å\n"
        f"Amplitude = {A:.2f} ± {A_err:.3f} ADU\n"
        f"Sigma Initial Parameter = {sigma_guess:.3f} \n"
        f"Sigma = {sigma:.3f} ± {sigma_err:.3f} \n"
    )
    print(f"Uncertainties (A, mu, sigma): {gerr}")

    # Plotting
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_title("Wavelength v. Flux Spectrum - Gaussian fit on emission line")
    ax.plot(wavelength, flux, c="#EB5959", lw=0.7, label="Spectrum")
    ax.plot(wavelength, c0, c="b", lw=2, label="Continuum")
    ax.axvspan(
        peak_wave - wv_width, peak_wave + wv_width, color="gray", alpha=0.3, label="Peak Region"
    )
    ax.plot(np.asarray(wavelength)[peak_region_mask], line, c="k", lw=1.5, label=f"Gaussian Fit \n \
        Centre = {mu:.3f} ± {mu_err:.3f} Å \n \
        FWHM = {fwhm:.6f} ± {fwhm_err:.3f} Å\n \
        Amplitude = {A:.2f} ± {A_err:.3f} ADU")
    ax.set_facecolor("lightgrey")
    ax.set_xlabel("Wavelength (Å)")
    ax.set_ylabel("Flux (ADU)")
    ax.legend()
    ax.grid(True)
    plt.show()



if __name__ == "__main__":
    main()
    exit()
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from specfunc import *
import argparse



plt.close('all')
wavelength, flux = get_spectrum("spectrum.txt")
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(wavelength, flux, c='#EB5959')
ax.set_title("Wavelength v. Flux Spectrum")
ax.set_xlabel(f"Wavelength (Å)")
ax.set_ylabel(f"Flux (ADU)")
ax.grid(True)

continuum, slope  = find_continuum(wavelength, flux)

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(wavelength, flux, c='#EB5959', label="Spectrum")
ax.plot(wavelength, continuum, c='blue', lw=2, label="Continuum (polynomial fit)")
ax.set_title("Wavelength v. Flux Spectrum")
ax.set_xlabel("Wavelength (Å)")
ax.set_ylabel("Flux (ADU)")
ax.set_facecolor('lightgrey')
ax.grid(True)
ax.legend()
plt.show()
print(f"Wave Range: {min(wavelength):.1f} to {max(wavelength):.1f} Å")
print(f"Slope: {slope}")


continuum_masked, slope, mask, peak_wave = find_continuum_masked(wavelength, flux)
print(f"wave range: {min(wavelength):.1f} to {max(wavelength):.1f}")
print(f"Peak Wave: {peak_wave}")
print(f"Slope: {slope}")

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(wavelength, flux, c='#EB5959', lw=0.7, label="Spectrum")
ax.plot(wavelength, continuum_masked, c='b', lw=2, label="Continuum")
ax.axvspan(peak_wave - 10, peak_wave + 10, color='gray', alpha=0.3, label="Masked")
ax.set_facecolor('lightgrey')
ax.legend()
ax.grid(True)
plt.show()


gopt, gerr, line, fwhm, c0, slope, sigma_guess = fit_gaussian(wavelength, flux)
A, mu, sigma = gopt
A_err, mu_err, sigma_err = gerr
fwhm_err = 2.355*sigma_err

print(f"Centre = {mu:.3f} ± {mu_err:.3f} Å, FWHM = {fwhm: .6f} ± {fwhm_err:.3f} Å, amplitude = {A:.2f} ± {A_err:.3f} ADU")
print(f"Slope: {slope}")

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(wavelength, flux, c='#EB5959', lw=0.7, label="Spectrum")
ax.plot(wavelength, c0, c='b', lw=2, label="Continuum")
ax.axvspan(peak_wave - 10, peak_wave + 10, color='gray', alpha=0.3, label="Peak Region")

ax.set_facecolor('lightgrey')
plt.plot(wavelength, line, c='k', lw=1.5, label="Gaussian Fit")

plt.legend()
plt.grid(True)
print(gerr)

plt.show()
# Introduction to Programming: Spectrum Fitting 

## Stellar spectra 

Stars emit light over a continuous spectrum of energy, and we can study the structure of this spectrum to learn about the composition, age, and behavior of that star. In these spectra, we observe **absorption lines** and **emission lines** that are generally produced by interactions between the star and its photosphere. We will not go into detail about the physics of these interactions, but suffice it to say that:

1. Absorption lines are "dips" in the spectrum at particular wavelengths where the observed light from the star decreases; and 
1. Emission lines are peaks in the spectrum at particular wavelengths where the observed light from the star increases.

Astronomers spend an awful lot of time studying these spectral features, and more often than not we attempt to model the dips and peaks using the Gaussian or normal distribution. 

## The Task


You are provided with an optical spectrum from an astronomical source in the file `spectrum.txt`. This spectrum contains a single emission line peak. Write a program that parses this data file and stores the wavelength and flux values in appropriate variables (or as a single structure, e.g. a `dict` object). Your program should include functions that:

1. Fit a low-order polynomial to the background of the spectrum (ignoring the emission line peak); 
1. Fit a Gaussian to the emission line peak; and
1. Extract all the relevant parameters (and uncertainties) from your Gaussian and polynomial functions

Note that the Gaussian should have the form:

```
```
$$
\displaystyle \ G(x; A, \mu, \sigma, c_0) = c_0 +  A \times \exp\left(-\frac{(x - \mu)^2}{2\sigma^2}\right)
$$
```
```
where $A$ is the amplitude, $\mu$ is the position of the center of the peak, $\sigma^2$ is the variance, and $c_0$ is a "baseline" that that Gaussian sits atop. This $c_0$ can be a constant (unlikely) or a function (more likely), so we can treat it like a low-order polynomial. A derived parameter from this is the so-called "full-width at half-maximum" or FWHM, which is related to $\sigma$ by $\mathrm{FWHM} \approx 2.355 \sigma$. 

Once you have fit the baseline (we often call it a "continuum") and the Gaussian peak, your program should make:
1. A plot of the full spectrum;
1. A plot of the full spectrum with the polynomial overlaid; and 
1. A plot of the full spectrum with the polynomial **and** the Gaussian overlaid.

Your program should also print the best-fit parameters and their uncertainties for your fitted curves. In particular, you should state the amplitude, the central wavelength of the peak, and the FWHM of the peak, including the appropriate units for each. These units can be found in the header information in the file. For each of your plots, ensure that there are clear axis labels and units.

As a guideline, structure your code so that it can be run from a terminal with

``
$ python scriptname.py spectrum.txt
``
## Notes:

You will of course want to examine the structure of the file first: headers *always* contain useful information, but not all useful information is *relevant* to the task at hand. The most rigorous (and best) approach is to have your parser efficiently handle all the header information, and you extract only the parts you need. You can of course skip the header information completely and extract only the data, but then you need to hard-code things like the units, observation time, etc., which means your code is not extensible so you could not use it on other similar files.

A significant problem in curve fitting is estimating the initial parameters. Sometimes allowing fitting routines to use their default "guesses" can work well enough, but it is not always guaranteed, so you could consider how to constrain your fitter so that it makes a reasonable guess for the parameters prior to attempting to fit them. 

In the Jupyter Notebook, we have provided some skeleton code to help you get started. 

## Useful Python Skills

* Parsing text files
* Writing functions
* Modelling with `scipy.optimize.curve_fit`
* Command line arguments & `argparse`

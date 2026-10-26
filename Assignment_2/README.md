# PHYC40870-Space Detector Laboratory - Assignment 2: Optical Detectors

## Folder hierarchy

```
Assignment_2/
├── hst-calibration/                       # Raw HST/WFPC2 exposures and their calibration files
│   ├── ubai2505m/                         #   MASKFILE, BLEVFILE, BIASFILE, DARKFILE, FLATFILE
│   ├── ubai2507m/                         #   for each exposure
│   └── ubai2508m/
├── hst-processed/                         # Calibrated HST images produced by the notebook
├── sentinel-processed/                    # Processed Sentinel-2 / Google Earth outputs
├── hst-assignment.ipynb                   # Part 1: HST calibration routine
├── sentinel-assignment.ipynb              # Part 2: Hunga Tonga analysis
├── optical-detectors-assignment-brief.html
├── hst-assignment-guidance.html
└── README.md
```

All paths in the notebooks are relative to `..`, so they can be run without changing any paths.


# Assignment 2 - Part 1: HST Calibration Routine
------

## Objectives

Calibrate raw HST WFPC2 F336W exposure ubai2505m from its raw data (mask, bias level, bias image, dark, flat), estimate and remove the sky, then compare the result with the archive science-ready image (ubai2505m_c0m_aligned.fits), both in counts (DN) and photometrically (flux and magnitude)

Equation: stars + noise = (raw - bias - dark) * flat - sky

#### 2. Mask invalid data with `MASKFILE`
-----

**We observe:**
1. Some defective individuels pixels on the image
2. Some defective pixels on the same column, on top of each other
3. For those defective pixels on top of each other, all pixels on top of them in these columns are classified as 'questionable'

**Analysis:**

According to \url{https://www.stsci.edu/instrument-news/isr/wfpc2/9503/9503_1.html}, these effects are due to **charge traps**: single pixels that don't pass charge along properly. As CCDs are read columns by columns, all previous pixels in the column are considered as 'questionable'

**Decision:**

As the statistics show that less of 1% of the pixels are defective or questionable, and as recommended on the previous cited source, the chosen decision is to mask the defective and questionable pixels with Nan values. Note that the usage of nan-safe functions is thus required from now on.

Another, more complex approach would have been to interpolate these pixels, but we decided not to do so as it would create fake data into our measurements

#%% md
### 2. Correct Analog-to-Digital conversion errors with `ATODFILE`
-----
**Not required**: the `raw.fits` files given are already ADC-corrected

#### 3. Remove bias level with `BLEVFILE`
-----
The `BLEVFILE` countains the ias level values: DC offsets applied to ensure our values are always positive.

Because HST uses 12 bits for number representation, values are between 0- 4095 range.

The bias level file uses the **overscan** region of each chip (pixels always covered) to calculate the padding required to ensure only positive numbers. For WFPC2, the overscan region is in columns 9-14 and rows 10-790 `data[9:790, 8:14]`.

Bias levels for even and odd rows are different:
- `BIASODD`: columns 9, 11, 13 ; considering Python indexing: 8, 10, 12
- `BIASEVEN`: columns 8, 10, 12 ; Python indexing: 7, 9, 11

Bias level correction
1. Get the mean value of the odd/even overscan regions
2. Substract that from all odd/even columns of the image


This is acheived by the `remove_bias_level` function in the `hst_utils` file

#### 4. Remove bias image with `BIASFILE`
-----
The `BIASFILE` is an image of the same shape as the raw science exposure which compensates for readout noise. We get it by just taking a short exposure with a closed shutted.

It can simply be substracted from our bias level corrected image
This is acheived by the `remove_bias_image` function in the `hst_utils` file

#### 5. Substract dark with `DARKFILE`
-----
The `DARKFILE` is a closed-shutter image which accounts for thermal noise (dark current). The reference file was normalized to an exposure time of 1 second (see its `HISTORY`), so its values are in DN/s.

Thus, the darkfile image should be first multiplied by the dark time of the science image (`DARKTIME` = 700 s in the raw header), then substracted from the bias corrected image.
This is acheived by the `remove_dark` function in the `hst_utils` file


#### 6. Flatfield correction with `FLATFILE`
-----

`FLATFILE` is an image taken with a uniform exposure that accounts for pixel sensitivity variations across the detector.
The WPFC2 pipeline delivers it as an inverse sensitivity.

Thus, it should be multiplied with the dark corrected image
This is acheived by the `correct_flatfield` function in the `hst_utils` file

#### 7. Shading removing with `SHADFILE`
-----

Not required because the exposure time is not very short.

#### 8. Removing the Sky Contribution
-----
After bias, dark and flat corrections, every pixel still contains a roughly constant background level. MAD sigma clipping replaces the standard deviation (which could be a possible background estimator) with the Median Absolute Deviation (MAD). The MAD is robust, ignores outliers and computes how far the pixels are from the median. 1.4826 converts MAD to a Gaussian standdard deviation (3 sigma).

Because sky computation is performed on flat-fielded but not distortion corrected images, it is important to keep in mind that flat-fielding is performed to obtain correct surface brightnesses.

Source: https://jwst-pipeline.readthedocs.io/en/1.18.x/jwst/skymatch/description.html

For each chip, everything 3 sigma above the median is flag, and the median of the remaining data is computed. This is the sky estimate and is subtracted from the corrected flatfield data. This is done by using the `filter_mad` and `get_sky` functions `hst_utils`.

#%% md

#%% md
### 10. Photometry calibration with `PHOTTAB`
-----

`PHOTTAB` is a throughput table generated by the pipeline from the HST component throughput tables. It contains the `PHOTFLAM`, `PHOTZPT` and `ZP_CORR` keys recquired for the photometry calibration.

**Strong assumption**: `PHOTTAB` is not provided in the hst-calibration files or in the raw data. Thus, the `PHOTFLAM`, `PHOTZPT` and `ZP_CORR` keys are taken directly from the science-ready image.

Reminder from HST workshop 2:
| Keyword    | Description                                    |
|:-----------|:-----------------------------------------------|
| `PHOTFLAM` | Inverse sensitivity                            |
| `PHOTZPT`  | Zero point magnitude                           |
| `ZP_CORR`  | Delta magnitude correction for contamination   |

Calibration steps:

1. Convert the image to a ***spectral flux density*** [# photons /(s *unit energy* Area)]
    - Divide the number of photons by the exposure time to get #photons/s.
    - Multiply the result by the Inverse sentivity (`PHOTFLAM`) to obtain $F_\lambda$
2. Compute the apparent and absolute magnitude (formulas from the Course manual):
    - *Apparent magnitude*
        $$
        m_{app} = -2.5 \times \log F_\lambda + ZPP
        $$
        Where $ZPP$ is the Zero-Point Magnitude (`PHOTZPT`)

    - *Absolute magnitude*
        $$
        M_{abs} = m_{app} + 5 - 5 \log(d_{pc})
        $$
        Where $\log(d_{pc})$ is the distance to the star in parsecs.
        **Assumtion**: the given image shows the **NGC1261** cluster, at a distance of $16.4pc$


The `compare_magnitudes` function computes the apparent magnitude for the previously calibrated data, and the reference data from the aligned.fits files. The decision to use the apparent magnitude and not distance was such that we could use `PHOTFLAM` and compute the flux from counts for the refernece file. The absolute zero-point cancels in the difference, so the result tests only the calibration (bias, dark, flat, sky and PHOTFLAM). This is only the pixel magnitude, and aperture photometry would be an improved step to compare individual stars.

#%% md
### 11. Analysis and Results for ubai2025m - Chip 0

Here, quantitative differnences have been computed for the calibrated image and the aligned reference image provided of **ubai2025m chip 0**. For the direct comparison between the aligned file and our calibration , 635,890 of 640,000 pixels are valid (99.4%). The 4,110 excluded pixels are the masked bad pixels which were identified earlier. The median of 0.0057 means the images differ by about 0.6% of the display range and 100.0% of pixels between -0.1 and 0.1 DN when only valid pixels are counted.

For the photometric calibration:

Mean flux agrees to 0.24%: 3.689×10^-19 vs 3.680×10^-19  is a ratio of 1.0024, or about 0.003 mag. The mean is dominated by bright pixels, so the overall flux scale (bias, dark, flat, PHOTFLAM) is reproduced decently accurately.

From running the notebook for different exposures, it is evident that ubai2505m aligns most accurately with its reference file, but the other exposures also show above 90% in magnitudes of bright pixels from magnitude calculation within 0.1 mag and the histograms in pixel-to-pixel comparison with the aligned images demonstrate the same structure and shape. 

This notebook could be improved by running iteratively through the different raw files, and storing results for each in a script. Unfortunately, this was resulting in a high runtime, but could be mitigated through more efficient functions and parsing. By applying the calibration to the other exposures, a next step would also be to remove cosmic rays.


The intermediate results for each step of the calibration for each chip are also printed here for inspection:


------------------------
Mask statistics for ubai2505m


Chip 0: total = 640000, valid = 635890 (99.36%), defective = 1169 (0.18%), questionable = 2941 (0.46%)
Chip 1: total = 640000, valid = 635586 (99.31%), defective = 1697 (0.27%), questionable = 2717 (0.42%)
Chip 2: total = 640000, valid = 637684 (99.64%), defective = 1171 (0.18%), questionable = 1145 (0.18%)
Chip 3: total = 640000, valid = 632032 (98.75%), defective = 1393 (0.22%), questionable = 6575 (1.03%)

------------------------
Blev overscan even columns statistics:
Chip 0: mean = 299.61, median = 300.00, std = 0.54, min = 298.00, max = 301.00
Chip 1: mean = 319.95, median = 320.00, std = 0.33, min = 319.00, max = 321.00
Chip 2: mean = 313.48, median = 313.00, std = 0.58, min = 311.00, max = 316.00
Chip 3: mean = 298.77, median = 299.00, std = 0.55, min = 297.00, max = 302.00

------------------------
Blev overscan odd columns statistics:
Chip 0: mean = 299.58, median = 300.00, std = 0.54, min = 298.00, max = 301.00
Chip 1: mean = 319.96, median = 320.00, std = 0.34, min = 319.00, max = 321.00
Chip 2: mean = 313.48, median = 313.00, std = 0.57, min = 312.00, max = 316.00
Chip 3: mean = 298.75, median = 299.00, std = 0.55, min = 297.00, max = 301.00

------------------------
Masked data statistics:
Chip 0: mean = 302.03, median = 301.00, std = 14.58, min = 292.00, max = 3055.00
Chip 1: mean = 321.72, median = 321.00, std = 15.59, min = 318.00, max = 4095.00
Chip 2: mean = 315.11, median = 314.00, std = 10.84, min = 311.00, max = 2453.00
Chip 3: mean = 301.15, median = 300.00, std = 15.07, min = 297.00, max = 4095.00

------------------------
Bias level corrected statistics:
Chip 0: mean = 2.43, median = 1.39, std = 14.58, min = -7.58, max = 2755.42
Chip 1: mean = 1.76, median = 1.04, std = 15.59, min = -1.96, max = 3775.05
Chip 2: mean = 1.63, median = 0.52, std = 10.84, min = -2.48, max = 2139.52
Chip 3: mean = 2.39, median = 1.23, std = 15.07, min = -1.77, max = 3796.23

------------------------
Bias image statistics:
Chip 0: mean = 0.19, median = 0.18, std = 0.17, min = -0.10, max = 91.15
Chip 1: mean = 0.15, median = 0.15, std = 0.19, min = -0.08, max = 64.59
Chip 2: mean = 0.19, median = 0.18, std = 0.32, min = -0.12, max = 200.41
Chip 3: mean = 0.20, median = 0.19, std = 0.40, min = -0.25, max = 164.52

------------------------
Bias image corrected statistics:
Chip 0: mean = 2.24, median = 1.19, std = 14.53, min = -7.76, max = 2755.28
Chip 1: mean = 1.61, median = 0.83, std = 15.55, min = -10.53, max = 3774.91
Chip 2: mean = 1.44, median = 0.38, std = 10.74, min = -2.71, max = 2139.33
Chip 3: mean = 2.19, median = 1.04, std = 14.94, min = -2.05, max = 3796.12

------------------------
Dark data * darktime (700.0s) statistics:
Chip 0: mean = 0.46, median = 0.37, std = 2.75, min = 0.00, max = 708.50
Chip 1: mean = 0.37, median = 0.28, std = 2.88, min = 0.00, max = 688.80
Chip 2: mean = 0.46, median = 0.35, std = 2.71, min = 0.00, max = 691.06
Chip 3: mean = 0.43, median = 0.34, std = 3.13, min = 0.00, max = 710.88

------------------------
Dark corrected statistics:
Chip 0: mean = 1.78, median = 0.79, std = 14.05, min = -14.82, max = 2754.85
Chip 1: mean = 1.24, median = 0.43, std = 15.23, min = -26.38, max = 3774.64
Chip 2: mean = 0.99, median = 0.05, std = 10.24, min = -17.73, max = 2138.95
Chip 3: mean = 1.77, median = 0.68, std = 14.33, min = -235.90, max = 3795.77

------------------------
Flatfield data statistics:
Chip 0: mean = 2.79, median = 0.96, std = 8.37, min = 0.05, max = 131.80
Chip 1: mean = 6.29, median = 1.02, std = 21.24, min = 0.01, max = 148.93
Chip 2: mean = 5.93, median = 1.02, std = 18.34, min = 0.10, max = 150.96
Chip 3: mean = 7.50, median = 1.02, std = 22.52, min = 0.01, max = 147.38

------------------------
Flatfield corrected statistics:
Chip 0: mean = 2.32, median = 0.75, std = 41.07, min = -334.01, max = 10971.29
Chip 1: mean = 2.83, median = 0.44, std = 376.98, min = -642.40, max = 264339.88
Chip 2: mean = 3.27, median = 0.06, std = 148.39, min = -1655.15, max = 40456.75
Chip 3: mean = 4.99, median = 0.69, std = 172.98, min = -571.37, max = 44191.27

Sky level per chip (DN): [ 0.722 -0.242  0.026  0.667]

------------------------
Final calibrated (sky subtracted) statistics:
Chip 0: mean = 1.59, median = 0.03, std = 41.07, min = -334.73, max = 10970.56
Chip 1: mean = 3.08, median = 0.69, std = 376.98, min = -642.15, max = 264340.12
Chip 2: mean = 3.24, median = 0.03, std = 148.39, min = -1655.17, max = 40456.73
Chip 3: mean = 4.32, median = 0.03, std = 172.98, min = -572.04, max = 44190.60



# Part 2: Sentinel-2 Images 

## Objectives

1. To plot the land area as a function of time from the Google Earth images 
2. TO plot the vegetation area as a function of time from the Sentinel-2 images 
3. To plot the vegetation area as a function of land area from the Sentinel-2 imaages 

1. For the Google Earth images: 

The images are plain .jpg files so there is no pixel size in the metadata. The pixel size has to be worked out from the scale bar drawn on each image. Everything after that follows the same idea as the Sentinel part: count pixels, then convert to km².
The scale bar is a bright horizontal line in the bottom part of the screenshot, so we look at he bottom 15% of the image. A pixel counts as "bright" when its red, green and blue values are all above 200 (the minimum of the three channels is taken, so coloured pixels are not picked up).
For every row in that strip, longest_run() finds the longest run of consecutive bright pixels (its length, start and end), this output is printed so we can insoect it, and we know Each scale bar represents a known real distance (DEFAULT_BAR_M = 600 m by default).

This is computed by: metres per pixel = bar length in metres / bar length in pixels
pixel area (m^2) = (metres per pixel)^2

To obtain the land area for each year, I created a land mask whcih can be visually inspected. We compute the G-B index: G-B index = (G - B) / (R + G + B) 
Water is blue-dominated and gives a low (negative) value, while land has relatively more green, so land stands out with a higher value. Dividing by the total brightness makes the index less sensitive to differences in lighting between images.
The 'land_mask' function marks a pixel as land when its G-B index is above a threshold. The bottom 12% of the image (logo and scale bar) and a 5-pixel frame around the edge are always excluded.

The threshold is set per image by eye in the RED_THRESH dictionary (the default is RED_THRESH_DEFAULT = 0.05), because the water colour and lighting differ between dates. The pixels for each mask are counted, and land area is calculated by: 
land area (km²) = number of land pixels x pixel area (m²) x 1e-6. 

2021Dec is not used because its land area was obscured by clouds to the point where it did not make sense to include this in any reasonable land estimations. For other years, the threshold values reflect reasonable estimations by looking at images directly.

Small "blobs" or clouds are removed as well which are clouds, e.g. 2019: 31861 land px  (blob filter min_size=4000, removed 7338 px), though some artefacts and inaccuracies remain due to clouds and shadowd (maybe large swarms of plankton?)

2. For the Sentinel-2: 

GeoTIFFs are latitude/longitude, so the pixel resolution that rasterio reports (src.res) is in degrees, not metres. 
To turn a pixel count into an area in km², the size of one pixel in metres is needed, there is a function to compute this in 'sentinel_utils'.
M_PER_DEG (metres per degree) = 111320, which constant is the number of metres in one degree of arc on the Earth's surface (roughly 111.32 km, the length of one degree at the equator, taking the Earth's circumference as about 40,075 km, which gives 40,075 km / 360 degrees). It is the conversion factor between the angular units of the raster and the metres we need. Without it, res would only be a number of degrees and the areas could not be given in m² or km² and then pixel_conversion(file, pixels) then simply multiplies a pixel count by this area.
This is multiplied by cos(latitude), the lines of latitude are all spaced about the same distance apart, so one degree of latitude is about 111.32 km everywhere. A pixel that is 1 degree wide is therefore narrower in metres at higher latitude. 
Without the cos(latitude) factor, the pixel area and every vegetation and land area, would be overestimated.

To compute NDVI: 'compute_ndvi()' calculates NDVI for each year using band 8 (near-infrared) and band 4 (red):

NDVI = (B8 - B4) / (B8 + B4)

This is done by make_ndi(), a general normalised difference function. Then, the pixels in the vegetation area are counted up and converted to physical area. The count is converted to km² with pixel_conversion(), which multiplies the pixel count by the pixel area from step 2 and then by 1e-6 (m² to km²). plot_vegetation_area() plots vegetation area against year
A mask is also used to obtain the vegetation area from the NDVI.tiff file, The two masks are compared pixel by pixel. The difference image is +1 where only my mask marks vegetation and -1 where only the pipeline does. IN 'NDVI_MaskComparison.png', there is a high IOU (intersection over union) between my mask and the pipeline masks, the histograms also show above 99% agreement in pixel-to-pixel compairson. 
Over all it also showed that the vegetation area grew with time. 

To calculate as a function of land area over time, the B12 band was used to estimate the land area from sentinel images as it was shortwave infrared (around 2190 nm) and works well for land area because water absorbs almost all light at that wavelength, while land does not.
Water is nearly black in SWIR, for this and for the vegetation indices, the threshold for masks was tuned by trial and error. Calculating the land area this way showed that the land area decreased wiht time, this could also be a slightly inaccurate result due to aggressive thresholding, but there is not a very significant difference between 2017 and 2018. 
The results showed that the vegetation as a fraction of land area increased with time. 

2017: vegetation = 0.566 km², land = 3.243 km², fraction = 0.174 (17.4%)
2018: vegetation = 0.634 km², land = 2.881 km², fraction = 0.220 (22.0%)
2019: vegetation = 0.710 km², land = 2.796 km², fraction = 0.254 (25.4%)


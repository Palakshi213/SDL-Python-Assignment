# !/usr/bin/env python 3
# sentinel_utils.py

# Contains all helper functions for the Sentinel-2 part of the assignment

"""
1. find_files_by_year(data_dir)
2. get_band_file(files, band, index_fallback=None)
3. read_band(file)
4. print_raster_metadata(file)
5. pretty_stats(image_data)
6. make_ndi(band1, band2, band3=None)
7. angular_pixel_calculation(file)
8. pixel_conversion(file, pixels)
9. compute_ndvi(files_by_year)
10. plot_ndvi(ndvi)
11. count_vegetation(ndvi, files_by_year, thresh)
12. plot_vegetation_area(veg_area)
13. read_pipeline_rgb(files)
14. plot_pipeline_comparison(ndvi, files_by_year)
15. compare_ndvi_masks(files_by_year, ndvi_thresh, margin)
16. load_b12(files)
17. normalise_b12(b12)
18. remove_small_objects(mask, min_size, connectivity, fill_holes)
19. build_land_masks(files_by_year, z_thresh, min_size_by_year)
20. plot_land_masks(b12_raw, land_masks, n_land)
21. land_area_over_time(n_land, files_by_year)
22. vegetation_fraction(veg_counts, land_counts, files_by_year)
"""

# Packages import
import numpy as np
import matplotlib.pyplot as plt
import rasterio
from pathlib import Path
from scipy import ndimage as ndi

# Constants
Z_THRESH = 5.0                      # normalised B12 threshold for land
MIN_SIZE_BY_YEAR = {"2019": 4000}   # blob size filter (cloud removal) per year
VEG_NDVI_THRESH = 0.3               # NDVI >= this counts as vegetation
PIPELINE_MARGIN = 0.15              # green must exceed red and blue by this
M_PER_DEG = 111320                  # metres per degree of latitude



def find_files_by_year(data_dir="sentinel-data"):
    """
    Return {year: sorted list of .tiff files} for every S2_<year>-* folder.
    """
    data_dir = Path(data_dir)
    files_by_year = {}
    for folder in sorted(data_dir.glob("S2_*")):
        year = folder.name.split("_")[1][:4]
        files_by_year[year] = sorted(folder.rglob("*.tiff"))
    return files_by_year


def get_band_file(files, band, index_fallback=None):
    """
    Pick the raw file of one band (e.g. "B12") by name. If the name does
    not match exactly one file, fall back to the position in the sorted list.
    """
    tokens = [f"{band}_Raw"]
    if len(band) == 2:                       # B8 -> also try B08
        tokens.append(f"B0{band[1]}_Raw")
    matches = [f for f in files if any(t in f.name for t in tokens)]
    if len(matches) == 1:
        return matches[0]
    if index_fallback is None:
        index_fallback = BAND_INDEX[band]
    return files[index_fallback]


def read_band(file):
    """Read the first band of a raster as a float array."""
    with rasterio.open(file) as src:
        return src.read(1).astype(float)

def pretty_stats(image_data):
    """Print out stats with nice formatting."""
    stats = {
        "Mean": np.mean(image_data),
        "Median": np.median(image_data),
        "Std Dev": np.std(image_data),
        "Min": np.min(image_data),
        "Max": np.max(image_data),
    }
    print("\nImage Statistics")
    print("-" * 25)
    for label, value in stats.items():
        print(f"{label:<7} : {value:>15,.4f}")
    print("-" * 25)

def make_ndi(band1, band2, band3=None):
    """
    Take two bands and make a normalized difference image,
    (b1 - b2) / (b1 + b2). Pixels <= 0 are set to NaN.
    If band3 is given, (b3 - b2) / (b3 + b2) is added.
    The input arrays are not modified.
    """
    band1 = band1.astype(float).copy()
    band2 = band2.astype(float).copy()
    band1[band1 <= 0] = np.nan
    band2[band2 <= 0] = np.nan
    result = (band1 - band2) / (band1 + band2)

    if band3 is not None:
        band3 = band3.astype(float).copy()
        band3[band3 <= 0] = np.nan
        result += (band3 - band2) / (band3 + band2)
    return result


def angular_pixel_calculation(file):
    """
    Pixel area in m² for a raster whose resolution is in degrees.
    The width shrinks with cos(latitude) at the image centre.
    """
    with rasterio.open(file) as src:
        resolution = src.res
        bounds = src.bounds
        latitude = (bounds.bottom + bounds.top) / 2

        pixel_width_m = abs(resolution[0]) * M_PER_DEG * np.cos(np.radians(latitude))
        pixel_height_m = abs(resolution[1]) * M_PER_DEG
        return pixel_width_m * pixel_height_m


def pixel_conversion(file, pixels):
    """Convert a pixel count to an area in m²."""
    return pixels * angular_pixel_calculation(file)


# ----------------------------------------------------------------------
# NDVI and vegetation
# ----------------------------------------------------------------------

def compute_ndvi(files_by_year):
    """NDVI = (B8 - B4) / (B8 + B4) for each year. Returns {year: array}."""
    ndvi = {}
    for year, files in files_by_year.items():
        b8 = read_band(get_band_file(files, "B8"))
        b4 = read_band(get_band_file(files, "B4"))
        ndvi[year] = make_ndi(b8, b4)
    return ndvi


def plot_ndvi(ndvi):
    """Plot the NDVI image of every year side by side."""
    fig, axes = plt.subplots(1, len(ndvi), figsize=(6 * len(ndvi), 5), tight_layout=True)
    axes = np.atleast_1d(axes)
    for ax, (year, veggie) in zip(axes, ndvi.items()):
        im = ax.imshow(veggie, vmin=-1, vmax=1, cmap="inferno")
        ax.set_title(f"NDVI {year}")
        fig.colorbar(im, ax=ax, fraction=0.046)
    return fig


def count_vegetation(ndvi, files_by_year, thresh=VEG_NDVI_THRESH):
    """
    Count the pixels with NDVI in [thresh, 1] and convert to km².
    Returns (veg_counts, veg_area_km2), both {year: value}.
    """
    veg_counts, veg_area = {}, {}
    for year, values in ndvi.items():
        count = int(np.sum((values >= thresh) & (values <= 1)))
        file = get_band_file(files_by_year[year], "B8")
        veg_counts[year] = count
        veg_area[year] = pixel_conversion(file, count) * 1e-6
        print(f"{year}: {count} pixels, {veg_area[year]:.2f} km²")
    return veg_counts, veg_area


def plot_vegetation_area(veg_area):
    """Plot the vegetation area (km²) against year."""
    years = sorted(veg_area)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot([int(y) for y in years], [veg_area[y] for y in years], marker="o")
    ax.set_xticks([int(y) for y in years])
    ax.set_xlabel("Year")
    ax.set_ylabel("Vegetation area (km$^2$)")
    ax.set_title("NDVI Vegetation Over Time")
    ax.grid(True)
    return fig


# ----------------------------------------------------------------------
# Comparison with the supplied NDVI (pipeline) files
# ----------------------------------------------------------------------

def read_pipeline_rgb(files):
    """Read the supplied *_NDVI.tiff as an (h, w, 3) float RGB image."""
    f = [x for x in files if x.name.endswith("_NDVI.tiff")][0]
    with rasterio.open(f) as src:
        return np.moveaxis(src.read(), 0, -1).astype(float)


def compare_ndvi_masks(files_by_year, ndvi_thresh=0.12, margin=PIPELINE_MARGIN):
    """
    Compare my NDVI vegetation mask (NDVI >= ndvi_thresh) with the pipeline
    mask (green exceeds red and blue by `margin`) for each year.
    Returns (fig, rows, diffs): rows is a list of dicts (one per year) and
    diffs is {year: difference image} (+1 only mine, -1 only pipeline, 0 agree).
    """
    years = sorted(files_by_year)
    rows = []
    diffs = {}
    fig, axes = plt.subplots(len(years), 3, figsize=(17, 4.3 * len(years)), tight_layout=True)
    axes = np.atleast_2d(axes)

    for i, year in enumerate(years):
        files = files_by_year[year]
        b8 = read_band(get_band_file(files, "B8"))
        b4 = read_band(get_band_file(files, "B4"))
        my_ndvi = make_ndi(b8, b4)

        rgb = read_pipeline_rgb(files)
        r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]

        pipe = ((g - r) > margin) & ((g - b) > margin)
        mine = my_ndvi >= ndvi_thresh
        diff = mine.astype(int) - pipe.astype(int)  # +1 only mine, -1 only pipeline
        diffs[year] = diff

        both = int((mine & pipe).sum())
        only_mine = int((mine & ~pipe).sum())
        only_pipe = int((pipe & ~mine).sum())
        iou = both / max(both + only_mine + only_pipe, 1)
        rows.append({
            "year": year, "mine_px": int(mine.sum()), "pipeline_px": int(pipe.sum()),
            "both": both, "only_mine": only_mine, "only_pipeline": only_pipe,
            "IoU": iou, "agree_%": 100 * (diff == 0).mean(),
        })

        im0 = axes[i, 0].imshow(mine, cmap="gray", vmin=0, vmax=1)
        axes[i, 0].set_title(f"Mine (NDVI >= {ndvi_thresh}) {year}")
        fig.colorbar(im0, ax=axes[i, 0], fraction=0.046)

        im1 = axes[i, 1].imshow(pipe, cmap="gray", vmin=0, vmax=1)
        axes[i, 1].set_title(f"Pipeline {year}")
        fig.colorbar(im1, ax=axes[i, 1], fraction=0.046)

        im2 = axes[i, 2].imshow(diff, cmap="RdBu_r", vmin=-1, vmax=1)
        axes[i, 2].set_title(f"Difference (mine - pipeline) {year}: IoU = {iou:.3f}")
        fig.colorbar(im2, ax=axes[i, 2], fraction=0.046)

        for a in axes[i]:
            a.axis("off")

    print(f"{'Year':6s} {'mine_px':>9s} {'pipe_px':>9s} {'both':>9s} "
          f"{'only_mine':>10s} {'only_pipe':>10s} {'IoU':>7s} {'agree_%':>8s}")
    for r in rows:
        print(f"{r['year']:6s} {r['mine_px']:9d} {r['pipeline_px']:9d} {r['both']:9d} "
              f"{r['only_mine']:10d} {r['only_pipeline']:10d} {r['IoU']:7.3f} {r['agree_%']:8.2f}")

    return fig, rows, diffs


# Land mask from B12 (ocean is dark in SWIR) and vegetation fraction


def load_b12(files):
    """Load B12, treating 0 / no-data as NaN."""
    b12 = read_band(get_band_file(files, "B12", index_fallback=10))
    b12[b12 <= 0] = np.nan
    return b12


def normalise_b12(b12):
    """
    Robust z-score relative to the ocean level of this image.
    Returns (z, median, sigma) where sigma = 1.4826 * MAD.
    """
    med = np.nanmedian(b12)
    sigma = 1.4826 * np.nanmedian(np.abs(b12 - med))
    return (b12 - med) / sigma, med, sigma


def remove_small_objects(mask, min_size=500, connectivity=2, fill_holes=False):
    """
    Remove connected blobs of True pixels smaller than min_size (in pixels).

    connectivity: 1 = 4-neighbour (edges only), 2 = 8-neighbour (edges and diagonals)
    fill_holes:   also fill enclosed holes in the blobs that are kept
    """
    structure = ndi.generate_binary_structure(2, connectivity)
    lab, n = ndi.label(mask, structure=structure)
    if n == 0:
        return mask.copy()

    sizes = ndi.sum(mask, lab, index=np.arange(1, n + 1))
    keep_labels = np.where(sizes >= min_size)[0] + 1
    cleaned = np.isin(lab, keep_labels)

    if fill_holes:
        cleaned = ndi.binary_fill_holes(cleaned)
    return cleaned


def build_land_masks(files_by_year, z_thresh=Z_THRESH, min_size_by_year=None):
    """
    Land = normalised B12 above z_thresh. Years listed in min_size_by_year
    also get small blobs (clouds) removed.
    Returns (b12_raw, land_masks, n_land), each {year: value}.
    """
    if min_size_by_year is None:
        min_size_by_year = MIN_SIZE_BY_YEAR

    b12_raw, land_masks, n_land = {}, {}, {}
    for year, files in files_by_year.items():
        b12_raw[year] = load_b12(files)
        z, med, sigma = normalise_b12(b12_raw[year])
        print(f"{year}: ocean median = {med:.5f}, ocean sigma = {sigma:.5f}")

        land = np.isfinite(z) & (z > z_thresh)
        n_before = int(land.sum())

        if year in min_size_by_year:
            land = remove_small_objects(land, min_size=min_size_by_year[year])

        land_masks[year] = land
        n_land[year] = int(land.sum())
        note = (f"(blob filter min_size={min_size_by_year[year]}, "
                f"removed {n_before - n_land[year]} px)"
                if year in min_size_by_year else "(no blob filter)")
        print(f"{year}: {n_land[year]} land px  {note}")
    return b12_raw, land_masks, n_land


def plot_land_masks(b12_raw, land_masks, n_land):
    """Show B12 restricted to the land pixels, one panel per year."""
    years = sorted(land_masks)
    vmax = np.nanpercentile(b12_raw[years[-1]], 99.5)
    fig, axes = plt.subplots(1, len(years), figsize=(6 * len(years), 5), tight_layout=True)
    axes = np.atleast_1d(axes)
    for ax, year in zip(axes, years):
        ax.imshow(np.ma.masked_array(b12_raw[year], mask=~land_masks[year]),
                  vmin=0, vmax=vmax, cmap="viridis")
        ax.set_title(f"{year}: {n_land[year]} px")
        ax.axis("off")
    return fig


def land_area_over_time(n_land, files_by_year):
    """
    Convert land pixel counts to km² for each year.
    Returns ({year: km2}, fig).
    """
    years = sorted(n_land)
    land_km2 = {}
    for y in years:
        file = get_band_file(files_by_year[y], "B12", index_fallback=10)
        land_km2[y] = pixel_conversion(file, n_land[y]) * 1e-6
        print(f"{y}: {n_land[y]} pixels, {land_km2[y] * 1e6:.0f} m², {land_km2[y]:.3f} km²")

    x = [int(y) for y in years]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(x, [land_km2[y] for y in years], marker="o")
    ax.set_xticks(x)
    ax.set_xlabel("Year")
    ax.set_ylabel("Land area (km$^2$)")
    ax.set_title("Land area over time")
    ax.grid(True)
    return land_km2, fig


def vegetation_fraction(veg_counts, land_counts, files_by_year):
    """
    Vegetation area / land area for each year.
    Returns (veg_km2, land_km2, frac, fig).
    """
    years = sorted(veg_counts)
    veg_km2, land_km2, frac = {}, {}, {}

    for y in years:
        file = get_band_file(files_by_year[y], "B12", index_fallback=10)
        veg_km2[y] = pixel_conversion(file, veg_counts[y]) * 1e-6
        land_km2[y] = pixel_conversion(file, land_counts[y]) * 1e-6
        frac[y] = veg_km2[y] / land_km2[y]
        print(f"{y}: vegetation = {veg_km2[y]:.3f} km², land = {land_km2[y]:.3f} km², "
              f"fraction = {frac[y]:.3f} ({100 * frac[y]:.1f}%)")

    x = [int(y) for y in years]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4), tight_layout=True)

    ax1.plot(x, [land_km2[y] for y in years], marker="o", label="Land")
    ax1.plot(x, [veg_km2[y] for y in years], marker="o", label="Vegetation")
    ax1.set_ylabel("Area (km$^2$)")
    ax1.set_title("Land and vegetation area")
    ax1.legend()

    ax2.plot(x, [frac[y] for y in years], marker="o", color="g")
    ax2.set_ylabel("Vegetation / land area")
    ax2.set_title("Vegetation as a fraction of land area")

    for ax in (ax1, ax2):
        ax.set_xticks(x)
        ax.set_xlabel("Year")
        ax.grid(True)

    return veg_km2, land_km2, frac, fig


def plot_difference_histogram(diffs, title="Pixel-by-pixel differences (mine - pipeline)"):
    """
    Histogram of the pixel-by-pixel differences, one panel per year.

    diffs: {year: difference image}. The y axis is logarithmic since most
    pixels agree (difference 0). Each bar is labelled with its pixel count.
    """
    years = sorted(diffs)
    fig, axes = plt.subplots(1, len(years), figsize=(5 * len(years), 4), tight_layout=True)
    axes = np.atleast_1d(axes)

    for ax, year in zip(axes, years):
        d = np.asarray(diffs[year])
        d = d[np.isfinite(d)]

        # Whole-number differences get one bar each, otherwise use fine bins
        if np.all(d == np.round(d)):
            values = np.arange(d.min(), d.max() + 1)
            counts = np.array([np.sum(d == v) for v in values])
            ax.bar(values, counts, width=0.8)
            ax.set_xticks(values)
            for v, c in zip(values, counts):
                ax.text(v, max(c, 1), f"{c}", ha="center", va="bottom", fontsize=8)
        else:
            ax.hist(d, bins=200)

        ax.set_yscale("log")
        ax.set_xlabel("Mine - pipeline")
        ax.set_ylabel("pixels")
        ax.set_title(f"{year}: {np.mean(d == 0) * 100:.1f}% agree")

    fig.suptitle(title)
    return fig

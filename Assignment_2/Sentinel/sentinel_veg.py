from pathlib import Path
import matplotlib.pyplot as plt

# Custom utils functions import
from sentinel_utils import (
    find_files_by_year,
    get_band_file,
    pretty_stats,
    read_band,
    compute_ndvi,
    plot_ndvi,
    count_vegetation,
    plot_vegetation_area,
    compare_ndvi_masks,
    plot_difference_histogram,
    build_land_masks,
    plot_land_masks,
    land_area_over_time,
    vegetation_fraction,
    angular_pixel_calculation,
)
import numpy as np


def save(fig, out_dir, name):
    fig.savefig(out_dir / f"{name}.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def main():
    data_dir = Path("sentinel-data")
    out_dir = Path("sentinel_plots")
    out_dir.mkdir(exist_ok=True)

    # -------------------------------------
    # Load the files
    files_by_year = find_files_by_year(data_dir)
    for year, files in files_by_year.items():
        print(year)
        for f in files:
            print("   ", f.name)


    # Pixel size of each year
    for year, files in files_by_year.items():
        area = angular_pixel_calculation(get_band_file(files, "B12", index_fallback=10))
        print(f"{year}: pixel area = {area:.2f} m², side = {np.sqrt(area):.2f} m")

    # -------------------------------------
    # NDVI and vegetation area
    ndvi = compute_ndvi(files_by_year)
    save(plot_ndvi(ndvi), out_dir, "NDVI")

    veg_counts, veg_area = count_vegetation(ndvi, files_by_year)
    save(plot_vegetation_area(veg_area), out_dir, "VegetationArea")

    # -------------------------------------

    fig, rows, diffs = compare_ndvi_masks(files_by_year)
    save(fig, out_dir, "NDVI_MaskComparison")

    # Histogram of the pixel-by-pixel differences
    save(plot_difference_histogram(diffs), out_dir, "NDVI_DifferenceHistogram")

    # -------------------------------------
    # Land mask from B12 and land area
    b12_raw, land_masks, n_land = build_land_masks(files_by_year)
    save(plot_land_masks(b12_raw, land_masks, n_land), out_dir, "LandMasks")

    land_km2, fig = land_area_over_time(n_land, files_by_year)
    save(fig, out_dir, "LandArea")

    # -------------------------------------
    # Vegetation as a fraction of land
    veg_km2, land_km2, frac, fig = vegetation_fraction(veg_counts, n_land, files_by_year)
    save(fig, out_dir, "VegetationFraction")


if __name__ == "__main__":
    main()
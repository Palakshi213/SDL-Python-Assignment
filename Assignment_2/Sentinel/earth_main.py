# earth_main.py
# Part 2 of the assignment: Hunga Tonga analysis from Google Earth images.
# All functions are found in earth_utils.py.

from pathlib import Path

import matplotlib.pyplot as plt

from earth_utils import (
    EXCLUDE,
    RED_THRESH,
    RED_THRESH_DEFAULT,
    load_white_light_files,
    select_images,
    measure_scale_bar,
    show_detection,
    scale_bar_table,
    analysis_region,
    # plot_colour_histograms,
    # plot_colour_indices,
    measure_land_areas,
    plot_land_masks,
    plot_land_area,
)


def main():
    data_dir = Path("sentinel-data")
    wl_dir = data_dir / "White_light"

    out_dir = Path("earth_plots")
    out_dir.mkdir(exist_ok=True)

    # Content of the data folders
    # ------------------------------------------------------------------
    # for folder in sorted(data_dir.glob("S2_*")):
    #     print(folder.name)
    #     for f in sorted(folder.iterdir()):
    #         print("   ", f.name)

    # Load the white light images
    wl = load_white_light_files(wl_dir)

    print(f"\n{'File':30s} {'Data shape':18s} Data type")
    for name, img in wl.items():
        print(f"{name:30s} {str(img.shape):18s} {img.dtype}")


    # Scale bar detection (every image, to check by eye)

    for name, img in wl.items():
        result = measure_scale_bar(img)
        fig = show_detection(name, img, result)
        fig.savefig(out_dir / f"{name}_ScaleBar.png", dpi=150, bbox_inches="tight")
        plt.close(fig)

    # Images used in the rest of the analysis (2021Dec is left out)
    white_images = select_images(wl_dir, exclude=EXCLUDE)
    print("\nImages analysed:", [p.stem for p in white_images])

    # Pixel size from the scale bar: summary table
    print()
    bar_results, pixel_area_m2 = scale_bar_table(white_images)


    # Land area from the G-B index

    print()
    areas, masks, gb_maps = measure_land_areas(
        white_images, pixel_area_m2 = pixel_area_m2, thresholds=RED_THRESH, default_thresh=RED_THRESH_DEFAULT
    )

    fig = plot_land_masks(white_images, gb_maps, masks, areas)
    fig.savefig(out_dir / "LandMasks.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    fig = plot_land_area(white_images, areas)
    fig.savefig(out_dir / "LandArea.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()

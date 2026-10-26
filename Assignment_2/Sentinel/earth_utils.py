#earth_utils.py
# Helper functions for Part 2 of the assignment (Hunga Tonga, Sentinel-2 images)
# Author: Palakshi RATTAN (and using functions used in the Lab Workbooks) #
"""
Functions
--------
Loading
    1. load_white_light_files(folder)
    3. select_images(folder, exclude)

Scale bar / pixel size
    4. longest_run(row)
    5. measure_scale_bar(img, bottom_frac, thresh, min_len)
    6. find_scale_bar(img, bottom_frac, thresh, min_len)
    7. show_detection(name, img, result)
    8. pixel_size(path, img)
    9. scale_bar_table(images)

Colour indices
    10. norm_diff(a, b)
    11. colour_diffs(img)

Land area
    12. green_blue_index(path)
    13. land_mask(path, thresh)
    14. measure_land_areas(paths, thresholds)
    15. plot_land_masks(paths, gb_maps, masks, areas, thresholds)
    16. plot_land_area(paths, areas)
"""

# Packages import
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

IMAGE_EXTS = {".png", ".jpg", ".jpeg"}

# Scale bar label for each image, in metres. Check each image by eye!
# Any file not listed here falls back to DEFAULT_BAR_M.

SCALE_BAR_M = {
    # "your_filename_stem": 600,
}
DEFAULT_BAR_M = 600

# # Area of one pixel in m^2, used for the land area (from the scale bar)
# PIXEL_AREA_M2 = 3.79

# G-B threshold above which a pixel counts as "land" (red in the G-B map)
# These are tuned by eye , more detailed workings for this are clear in the Google_Earth_rough.ipynb file
RED_THRESH_DEFAULT = 0.05
RED_THRESH = {
    "2014Feb": 0.03,
    "2016May": 0.01,
    "2020Nov": 0.01,
    "2022Jan": 0.08,
    "2023Oct": 0.01,
}

# Images that are not used in the analysis
EXCLUDE = {"2021Dec"}

def load_white_light_files(folder):
    """Return {file_stem: uint8 RGB array (rows, cols, 3)} for every image in folder."""
    folder = Path(folder)
    out = {}
    for path in sorted(folder.iterdir()):
        if path.suffix.lower() in IMAGE_EXTS:
            img = mpimg.imread(path)[..., :3]
            if img.dtype != np.uint8:
                img = (img * 255).astype(np.uint8)
            out[path.stem] = img
    return out
#

def load_rgb(path):
    """Load an image as a float RGB array scaled to 0..1."""
    img = mpimg.imread(path).astype(float)
    if img.max() > 1.5:
        img /= 255.0
    return img[..., :3]


def select_images(folder, exclude=EXCLUDE):
    """Sorted list of the .jpg paths in folder, leaving out the stems in exclude."""
    folder = Path(folder)
    return sorted(
        p for p in folder.iterdir()
        if p.suffix.lower() in {".jpg", ".jpeg"} and p.stem not in exclude
    )


# ----------------------------------------------------------------------
# Scale bar / pixel size


def longest_run(row):
    """Longest run of True in a 1D boolean array to find the length, start, end """

    padded = np.concatenate([[0], row.astype(np.int8), [0]])
    edges = np.diff(padded)
    starts, ends = np.where(edges == 1)[0], np.where(edges == -1)[0]
    if len(starts) == 0:
        return 0, None, None
    i = np.argmax(ends - starts)
    return ends[i] - starts[i], starts[i], ends[i]


def measure_scale_bar(img, bottom_frac=0.15, thresh=200, min_len=20):
    """
    Search the bottom strip of the image for the longest horizontal run of
    bright pixels (the scale bar). Returns (length_px, row, x_start, x_end).
    """
    h = img.shape[0]
    y0 = int((1 - bottom_frac) * h)
    bright = img[y0:].min(axis=-1) > thresh        # all of R, G, B bright

    best = (0, None, None, None) # For some images, there are multiple runs. THis part is largely unused since discarding 2021DEC as there were many bright white lines
    for r, row in enumerate(bright):
        length, xs, xe = longest_run(row)
        if length > best[0]:
            best = (length, y0 + r, xs, xe)
    if best[0] < min_len:
        raise ValueError("No scale bar found")
    return best


def find_scale_bar(img, bottom_frac=0.15, thresh=200, min_len=20):
    """
    Return the distinct bright horizontal runs in the bottom strip, longest first (the bar is the first).
    y0 is the first row of the strip.
    """
    h = img.shape[0]
    y0 = int((1 - bottom_frac) * h)
    bright = img[y0:, :, :3].min(axis=-1) > thresh

    cands = set()
    for row in bright:
        length, xs, xe = longest_run(row)
        if length >= min_len:
            cands.add((int(length), int(xs), int(xe)))
    return sorted(cands, reverse=True), y0


def show_detection(name, img, result, bottom_frac=0.15):
    """Plot the bottom strip of img with the detected scale bar in red. This just retirns cropped iamges"""
    length, row, xs, xe = result
    h = img.shape[0]
    y0 = int((1 - bottom_frac) * h)
    fig, ax = plt.subplots(figsize=(12, 3))
    ax.imshow(img[y0:], extent=[0, img.shape[1], h, y0])
    ax.hlines(row, xs, xe, colors="red", lw=1)
    ax.set_title(f"{name}: {length} px")

    return fig


def pixel_size(path, img, scale_bar_m=SCALE_BAR_M, default_bar_m=DEFAULT_BAR_M):
    """
    Metres per pixel of one image, from its scale bar.
    img is the float 0..1 RGB image from load_rgb().
    Returns (m_per_px, y0, bar_length_px).
    """
    cands, y0 = find_scale_bar((img * 255).astype(np.uint8))
    if not cands:
        raise RuntimeError(f"No scale bar found in {Path(path).name}")
    L, xa, xb = cands[0]
    bar_m = scale_bar_m.get(Path(path).stem, default_bar_m)
    return bar_m / L, y0, L


def scale_bar_table(paths, scale_bar_m=SCALE_BAR_M, default_bar_m=DEFAULT_BAR_M):
    """
    Measure the scale bar of every image and print a summary table.
    Returns {stem: dict of the measured values}.
    """
    results = {}
    for path in paths:
        name = Path(path).stem
        img = load_rgb(path)
        cands, y0 = find_scale_bar((img * 255).astype(np.uint8))
        if not cands:
            print(f"{name}: no scale bar found, measure manually")
            continue

        L, xa, xb = cands[0]                       # longest candidate = the bar
        bar_m = scale_bar_m.get(name, default_bar_m)
        m_per_px = bar_m / L
        results[name] = {
            "y0": y0, "xa": xa, "xb": xb,
            "bar_px": L, "bar_m": bar_m,
            "m_per_px": m_per_px,
            "pixel_area_m2": m_per_px ** 2,
            # "rel_area_err": 2 * dL / L,
        }

    print(f"{'File':30s} {'bar (px)':>9s} {'bar (m)':>8s} {'m/px':>8s} {'m^2/px':>8s} {'area err':>9s}")
    for name, r in results.items():
        print(f"{name:30s} {r['bar_px']:9.1f} {r['bar_m']:8d} {r['m_per_px']:8.3f} "
              f"{r['pixel_area_m2']:8.2f} ")

    pixel_area_m2 = next(iter(results.values()))["pixel_area_m2"]  # first image
    print(f"\nPixel area used: {pixel_area_m2:.2f} m^2")

    return results, pixel_area_m2



def norm_diff(a, b):
    """Normalised difference (a - b) / (a + b), range -1..1."""
    return (a - b) / (a + b + 1e-10)


def colour_diffs(img):
    """Normalised colour differences of a 0..1 RGB image."""
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    return {
        "red-blue": norm_diff(r, b),
        "red-green": norm_diff(r, g),
        "green-blue": norm_diff(g, b),
    }


def analysis_region(img, y0, border=5):
    """True where pixels should be analysed (excludes scale bar strip and frame)."""
    roi = np.ones(img.shape[:2], bool)
    roi[y0:, :] = False
    roi[:border, :] = False
    roi[:, :border] = False
    roi[:, -border:] = False
    return roi


# def plot_colour_histograms(img, roi, title=None):
#     """Histograms (log y) of the three colour differences inside the roi."""
#     diffs = colour_diffs(img)
#     bins = np.linspace(-1, 1, 1000)
#
#     fig, ax = plt.subplots(ncols=3, figsize=(15, 4), tight_layout=True)
#     for a, (label, d) in zip(ax, diffs.items()):
#         h, edges = np.histogram(d[roi], bins=bins)
#         a.plot(edges[:-1], h)
#         a.set_yscale("log")
#         a.set_title(label)
#     if title:
#         fig.suptitle(title)
#     return fig


def _rgb255(path):
    """Float RGB array on a 0..255 scale (so differences do not wrap)."""
    rgb = mpimg.imread(path)[:, :, :3].astype(float)
    if rgb.max() <= 1.0:
        rgb = rgb * 255
    return rgb



# ----------------------------------------------------------------------
# Land area
# ----------------------------------------------------------------------

def green_blue_index(path):
    """(G - B) / (R + G + B) of one image; NaN on pure black pixels."""
    rgb = _rgb255(path)
    total = rgb.sum(axis=-1)
    total[total == 0] = np.nan
    return (rgb[..., 1] - rgb[..., 2]) / total


def land_mask(gb, thresh, bottom_frac=0.12, border=5):
    """
    Boolean mask of the pixels with G-B above thresh, leaving out the
    logo / scale bar strip (bottom `bottom_frac` of the image) and the frame.
    """
    mask = (gb > thresh) & ~np.isnan(gb)
    mask[int((1 - bottom_frac) * gb.shape[0]):, :] = False
    mask[:border, :] = False
    mask[:, :border] = False
    mask[:, -border:] = False
    return mask


def measure_land_areas(paths, pixel_area_m2, thresholds=RED_THRESH, default_thresh=RED_THRESH_DEFAULT,
                     ):
    """
    Count the land pixels of every image and convert them to km^2.
    Returns (areas, masks, gb_maps), each a dict keyed by file stem.
    """
    areas, masks, gb_maps = {}, {}, {}
    for path in paths:
        thresh = thresholds.get(path.stem, default_thresh)
        gb = green_blue_index(path)
        mask = land_mask(gb, thresh)

        gb_maps[path.stem] = gb
        masks[path.stem] = mask
        areas[path.stem] = int(mask.sum()) * pixel_area_m2 * 1e-6

        print(f"{path.name:20s} thresh = {thresh:.3f}   land area: {areas[path.stem]:.3f} km²")
    return areas, masks, gb_maps


def plot_land_masks(paths, gb_maps, masks, areas, thresholds=RED_THRESH,
                    default_thresh=RED_THRESH_DEFAULT):
    """One row per image: G-B map | G-B map with the counted pixels highlighted."""
    n = len(paths)
    fig, axes = plt.subplots(n, 2, figsize=(14, 6 * n), tight_layout=True, squeeze=False)

    for (ax_gb, ax_hl), path in zip(axes, paths):
        stem = path.stem
        gb, mask = gb_maps[stem], masks[stem]
        thresh = thresholds.get(stem, default_thresh)

        im = ax_gb.imshow(gb, cmap="RdBu_r", vmin=-0.2, vmax=0.2)
        ax_gb.set_title(f"{stem}: G-B")
        fig.colorbar(im, ax=ax_gb, fraction=0.046)

        ax_hl.imshow(gb, cmap="RdBu_r", vmin=-0.2, vmax=0.2)
        ax_hl.imshow(np.ma.masked_where(~mask, mask), cmap="Wistia", alpha=0.8)
        ax_hl.set_title(f"counted (G-B > {thresh:.2f}): {mask.sum()} px, {areas[stem]:.2f} km²")

        ax_gb.axis("off")
        ax_hl.axis("off")
    return fig


def plot_land_area(paths, areas):
    """Land area of every image, in the order of paths."""
    values = [areas[p.stem] for p in paths]
    labels = [p.stem for p in paths]

    fig = plt.figure(figsize=(10, 5))
    plt.plot(values, "o-")
    plt.xticks(range(len(labels)), labels, rotation=45, ha="right")
    plt.xlabel("Year")
    plt.ylabel("Land area (km$^2$)")
    plt.title("Land Area by Image")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    return fig

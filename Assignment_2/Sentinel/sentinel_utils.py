from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

'''
Author: Palakshi Rattan
Date: 


FizzBuzz.py includes:
    1. Default Setting:
    2. Custom Setting:
    3. Function to create a custom set of rules
    4. User input for the max number

'''

def load_white_light_files(folder):
    """Returns {file_stem: image_array}, mirroring the earlier loaders."""
    folder = Path(folder)
    out = {}
    exts = {".jpg", ".jpeg"}
    for path in sorted(folder.iterdir()):
        if path.suffix.lower() in exts:
            with Image.open(path) as im:
                out[path.stem] = np.array(im.convert("RGB"))
    return


def longest_run(row):
    """Longest run of True in a 1D boolean array -> (length, start, end)."""
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
    bright pixels (the scale bar). Returns (length_px, row, x_start, x_end)..
    """
    h = img.shape[0]
    y0 = int((1 - bottom_frac) * h)
    bright = img[y0:].min(axis=-1) > thresh        # all of R, G, B bright

    best = (0, None, None, None)
    for r, row in enumerate(bright):
        length, xs, xe = longest_run(row)
        if length > best[0]:
            best = (length, y0 + r, xs, xe)
    if best[0] < min_len:
        raise ValueError("No scale bar found")
    return best


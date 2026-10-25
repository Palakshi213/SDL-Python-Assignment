
from matplotlib.colors import Normalize
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from pathlib import Path
from matplotlib.colors import Normalize

# Custom utils functions import
from Assignment_2.HST.hst_utils import (
    open_fits_file,
    load_calibration_files,
    normalize_image,
    transform_by,  # AUTHOR: Dr Andrew Kirwan
    plot_calibration_files,
    print_statistics,
    mask_invalid_data,
    mask_statistics,
    remove_bias_level,
    remove_bias_image,
    plot_correction,
    remove_dark,
    correct_flatfield,
    )

#import Assignment_2.HST.hst_utils as utils
#print([name for name in dir(utils) if not name.startswith("_")])

def main():

    calib_dir = Path("hst-calibration")
    ubai2505m = load_calibration_files(calib_dir / "ubai2505m")
    ubai2507m = load_calibration_files(calib_dir / "ubai2507m")
    ubai2508m = load_calibration_files(calib_dir / "ubai2508m")

    exposure = ubai2507m
    exposure_name = "ubai2027m"

    out_dir = Path("calibration_plots")
    out_dir.mkdir(exist_ok=True)

    print("File type | Data shape |  Data type")
    for file_type, (header, data) in exposure.items():
        print(f"{file_type:10s} {str(data.shape):16s} {data.dtype}")

    fig = plot_calibration_files(exposure, chip=0)
    fig.suptitle(f"Calibration: {exposure_name}")
    fig.savefig(out_dir / f"{exposure_name}_Calibration.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    raw_header, raw_data = exposure["raw"]
    mask_header, mask_data = exposure["maskfile"]
    blev_header, blev_data = exposure["blevfile"]
    bias_header, bias_data = exposure["biasfile"]
    dark_header, dark_data = exposure["darkfile"]   # Get the darkfile & exposure time
    dark_time = raw_header["DARKTIME"]
    flat_header, flat_data = exposure["flatfile"]     # Get the flatfile

    raw_data_masked = mask_invalid_data(raw_data, mask_data)
    print("\n------------------------ ")
    stats = mask_statistics(exposure)

    raw_data_blev_corrected = remove_bias_level(raw_data_masked, blev_data)

    # The subtracted bias level is the difference between the two images
    bias_level = raw_data_masked - raw_data_blev_corrected

    raw_data_bias_corrected = remove_bias_image(raw_data_blev_corrected, bias_data)
    raw_data_dark_corrected = remove_dark(raw_data_bias_corrected, dark_data, dark_time)
    raw_data_flat_corrected = correct_flatfield(raw_data_dark_corrected, flat_data)

    # -------------------------------------

    # Plot the maskfile on top of the rawfile, clearly highlighting the masked pixels.
    # A second plot zooms on the area where there are some bad columns.
    chip = 0
    raw_image = transform_by("sqrt", raw_data[chip], pmin=1, pmax=99)

    defective_y, defective_x = np.where(mask_data[chip] == 2)
    questionable_y, questionable_x = np.where(mask_data[chip] == 256)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))
    for ax in [ax1, ax2]:
        ax.imshow(raw_image, origin="lower", cmap="gray")
        ax.scatter(defective_x, defective_y, s=1, color="red", label="defective")
        ax.scatter(
            questionable_x,
            questionable_y,
            s=1,
            color="cyan",
            label="questionable",
        )

    ax1.set_title(f"Raw image with masked pixels (chip {chip})")
    ax1.legend(loc="lower left", markerscale=10, fontsize=16)

    ax2.set_xlim(350, 500)
    ax2.set_ylim(500, 650)
    ax2.set_title("Zoom on the bad columns")
    ax2.legend(loc="lower left", markerscale=10, fontsize=16)

    fig.tight_layout()
    fig.suptitle(f"Raw Image with Masked Pixels: {exposure_name}")
    fig.savefig(out_dir / f"{exposure_name}_MaskedImage.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    # -------------------------------------

    print("------------------------ ")
    print("Raw Data Masked:")
    for chip in range(raw_data_masked.shape[0]):
        print(f"Chip {chip}: {np.sum(np.isnan(raw_data_masked[chip]))} pixels set to NaN")

    # Only the overscan columns are pixel data (column 0 and 1 are not)
    print("\n------------------------ ")
    print_statistics(blev_data[:, :, 7:12:2], name="Blev overscan even columns")
    print("------------------------ ")
    print_statistics(blev_data[:, :, 8:13:2], name="Blev overscan odd columns")

    # Statistics before and after the bias correction
    print("------------------------ ")
    print_statistics(raw_data_masked, name="Masked data")
    raw_data_blev_corrected = remove_bias_level(raw_data_masked, blev_data)
    print("------------------------ ")
    print_statistics(raw_data_blev_corrected, name="Bias corrected")

    # Logging
    print("------------------------ ")
    print_statistics(raw_data_bias_corrected, name="Bias corrected")
    print("------------------------ ")
    print_statistics(dark_data * dark_time, name=f"Dark data * darktime({dark_time}s)")
    print("------------------------ ")
    print_statistics(raw_data_dark_corrected, name="Dark corrected")

    # Logging
    print("------------------------ ")
    print_statistics(raw_data_bias_corrected, name="Dark corrected")
    print("------------------------ ")
    print_statistics(flat_data, name="Flatfield data")
    print("------------------------ ")
    print_statistics(raw_data_dark_corrected, name="Flatfield corrected")

    # Correction Plots

    fig = plot_correction(
        raw_data_masked,
        raw_data_blev_corrected,
        bias_level,
        ["Masked data", "Bias level corrected", "Difference"],
    )
    fig.suptitle(f"Bias Level Corrected: {exposure_name}")
    fig.savefig(out_dir / f"{exposure_name}_BiasLevel_Corrected.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    fig = plot_correction(
        raw_data_bias_corrected,
        dark_data * dark_time,
        raw_data_dark_corrected,
        ["Bias corrected", f"Dark image x {dark_time:.0f} s", "Dark corrected"],
    )
    fig.suptitle(f"Dark Corrected: {exposure_name}")
    fig.savefig(out_dir / f"{exposure_name}_DarkCorrected.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    fig = plot_correction(
        raw_data_dark_corrected,
        flat_data,
        raw_data_flat_corrected,
        ["Dark corrected", "Flatfield image", "Flatfield corrected"],
    )
    fig.suptitle(f"Flatfield correction: {exposure_name}")
    fig.savefig(out_dir / f"{exposure_name}_FlatField.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

if __name__ == "__main__":
    main()
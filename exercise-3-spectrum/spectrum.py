import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

def parse_textfile(filename):
    """

    :param filename: A string which contains the file to parse
    :return: result: A dictionary which contains the headers and data from a .txt file
    """

    header = {}
    data_rows = []
    current_key = None

    with Path(filename).open("r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue

            if stripped.startswith("#"):
                current_key = stripped[1:].strip()
                if current_key != "DATA":
                    header[current_key] = []
            elif current_key == "DATA":
                data_rows.append(stripped)
            elif current_key is not None:
                header[current_key].append(stripped)

    # Join multi-line values (e.g. COMMENT) into single strings
    result = {key: " ".join(values) for key, values in header.items()}

    # First data row is the column header (WAVELENGTH,FLUX)
    if data_rows:
        columns = [c.strip() for c in data_rows[0].split(",")]
        data = {col: [] for col in columns}
        for row in data_rows[1:]:
            for col, value in zip(columns, row.split(",")):
                data[col].append(float(value))
        result["DATA"] = data # Separate the data from the header information

    return result

def get_spectrum(filename):
    """
    :param filename: A string which contains the file to parse
    :return: wavelength, flux : Lists of floats which contains wavelength and flux data, from the spectrum
    """

    spectrum = parse_textfile("spectrum.txt")
    wavelength = spectrum["DATA"]["WAVELENGTH"]
    flux = spectrum["DATA"]["FLUX"]
    return wavelength, flux

wavelength, flux = get_spectrum("spectrum.txt")


fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(wavelength, flux, c='#EB5959')
ax.set_title("Wavelength v. Flux Spectrum")
ax.set_xlabel(f"Wavelength (Å)")
ax.set_ylabel(f"Flux (ADU)")
ax.grid(True)
plt.show()

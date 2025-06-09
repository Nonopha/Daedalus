import os
import numpy as np
import pandas as pd
import rasterio
import matplotlib.pyplot as plt
from scipy import stats
from openpyxl.drawing.image import Image as XLImage


def load_raster(raster_path):
    with rasterio.open(raster_path) as src:
        band = src.read(1).astype(float)
        nodata = src.nodata
    return band, nodata


def compute_statistics(band, nodata):
    band[band == nodata] = np.nan
    data = band[~np.isnan(band)]

    if data.size == 0:
        return None

    stats_dict = {
        'Count': data.size,
        'Missing Values': np.isnan(band).sum(),
        '% Missing': (np.isnan(band).sum() / band.size) * 100,
        'Cardinality': len(np.unique(data)),
        'Min': np.min(data),
        '1st Quartile': np.percentile(data, 25),
        'Mean': np.mean(data),
        'Median': np.median(data),
        'Mode': stats.mode(data, nan_policy='omit', keepdims=True)[0][0],
        '3rd Quartile': np.percentile(data, 75),
        'Max': np.max(data),
        'Std Dev': np.std(data)
    }
    return pd.DataFrame(stats_dict.items(), columns=['Statistic', 'Value']), data


def plot_histogram(data, output_path, title):
    plt.figure(figsize=(8, 4))
    plt.hist(data, bins=50, color='skyblue', edgecolor='black')
    plt.title(f'Histogram of {title}')
    plt.xlabel('Pixel Value')
    plt.ylabel('Frequency')
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def add_dataframe_to_sheet(writer, df, sheet_name):
    df.to_excel(writer, sheet_name=sheet_name, index=False)


def add_image_to_sheet(workbook, image_path, sheet_name):
    ws = workbook.create_sheet(sheet_name)
    img = XLImage(image_path)
    img.anchor = 'A1'
    ws.add_image(img)


def process_raster_file(raster_path, writer, hist_folder):
    filename = os.path.basename(raster_path)
    sheet_base = os.path.splitext(filename)[0][:31]

    band, nodata = load_raster(raster_path)
    result = compute_statistics(band, nodata)

    if result is None:
        print(f"⚠️ Skipping {filename}: No valid data.")
        return

    stats_df, data = result
    hist_path = os.path.join(hist_folder, f"{sheet_base}_hist.png")

    add_dataframe_to_sheet(writer, stats_df, sheet_base)
    plot_histogram(data, hist_path, filename)
    add_image_to_sheet(writer.book, hist_path, sheet_base + "_Hist")


def process_all_rasters(folder_path, output_excel):
    hist_folder = os.path.join(folder_path, "histograms")
    os.makedirs(hist_folder, exist_ok=True)

    writer = pd.ExcelWriter(output_excel, engine='openpyxl')

    tif_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".tif")]
    if not tif_files:
        print("❌ No .tif files found in the folder.")
        return

    for file in tif_files:
        raster_path = os.path.join(folder_path, file)
        process_raster_file(raster_path, writer, hist_folder)

    writer.close()
    print(f"\n✅ All rasters processed. Output saved to: {output_excel}")


def main():
    folder_path = r"\\sungis15\Hons_scratch\_share\Fire_Project\Daedalus\Processed data\Intermediates\Prediction_Rasters_Clipped"
    if not os.path.isdir(folder_path):
        print("❌ Invalid folder path.")
        return

    output_excel = os.path.join(folder_path, "raster_statistics.xlsx")
    process_all_rasters(folder_path, output_excel)


if __name__ == "__main__":
    main()
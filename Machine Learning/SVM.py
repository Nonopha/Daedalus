import os
import numpy as np
import pandas as pd
import rasterio
from rasterio.warp import reproject, Resampling
from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder, StandardScaler

IMPORTANCE_DICT = {
    'TWI': 0.1114785311506568,
    'Slope': 0.09992448237583644,
    'LC_2019': 0.07584589357037792,
    'LC_2020': 0.07264457985226998,
    'LC_2016': 0.06868339128192158,
    'ndvi_2016': 0.06504572713464471,
    'LC_2017': 0.05726799921412519,
    'ndvi_2017': 0.055239717284933126,
    'LC_2018': 0.05486686409091755,
    'ndvi_2019': 0.05159100211967107,
    'ndvi_2018': 0.04670668708215117,
    'ndvi_2020': 0.04613048380127212,
    'Rain_2019': 0.03809224377354962,
    'ASPECT': 0.03643968332953618,
    'Rain_2018': 0.03333840624462764,
    'Rain_2016': 0.03080693219713554,
    'Rain_2017': 0.029734304441143316,
    'Rain_2020': 0.026163071055229935
}

STATIC_FEATURES = ['TWI', 'Slope', 'ASPECT']
YEARS = [2016, 2017, 2018, 2019, 2020]
CSV_PATH = r"\\sungis15\Hons_scratch\_share\Fire_Project\Daedalus\Processed data\Samples\ML_input.csv"
OUTPUT_DIR = r"\\sungis15\Hons_scratch\_share\Fire_Project\Daedalus\Outputs"

def compute_fire_risk_index(df, features):
    weights = {f: IMPORTANCE_DICT.get(f, 0) for f in features}
    total_weight = sum(weights.values())
    normalized = {f: w / total_weight for f, w in weights.items()}
    return sum(df[f] * normalized[f] for f in features)

def balance_classes(df, target_col):
    fire_df = df[df[target_col] == 1]
    no_fire_df = df[df[target_col] == 0]
    n_samples = min(len(fire_df), len(no_fire_df))
    balanced_df = pd.concat([
        fire_df.sample(n_samples, random_state=42),
        no_fire_df.sample(n_samples, random_state=42)
    ]).sample(frac=1, random_state=42)
    return balanced_df

def process_year(df, year):
    year_str = str(year)
    lc = f"LC_{year_str}"
    ndvi = f"ndvi_{year_str}"
    rain = f"Rain_{year_str}"
    fire_col = f"Fires_{year_str}"
    risk_index_col = f"FireRiskIndex_{year_str}"
    pred_col = f"FireOccurrence_Predicted_{year_str}"
    encoded_col = f"encoded_target_{year_str}"

    features = STATIC_FEATURES + [lc, ndvi, rain]
    cols = features + [fire_col]
    sub_df = df[cols].dropna().copy()

    sub_df[risk_index_col] = compute_fire_risk_index(sub_df, features)
    full_features = features + [risk_index_col]

    label_encoder = LabelEncoder()
    sub_df[encoded_col] = label_encoder.fit_transform(sub_df[fire_col])
    balanced_df = balance_classes(sub_df, encoded_col)

    X_train = balanced_df[full_features]
    y_train = balanced_df[encoded_col]
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    model = SVC(kernel='rbf', C=1.0, gamma='scale')
    model.fit(X_train_scaled, y_train)

    X_full_scaled = scaler.transform(sub_df[full_features])
    predictions = model.predict(X_full_scaled)
    sub_df[pred_col] = label_encoder.inverse_transform(predictions)

    output_cols = cols + [risk_index_col, pred_col]
    output_path = os.path.join(OUTPUT_DIR, f"fire_risk_{year_str}.xlsx")
    sub_df[output_cols].to_excel(output_path, index=False)
    print(f"Saved: {output_path}")

    return model, scaler, label_encoder, features, risk_index_col

def predict_on_rasters(model, scaler, features, weights, raster_paths, output_path, nodata=-9999):
    arrays = []
    with rasterio.open(raster_paths[0]) as ref:
        ref_crs = ref.crs
        ref_bounds = ref.bounds
        dst_transform = rasterio.transform.from_origin(ref_bounds.left, ref_bounds.top, 25, 25)
        dst_width = int((ref_bounds.right - ref_bounds.left) / 25)
        dst_height = int((ref_bounds.top - ref_bounds.bottom) / 25)
        dst_shape = (dst_height, dst_width)
        ref_meta = ref.meta.copy()
        ref_meta.update({
            'transform': dst_transform,
            'height': dst_height,
            'width': dst_width,
            'crs': ref_crs,
            'count': 1,
            'dtype': rasterio.int16,
            'nodata': nodata
        })

    for path in raster_paths:
        with rasterio.open(path) as src:
            data = np.full(dst_shape, nodata, dtype=np.float32)
            reproject(
                source=rasterio.band(src, 1),
                destination=data,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=dst_transform,
                dst_crs=ref_crs,
                resampling=Resampling.bilinear
            )
            arrays.append(data)

    arrays = np.stack(arrays, axis=-1)
    flat = arrays.reshape(-1, arrays.shape[-1])
    mask = np.any(flat == nodata, axis=1)
    valid = ~mask
    flat_valid = flat[valid]

    total_weight = sum(weights[f] for f in features)
    normalized_weights = np.array([weights[f] / total_weight for f in features])
    risk_index = np.dot(flat_valid, normalized_weights).reshape(-1, 1)
    X_valid = np.hstack([flat_valid, risk_index])

    X_scaled = scaler.transform(X_valid)
    preds = model.predict(X_scaled)

    result = np.full(flat.shape[0], nodata, dtype=np.int16)
    result[valid] = preds
    result = result.reshape(dst_shape)

    with rasterio.open(output_path, 'w', **ref_meta) as dst:
        dst.write(result, 1)
    print(f"Raster prediction saved to: {output_path}")

def main():
    df = pd.read_csv(CSV_PATH, sep=";")
    for year in YEARS:
        model, scaler, encoder, features, risk_col = process_year(df, year)

        raster_paths = [
            fr"\\sungis15\Hons_scratch\_share\Fire_Project\Daedalus\Intermediates\Prediction_Rasters\input_TWI.tif",
            fr"\\sungis15\Hons_scratch\_share\Fire_Project\Daedalus\Intermediates\Prediction_Rasters\input_slope.tif",
            fr"\\sungis15\Hons_scratch\_share\Fire_Project\Daedalus\Intermediates\Prediction_Rasters\input_aspect.tif",
            fr"\\sungis15\Hons_scratch\_share\Fire_Project\Daedalus\Intermediates\Prediction_Rasters\Landcover_{year}.tif",
            fr"\\sungis15\Hons_scratch\_share\Fire_Project\Daedalus\Intermediates\Prediction_Rasters\NDVI_{year}.tif",
            fr"\\sungis15\Hons_scratch\_share\Fire_Project\Daedalus\Intermediates\Prediction_Rasters\Rain_{year}.tif"
        ]
        output_raster = fr"\\sungis15\Hons_scratch\_share\Fire_Project\Daedalus\Outputs\fire_prediction_{year}.tif"
        predict_on_rasters(model, scaler, features, IMPORTANCE_DICT, raster_paths, output_raster)

if __name__ == "__main__":
    main()
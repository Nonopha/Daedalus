import arcpy
import os

def clip_rasters(input_raster_folder, clip_shapefile, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    arcpy.env.workspace = input_raster_folder
    raster_list = arcpy.ListRasters("*", "TIF")

    if not raster_list:
        print("❌ No TIFF rasters found in the input folder.")
        return

    print(f"Found {len(raster_list)} rasters. Starting clipping...")

    for raster in raster_list:
        input_raster_path = os.path.join(input_raster_folder, raster)
        out_raster_path = os.path.join(output_folder, raster)

        print(f"Clipping {raster}...")

        try:
            arcpy.Clip_management(
                in_raster=input_raster_path,
                rectangle="#",
                out_raster=out_raster_path,
                in_template_dataset=clip_shapefile,
                nodata_value="0",
                clipping_geometry="ClippingGeometry",
                maintain_clipping_extent="NO_MAINTAIN_EXTENT"
            )
            print(f"Saved clipped raster to: {out_raster_path}")
        except Exception as e:
            print(f"Error clipping {raster}: {e}")

    print("✅ All rasters processed.")

if __name__ == "__main__":
    input_folder = r"\\sungis15\Hons_scratch\_share\Fire_Project\Daedalus\Processed data\Intermediates\Prediction_Rasters"
    clip_shp = r"\\sungis15\Hons_scratch\_share\Fire_Project\Daedalus\Processed data\Intermediates\Validation_Pred\clip.shp"  # Your shapefile path here
    output_clip_folder = r"\\sungis15\Hons_scratch\_share\Fire_Project\Daedalus\Processed data\Intermediates\Prediction_Rasters_Clipped"

    clip_rasters(input_folder, clip_shp, output_clip_folder)
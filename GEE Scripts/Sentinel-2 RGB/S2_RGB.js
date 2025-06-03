// This script creates a composite RGB image from Sentinel-2 data for the year 2016
// Example code used to modify, clip & export
// Comments included are from the original code

var boundary = ee.FeatureCollection('projects/git712-gds/assets/Extent');


// Function to mask clouds using the Sentinel-2 QA band.
function maskS2clouds(image) {
  var qa = image.select('QA60')

  // Bits 10 and 11 are clouds and cirrus, respectively.
  var cloudBitMask = 1 << 10;
  var cirrusBitMask = 1 << 11;

  // Both flags should be set to zero, indicating clear conditions.
  var mask = qa.bitwiseAnd(cloudBitMask).eq(0).and(
    qa.bitwiseAnd(cirrusBitMask).eq(0))

  // Return the masked and scaled data, without the QA bands.
  return image.updateMask(mask).divide(10000)
    .select("B.*")
    .copyProperties(image, ["system:time_start"])
}

// Map the function over one year of data and take the median.
// Load Sentinel-2 TOA reflectance data.
var collection = ee.ImageCollection('COPERNICUS/S2_HARMONIZED')
  .filterDate('2016-01-01', '2016-12-31') // Change dates to cover the year 2016-2020
  // Pre-filter to get less cloudy granules.
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
  .map(maskS2clouds)

var composite = collection.median().clip(boundary)

// Display the results.
Map.centerObject(boundary, 11);
Map.addLayer(composite, { bands: ['B4', 'B3', 'B2'], min: 0, max: 0.3 }, 'Clipped RGB Composite');
Map.addLayer(boundary, { color: 'red' }, 'Boundary');

//Export to Drive
Export.image.toDrive({
  image: composite,
  description: 'Sentinel2_2016_Composite_RGB',
  folder: 'GEE_exports',
  fileNamePrefix: 'Sentinel2_2016_Jonkershoek_RGB',
  region: boundary.geometry(),
  scale: 10,
  crs: 'EPSG:4326',
  maxPixels: 1e13
});
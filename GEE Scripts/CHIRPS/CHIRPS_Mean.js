// Shapefile import
var boundary = ee.FeatureCollection("projects/git712-gds/assets/Extent");

// Load CHIRPS daily precipitation data
var dataset = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
                  .filter(ee.Filter.date('2016-01-01', '2016-01-31'));

var precipitation = dataset.select('precipitation');

// You can sum the days to get total rainfall over the period
var totalPrecip = precipitation.mean().clip(boundary);

// Visualization settings
var precipitationVis = {
  min: 1,
  max: 100,
  palette: ['001137', '0aab1e', 'e7eb05', 'ff4a2d', 'e90000'],
};

// Display the result
Map.centerObject(boundary, 10);
Map.addLayer(totalPrecip, precipitationVis, 'Mean Precipitation');
Map.addLayer(boundary, {color: 'black'}, 'Boundary');

// Export the clipped CHIRPS data as GeoTIFF
Export.image.toDrive({
  image: totalPrecip,
  description: 'CHIRPS_Precip',
  folder: 'GEE_exports',
  fileNamePrefix: 'CHIRPS_MeanRain_Jonkershoek',
  region: boundary.geometry(),
  scale: 5000, // CHIRPS native resolution ~5.5km
  crs: 'EPSG:4326',
  maxPixels: 1e13
});
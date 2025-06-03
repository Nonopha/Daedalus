
// Define the Cape Town boundary using the FeatureCollection of South African municipalities
var boundary = ee.FeatureCollection("projects/git712-gds/assets/Extent");

// Center the map
Map.centerObject(boundary, 9);
Map.addLayer(boundary, {color: 'blue'}, 'Cape Town Boundary');

// Load the Dynamic World dataset
var dynamicWorld = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1");

// Filter to a date range (e.g., entire year 2021)
var dw2021 = dynamicWorld.filterDate('2021-01-01', '2021-12-31')
                         .filterBounds(boundary);

// Get the mode land cover class (most frequent class per pixel)
var dwMode = dw2021.map(function(img) {
  return img.select('label');
}).reduce(ee.Reducer.mode());

// Define visualization parameters for the 9 land cover classes
var dwVis = {
  min: 0,
  max: 8,
  palette: [
    "#419BDF", // Water
    "#397D49", // Trees
    "#88B053", // Grass
    "#7A87C6", // Flooded vegetation
    "#E49635", // Crops
    "#DFC35A", // Shrub & scrub
    "#C4281B", // Built-up
    "#A59B8F", // Bare ground
    "#B39FE1"  // Snow & ice
  ]
};

// Add the Dynamic World mode classification to the map
Map.addLayer(dwMode.clip(boundary), dwVis, 'Dynamic World (2021 Mode)');
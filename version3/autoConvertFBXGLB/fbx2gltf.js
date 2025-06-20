const fs = require('fs');
const path = require('path');
const convert = require('fbx2gltf');

// Get the input and output paths from command line arguments
const inputPath = process.argv[2];

// Get filename and folder from input path
const filename = path.basename(inputPath, path.extname(inputPath));
const folder = path.dirname(inputPath);

console.log('Input folder and filename:', folder + ' ' + filename);

// Output path
const outputDir = path.join(folder, 'glb');
var outputPath = path.join(outputDir, `${filename}.glb`);

// Create the output directory if it does not exist
if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
}

// If output file already exists, increment the filename
let i = 1;
while (fs.existsSync(outputPath)) {
    outputPath = path.join(outputDir, `${filename}_${i++}.glb`);
}

convert(inputPath, outputPath, []).then(
    destPath => {
        console.log('Conversion successful! GLB file generated at:', destPath);
    },
    error => {
        console.error('Conversion failed:', error);
    }
);

# STL Buster

## What It Does

Splits large 3D models (STL files) into 4 parts with customizable interlocking tooth joints for easy assembly. Perfect for 3D printing objects that are too large for your printer's build volume.

## The Problem It Solves

When a 3D model is too large to print in one piece, you need to:
1. Split it into smaller pieces that fit your printer
2. Add joining mechanisms so the pieces can be assembled
3. Ensure proper alignment during assembly

STL Buster automates this process, creating interlocking tooth joints that snap together without glue.

## How It Works

1. **Upload**: Load your STL file (binary or ASCII format)
2. **Preview**: View all 4 split pieces in the browser
3. **Customize**: Adjust tooth joint parameters for perfect fit
4. **Download**: Get individual STL files for each piece, ready to print

## Features

### Splitting Logic
- Automatically divides model into 4 quadrants
- Maintains proper geometry at split lines
- Preserves model integrity and manifoldness

### Tooth Joint System
Fully customizable interlocking joints:
- **Tooth Height**: How deep the joint extends (5-100mm)
- **Tooth Size**: Width of each tooth (1-20mm)
- **Tooth Ratio**: Tooth-to-gap proportion (0.5-3.0)
- **Tooth Rounding**: Edge smoothness (0.1-5mm)
- **Tooth Gap**: Clearance for fit tolerance (0-2mm)

### Preview System
- Real-time 3D preview of each piece
- Individual canvas for each quadrant
- Visual verification before download
- Responsive layout (2x2 grid)

### Export Options
- Download individual pieces as separate STL files
- "Download All" button for batch export
- Maintains original model units and scale

## Technical Details

### Technologies
- Three.js for 3D rendering and geometry manipulation
- STLLoader for file parsing
- Client-side processing (no server required)
- Canvas-based 3D preview

### Supported Formats
- Binary STL
- ASCII STL
- All standard 3D model scales

### Tooth Joint Algorithm
Creates interlocking geometry by:
1. Calculating split planes along X and Y axes
2. Generating tooth profiles at intersection lines
3. Adding teeth to one piece, recesses to the mating piece
4. Applying rounding for printability and tolerance

## Use Cases

1. **Large 3D Prints**: Split models bigger than your print bed
2. **Multi-Color Printing**: Print sections in different colors
3. **Material Efficiency**: Print in orientations that minimize support
4. **Assembly Projects**: Create modular, snap-together designs
5. **Prototype Testing**: Print sections individually for fit testing

## Best Practices

### Tooth Joint Settings
- **Tight Fit**: Smaller gap (0-0.2mm), higher ratio (1.5-2.0)
- **Loose Fit**: Larger gap (0.3-0.5mm), lower ratio (1.0-1.4)
- **Smooth Surface**: Higher rounding (1.5-3mm)
- **Strong Joint**: Larger tooth size (5-10mm), more height (20-40mm)

### Printing Tips
- Print all pieces in the same orientation for consistent tolerances
- Use supports on tooth joints if needed
- Test fit with one joint before printing all pieces
- Consider print temperature effects on tolerances

## Future Enhancements

### Advanced Splitting
- Custom split planes (not just X/Y quadrants)
- Split into more than 4 pieces
- Non-uniform splits for specific geometries
- Split preview with joint lines visible

### Joint Types
- Dovetail joints
- Pin and socket connectors
- Screw holes for fasteners
- Magnetic alignment holes

### Smart Features
- Automatic optimal split plane detection
- Stress analysis for joint placement
- Auto-tolerance adjustment based on material
- Joint strength calculator

### User Experience
- Drag-and-drop file upload
- 3D manipulation controls (rotate, zoom, pan)
- Before/after comparison view
- Assembly instructions generator

## File Structure

```
stl-buster/
├── index.html    # Main app with Three.js integration
└── claude.md     # This documentation
```

## Known Limitations

- Fixed 4-piece split pattern (quadrants)
- Tooth joints only on X/Y split planes
- No Z-axis splitting
- Large files may be slow to process
- Preview rendering performance depends on model complexity
- No undo functionality

## Development Notes

- Uses Three.js r128 or later
- Geometry modifications are CPU-intensive for complex models
- Consider Web Workers for background processing of large files
- Tooth generation algorithm could be optimized for speed
- Future: Add progress indicators for long operations

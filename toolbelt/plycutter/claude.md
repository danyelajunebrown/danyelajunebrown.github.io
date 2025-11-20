# Plycutter

## What It Does

Converts 3D models (STL files) into flat 2D patterns (DXF files) with finger joints for laser cutting. Takes a 3D object and "unrolls" it into plywood-friendly panels that can be cut and assembled.

## The Problem It Solves

You want to build a 3D object from plywood using a laser cutter, but:
- 3D CAD is complex and time-consuming
- Manual flattening is error-prone
- Finger joints need precise calculations
- Assembly without instructions is difficult

Plycutter automates the entire process: upload STL → get laser-ready DXF patterns with finger joints.

## How It Works

1. **Upload STL**: Load your 3D model file
2. **Configure**: Set material thickness and joint parameters
3. **Process**: Plycutter analyzes the mesh and generates flat patterns
4. **Preview**: View the sliced panels in your browser
5. **Download DXF**: Get laser-cutter-ready files

## Features

### STL Processing
- Binary and ASCII STL support
- Automatic mesh analysis
- Face normal detection
- Edge identification

### Slicing Algorithm
- Horizontal plane slicing at regular intervals
- Contour extraction from intersections
- Automatic pattern nesting
- Orientation optimization for material efficiency

### Finger Joint Generation
- Parametric finger joint sizing
- Automatic joint placement on edges
- Tolerance adjustment for fit
- Tab/slot pairing for assembly

### DXF Export
- Industry-standard format
- Compatible with most laser cutters
- Layered organization
- Dimension annotations
- Assembly numbers

### Settings
- **Slice Thickness**: Material thickness (plywood depth)
- **Finger Width**: Joint tab width
- **Finger Depth**: How deep joints interlock
- **Tolerance**: Gap for tight/loose fit
- **Slice Interval**: Spacing between horizontal slices

## Technical Details

### Technologies
- Three.js for STL parsing and 3D visualization
- Custom slicing algorithm
- DXF file generation library
- Canvas-based 2D preview
- Pure client-side processing

### Supported Formats
**Input:**
- STL (binary and ASCII)
- Millimeter or inch units

**Output:**
- DXF (AutoCAD format)
- Compatible with:
  - Epilog laser cutters
  - Glowforge
  - Trotec
  - Universal Laser Systems
  - Any DXF-compatible cutter

### Slicing Process
1. Orient model for optimal slicing plane
2. Generate horizontal cutting planes
3. Calculate mesh intersections
4. Extract 2D contours
5. Generate finger joints on adjoining edges
6. Nest patterns for material efficiency
7. Export as DXF layers

## Use Cases

1. **Furniture Design**: Chairs, tables, shelves from 3D models
2. **Architectural Models**: Buildings, landscapes at scale
3. **Product Prototyping**: Test forms before injection molding
4. **Art Installations**: Large sculptural pieces from plywood
5. **Educational Models**: Anatomical, geological, mechanical models
6. **Custom Packaging**: Fitted boxes and enclosures
7. **Props and Cosplay**: Armor, weapons, set pieces

## Material Recommendations

### Plywood Types
- **Baltic Birch**: Best for fine detail, strong joints
- **MDF**: Smooth finish, less structural strength
- **Hardwood Ply**: Oak, maple for premium pieces
- **Acrylic**: Transparent pieces (adjust for brittleness)

### Thickness Guide
- 3mm (1/8"): Small models, decorative
- 6mm (1/4"): Medium projects, furniture
- 12mm (1/2"): Large furniture, structural
- 18mm (3/4"): Heavy-duty construction

## Assembly Tips

1. **Dry Fit First**: Assemble without glue to check fit
2. **Adjust Tolerance**: If too tight, increase tolerance and recut
3. **Gluing**: Use wood glue on finger joints for permanence
4. **Clamping**: Clamp while glue dries for tight joints
5. **Sanding**: Light sanding improves joint fit
6. **Finishing**: Sand, stain, or paint after assembly

## Future Enhancements

### Advanced Features
- Curved surface unrolling (not just horizontal slices)
- Multiple assembly methods (tabs, dowels, screws)
- Automatic kerf compensation for laser cutter
- Material optimization to minimize waste
- Assembly instruction generation

### Smart Joints
- Dovetail joints for stronger connections
- Hidden joints for cleaner aesthetics
- Slot and tab variations
- Automatic joint sizing based on stress analysis

### User Experience
- 3D preview with finger joints visible
- Interactive joint editing
- Material cost calculator
- Assembly animation
- Engraving for piece numbers/orientation

### Export Options
- PDF with printing guides for manual cutting
- G-code generation for CNC routers
- SVG export for web viewing
- Assembly manual PDF generation

## File Structure

```
plycutter/
├── index.html            # Main web application
├── plycutter.js          # Legacy/alternative implementation
├── simple_plycutter.py   # Python backend (optional)
└── claude.md            # This documentation
```

## Known Limitations

- Only horizontal slicing (not optimal for all shapes)
- Finger joints limited to straight edges
- No support for curved surfaces
- Complex models may generate many small pieces
- Material waste not optimized
- No assembly instructions generated
- Processing time increases with model complexity

## Development Notes

- Python backend (`simple_plycutter.py`) suggests server-side processing capability
- JavaScript version runs entirely in browser
- Consider adding Web Workers for large model processing
- DXF generation could be optimized for smaller file sizes
- Future: Implement local storage for settings
- Add progress indicators for long operations

## Credits

Based on open-source slicing algorithms and DXF generation libraries. Check the credit banner in the app for original contributors and inspiration.

## Best Practices

### For Best Results
- Clean, manifold STL files (no holes or gaps)
- Orient model for logical assembly
- Start with simple shapes to test settings
- Use test cuts to dial in tolerances
- Keep finger joint count reasonable (not too many)

### Common Issues
- **Joints too tight**: Increase tolerance (+0.1mm)
- **Joints too loose**: Decrease tolerance (-0.1mm)
- **Pieces don't align**: Check model is manifold
- **Too many pieces**: Increase slice interval
- **Material warping**: Use thicker material or add bracing

## Community

Share your creations and get help:
- Tag your builds on social media
- Contribute improvements on GitHub
- Share optimal settings for different materials
- Report bugs and feature requests

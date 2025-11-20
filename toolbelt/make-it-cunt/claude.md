# Make It Cunt

## What It Does

A garment extension pattern generator that helps you lengthen clothes that are too short. Perfect for tall people, growing kids, or anyone who wants to add length to their favorite garments.

## The Problem It Solves

When a garment is too short, you can't just hem it longer. This tool creates custom extension patterns that you can:
- Cut from matching or contrasting fabric
- Sew into the garment to add precise length
- Use to modify pants, shirts, sleeves, etc.

## How It Works

1. **Measure**: Tap two points on a photo/drawing of your garment to establish scale
2. **Calculate**: Enter your desired final length in inches
3. **Generate**: The tool creates an SVG pattern with the exact extension dimensions
4. **Download**: Save the SVG pattern to print or send to a cutter

## Features

### Measurement System
- Visual canvas-based measurement tool
- Two-point click measurement
- Automatic scale calculation from pixel distance to real inches
- Clear visual feedback with red points and blue measurement line

### Pattern Generation
- Automatic seam allowance (0.5 inches)
- Garment-specific width defaults:
  - Pants: 8 inches
  - Shirts: 10 inches
- SVG output with labeled dimensions
- Print-ready format

### Output
- Downloadable SVG pattern file
- Includes extension length and seam allowance notes
- Scalable vector format works with laser cutters and plotters

## Technical Details

### Technologies
- Pure HTML5 Canvas for measurement interface
- SVG generation for pattern output
- Vanilla JavaScript - no dependencies
- Client-side only - no server required

### Calculation Logic
```
1. User clicks 2 points on garment → measure pixel distance
2. User enters desired length in inches
3. Calculate scale: desired_length / pixel_distance
4. Calculate extension needed: desired_length - (measured_length * scale)
5. Generate pattern: extension_length + seam_allowances
```

## Use Cases

1. **Lengthening pants** that are too short
2. **Extending shirt sleeves** for longer arms
3. **Adding length to dresses** or skirts
4. **Growing room** for kids' clothes
5. **Fashion alterations** with contrasting fabric bands

## Future Enhancements

### Advanced Measurements
- Upload photo/image for measurement
- Multiple measurement points for curved garments
- Metric/Imperial unit toggle
- Save measurement profiles

### Pattern Features
- Custom seam allowance settings
- Curved pattern pieces for fitted garments
- Gusset and dart placement
- Multiple pattern pieces per garment
- Pattern matching guides for stripes/prints

### Garment Library
- Pre-set dimensions for common garment types
- Custom garment type creation
- Body measurement integration
- Size grading tools

### Output Options
- PDF pattern with printing guides
- Direct integration with cutting machines
- Email/share pattern files
- Pattern piece labeling and assembly instructions

## File Structure

```
make-it-cunt/
├── index.html    # Main app
└── claude.md     # This documentation
```

## Known Limitations

- Currently only supports straight rectangular extensions
- No support for curved or shaped pattern pieces
- Width is preset by garment type (not measured)
- Requires manual photo setup for accurate measurement
- SVG rendering depends on browser support

## Development Notes

- Canvas size is fixed (400x300) - consider making responsive
- Scale calculation assumes linear measurement (works best for straight edges)
- Future: Add image upload and overlay on canvas for easier measurement
- Future: Add print layout tools with tiling for large patterns

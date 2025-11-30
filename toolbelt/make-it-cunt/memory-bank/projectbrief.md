# Project Brief: Make It Cunt

## Overview
"Make It Cunt" is a web-based garment extension pattern generator that helps users create custom sewing patterns to lengthen clothes that are too short. The tool uses visual measurement and automatic calculation to generate print-ready SVG patterns.

## Objectives
- **Primary**: Create an easy-to-use tool for generating precise garment extension patterns
- **Secondary**: Eliminate the need for manual pattern drafting when lengthening garments
- **Tertiary**: Support multiple garment types with appropriate width defaults
- **User Experience**: Make pattern creation accessible to sewers of all skill levels

## Success Criteria
- Users can accurately measure garments using a visual canvas interface
- Generated patterns include correct dimensions with seam allowances
- Patterns are downloadable in SVG and PDF formats
- The tool works entirely client-side with no server dependency
- Measurement profiles can be saved and reused

## Constraints
- **Technical**: Must work as a single-page application with no backend
- **Browser**: Requires HTML5 Canvas and SVG support
- **Scope**: Currently limited to straight rectangular extensions (no curves)
- **Units**: Must support both imperial (inches) and metric (cm) measurements
- **Platform**: Web-based, accessible via modern browsers

## Target Users
1. **Tall people** who frequently need to lengthen ready-to-wear garments
2. **Parents** adding growing room to children's clothes
3. **Fashion enthusiasts** creating custom alterations with contrasting fabric bands
4. **Sewing beginners** who need guidance on pattern dimensions
5. **Sustainable fashion advocates** extending garment life through alterations

## Timeline
- **Phase 1** (Complete): Core measurement and pattern generation functionality
- **Phase 2** (Complete): Profile saving system with localStorage
- **Phase 3** (Complete): Unit conversion (inches/cm) support
- **Phase 4** (Complete): Image upload for visual measurement
- **Future**: Advanced pattern features (curves, darts, multiple pieces)

## Core Problem Statement
When garments are too short, traditional hemming cannot add length. Users need an accurate way to create extension patterns without manual drafting skills. This tool bridges that gap by automating the mathematical calculations and providing print-ready patterns.

## Key Differentiators
- Visual measurement system (click-to-measure on canvas)
- Automatic scale calculation from pixel-to-real-world measurements
- Instant pattern generation with proper seam allowances
- No installation or signup required
- Works with uploaded garment photos or blank canvas

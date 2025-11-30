# Product Context

## User Stories

### Primary User Stories
- **As a tall person**, I want to add length to ready-to-wear pants so that they fit my proportions properly
- **As a parent**, I want to create extension patterns for my growing child's clothes so that I can extend their usability without buying new ones
- **As a sewing enthusiast**, I want to generate accurate patterns quickly so that I don't have to manually draft rectangular extensions
- **As a fashion alteration specialist**, I want to add contrasting fabric bands to garments so that I can create unique custom pieces
- **As a beginner sewer**, I want clear measurements and seam allowances included so that I can successfully complete the alteration

### Secondary User Stories
- **As a sustainable fashion advocate**, I want to extend the life of garments so that I reduce textile waste
- **As a user with multiple garments to alter**, I want to save measurement profiles so that I don't have to re-enter dimensions each time
- **As someone working with fabric shops**, I want to download patterns as SVG so that I can send them to laser cutters or plotters
- **As an international user**, I want to toggle between inches and centimeters so that I can work in my preferred measurement system

## Business Requirements

### Core Functionality
1. **Visual Measurement System**: Users must be able to establish scale by clicking two points on a garment image or canvas
2. **Automatic Calculation**: System must convert pixel measurements to real-world dimensions and calculate extension needs
3. **Pattern Generation**: Tool must create accurate SVG patterns with dimensions, seam allowances, and cutting instructions
4. **Multi-Format Export**: Patterns must be downloadable as SVG and printable as PDF

### Data Management
1. **Profile Storage**: Users can save garment profiles with measurements to localStorage
2. **Unit Conversion**: System supports both imperial (inches) and metric (cm) with automatic conversion
3. **No Account Required**: All functionality works client-side without user registration

### Garment Types Supported
- Pants (8" default width)
- Shirts (10" default width)
- Sleeves (6" default width)
- Dresses (12" default width)
- Skirts (14" default width)
- Custom width option for unique garments

## UX Goals

### Simplicity & Clarity
- **Single-page experience**: All functionality accessible without navigation
- **Step-by-step workflow**: Numbered sections guide users through the process (1. Setup, 2. Configure, 3. Pattern, 4. Save)
- **Visual feedback**: Immediate visual confirmation of measurement points and calculations
- **Inline instructions**: Yellow instruction box explains the process upfront

### Accessibility
- **No learning curve**: Instructions are clear enough for first-time users
- **Forgiving interface**: Users can reset measurements and try again without penalty
- **Status messages**: Color-coded feedback (success, warning, info) keeps users informed
- **Responsive design**: Works on different screen sizes (desktop focus)

### Aesthetic
- **Modern gradient background**: Purple gradient creates an engaging, creative atmosphere
- **Clean white panels**: Information is organized in crisp, readable sections
- **Consistent color scheme**: Purple/violet branding with orange accents for alerts
- **Professional pattern output**: Generated patterns look production-ready

## Feature Priorities

### Must Have (Implemented ✓)
1. ✅ Visual canvas measurement system
2. ✅ Two-point click measurement with pixel distance calculation
3. ✅ Scale calculation (pixels per unit)
4. ✅ Extension length calculation with seam allowance
5. ✅ SVG pattern generation with dimensions and labels
6. ✅ Garment type selector with preset widths
7. ✅ Custom width option
8. ✅ Profile save/load system with localStorage
9. ✅ Unit conversion (inches ↔ centimeters)
10. ✅ Image upload for measurement reference
11. ✅ SVG download functionality
12. ✅ PDF export (via print dialog)

### Should Have (Future Enhancements)
1. Pattern grids for measurement reference
2. Fold line indicators on patterns
3. Multiple pattern pieces per garment
4. Pattern piece labeling system
5. Fabric requirement calculator
6. Seam allowance customization per edge
7. Pattern piece rotation tools
8. Measurement history tracking

### Nice to Have (Backlog)
1. Curved pattern pieces for fitted garments
2. Dart placement tools
3. Gusset creation
4. Pattern matching guides for prints/stripes
5. Body measurement integration
6. Size grading functionality
7. Pattern assembly instructions
8. Integration with cutting machine software
9. Social sharing of saved profiles
10. Pattern template library

## Known Pain Points

### Current Limitations
1. **Canvas resolution**: Fixed canvas size may not work well for very detailed measurements
2. **Straight pieces only**: Cannot generate curved or shaped pattern pieces
3. **Width not measured**: Users must know or estimate garment width rather than measuring it
4. **Image scaling**: Users need to understand scale establishment for accurate measurements
5. **PDF generation**: Uses browser print dialog rather than direct PDF creation with proper page layout

### User Education Needs
1. Users must understand the two-point measurement concept
2. Users need to identify a known measurement on their garment for scale
3. Understanding seam allowance and how it affects cutting
4. Knowing which measurement units match their fabric/ruler

### Technical Constraints
1. Requires modern browser with Canvas API support
2. localStorage limits on profile storage
3. SVG compatibility varies across cutting software
4. No real-time collaboration or cloud sync

## Success Metrics

### User Engagement
- Pattern generation completion rate
- Profile save/load usage
- Return usage (multiple sessions)
- Image upload adoption

### Pattern Quality
- Accuracy of measurements (user feedback)
- Successful alterations (testimonials)
- Pattern usability in real sewing projects

### Tool Performance
- Page load time < 2 seconds
- Measurement response time instant
- Pattern generation < 1 second
- Export/download success rate

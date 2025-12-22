# Scanning Guide: Revopoint Inspire

This guide covers how to capture body and garment scans using the **Revopoint Inspire 3D Scanner** with **Revo Scan 5** software for use with Make It Cunt v3.0.

## Quick Reference

| Specification | Value |
|---------------|-------|
| **Accuracy** | 0.2mm (single image) |
| **Point Distance** | ~0.3mm spacing |
| **Software** | Revo Scan 5 |
| **Export Formats** | PLY, OBJ, STL, FBX, GLTF, 3MF, ASC |
| **Recommended Format** | **PLY** (best compatibility) |
| **Native Units** | mm (matches backend) |

---

## Scanner Setup

### Before First Scan
1. Install **Revo Scan 5** from Revopoint website
2. Connect Revopoint Inspire via USB
3. Launch Revo Scan 5 and ensure scanner is recognized
4. Ensure adequate lighting (natural light or diffuse artificial)
5. Clear scan area of clutter

### Optimal Environment
- **Lighting**: Bright, diffuse lighting (avoid direct sunlight or harsh shadows)
- **Background**: Plain, non-reflective background if possible
- **Temperature**: Room temperature (scanner performs best at 20-25°C)
- **Movement**: Minimize movement of subject/garment during scan

---

## Body Scanning

### Preparation

**Subject Preparation:**
- Wear **form-fitting clothing** (leggings, tank top, or similar)
- Avoid loose, flowing fabrics that obscure body shape
- Hair tied back if scanning upper body
- Remove jewelry, watches, bags
- Stand still and breathe normally

**Best Pose:**
- Stand upright, arms slightly away from body (T-pose or slight variation)
- Feet shoulder-width apart
- Look straight ahead
- Relax but maintain posture

**Why This Pose?**
- Arms away from body allows scanner to capture armpit/shoulder area
- Upright stance gives accurate torso length measurements
- Stable, repeatable pose for consistent results

### Scanning Process

1. **Launch Revo Scan 5** and select "Body Scan" mode
2. **Start at front**, slowly move scanner around body in a circular path
3. **Move vertically** as you circle (capture head-to-toe)
4. **Overlap scans** - keep previous scan area visible as you move
5. **Complete 360° circuit** - aim for full coverage
6. **Check coverage** in Revo Scan 5 preview (fill any gaps)

**Scan Tips:**
- Move scanner smoothly (not too fast)
- Keep scanner 30-50cm from subject
- Maintain consistent distance
- If scan loses tracking, back up slightly and re-establish

**Typical Scan Time:** 3-5 minutes for full body

### Post-Processing in Revo Scan 5

1. **Review scan** - check for missing areas
2. **Fill small holes** (automatic in Revo Scan 5)
3. **Remove base/floor** if captured (crop tool)
4. **Smooth if needed** (light smoothing, don't over-process)
5. **Export as PLY** → save to dedicated folder

**Export Settings:**
- Format: **PLY**
- Units: **mm** (default)
- Resolution: Keep native resolution (~0.3mm point spacing)
- No texture needed (backend only uses geometry)

---

## Garment Scanning

### On Dress Form (Recommended)

**Why Dress Form?**
- Captures garment's draped shape
- Shows how fabric hangs and folds naturally
- Easier to scan (stationary) vs. wearing garment
- Better for analyzing fit issues (compression, tenting)

**Setup:**
1. Place garment on **dress form** similar to your body proportions
2. Adjust dress form to match your key measurements (bust, waist, hip)
3. Ensure garment sits naturally (not pulled, stretched, or bunched)
4. Position dress form on turntable if available (easier scanning)
5. Plain background behind dress form

**Scanning Process:**
1. **Launch Revo Scan 5** and select "Object Scan" mode
2. **Start at front center**, capture front panel
3. **Move around garment** in circular motion
4. **Capture all seams** (especially stress points like shoulders, crotch)
5. **Get inside details** if needed (waistband, pockets)
6. **Complete 360° scan**

**Typical Scan Time:** 2-4 minutes per garment

### Flat Garment Scan (Alternative)

If you don't have a dress form:
1. Lay garment flat on non-reflective surface
2. Smooth out wrinkles
3. Scan front, then flip and scan back
4. Note: Flat scans lose information about drape/fit

**Warning:** Flat scans are less accurate for fit analysis.

### Post-Processing in Revo Scan 5

1. **Review coverage** - ensure all seams captured
2. **Remove dress form** (crop/erase tool) - keep only garment
3. **Clean up scan** - remove stray points, base, background
4. **Export as PLY**

**Export Settings:**
- Format: **PLY**
- Units: **mm**
- Include only garment geometry (no dress form)

---

## File Organization

Recommended folder structure:

```
make-it-cunt-scans/
├── body-scans/
│   ├── 2025-12-22-body-01.ply
│   ├── 2025-12-22-body-02.ply  (if doing multiple scans)
│   └── ...
├── garment-scans/
│   ├── pants/
│   │   ├── jeans-black-01.ply
│   │   └── ...
│   ├── shirts/
│   │   └── ...
│   └── dresses/
│       └── ...
└── results/
    └── (generated patterns will go here)
```

**Naming Convention:**
- Body scans: `YYYY-MM-DD-body-##.ply`
- Garment scans: `descriptive-name-##.ply` (e.g., `navy-jeans-01.ply`)

---

## Quality Checklist

### Body Scan Quality
- [ ] Full 360° coverage (no large gaps)
- [ ] Head to feet captured
- [ ] Arms clearly separated from torso
- [ ] No major noise or artifacts
- [ ] Subject didn't move during scan
- [ ] Exported as PLY in mm units

### Garment Scan Quality
- [ ] All seams visible
- [ ] No dress form geometry in export
- [ ] Captures natural drape/hang
- [ ] Waistband/hem clearly defined
- [ ] Problem areas captured (shoulders, crotch, etc.)
- [ ] Exported as PLY in mm units

---

## Troubleshooting

### Scanner Won't Track
- **Cause**: Too fast movement, poor lighting, reflective surfaces
- **Fix**: Move slower, improve lighting, cover reflective areas

### Gaps in Coverage
- **Cause**: Moved too fast, skipped areas
- **Fix**: Do second pass focusing on gap areas, overlap more

### Noisy Scan (lots of stray points)
- **Cause**: Dark clothing, poor lighting, moving subject
- **Fix**: Better lighting, lighter clothing, ensure subject stays still

### Mesh Has Holes
- **Cause**: Scanner couldn't see area (occlusion, poor angle)
- **Fix**: Multiple scanning passes, fill holes in Revo Scan 5 or let backend handle it

### Wrong Scale
- **Cause**: Exported in wrong units
- **Fix**: Always export in **mm** (millimeters), backend auto-detects but mm is safest

---

## First Scan Checklist

Before your first scan session:
- [ ] Revo Scan 5 installed and scanner connected
- [ ] Adequate lighting in scan area
- [ ] Subject wearing form-fitting clothes (for body scan)
- [ ] Dress form set up (for garment scan)
- [ ] Scan folder structure created
- [ ] Backend server dependencies installed (`pip install -r requirements.txt`)
- [ ] Backend server tested (`python server/app.py`)

---

## Integration with Make It Cunt

### Workflow
1. **Scan body** with Revopoint Inspire → export as PLY
2. **Scan garment** on dress form → export as PLY
3. **Upload both to Make It Cunt backend**:
   - POST body PLY to `/api/mesh/upload/body`
   - POST garment PLY to `/api/mesh/upload/garment`
4. **Run fit analysis**: POST to `/api/analysis/fit`
5. **Generate patterns**: POST to `/api/patterns/generate`
6. **Download SVG patterns** and print for sewing

### Expected Results
- **Body scan**: Backend extracts landmarks (waist, hip, shoulders, etc.)
- **Garment scan**: Backend detects seams, classifies garment type
- **Fit analysis**: Compression zones (too tight), gap zones (tenting), length deficits
- **Patterns**: Shaped extensions, gussets, darts (not rectangles!)

---

## Tips for Best Results

### Body Scanning
- **Multiple scans**: Do 2-3 body scans, use the best one
- **Consistent pose**: Use same pose each time for comparison
- **Mark landmarks**: If backend struggles, consider marking body landmarks with tape
- **Movement profile**: Tell backend your movement needs ("wild" for dance)

### Garment Scanning
- **Pre-wash garments**: Scan after washing (captures final size)
- **Note fit issues**: Before scanning, note where garment is too tight/loose/short
- **Multiple angles**: Capture problem areas from multiple angles
- **Seam focus**: Ensure all seams are clearly visible (backend uses these)

### General
- **Lighting matters**: Good lighting = clean scans = better analysis
- **Take your time**: Rushing = gaps and artifacts
- **Practice scans**: Do a few practice scans to get comfortable with scanner
- **Check in Revo Scan 5**: Review scan quality before exporting

---

## Advanced: Movement Envelope

For users with extreme movement needs (dance, performance, martial arts):

**What is it?** The "movement envelope" expands your body mesh to show space needed for movement. The backend will check if garment accommodates this.

**How to specify:**
- When uploading body scan, include parameter: `movement_profile=wild`
- Options: `standard`, `fitted`, `wild`
- `wild` adds significant ease at stress points:
  - Shoulders: +80mm
  - Crotch: +100mm
  - Knees: +80mm
  - Bust: +50mm

**Use case:** If you do wild movement (dance, parkour), use `wild` profile. Backend will recommend gussets/ease at stress points.

---

## Need Help?

Common issues and solutions:

| Issue | Solution |
|-------|----------|
| Scanner not recognized | Check USB connection, restart Revo Scan 5 |
| Scan looks noisy | Improve lighting, scan slower, lighter clothing |
| Backend rejects mesh | Check format (must be PLY/OBJ/STL), check file isn't corrupted |
| Backend shows weird dimensions | Verify units are mm in export settings |
| Fit analysis seems wrong | Ensure body and garment scans are aligned, check scan quality |

**Next Steps:** See [TESTING.md](TESTING.md) for how to test your scans with the backend.

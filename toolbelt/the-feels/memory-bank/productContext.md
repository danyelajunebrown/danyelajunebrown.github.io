# Product Context

## Purpose
This application helps users track their emotional states and coping skills for DBT therapy. The diary card feature lets users visualize their emotional patterns over a week and share them with therapists.

The VR/AR kiosk turns the same data into an embodied experience: the diary owner's whole year of feelings becomes a physical walk, so a viewer can literally move through someone's emotional timeline.

## User Experience Goals

### Diary app (`index.html`)
- Simple, intuitive feelings selection via spinning wheel
- Clear visual feedback for intensity and skills
- Easy-to-use weekly diary card with drag-and-drop
- Reliable PDF export for sharing with therapists
- Self-service password changes

### VR kiosk (`vr.html`)
- Zero UI / no dialogues — a single tap to begin, then only the walk
- The wearer controls all movement by physically walking; nothing moves them
- Each emotion floods the passthrough view with its color until the next zone
- Block length is proportional to how long that feeling was actually felt

## Success Criteria
- Diary: full content captured in PDF, centered, no UI artifacts
- Kiosk: emotion colors track the wearer's real position along the path
- Kiosk: data refreshes live so a newly logged feeling reshapes the path
- No credentials stored in any public file

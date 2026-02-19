# The Feels

**Also known as:** All The Feels, Diary Card

## What It Does

A DBT (Dialectical Behavior Therapy) diary card tracker that helps you monitor emotions, urges, and skills practice. Generates beautiful PDF reports to share with your therapist.

## The Problem It Solves

DBT requires daily tracking of:
- Emotional intensity and types
- Urges and target behaviors
- Skills used (mindfulness, distress tolerance, emotion regulation, interpersonal effectiveness)
- Medication adherence

Traditional paper diary cards are easy to lose, hard to analyze, and time-consuming to fill out. This app makes tracking easier and generates professional reports for therapy sessions.

## How It Works

1. **Authenticate**: Sign in with email (Supabase auth)
2. **Log Daily**: Record emotions, urges, and skills used
3. **Track Progress**: View your patterns over time
4. **Generate Report**: Create PDF diary card for your therapist
5. **Cloud Sync**: All data stored securely in Supabase

## Features

### Emotion Tracking
- Visual emotion wheel for easy selection
- Intensity ratings (0-10 scale)
- Multiple emotions per day
- Spinning emotion wheel animation (60s rotation)

### Urges Tracking
- Common urges (self-harm, substance use, etc.)
- Intensity ratings
- Whether you acted on the urge
- Custom urge types

### Skills Practice
- Four DBT skill modules:
  - **Mindfulness**: Observe, describe, participate
  - **Distress Tolerance**: TIPP, ACCEPTS, self-soothe
  - **Emotion Regulation**: Check the facts, opposite action
  - **Interpersonal Effectiveness**: DEAR MAN, GIVE, FAST
- Checkbox tracking for each skill used
- Daily skills summary

### Reporting
- PDF generation with html2canvas + jsPDF
- Professional diary card format
- Weekly/monthly summaries
- Graphs and visualizations
- Shareable with therapist

### Cloud Storage
- Supabase backend integration
- Secure authentication
- Real-time data sync
- Historical data access
- Privacy-focused design

## Technical Details

### Technologies
- Supabase for auth + database
- html2canvas for screenshot capture
- jsPDF for PDF generation
- Vanilla JavaScript + CSS3
- Responsive mobile-first design

### Data Schema
```javascript
{
  user_id: uuid,
  date: timestamp,
  emotions: [
    { emotion: string, intensity: number }
  ],
  urges: [
    { type: string, intensity: number, acted: boolean }
  ],
  skills: {
    mindfulness: [skill_names],
    distress_tolerance: [skill_names],
    emotion_regulation: [skill_names],
    interpersonal_effectiveness: [skill_names]
  },
  medications_taken: boolean,
  notes: text
}
```

### External Dependencies
- Supabase JS SDK v2.39.7
- html2canvas v1.4.1
- jsPDF v2.5.1

## Use Cases

1. **DBT Therapy Clients**: Track daily practice between sessions
2. **Therapists**: Monitor client progress and skills usage
3. **Mental Health Tracking**: General emotional awareness
4. **Research**: Collect longitudinal emotional data
5. **Self-Improvement**: Identify patterns and triggers

## Assets

### Feelings Wheel Images
- `feelings wheel.jpeg` (161KB)
- `feelings wheel.png` (589KB)
- Visual reference for emotion selection
- Both formats included for compatibility

## Future Enhancements

### Advanced Tracking
- Custom emotion categories
- Photo/voice note attachments
- Sleep and exercise tracking
- Medication reminder system
- Crisis plan integration

### Analytics
- Emotion patterns over time
- Skill effectiveness analysis
- Trigger identification
- Correlation between emotions and behaviors
- Predictive insights

### Sharing & Collaboration
- Share reports with therapist directly
- Therapist dashboard for multiple clients
- Family/support person viewing permissions
- Emergency contact integration

### Gamification
- Streak tracking for daily logging
- Skills practice achievements
- Progress milestones
- Motivational reminders

### Export Options
- CSV export for personal analysis
- Integration with other health apps
- Backup and restore functionality
- Print-friendly layouts

## File Structure

```
the-feels/
├── index.html              # Main app
├── feelings wheel.jpeg     # Emotion reference image
├── feelings wheel.png      # Emotion reference image (PNG)
└── claude.md              # This documentation
```

## Known Limitations

- Requires internet connection for Supabase
- PDF generation limited by browser capabilities
- Large datasets may slow down rendering
- No offline mode (yet)
- Single-user focus (no group/family tracking)

## Privacy & Security

- All data encrypted in transit (HTTPS)
- Supabase handles authentication securely
- No third-party analytics or tracking
- User controls their own data
- HIPAA considerations for production use

## Development Notes

- Supabase project URL and keys need to be configured
- Consider implementing offline-first with service workers
- PDF generation could be moved to server-side for better quality
- Emotion wheel images could be optimized (589KB PNG is large)
- Future: Add data export before deletion features
- Consider accessibility improvements (screen reader support)

## DBT Skills Reference

### Mindfulness
- Observe (notice without judgment)
- Describe (put words to experience)
- Participate (engage fully)
- Non-judgmentally
- One-mindfully
- Effectively

### Distress Tolerance
- TIPP (Temperature, Intense exercise, Paced breathing, Progressive relaxation)
- ACCEPTS (Activities, Contributing, Comparisons, Emotions, Pushing away, Thoughts, Sensations)
- Self-soothe with five senses
- Improve the moment
- Pros and cons

### Emotion Regulation
- Check the facts
- Opposite action
- Problem solving
- ABC PLEASE (Accumulate positives, Build mastery, Cope ahead)
- Reduce vulnerability

### Interpersonal Effectiveness
- DEAR MAN (Describe, Express, Assert, Reinforce, Mindful, Appear confident, Negotiate)
- GIVE (Gentle, Interested, Validate, Easy manner)
- FAST (Fair, Apologies, Stick to values, Truthful)

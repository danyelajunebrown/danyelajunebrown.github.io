# The Feels — Headset Setup Runbook

How to load `vr.html` onto a Meta Quest 3 that has **no controllers**.

Open this file on your phone while you're setting up — you can't read your
laptop while wearing the headset.

## The blocker

Without controllers, the OOBE pairing screen needs a click that hand
tracking can't always provide on a fresh/factory-reset Quest 3 (hand
tracking isn't guaranteed to be live in OOBE until firmware ≥ v59).

The fallback Meta builds into OOBE for this exact case is **gaze cursor +
volume button**. Most users don't notice it's there because they have
controllers.

## Physical button map (you can't see these with the headset on)

| Button | Location | What it does in OOBE |
|---|---|---|
| Power | Right side of headset, near temple | Short press = select, 2s hold = sleep menu, 10s hold = force off |
| Volume down | Bottom-right edge, button closer to the front | Primary "select" for gaze cursor |
| Volume up | Bottom-right edge, button closer to your face | Secondary "select" / increase highlight |

The volume buttons are on the *underside* of the headset, not the side.
Feel for the rocker with your right thumb while holding the headset.

## Activating the gaze cursor

1. Put the headset on.
2. Hold still and look forward for ~2 seconds — a small white dot should
   fade in at the center of your view.
3. If no dot appears: **press and hold both volume buttons together for
   ~3 seconds** to force-enable the accessibility gaze cursor.
4. Slowly turn your head. Verify the dot stays in the center of your view
   and that on-screen buttons highlight when the dot lands on them.

## Completing OOBE without controllers

### Step 0 — Phone prep (do this BEFORE powering on the headset)

1. Install **Meta Horizon** (App Store / Google Play).
2. Create a Meta account inside the app (email + password + DOB).
3. In the app: **Menu → Devices → Pair new headset → Quest 3**. Leave this
   screen open.

### Step 1 — Power on

Hold the headset power button (right side) for 3 seconds until the boot
chime plays. Wait through the boot logo (~30 seconds).

### Step 2 — Language select

A grid of languages appears. Gaze at your language → volume-down to
select. If volume-down does nothing, try volume-up, then a short tap of
the power button.

### Step 3 — Phone pairing

A 5-digit code appears in the headset. Enter the code in the Horizon app
on your phone. The phone takes over the next several steps (terms,
Wi-Fi, account sign-in).

**At the end of phone pairing, the headset will show a "Continue" /
"Confirm pairing" button.** This is the step you got stuck on. Gaze at
that button so it highlights, then press volume-down.

### Step 4 — Firmware update

A factory-reset Quest 3 will almost always download a firmware update
here (20–40 minutes). Plug in the charger. Walk away. The headset
restarts itself when done.

### Step 5 — Land in Quest Home

After update, hand tracking is reliably enabled. Pinching (index +
thumb) becomes the primary click. The gaze cursor is no longer needed.

## Launching `vr.html`

1. Open Meta Quest Browser (pinned to the dock by default).
2. From the Horizon app on the phone:
   **Devices → your headset → Send link to headset**
   Paste: `https://danyelajunebrown.github.io/toolbelt/the-feels/vr.html`
3. The link opens in the headset browser. Bookmark / pin to home so
   subsequent launches are one pinch from Home.
4. Pinch the "the feels" tap target → camera permission prompt → pinch
   Allow → passthrough AR session begins. Walk the path.

## Last-resort fallbacks if gaze cursor will not work

The gaze cursor falls back if the firmware is too old (pre-v45ish — rare
for a Quest 3 but possible on a long-offline device).

1. **Borrow one controller.** Any Quest 2/3/3S/Pro Touch controller pairs
   with a Quest 3. You only need one, doesn't matter left or right.
   To pair: hold Meta + B (right) or Menu + Y (left) for ~5 seconds while
   in OOBE.
2. **Bard media/IT lab.** Most college media labs have Quest hardware.
3. **Meta support replacement controllers** — warranty path, too slow for
   a critical-path show.

## Why this isn't documented better

Meta's public OOBE docs assume controllers are present. The gaze + volume
path is an accessibility feature for users who can't operate controllers
and is mentioned only in the volume-controls help article and a handful
of community forum threads, not in the main setup guide.

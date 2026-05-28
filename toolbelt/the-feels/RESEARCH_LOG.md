# Headset Setup — Research Log

A trail of what was tried and what each iteration learned, kept for the ISP
methodology record.

## The blocker

A factory-reset Quest 3 with no controllers, stuck on the controller-pair
animation screen during OOBE. Volume buttons triggered the volume HUD,
not the gaze cursor. Hand tracking did not auto-engage. Phone-pairing
connection appeared in the Meta Horizon app but the headset-side confirm
could not be reached.

## Iteration 0 — Hand tracking + Horizon app pairing

**Hypothesis.** Quest 3 firmware ≥ v59 (mid-2024) supports a
hand-tracking OOBE path: wave both hands at the cameras, virtual hands
appear, pinch to confirm pairing.

**Result.** Did not engage on this device. Most likely the device is on
older firmware (it was offline for some time before this attempt).

## Iteration 1 — Gaze cursor + volume buttons

**Hypothesis.** Meta's documented controller-less OOBE fallback is a
white gaze cursor + volume-button select. This is referenced explicitly
in Meta's warranty-replacement support doc and in the volume-controls
help article.

**Result.** Volume buttons only changed the volume HUD; no gaze cursor
appeared. The two-volume-button accessibility toggle did nothing. This
specific screen (the controller-pair animation) does not appear to enable
gaze cursor input on the firmware running on this device.

## Iteration 2 — The Pyro57000 / quest3_hacking_platform repo

**Hypothesis.** A GitHub repo explicitly titled "quest3 hacking platform"
will contain OOBE bypass techniques over USB-C ADB.

**Result.** The repo (https://github.com/Pyro57000/quest3_hacking_platform)
is post-setup oriented. Its contents:

- `HMD setup/` — using Quest 3 as a Linux desktop display (Wivrn, StardustXR)
- `termux_stuff/` — Termux on Quest for CLI access
- `adguard_block_meta_telem.txt` / `pihole_blick_meta_telme.txt` /
  `raw domains to block` — DNS blocklists for Meta telemetry
- `README.md` — "I'll keep my notes, tips, and tricks for using the
  quest 3 as a component in a hacking platform here."

Every technique in the repo assumes Developer Mode is on, which assumes
a Meta account is signed in, which assumes OOBE is complete. **The repo
does not bypass OOBE.** Useful AFTER OOBE — not for unblocking it.

## Iteration 3 — ADB / fastboot / recovery over USB-C

**Hypothesis.** With a USB-C cable connecting the headset to a computer,
we can issue ADB or fastboot commands to skip OOBE.

**Result.** Not possible on retail Quest 3 with current firmware. Findings:

1. **ADB** requires USB debugging to be enabled, which requires Developer
   Mode, which requires a Meta account logged in via the Horizon mobile
   app. All gated on OOBE complete.
2. **Recovery mode** (hold Power + Volume-Down for 10–15s at boot) offers
   only: Factory Reset, Boot Device, Reboot, Power Off. Physical buttons
   navigate (Vol Up/Down) and select (Power). No command execution, no
   OOBE skip.
3. **Fastboot** access requires bootloader unlock, which Meta does not
   offer to consumers — bootloaders are signed.
4. **USB accessory mode** is not exposed pre-OOBE; the device does not
   present an ADB endpoint until Developer Mode is enabled in user-space.

There is no public consumer-grade OOBE bypass for Quest 3. This is
Meta's design.

## Iteration 4 — BLE Touch-controller emulation

**Hypothesis.** A Bluetooth LE device (phone, ESP32, Raspberry Pi) can
imitate a Meta Touch controller's pairing handshake to fool OOBE into
believing a controller is present.

**Result.** Research-level only. Touch Plus controllers use a proprietary
BLE GATT profile + signed pairing exchange. No public tool emulates this
at consumer level. Not a viable path for the ISP timeline.

## Iteration 5 — Timeout wait (currently pending test)

**Hypothesis.** Per Meta's warranty-replacement support doc, the
"controllers can't be located" screen times out after 5–10 minutes and
advances to a state where gaze cursor input works.

**Test plan.** Set the headset down on the controller-pair screen for 10
minutes uninterrupted. Re-don it. Look for the gaze cursor on whatever
screen follows. Pair to the Horizon mobile app via the gaze + volume
path from there.

**Status.** To be tested.

## Iteration 6 — iPhone GPS fallback (`walk.html`)

**Hypothesis.** The artwork's core — walking a 172m real-world path
through a year of logged feelings, with color flooding the view to the
current emotion — does not strictly require AR passthrough. An iPhone
held in hand, using GPS for path position and a full-screen color flood
instead of a tinted plane, expresses the same idea.

The Quest 3 has no GPS and had to derive position from SLAM tracking.
The iPhone has GPS natively, so the iPhone version arguably *fits* the
real-world-coordinate concept better than the Quest version.

**Implementation.** `toolbelt/the-feels/walk.html` — a single-page
standalone document. Reads the same `diary_entries` rows from the same
Supabase project with the same anonymous read-only RLS scope. Builds the
same proportional path blocks. Uses `navigator.geolocation.watchPosition`
to track the walker, projects the walker's position onto the start→end
bearing, maps that to a segment, floods the screen with that emotion's
color, names the emotion. Broadcasts progress to the same
`feels-live` Supabase Realtime channel that `live.html` already listens
to, so the existing spectator view works unchanged.

**Status.** Built. Ready for outdoor test on the path.

## What this means for the demo

- **Path A (preferred):** wait out the 10-minute timeout, complete OOBE
  via gaze cursor + Horizon app, run `vr.html` on the headset as
  originally designed.
- **Path B (parallel, no hardware dependency):** demo `walk.html` on the
  iPhone, with `live.html` open on a second phone for the spectator
  view. The artwork lands even if the Quest never wakes up.

Having Path B ready de-risks the demo entirely. If the headset cooperates,
the Quest version is the centerpiece and `walk.html` is the "accessible
companion." If it doesn't, `walk.html` IS the demo.

## Sources

- Meta — Set up Meta Quest warranty replacement headset
  https://www.meta.com/help/quest/1193849938692424/
- Meta — Pair and unpair Meta Quest Touch controllers
  https://www.meta.com/help/quest/967070027432609/
- Meta — Hand and Body Tracking on Meta Quest
  https://www.meta.com/help/quest/290147772643252/
- Meta — How to set up your Meta Quest 3
  https://www.meta.com/en-gb/help/quest/10004693912934783/
- Meta — Volume controls on Meta Quest
  https://www.meta.com/help/quest/1246789140106946/
- Meta Community Forums — "Can't skip pairing with controllers after factory reset on Quest 3"
  https://communityforums.atmeta.com/t5/Get-Help/Can-t-skip-pairing-with-controllers-after-factory-reset-on-Quest/td-p/1176969
- Meta Community Forums — "Quest 3 stuck on same five-digit pairing code"
  https://communityforums.atmeta.com/discussions/PairingConnection/quest-3-stuck-on-same-five-digit-pairing-code/1362837
- Meta Community Forums — "Look at your selection and press the volume button"
  https://communityforums.atmeta.com/t5/Oculus-Quest-2-and-Quest/quot-Look-at-your-selection-and-press-the-volume-button-quot/td-p/771199
- Meta Developers — Use ADB with Meta Quest
  https://developers.meta.com/horizon/documentation/native/android/ts-adb/
- 9meters — Meta Quest 3 Controller Not Working: Troubleshooting Guide
  https://9meters.com/technology/vr/meta-quest-3-controller-not-working-troubleshooting-guide
- Kiwi Design — How To Factory Reset Meta Quest 3
  https://www.kiwidesign.com/blogs/news-1/how-to-factory-reset-meta-quest-3-a-step-by-step-guide
- Pyro57000/quest3_hacking_platform
  https://github.com/Pyro57000/quest3_hacking_platform/tree/main

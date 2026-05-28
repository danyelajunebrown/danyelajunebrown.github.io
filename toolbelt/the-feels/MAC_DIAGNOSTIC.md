# Quest 3 over USB-C — Mac Diagnostic Runbook

For the 10-minute-timeout-just-finished moment. Run these on the Mac mini.
Copy-paste each block. Paste the OUTPUT back to me — I read the
fingerprint and we decide the next step from there.

## 0 — One-time setup (if not already installed)

Android platform-tools provides both `adb` and `fastboot`. If they're
not on the Mac mini already:

```bash
brew install --cask android-platform-tools
```

Verify:

```bash
adb version
fastboot --version
```

## 1 — Baseline: what does the Mac see right now?

With the headset on, currently stuck on the controller-pair screen,
plug the USB-C cable from headset to Mac. Then:

```bash
system_profiler SPUSBDataType | grep -A 20 -i -E "oculus|meta|quest|2833"
```

What we're looking for:

- **`Vendor ID: 0x2833`** confirms it's a Meta device.
- **`Product ID:`** tells us which mode / state. Known IDs:
  - `0x0186` — Quest 3 normal user mode (no ADB endpoint until Developer Mode is on)
  - `0x0137` — Quest 3 charging / pre-pair state (no ADB)
  - `0x0a83` or similar — fastboot mode
  - `0x9008` — **EDL / Qualcomm emergency download mode** (this would be a big deal — it means the device exposes a firehose interface)
- **`Speed:`** USB 2 vs USB 3 — just informational.
- **Interface count** under the device — tells us whether ADB/MTP/HID endpoints are advertised.

Also check whether ADB sees anything:

```bash
adb devices -l
```

Expected at this state: empty list. If it lists the headset → unusual,
and it means we have a path. Either way paste the output back.

## 2 — If the 10-minute timeout advanced the screen

Don't touch the buttons yet. Re-do step 1 from the new screen. The USB
descriptor may change once OOBE progresses (different state = different
endpoints sometimes).

Also try the gaze cursor + volume-down from SETUP.md on whatever new UI
appeared. If you see a Continue / Skip / Accessibility option on screen
and the gaze cursor highlights it, this is the unblock.

## 3 — If the timeout did NOT advance and we need to power-cycle

Three boot modes to try, one at a time. Between each: hold power 15s to
force-shutdown, wait 5s, then attempt the next combo from off.

### 3a — Recovery mode

Hold **Power + Volume-DOWN** together for 10-15 seconds from off.
Release when the screen turns on. You should see a text menu (Boot
device / Recovery / Factory Reset / Power Off). Navigate with volume
buttons, select with power button — that's the documented physical-only
nav for this menu.

Run step 1 again here. Recovery mode often exposes a different USB
descriptor. Paste the output.

### 3b — Fastboot / bootloader mode

From off, hold **Power + Volume-UP**. (Less documented for Quest 3 than
recovery — may or may not work.) If it boots into a fastboot screen,
run:

```bash
fastboot devices
fastboot getvar all 2>&1 | head -50
```

`getvar all` dumps the bootloader's variable state including
unlock-eligibility, hardware revision, slot info. Paste the output.

### 3c — EDL (Qualcomm Emergency Download Mode)

From off, hold **Power + Volume-DOWN + Volume-UP** simultaneously for
~5 seconds. This is the deepest recovery mode — the device boots into a
ROM-level state where the screen stays black but USB exposes a Qualcomm
firehose interface (PID 0x9008). Run step 1 again. If you see PID
9008 we have a foothold I can work with even though Meta's bootloader
is signed.

## 4 — What I do with each fingerprint

- **Normal mode, no ADB advertised:** confirms what research said —
  no ADB pre-OOBE. We move to fingerprinting recovery/fastboot/EDL.
- **Fastboot mode visible:** I'll write specific fastboot commands
  based on the `getvar all` output. Some Quest revisions accept
  `fastboot oem` commands that toggle developer flags.
- **EDL mode visible:** I'll point you at the QuestEscape research
  tools (`oem_dump_partition.py`, BLE companion analysis) and we
  can read partitions to confirm firmware version + see what
  recovery paths the specific firmware allows.
- **Anything unexpected** (unknown PID, unlisted interfaces, MTP
  endpoint advertised): we research from there. Unexpected is
  information, not failure.

## Important boundaries

- I won't recommend flashing anything to the device. Even with an
  identified path, custom firmware on a signed bootloader risks
  bricking, and that's not a tradeoff to make for an ISP demo.
- Read-only diagnostics first. Any modifying action gets your
  explicit sign-off before I write it up.

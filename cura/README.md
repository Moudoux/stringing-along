# Ender 3 V2 — PETG profile

Printer: Creality Ender 3 V2, stock Bowden, 0.4 mm nozzle, Professional Firmware with probe (UBL).
Cura printer type: **Creality Ender-3 / Ender-3 v2**, material **Generic PETG**.

## Files

| File | What it is |
|---|---|
| `Ender3V2_PETG.curaprofile` | Import in Cura: Preferences → Configure Cura → Profiles → Import |
| `start_gcode_PETG.txt` | Paste in Cura: Preferences → Printers → Machine Settings → Start G-code |
| `petg_profile.py` | The settings list (edit values here, then re-run to rebuild the profile) |
| `slice_petg.sh` | Slice STLs to G-code from the command line with Cura's engine |
| `resolve_settings.py`, `slice.py`, `place_stl.py`, `finish_gcode.py` | Helpers used by `slice_petg.sh` |

## Settings and why

| Setting | Value | Why |
|---|---|---|
| Nozzle | 235 °C first layer, 230 °C after | PETG strings less on the cooler side |
| Bed | 80 °C first layer, 75 °C after | Good grip without over-bonding |
| Fan | 0% layer 1 → 40% by layer 3, up to 70% on short layers, 100% bridges | First-layer adhesion, then crisp details |
| Minimum layer time | 12 s (min speed 8 mm/s), **Lift Head off** | Lift Head let the hot nozzle ooze onto small parts |
| Retraction | 6 mm @ 45 mm/s, no Z-hop, outer-wall wipe 0.2 mm | Stock Bowden; reduces stringing |
| Travel | Combing "not in skin", avoid printed parts | Keeps strings inside the part |
| Speeds | 45 general, 25 outer wall, 40 inner wall, 35 top/bottom, 50 infill, 20 first layer, 150 travel; small features at 40% | |
| Layers / strength | 0.2 mm, 3 walls, 5 top / 4 bottom, 20% gyroid | |
| Adhesion | Skirt, 3 loops, 10 mm gap | Outline to check the first layer |
| Supports | Off | |

## Start G-code (what it does)

1. Bed to first-layer temperature while the nozzle waits at **150 °C** (PETG does not ooze while probing).
2. `G28`, then your `G29 P1` (probe mesh), `G29 A` (activate UBL), `C108` (close mesh viewer).
3. Heat nozzle to first-layer temperature, then draw the double purge line on the left edge (X 0.1/0.4, Y 20→200).

## Tips

- Dry PETG before important prints: 65 °C for 4–6 h. Wet PETG strings and looks foamy.
- Bed: the user's is a thin flexible plate made for PETG, not glass. On bare glass, wipe on a thin layer of glue stick so PETG releases.
- PETG likes a slightly less squished first layer than PLA: about +0.02–0.05 mm Z-offset.

## Re-slicing from the command line

```bash
cd /home/user/Applications/Solidcraft/projects/pi4-ssd-case   # any project folder works
bash ../../cura/slice_petg.sh tray-slide.stl pi-deck-slide.stl
```

Uses Cura 5.13's engine at `/opt/ultimaker-cura`. Each STL gets a `*_PETG.gcode` next to it with the real print time in the header.

## History

- 2026-10-27: first profile (235/240 °C, 5 mm retraction, Lift Head on).
- 2026-10-28: after a stringy, blobby peg test print: 230/235 °C, 6 mm @ 45 mm/s, wipe on, Lift Head off.

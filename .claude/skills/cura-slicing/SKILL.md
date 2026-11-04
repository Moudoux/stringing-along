---
name: cura-slicing
description: Slice STL files into G-code for the user's Ender 3 V2 with Cura's engine from the command line, using their tuned PETG profile, and change slicer settings for a particular print. Use this whenever the user wants something sliced, re-sliced or ready to print, asks about print time, filament, layer height, walls, infill, temperatures or retraction, or reports stringing, blobs or other print quality trouble, even if they don't mention Cura.
---

# Cura slicing for the Ender 3 V2

The printer is a Creality Ender 3 V2 with a stock Bowden extruder, a 0.4 mm nozzle and Professional Firmware with a probe (UBL). The usual material is PETG, on a thin flexible plate made for PETG. Cura slices for a 220 x 220 bed.

The shared setup lives in `/home/user/Applications/Solidcraft/cura/`, not in each project. Its `README.md` lists the settings and why each was chosen, and `petg_profile.py` is the source of truth for the values.

## Slice

Run this with bash from the project folder, with the STLs in `projects/<name>/`:

```bash
bash ../../cura/slice_petg.sh part.stl [more.stl ...]
```

Each STL gets a `part_PETG.gcode` next to it. The script centres the model and drops it to Z0, so the STL's own position doesn't matter. Orientation does: export the STL the way up it should print.

Then read the header and report the real figures:

```bash
head -4 part_PETG.gcode
```

`;TIME:` is in seconds. `;Filament used:` is in metres.

Check these before calling it done:

- It fits: within 220 x 220, leaving room for the skirt, which is 3 loops with a 10 mm gap.
- It printed `resolved 736 settings, 0 failed`, or a similar count with 0 failed.
- The time and filament look right for the part's size. `;TIME:6666` or `Filament used: 0m` means the final step didn't run.
- Small features are at least about 1.5 mm wide, as narrower ones don't hold their shape in PETG.

## Settings for one print

The profile is a good default, so leave it alone unless the job needs something else. For one-off changes, work on a copy so the shared profile stays the same for later jobs:

```bash
cp -r /home/user/Applications/Solidcraft/cura "$SCRATCH/cura-custom"
# edit SETTINGS in "$SCRATCH/cura-custom/petg_profile.py"
bash "$SCRATCH/cura-custom/slice_petg.sh" part.stl
```

Keep a note of the changes in the project, because re-slicing with the shared script later gives a different print. The Claude Monitor stand is an example: 0.16 mm layers, 2 walls and a 10% grid, where the shared script would give 0.2 mm, 3 walls and 20% gyroid. When re-slicing an old file, compare the new header with the old one.

The temperatures in the start G-code are filled in by `sed` inside `slice_petg.sh`, as 80 and 235, so changing first-layer temperatures means changing that too.

Change the shared `petg_profile.py` only when the user wants a new default. Then record why in the "History" section of `cura/README.md`.

## Current defaults

- Nozzle 235 C for the first layer, then 230. Bed 80, then 75.
- 0.2 mm layers, 3 walls, 5 top and 4 bottom, 20% gyroid, skirt, no supports.
- Retraction 6 mm at 45 mm/s, no Z-hop, combing "not in skin", outer-wall wipe 0.2 mm.
- Speeds: 45 general, 25 outer wall, 40 inner wall, 35 top and bottom, 50 infill, 20 first layer, 150 travel.
- Fan: 0% on layer 1, 40% by layer 3, up to 70% on short layers.
- Minimum layer time 12 s with **Lift Head off**, as lifting let the hot nozzle ooze onto small parts.
- Start G-code: bed to temperature with the nozzle at 150 so PETG doesn't ooze, `G28`, `G29 P1`, `G29 A`, `C108`, nozzle to temperature, then a double purge line at X0.1 and X0.4.

## If a print comes out badly

- **Stringing, or a foamy look:** usually wet PETG. Suggest drying at 65 C for 4 to 6 hours before changing settings.
- **Blobs on small parts:** check Lift Head is still off, and check the feature width above.
- **First layer:** PETG likes a little less squish than PLA, about +0.02 to 0.05 mm on the Z offset.
- Slight imperfections are normal for PETG on this printer, and the user knows that, so don't chase them unless asked.

## How the pipeline works

`slice_petg.sh` runs `petg_profile.py`, `resolve_settings.py`, `place_stl.py`, `slice.py` and `finish_gcode.py`. If it breaks, these are the causes already found:

- `/opt/ultimaker-cura/CuraEngine` has a relative ELF interpreter, so it runs as `/lib64/ld-linux-x86-64.so.2 /opt/ultimaker-cura/CuraEngine` with `LD_LIBRARY_PATH=/opt/ultimaker-cura` and `CURA_ENGINE_SEARCH_PATH` set to the resources' `definitions` and `extruders`.
- The CLI only reads `default_value`, never `value` formulas, so every setting has to be resolved first, or it dies with `no value given: roofing_layer_count`.
- `-s` and `key=value` must be separate arguments.
- The engine centres the bed itself, so models are centred on (0,0), not (117.5,117.5).
- The engine writes placeholders for `;TIME:` and `;Filament used:`, which `finish_gcode.py` replaces.
- The scripts need bash, not zsh, for `mapfile`, and the Python ones run with `python3 -I`.
- Files sliced before 2026-11-03 have a broken `G1 X0 Y{machine_depth}` in their end G-code, so re-slice those.

## Next step

To print the result, use the `tramline` skill. Don't start a print from here.

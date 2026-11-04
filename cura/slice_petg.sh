#!/usr/bin/env bash
# Slice STL files for the Ender 3 V2 with the PETG profile, using Cura's own engine.
# usage: ./slice_petg.sh part.stl [more.stl ...]   -> part_PETG.gcode next to each STL
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

python3 -I "$HERE/petg_profile.py" "$HERE" >/dev/null
sed -e 's/{material_bed_temperature_layer_0}/80/g' \
    -e 's/{material_print_temperature_layer_0}/235/g' \
    "$HERE/start_gcode_PETG.txt" > "$WORK/start.gcode"
python3 -I "$HERE/resolve_settings.py" "$HERE/Ender3V2_PETG.curaprofile" "$WORK/start.gcode" "$WORK/settings.nul" | head -1

for stl in "$@"; do
    out="${stl%.stl}_PETG.gcode"
    python3 -I "$HERE/place_stl.py" "$stl" "$WORK/placed.stl" 0 0 >/dev/null
    python3 -I "$HERE/slice.py" "$WORK/settings.nul" "$out" "$WORK/placed.stl" | grep -v '^exit 0$' || true
    python3 -I "$HERE/finish_gcode.py" "$out"
done

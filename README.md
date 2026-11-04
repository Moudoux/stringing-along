# Stringing Along

Design a part, slice it and print it on an Ender 3 V2, with Claude Code driving each step. The name comes from PETG, which strings along behind the nozzle whenever it gets the chance.

## What's here

| Folder | What it is |
|---|---|
| [`tramline/`](tramline/README.md) | A small Go print server for a Raspberry Pi. It switches the printer's plug, preheats, checks the bed's tram, and prints from the SD card or by streaming from the Pi. |
| [`cura/`](cura/README.md) | The tuned PETG profile, start G-code and scripts that slice STLs with Cura's engine from the command line. |
| `.claude/skills/` | Claude Code skills for this project: `solidcraft-design`, `cura-slicing` and `tramline`. |

## How it fits together

1. **Design** in SolidCraft, a parametric CAD app, through its MCP server. Each design lives in `projects/<name>/`.
2. **Slice** the STL:

   ```bash
   cd projects/<name>
   bash ../../cura/slice_petg.sh part.stl
   ```

   This writes `part_PETG.gcode` next to the STL.
3. **Print** with Tramline. It always checks tram first, and asks for confirmation that the bed is clear:

   ```bash
   cd tramline
   dist/tramline-linux-amd64 upload part_PETG.gcode
   dist/tramline-linux-amd64 print part_PETG.gcode --bed-clear
   ```

## Not in this repository

These stay on the local machine, see [`.gitignore`](.gitignore):

- The SolidCraft binaries (`solidcraft`, `solidcraft-cli`, `solvecraft-cli`).
- `projects/`, the designs, STLs and G-code.
- `tramline/dist/`, `tramline/.cache/` and `tramline/test-logs/`. The Tramline README refers to files in `test-logs/`, and those only exist locally.

Tramline's keys stay out too, in `~/.config/tramline/` on the client and `/var/lib/tramline/` on the Pi.

## Requirements

- **Slicing:** Cura 5.13 at `/opt/ultimaker-cura`, plus Python 3 and bash.
- **Building Tramline:** Docker. Build only with `tramline/build.sh`, as it uses the Go standard library inside a container and needs no Go on the host.
- **Printing:** an Ender 3 V2 running Professional Firmware with a probe, a Raspberry Pi, and a Hue plug.

## Status

Tramline's stage 10 passed on the real printer on 2026-11-04, including a 63-minute streamed print. See the status table at the top of the [Tramline README](tramline/README.md) for what's proven on the printer and what has only run on the simulator.

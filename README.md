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
3. **Print** with Tramline. It turns the printer on, always checks tram first, needs your confirmation that the bed is clear, and turns the printer off afterwards. See [Tramline's README](tramline/README.md#printing) for printing from the card instead:

   ```bash
   cd tramline
   dist/tramline-linux-amd64 upload part_PETG.gcode
   dist/tramline-linux-amd64 print part_PETG.gcode --from pi --bed-clear
   ```

   On a Mac the client is `dist/tramline-darwin-arm64`.

## Not in this repository

These stay on the local machine, see [`.gitignore`](.gitignore):

- The SolidCraft binaries on Linux (`solidcraft`, `solidcraft-cli`, `solvecraft-cli`). On a Mac, SolidCraft is an app in `/Applications`.
- `projects/`, the designs, STLs and G-code.
- `tramline/dist/`, `tramline/.cache/` and `tramline/test-logs/`. Tramline's engineering notes refer to files in `test-logs/`, and those only exist locally.

Tramline's keys stay out too, in `~/.config/tramline/` on the client and `/var/lib/tramline/` on the Pi. See [Setting up a new computer](#setting-up-a-new-computer) for how to replace what's missing.

## Setting up a new computer

Claude Code picks up the skills by itself when started in this folder, but they rely on things git doesn't carry. Run these from the repository root. It works on Linux and macOS, and the steps say where they differ.

```bash
git clone git@github.com:Moudoux/stringing-along.git
cd stringing-along
```

### SolidCraft, for designing

1. Install it:
   - **macOS:** install the SolidCraft app in `/Applications`.
   - **Linux:** copy the binaries `solidcraft`, `solidcraft-cli` and `solvecraft-cli` into the repository root from a computer that has them.
2. Connect it to Claude Code:

   ```bash
   # macOS
   claude mcp add solidcraft -- /Applications/SolidCraft.app/Contents/MacOS/solidcraft-cli mcp
   # Linux
   claude mcp add solidcraft -- "$PWD/solidcraft-cli" mcp
   ```

3. Copy `projects/` across too, if you want the existing designs.

### Cura, for slicing

Install Cura 5.13, as the scripts run the engine inside it and expect it in one place. These are the only paths that aren't relative:

- **macOS:** `/Applications/UltiMaker Cura.app`, the usual place. Set `CURA_APP` if it's somewhere else. Cura has no command of its own to put on the PATH, and doesn't need one.
- **Linux:** `/opt/ultimaker-cura`.

Older versions aren't safe to assume: 5.7.2 heats the nozzle to 235 C before the start G-code runs, so PETG oozes while probing. You also need Python 3 and bash.

### Tramline, for printing

The server is already on the Pi, so a new computer only needs a client. It must be on the same network as the Pi, and needs Docker to build.

1. Build the client, which writes to `tramline/dist/`. Only use this script, as it needs no Go on the host:

   ```bash
   tramline/build.sh
   ```

2. Create this computer's key, in `~/.config/tramline/` on Linux and macOS alike. It stays on this computer, and the command prints only the public fingerprint:

   ```bash
   tramline/dist/tramline-linux-amd64 keygen    # on a Mac: tramline/dist/tramline-darwin-arm64
   ```

3. On the Pi, get the server's fingerprint and allow the new client:

   ```bash
   sudo -u tramline tramline fingerprint
   sudo -u tramline tramline allow <client-fingerprint> --name <computer-name>
   ```

4. Back on the new computer, log in and check it works:

   ```bash
   tramline/dist/tramline-linux-amd64 login https://raspberrypi:8726 <server-fingerprint>
   tramline/dist/tramline-linux-amd64 status
   ```

5. Add an SSH host called `raspberrypi` to `~/.ssh/config`, using user `pi`. Saving logs and `deploy/install.sh` both use it. The client itself doesn't need SSH.

### Claude's rules and notes

These stay on the original computer, in `~/.claude/`:

- **Global rules:** `~/.claude/CLAUDE.md` holds the rules on never reading secrets, never running sudo, and handing off to a new session. The `tramline` skill repeats the first two, but only while that skill is in use, so copy the file across to keep them in every session.
- **Memory:** Claude's notes aren't copied, so it starts without them. The READMEs and skills hold most of what matters.

### Setting up a new Pi

This is only needed if the Pi itself is replaced. See Security, Install and updates, Config and the test plan in [Tramline's engineering notes](tramline/ENGINEERING-NOTES.md). In short: `deploy/install.sh <ssh-host>`, `tramline init --ip <address>` and `tramline hue pair` on the Pi, then fill in `/etc/tramline/config.json` with the plug's UUID from `tramline hue plugs`. These need sudo on the Pi, and the printer needs the USB cable with its +5V wire cut, see The USB cable in that README.

## Status

Tramline's stage 10 passed on the real printer on 2026-11-04, including a 63-minute streamed print. See the status table at the top of [Tramline's engineering notes](tramline/ENGINEERING-NOTES.md) for what's proven on the printer and what has only run on the simulator.

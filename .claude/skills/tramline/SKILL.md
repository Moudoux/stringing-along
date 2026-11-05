---
name: tramline
description: Use the user's Tramline print server to run their Ender 3 V2 from a Raspberry Pi, covering printer status, plug power, preheat and cool, tram checks, uploading G-code, copying to the SD card, starting, scheduling, watching, cancelling and reporting prints, and testing or changing Tramline itself. Use this whenever the user wants something printed or asks about the printer, the bed, a running print, the plug or the Pi print server, even if they don't say "Tramline".
---

# Tramline

Tramline is the user's small Go print server. It runs on their Raspberry Pi 4 as the `tramline` systemd service, on port 8726 at `raspberrypi`, and talks to the printer over USB and to a Hue plug. That name is the LAN address at home. The server follows the addresses of `eth0` and `tailscale0` rather than a fixed one (see the notes' "Listening by interface").

Paths here are relative to the repository root, the folder holding `.claude/`. Run commands from there, or adjust the path.

- Client: `tramline/dist/tramline-linux-amd64` on the Linux desktop, or `tramline/dist/tramline-darwin-arm64` on the Mac. Work on either, and use the one for the machine you're on. `tramline/build.sh` builds it if it's missing. Run `help` on it for the full command list.
- Source of truth: the engineering notes in `tramline/notes/`, with `tramline/README.md` as the short overview. Read `notes/README.md` (the index, with the status table and which file holds each section) and `notes/next-session.md` before working on Tramline itself, then only the files for the topic in hand. Treat them as newer than this skill where they differ. Paths in the notes are relative to `tramline/`.
- Web page: `tramline web` opens a read-only status and 3D print view at `http://raspberrypi:8726/`, and `web --url` only shows the address. It needs no certificate and doesn't touch the printer. Its head position is worked out from the file position, not measured, and from the card that's only read about every 30 seconds.
- GUI: `tramline gui` is for the user: a browser GUI on their computer with everything the commands do, served on `127.0.0.1` with a one-time sign-in link. Claude keeps using the commands. Don't run `tramline gui --no-open` to read its link, as that's only shown in a terminal on purpose.
- Clocks: the Pi is on GMT, and this machine may be an hour ahead. Say which one a time is in.

## Rules that always apply

- **Ask before anything that touches the printer,** including switching the plug, heating, moving, tram checks, copies and prints. Say what it will do and how long it should take. Approval covers only what was described, so ask again next time. `status`, `files` and `schedule list` are read-only and need no approval.
- **Ask the user to confirm the bed is clear before every print and tram check.** There's no camera, and a finished print may still be on the bed. Only pass `--bed-clear` after they confirm it for this run.
- **Never read secrets,** here or on the Pi: `~/.config/tramline/client.key`, and `hue.key` and `tls.key` in `/var/lib/tramline/`. Running the client is fine, as it uses them without printing them.
- **Never run sudo on the Pi,** and don't use Docker to get around it. Give the user the exact command to run: `deploy/install.sh raspberrypi`, restarting the service, or editing `/etc/tramline/config.json`. Ask before any lasting change on the Pi and list what it changes.
- **Don't restart or install during a stream,** as a stream can't survive it.
- **Be plain about what has only run on the simulator.** The engineering notes' table and "Not proven on the real printer" list say which is which.

## Printing a file

1. Run `status`. Stop if a job is already running or waiting.
2. Check `files` for the name. If this is a new or changed file, check its slicer time in the header (`;TIME:`, in seconds).
3. Ask the user, in one message: can you confirm the bed is clear, and may I start? Give the file, the route, the slicer time, and about 7 more minutes for heating, the tram check and the mesh. Say the printer turns off by itself at the end.
4. Upload if needed: `upload <path>`, which only saves on the Pi. Choose the route, see below: `--from pi`, or for `--from sd` run `copy <file>` first, with the printer on. Copies run at about 14 KB/s, so over about 4 MB is better from the Pi.
5. Start: `print <file> --from pi|sd --bed-clear`. It switches the plug on if needed, and returns once the job is in `heating`, which may take 20 seconds from off. When the job ends, however it ended, the server turns the heaters off and cuts the plug once the nozzle is below 50°C.
6. Watch with `status` in the background, every 10 seconds or so, saved to a log in `tramline/test-logs/` if this is a test. When it's a long print, tell the user how to check back rather than holding the session.
7. When the job ends, report from `status` and the server log, as below.

The job's states go `heating`, `soaking`, `checking`, `starting`, `running`, then `finished`, `cancelled` or `failed`. A failed check goes to `adjusting`. The tram check made when scheduling ends as `scheduled` instead of starting the file.

### A failed tram check

The limit is 0.05 mm, and this bed sits close to it, at 0.029 to 0.055 mm. A fail isn't an error: nothing has started, and the head is parked, and if they `cancel` from here the printer turns off once cool. Tell the user the corner, the direction and the numbers that `status` gives, wait for them to say it's adjusted, then run `print --continue`, which checks again. There's no override, and the user doesn't want one.

### Scheduling a print

For "schedule this print at 6 am tomorrow":

1. Run `date` here, and work out the full date and time in this machine's timezone. The Pi's clock doesn't matter, as the client sends an absolute time.
2. Run `status` and `files`, and upload the file if needed, as for a print. It has to be on the Pi first.
3. Ask, in one message: can you confirm the bed is clear and will stay clear, and may I start? Read the date back in full, such as "Friday 6 November at 06:00 GMT". Say that it heats and checks tram now, about 5 minutes, then powers off, then at that time powers on, checks again and prints unattended, and powers off afterwards, as every print does.
4. Run `schedule <file> --from pi|sd --at "YYYY-MM-DD HH:MM" --bed-clear`. Choose the route as for a print, and `--from sd` needs its `copy` first. Watch `status`, as for a print. A failed first check is handled the same way, with `print --continue`.
5. Report once `schedule list` says `waiting` and `status` shows the plug off.

The time must be 15 minutes to 30 days away. `schedule list` shows what's waiting and how recent ones ended, with the reason and readings, and `status` and the web page show them too. `schedule cancel <id>` needs no bed check, but ask first if the job is heating or moving. A print that's already running is stopped with `cancel`.

- **Tell the user:** a failed check at the scheduled time cancels the print with no retry, and nothing notifies them, so they should check `schedule list`.
- **Only the most recent bed-clear counts:** if any print starts after a schedule was made, that schedule cancels itself without moving. So a second scheduled print only runs if it's scheduled after the first's part has been removed. Warn the user of that when they queue more than one, and before starting a normal print while one is waiting.
- **Files:** `files rm` and uploads over a file are refused while a schedule needs it.
- **Over 15 minutes late,** because the server was down, it's `missed` and doesn't start.
- **Don't install a new build close to a scheduled time,** or while one is printing by stream.

### Which route a file takes

- `print` and `schedule` always take `--from pi` or `--from sd`, and neither falls back to the other.
- `--from pi` streams one line at a time, even if the file is verified on the card.
- `--from sd` is refused unless the file has a verified copy on the card, from `copy`.
- `copy` skips a file already verified on the card, so testing a copy also needs a new name.

### Stopping a print

| | From the card | Streaming from the Pi |
|---|---|---|
| `cancel` | Heaters off, then `G28XY`, so the head crosses the part | Lifts 5 mm, heaters off, no homing |
| LCD's Stop | The firmware's own, and Tramline leaves it alone. Not tested here | Same as `cancel`, tested |
| LCD's Pause | Not tested here | **Not supported, tell the user not to press it.** Over 5 minutes paused, `M85` kills the print |
| `estop` | `M112`, then cuts the plug. Tested on a cold print only | The same, simulator only |

`cool` also cancels a running print. Only use `estop` when the user asks or something is clearly unsafe.

After a Tramline cancel of a stream, the LCD says print done at 100%. Trust `tramline status`, not that screen.

### Power

Every print Tramline starts ends with the plug cut once the nozzle is below 50 C, so there's rarely a need to run `power off`. `print` and `schedule` switch it on themselves, and `copy`, `preheat` and `tram` still need `power on` first. That cut waits if the link is down, and stops for good if someone heats, trams, copies or runs `power on` first. Prints from the LCD don't get it. `power off` refuses until the nozzle is below 50 C, or during a print. An automatic permission check has blocked Claude's `power` command before. If that happens, don't work around it: ask the user to run the command or switch the plug.

## Traps

- **`M27` can take minutes to answer during a print.** Never put a short limit on it, and never retry it while one is waiting.
- **`files rm` also deletes the Pi's copy,** not only the card's. Look before deleting.
- **A "cold" file isn't cold:** the tram check before it still heats to 80/150 and moves the head, and the heaters stay on after a file that doesn't turn them off, until `tramline cool`.
- **The Pi's logs don't survive a reboot,** so save them soon after a test.

## Reporting a print or test

Save the server log first, using the start time from the job:

```bash
ssh raspberrypi "journalctl -u tramline --since 'YYYY-MM-DD HH:MM:SS' --no-pager -o short-precise" > tramline/test-logs/<date-name>/<test>/server.log
```

Kernel messages come from `ssh raspberrypi "journalctl -k --since '...' --no-pager"`, no sudo needed. During power tests, capture them live to a local file with `ssh raspberrypi 'journalctl -kf -o short-precise'`, and don't stop that with `pkill -f`.

Then report the outcome, the print time against the slicer's, and:

- `sd: printer asked for line`: every real resend, with its in-flight bytes and timing.
- `stream: no ok for 5s`: nudges. They're expected at `G28`, `G29`, `M109` and the end's long move. During printing they'd be worth a look.
- `stream: ok times`: mean, longest and planner free. Near 0 free means the planner stayed full. Empty during moves would mean the link starved it.
- Errors, kernel messages and `stream: printer said` lines. Replies from the printer are occasionally damaged, and a `planner free` over 15 is one of those rather than a real figure.

Ask the user how the part came out and what the LCD showed, as Tramline can't see either. Record results in the engineering notes, including its status line, table and "Next session".

## Changing Tramline

- Build only with `./build.sh`, which runs in a container, so Docker has to be running (`open -a Docker` on a Mac). Don't use Go on the host. Tests only run on Linux, in that container; macOS gets `go vet` and a build. Macs build the client and `serve --sim`, and only Linux can open a real serial port.
- gofmt runs inside `build.sh`, so format by hand.
- Standard library only.
- The engineering notes are the record. Put new findings in the file for their topic, or a new file, and keep `notes/README.md` in step: its file list, section index and status table. The README stays a short overview, so only change it when how Tramline is used changes. The code is in the `stringing-along` git repository, and `test-logs/` and `dist/` aren't committed. Commit or push only when the user asks.
- The user installs new builds with `deploy/install.sh raspberrypi`. Check that `status` shows the expected server version afterwards.
- `go test` doesn't run the browser code in `internal/webui/` (the read-only page in `page/`, the GUI in `gui/`, the shared 3D view in `shared/`), so check a change to it in a browser. `./sim-gui.sh [--fail-tram] [file ...]` runs `tramline gui` against a simulated printer the same way, see the Desktop GUI notes, which also describe driving headless Chrome to check it. `./sim-web.sh [--sd] [--minutes <n>] [--no-open] [--lan] <file>` runs a print on a simulated printer on this machine, with a throwaway login, and touches neither the Pi nor the printer. See "Trying it on the simulator" in the engineering notes.
- The simulator differs from the real firmware in known ways, listed under "Streaming design" in the engineering notes, so a pass there doesn't settle anything about timing or the receive buffer.

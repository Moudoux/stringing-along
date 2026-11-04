---
name: tramline
description: Use the user's Tramline print server to run their Ender 3 V2 from a Raspberry Pi, covering printer status, plug power, preheat and cool, tram checks, uploading G-code, copying to the SD card, starting, watching, cancelling and reporting prints, and testing or changing Tramline itself. Use this whenever the user wants something printed or asks about the printer, the bed, a running print, the plug or the Pi print server, even if they don't say "Tramline".
---

# Tramline

Tramline is the user's small Go print server. It runs on their Raspberry Pi 4 at 192.168.1.121:8726 as the `tramline` systemd service, and talks to the printer over USB and to a Hue plug.

- Client: `/home/user/Applications/Solidcraft/tramline/dist/tramline-linux-amd64`. Run `help` on it for the full command list.
- Source of truth: `/home/user/Applications/Solidcraft/tramline/README.md`. Read its "Next session" section before working on Tramline itself, and treat it as newer than this skill where they differ.
- Clocks: the Pi is on GMT, and this machine may be an hour ahead. Say which one a time is in.

## Rules that always apply

- **Ask before anything that touches the printer,** including switching the plug, heating, moving, tram checks, copies and prints. Say what it will do and how long it should take. Approval covers only what was described, so ask again next time. `status` and `files` are read-only and need no approval.
- **Ask the user to confirm the bed is clear before every print and tram check.** There's no camera, and a finished print may still be on the bed. Only pass `--bed-clear` after they confirm it for this run.
- **Never read secrets,** here or on the Pi: `~/.config/tramline/client.key`, and `hue.key` and `tls.key` in `/var/lib/tramline/`. Running the client is fine, as it uses them without printing them.
- **Never run sudo on the Pi,** and don't use Docker to get around it. Give the user the exact command to run: `deploy/install.sh raspberrypi`, restarting the service, or editing `/etc/tramline/config.json`. Ask before any lasting change on the Pi and list what it changes.
- **Don't restart or install during a stream,** as a stream can't survive it.
- **Be plain about what has only run on the simulator.** The README's table and "Not proven on the real printer" list say which is which.

## Printing a file

1. Run `status`. Stop if a job is already running or waiting.
2. Check `files` for the name. If this is a new or changed file, check its slicer time in the header (`;TIME:`, in seconds).
3. Ask the user, in one message: can you confirm the bed is clear, and may I start? Give the file, the slicer time, and about 7 more minutes for heating, the tram check and the mesh.
4. Upload if needed: `upload <file>`. The default `mode auto` copies to the card unless that would take over 5 minutes at about 14 KB/s, so files over about 4 MB stay on the Pi and stream.
5. Start: `print <name> --bed-clear`. It returns straight away with the job in `heating`.
6. Watch with `status` in the background, every 10 seconds or so, saved to a log in `test-logs/` if this is a test. When it's a long print, tell the user how to check back rather than holding the session.
7. When the job ends, report from `status` and the server log, as below.

The job's states go `heating`, `soaking`, `checking`, `starting`, `running`, then `finished`, `cancelled` or `failed`. A failed check goes to `adjusting`.

### A failed tram check

The limit is 0.05 mm, and this bed sits close to it, at 0.029 to 0.055 mm. A fail isn't an error: nothing has started, and the head is parked. Tell the user the corner, the direction and the numbers that `status` gives, wait for them to say it's adjusted, then run `print --continue`, which checks again. There's no override, and the user doesn't want one.

### Which route a file takes

- A file verified on the card prints from the card, even under `mode stream`.
- Anything else streams from the Pi, one line at a time.
- To stream a file already verified on the card, use a new name uploaded with `--pi-only`.
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

`power off` refuses until the nozzle is below 50 C, or during a print. An automatic permission check has blocked Claude's `power` command before. If that happens, don't work around it: ask the user to run the command or switch the plug.

## Traps

- **`M27` can take minutes to answer during a print.** Never put a short limit on it, and never retry it while one is waiting.
- **`files rm` also deletes the Pi's copy,** not only the card's. Look before deleting.
- **A "cold" file isn't cold:** the tram check before it still heats to 80/150 and moves the head, and the heaters stay on after a file that doesn't turn them off, until `tramline cool`.
- **The Pi's logs don't survive a reboot,** so save them soon after a test.

## Reporting a print or test

Save the server log first, using the start time from the job:

```bash
ssh raspberrypi "journalctl -u tramline --since 'YYYY-MM-DD HH:MM:SS' --no-pager -o short-precise" > test-logs/<date-name>/<test>/server.log
```

Kernel messages come from `ssh raspberrypi "journalctl -k --since '...' --no-pager"`, no sudo needed. During power tests, capture them live to a local file with `ssh raspberrypi 'journalctl -kf -o short-precise'`, and don't stop that with `pkill -f`.

Then report the outcome, the print time against the slicer's, and:

- `sd: printer asked for line`: every real resend, with its in-flight bytes and timing.
- `stream: no ok for 5s`: nudges. They're expected at `G28`, `G29`, `M109` and the end's long move. During printing they'd be worth a look.
- `stream: ok times`: mean, longest and planner free. Near 0 free means the planner stayed full. Empty during moves would mean the link starved it.
- Errors, kernel messages and `stream: printer said` lines. Replies from the printer are occasionally damaged, and a `planner free` over 15 is one of those rather than a real figure.

Ask the user how the part came out and what the LCD showed, as Tramline can't see either. Record results in the README, including its status line, table and "Next session".

## Changing Tramline

- Build only with `./build.sh`, which runs in a container. Don't use Go on the host.
- gofmt runs inside `build.sh`, so format by hand.
- Standard library only.
- The README is the record. The code is in the `stringing-along` git repository, and `test-logs/` and `dist/` aren't committed. Commit or push only when the user asks.
- The user installs new builds with `deploy/install.sh raspberrypi`. Check that `status` shows the expected server version afterwards.
- The simulator differs from the real firmware in known ways, listed under "Streaming design" in the README, so a pass there doesn't settle anything about timing or the receive buffer.

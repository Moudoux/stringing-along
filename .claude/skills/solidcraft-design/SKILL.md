---
name: solidcraft-design
description: Design parts for 3D printing in the user's SolidCraft CAD app on this machine, covering where projects go, starting the app so the user can watch, exporting, known traps, and design rules that suit their PETG prints on an Ender 3 V2. Use this alongside SolidCraft's own modelling guide whenever the user wants a part, case, enclosure, bracket, stand or other model designed or changed, or mentions SolidCraft, a .scd or .sc file, or making an STL.
---

# SolidCraft design on this machine

SolidCraft has its own modelling guide built in, which covers command shapes, ids, plane axes and the workflow. This skill adds what's particular to this machine and printer.

## Start

1. **Start the app first,** so the user can watch the model appear. On macOS, run `open -a SolidCraft`. On Linux, run `./solidcraft` from the repository root in the background. Skip this if it's already running. The MCP server stays headless once a session has work in it, so this has to come before any design call. Tell the user if the session is still headless.
2. **Read the built-in guide:** `skill_reference {"skill":"solidcraft-modeling"}` for the reference, and `file: "SKILL.md"` for the workflow. There are also `solidcraft-mechanisms`, `solidcraft-editing` and `solidcraft-checking`.
3. **Run `inspect_design {"measure":false,"sketches":false}`** before `new_design` or `open`, and ask first if there's work in it, because both discard unsaved work.

If the MCP stays headless with the app running, `current.port` and `current.pid` in the control folder may point at a dead instance, such as a second launch that exited. Rewrite them to the live instance. The folder is `~/Library/Application Support/SolidCraft/control/` on macOS, where `lsof -nP -iTCP -sTCP:LISTEN` shows the instance, and `~/.local/share/solidcraft/control/` on Linux, where `ss -ltnp` does.

## Where files go

Each project has its own folder, `projects/<name>/` under the repository root, holding its design, STLs and G-code. Never leave them in the home folder.

`save` and `export` may refuse paths outside their allowed folders, which the error names: the recovery folder under the SolidCraft folder above and a `solidcraft-mcp-...` temporary folder that changes when the server restarts. If so, write there and `cp` the file into the project folder.

## Designing for this printer

The target is a 220 x 220 bed, a 0.4 mm nozzle, 0.2 mm layers and PETG.

- **Features need width.** Anything under about 1.5 mm, or 3 to 4 extrusion widths, can't hold its shape in PETG, and tuning won't fix it. Split snap pegs about 3 mm wide, with 1.1 mm halves, came out as blobs with strings.
- **Clips and snaps:** make flexing parts at least 1.2 mm thick, several mm wide and long enough to keep strain at about 2% or less. Prefer solid locating pins and edge tabs to split pegs.
- **Use official drawings for real components,** such as datasheets.raspberrypi.com, rather than remembering where things are. Look up and state the source.
- **Offer a small fit test before a long print,** when a part has to fit something real. Don't assume the user wants one printed, though.
- **Think about the way up it will print.** Export a separate print-oriented STL when that differs from the design's orientation, as with `case-top-print.stl`.
- Check the parts fit the bed with room for the skirt, about 12 mm a side.

## Traps found here

These come from earlier versions of SolidCraft, so if one no longer applies, carry on. The built-in reference has newer ones.

- **Cuts between curved faces:** a cut whose start face is coplanar with a curved-face body, or that ends exactly tangent to a slot wall, can fail with `exact fallback ... planar faces only`. Start the sketch 0.5 to 1 mm outside the material and overshoot the depth slightly.
- **Fillets** fail when the blend would eat into a neighbouring feature, such as rails at a corner, so fillet only clear corners.
- **`solid.pattern.circular` of a join-extrude** clipped its copies to the existing body's height, and left some floating. Draw the rotated copies in one sketch instead, and work out the coordinates in Python.
- **`sketch.circle.center`'s radius** must be a number, not a parameter expression.
- **The XZ sketch plane** maps sketch y to world -Z.
- **After an STL export,** check that the mesh has the number of connected components you expect, as a separate shell is easy to miss in a screenshot.

## Finish

Save the design, and export `.step` if it might be needed elsewhere, as well as an STL for printing. Verify with `measure` against numbers you worked out, as the built-in guide says, then show the user a screenshot.

## Next step

Use the `cura-slicing` skill to slice the STL, and then the `tramline` skill to print it. The user decides when to print.

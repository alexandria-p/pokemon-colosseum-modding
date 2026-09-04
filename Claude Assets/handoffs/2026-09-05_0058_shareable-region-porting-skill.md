# Handoff — 2026-09-05 00:58

**Change:** Built a shareable skill packaging the PAL↔US porting method, for
someone else to load into their own Claude. Also hardened `map_convert.py` map
discovery, which the sharing exposed as fragile.

## Files

| Path | What |
|---|---|
| `Claude Output/colosseum-region-porting.skill` | **the shareable artifact** — hand this over |
| `Claude Output/skill/colosseum-region-porting/SKILL.md` | its source |
| `Claude Output/skill/colosseum-region-porting/scripts/` | `map_convert.py`, `ppc.py` (bundled, genericised) |
| `Claude Assets/tools/map_convert.py` | improved map discovery |

10.5 KB, three files. Self-contained: it names the external sources
(StarsMmd's symbol maps, Ralf's tables and code archives) rather than assuming
our workspace.

## What it contains

Everything actually used to port codes in this project:

* both save-base pointers (`US 0x8047ADB8` / `PAL 0x804C8268`), how the US one
  was derived three ways, and the SDA bases
* the size-sequence alignment method, the confidence tiers, and the
  false-negative region below `0x80006000` with the named-symbol fallback
* why data addresses cannot be extrapolated, with the four observed deltas
  showing they are not constant, and the four lookup routes
* the region-independent save and record layouts — the reason ports are cheap
* Gecko C2 rules: re-emitting the overwritten instruction, line counts,
  PC-relative branches, LR, the `ori` vs `lwz` sign-extension trap, the
  build-fingerprint guard idiom
* the five-step verification workflow and how to read a dump
* both regions' anti-AR NOP sets and the Dolphin requirements
* a full worked example (the original PAL shiny code → US)
* a table of 15 confirmed address pairs
* the Colosseum-specific gotcha that a shadow's PID is rolled once and persisted

## The fix the sharing exposed

`map_convert.py` searched for the maps by walking upward **from the script's own
location**. Fine in our workspace, useless for anyone who puts the skill in one
place and their maps in another — which is the normal case for a recipient.

Now it looks in order: `$COLO_MAPS_DIR`, then upward from the **working
directory**, then upward from the script. Tested both ways: bundled copy run
from a project root with the maps above it, and the workspace copy unchanged.

Worth noting as a general point — a tool that works because of where *we* keep
things is not portable, and packaging it for someone else is what surfaces that.

## Not included, deliberately

The MRAM dumps (large, and contain a personal save), the workspace notes and
handoffs, and the codes themselves. The skill teaches the method; the codes are
separate deliverables if they want them.

## Caveat carried into the skill

The confidence tiers are reproduced as written, including that short alignment
runs remain unproven and the sub-`0x80006000` blind spot is real. A recipient
inheriting only the successes would otherwise over-trust the tool.

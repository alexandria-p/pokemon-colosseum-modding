# Handoff — 2026-09-04 21:01

**Change:** Moved the `.skill` file to the project root (it is a source input,
not chat-generated), and produced a corrected replacement for the **installed**
`pokemon-colosseum` skill.

## Files

| Path | What |
|---|---|
| `pokemon-colosseum.skill` (root) | the ORIGINAL, unchanged, moved out of `Claude Assets\` |
| `Claude Output/skill/pokemon-colosseum/SKILL.md` | the corrected source |
| `Claude Output/pokemon-colosseum.skill` | corrected, packaged for install |
| `Claude Output/PROJECT_NOTES.md` | §1 layout + a warning about the live skill's errors |

## Why this mattered more than the file's location

The `.skill` is a copy of a skill that is **installed and live** — it appears in
the available-skills list. Its errors are therefore not inert: any future session
that loads it inherits them.

## What was wrong, and is now fixed

| Was | Is |
|---|---|
| party/box stride `0x140` (slot 2 PID `+0x1E4`, slot 3 `+0x324`…) | **`0x138`** (slot 2 `+0x1DC`, slot 3 `+0x314`) |
| "Shadow Registry" at `+0x82B0`, 48 entries | **Strategy Memo** at `+0x82AC`, 386 entries, count at `+0x82A8` |
| entries have "PID1" and "PID2" | `+0x04` is the owner's **OT ID dword**; only `+0x08` is a PID |
| "all 48 Shadow PIDs pre-generated" | all **386** memo slots carry a pre-seeded PID; whether it *becomes* the assigned PID is unresolved |
| Gecko C2 troubleshooting: "try line counts 00000008/9/A" | count the 8-byte lines; guessing the count is not a debugging step |
| PAL only | **both regions**, addresses given as US / PAL throughout |

Kept as-is because the dumps confirmed them: the breakpoint list, the PID event
trace, the MRAM-dump-instead-of-value-search rule, the fresh-dump rule, and the
PkHeX procedure.

## What was added

* US addresses beside every PAL one, and the region-conversion rules (§11).
* The unified Pokémon record layout — save entry and both battle arrays are one
  record type.
* The two in-battle arrays and `arrayA = arrayB − 0xAEC`.
* Both regions' anti-AR NOP sets.
* Gecko C2 rules that actually bite: re-emitting the overwritten instruction,
  not clobbering `LR`, checking what runs between a caller-side hook and the
  call, `ori` zero-extends vs `lwz` sign-extends, and the build-fingerprint
  guard idiom.
* **Display shiny vs actual shiny** — three of the four common write-patches are
  display-only; US `8012442C` is the one that changes the rolled PID.
* The warning that species numbers are Gen-3 internal indices, not dex numbers.
* The heap battle object signature, with the explicit warning never to hardcode
  its address.

## Installing

`Claude Output/pokemon-colosseum.skill` is a zip containing
`pokemon-colosseum/SKILL.md`, the same structure as the original, and keeps the
same `name: pokemon-colosseum` so it replaces the installed copy rather than
sitting alongside it. The `description` was broadened from "(PAL) version" to
cover both regions, so it will trigger on US work too.

5259 bytes vs the original's 2945. UTF-8 verified.

The original at the project root is left untouched for comparison.

## Still open

Unchanged: Strategy Memo pre-seed causality, the u3 scratch struct's constant
`5`, the `saveBase + 0xAF4` money/TID collision.

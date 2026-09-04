# Handoff — 2026-09-04 20:41

**Change:** Directory restructure absorbed. Fixed a tool the move broke, updated
every path reference, and mined the newly added source material.

## New structure and the placement rule

```
Claude Assets\      working material for Claude  (handoffs, tools, the .skill playbook)
Claude Output\      deliverables                 (PROJECT_NOTES, PID_LIFECYCLE, codes\)
Pokemon Colosseum - Offsets and Maps\   maps + WiiRD tables + a new AR table
Existing Gecko and AR codes by Ralf\    ~460-476 published codes per file, US/PAL x Gecko/AR
GoD-Tool by Stars\                      (renamed)
Original Attempt & Knowledge - PAL Gecko shiny hunting.zip   (new)
```

**Rule recorded in `Claude Output/PROJECT_NOTES.md` §1:** anything generated in a
chat session goes in `Claude Assets\` or `Claude Output\`. The source folders —
maps, offset tables, Ralf's archive, GoD-Tool, the research zip — are inputs and
are not written to.

## The move broke `map_convert.py` — fixed

It had the project root and both map filenames hardcoded relative to its own
location, so relocating it to `Claude Assets\tools\` made every invocation die
with `FileNotFoundError`.

Rewritten to locate the maps itself: it walks upward from the script looking for
files whose names contain `GC6P01` / `GC6E01`. Tested from the project root and
from `Claude Output/codes/` — works from any working directory, and will survive
the next reorganisation.

Note the path now contains spaces, so it needs quoting:

```bash
python "Claude Assets/tools/map_convert.py" 0x80128584
```

All path references in `PROJECT_NOTES.md`, `PID_LIFECYCLE.md` and the three code
files were updated to the new locations.

## New source material — Ralf's code archive is the valuable one

Four files, ~460-476 codes each: US/PAL x Gecko/AR. Added to
`PROJECT_NOTES.md` §6 as **lookup route 0b**, because the same code is published
for both regions — **finding one in both files hands you the PAL→US mapping of
every address it touches, for free.** It is also the fastest way to check
whether something already exists before building it.

There is **no force-shadow-shiny code in the archive** — ours remains original.

### What it confirms

| Ralf code | Writes | Confirms |
|---|---|---|
| "Shiny Nation" | our all-new-shiny code, exactly | the conversion, third independent source |
| "Female Nation" | `04124424 3B200001` = `li r25, 1` | `80124424` is `mr r25, r4`, so **`r4` = gender** |
| "Shiny Starter Pokemon" | `04130B24` / `04130C4C` = `li r6, 1` | two starter-generation **call sites** passing the flag in `r6` |
| "Complete Strategy Memo" | `120082A8 00000182`, fills at step `0x0C` | **386 entries, count at `+0x82A8`, 12-byte stride** — our memo model exactly |

### The genuinely new fact: which write does what

Ralf's toggle variant "All Pokemon Are Shiny On/Off" uses only **three** of the
four writes — `80121D44`, `80125408`, `801272CC` — and labels it **"GFX only"**.

So those three are the *display* shiny checks, and **`8012442C` (the
`mr r27, r6` inside the PID generator) is the one that actually changes the
rolled PID.** That is a real functional split we had not established: patching
the three display sites makes Pokémon *look* shiny; patching `8012442C` makes
them *be* shiny. Recorded in `PROJECT_NOTES.md` §9 and in the code file.

It also explains why `force_shadow_shiny_US` works with no display patches at
all — it hooks the generator itself.

## The AR offset table

`Pokemon_Colosseum_NTSC-U_AR_Offset_Table/` is the same data as the WiiRD table
in Action Replay form: `42<pointer>` plus a **halfword index**, not a byte
offset. `4247ADB8 004Exxxx` is `saveBase + 0x4E*2 = +0x9C` = Trainer Secret ID.
Double the index to get the byte offsets used throughout these notes. Recorded
in §6.

## Not yet read

The `Original Attempt & Knowledge` zip holds four files (the original PAL
research notes, a 1-in-4 shiny code, a guaranteed-shiny code, and a copy of the
`.skill`). Contents listed but not mined — the PAL research notes are likely
already reflected in `PID_LIFECYCLE.md`, and the two shiny codes are worth a
look next session if a variant is ever wanted.

## Still open

Unchanged: Strategy Memo pre-seed causality, the u3 scratch struct's constant
`5`, and the `saveBase + 0xAF4` money/TID collision.

# Handoff — 2026-09-04 17:16

**Change:** Set up the project reference files and converted the "force shadow
Pokémon shiny" Gecko code from PAL (GC6P01) to US (GC6E01).

## Files added

| Path | What it is |
|---|---|
| `PROJECT_NOTES.md` | Summary of the project's schema and rules — builds, map format, address-translation rule, Colosseum memory schema, shiny mechanics, Gecko C2 rules, Dolphin working agreement, GoD-Tool notes |
| `tools/map_convert.py` | PAL <-> US address translator |
| `codes/force_shadow_shiny_US.txt` | The converted code plus what still needs verifying |
| `handoffs/` | This folder; one dated file per major change |

## Method used for the conversion

The two symbol maps contain no data/BSS symbols, only `.text`. Both builds are
the same source compiled per region, so the *sequence of function sizes* in
`.text` is nearly identical. `tools/map_convert.py` runs a `difflib` sequence
alignment over those size sequences and maps an address as

```
us_addr = us_func_start + (pal_addr - pal_func_start)
```

reporting the length of the exact-size run it landed in as a confidence signal.

## What was decided

**Hook address: PAL `0x80128584` → US `0x80124410`.** Conclusive — same 0x4B4
size, inside a 95-function exact alignment run, and the annotated US symbol is
`zz_generate_pid_gender_r4_nature_r5_shiny_r6_trainer_id_r7`, which independently
confirms the PAL code's semantics (`r6` = shiny flag, `r7` = trainer ID).

What the original code does: it hooks the PID generator's first instruction,
forces the shiny argument on (`r6 = 1`), and replaces the trainer-ID argument
(`r7`) with the *player's* trainer ID read from the save struct
(`saveBase + 0x9C`, halves swapped). Without the `r7` swap the PID would be
rolled shiny against the AI trainer's ID, not yours, so it would stop being
shiny the moment you caught it. The final `9421FFC0` re-emits the prologue
instruction the C2 branch overwrote.

## Left unverified — this is the blocker

**The US address of the save-base-pointer global (PAL `0x804C8268`).** Globals
are not in either map and there is no US DOL or MRAM dump in the workspace, so
it cannot be derived from the files on hand.

* Provisional value shipped in the code file: **`0x804C3688`** — PAL address
  minus the 0x4BE0 `.text` size difference. This ignores any `.data`/`.rodata`
  size difference between regions, so treat it as a guess, not a result.
* Exact route: disassemble US `0x80128E14`
  (`savedataBiosSetNowSavedataPtr`, `memcard.a savedataBios.o`, 16 bytes) — its
  single `stw` names the global outright. Or dump MRAM with a save loaded and
  locate it from the dump.

Also unverified:

* That US `0x80124410` really begins with `stwu r1, -0x40(r1)`. Same function
  size in both builds says it should, but it is one glance in Dolphin.
* The anti-Action-Replay NOP set. PAL `800387E4` / `800388D4` / `8003898C` map
  to US `80036598` / `80036688` / `80036740`, and PAL `80005E48` maps to US
  `80005D50`; all four came from 5–14 function runs ("likely", not
  "conclusive"). PAL `80005614`, `80005D1C` and the `8026AF80/84` writes have no
  aligned counterpart — that early region diverges too much between builds.

## Next step

Get the US save-base-pointer global (one of the two routes above), drop it into
the `lis`/`ori` pair in `codes/force_shadow_shiny_US.txt`, and the code is done.

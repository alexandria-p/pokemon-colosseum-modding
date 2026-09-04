# Handoff — 2026-09-04 23:12

**Change:** `force_shadow_shiny_US` v2 — restricted to shadow Pokémon by moving
the hook from the PID generator to its call site. Also established, from the
code, that a shadow's PID is rolled once and then persisted.

## Files

| Path | What |
|---|---|
| `Claude Output/codes/force_shadow_shiny_US.txt` | rewritten — v2 primary, v1 retained below as the known-good fallback |
| `Claude Output/PROJECT_NOTES.md` | §9 gains the roll-vs-reuse branch and the shadow definition table |

## v2

```
C21FA3E8 00000006
38C00000 281E0000
41820024 3D608047
616BADB8 816B0000
280B0000 41820010
80EB009C 54E7803E
38C00001 60000000
```

```
li     r6, 0             ; the overwritten original
cmplwi r30, 0            ; the game's own is-shadow flag
beq    done              ; ordinary Pokemon -> untouched
lis    r11, 0x8047
ori    r11, r11, 0xADB8
lwz    r11, 0(r11)
cmplwi r11, 0
beq    done              ; no save loaded
lwz    r7, 0x9C(r11)
rotlwi r7, r7, 16
li     r6, 1             ; force shiny
done:
nop
```

## Why the hook moved

v1 hooked the PID generator (`0x80124410`), which every Pokémon goes through —
that is why it made everything shiny. v2 hooks the **call site** at
`0x801FA3E8` (`li r6, 0`, the shiny-flag argument), inside
`zz_gen_battle_pokemon_from_data_table?`.

`r30` is the game's own is-shadow flag: loaded once at `0x801FA004` from
pokemon-data field 19, never rewritten in the function, and branched on by the
game itself at `0x801FA398` and `0x801FA408`. Gating on it is exactly the
distinction the game already makes.

Stars names the same instruction `shinyLockRAMOffset = 0x801fa3e8` in
`Code Snippets CM.swift`, with `shadowsOnlyLockRAMOffset = 0x801fa3d8` — so this
is the intended place for a shadows-only gate.

## The lifecycle question, answered from the code

```
801FA398  cmplwi r30, 0          ; is-shadow?
801FA39C  beq    801FA3D8        ; no  -> roll a new PID
801FA3A4  bl     801EE8F4        ; does this shadow already have a PID?
801FA3B0  bne    801FA3D8        ; no  -> roll a new PID
801FA3B8  bl     801EE750        ; yes -> fetch the stored one
801FA3D0  bl     set field 111
801FA3D4  b      801FA408        ;        generator skipped entirely
```

`0x801EE750` reads `base + index*12 + 8`, base from
`trainer_get_data_pointer(0, 15)` — the same 12-byte stride and PID-at-`+0x08`
as the Strategy Memo. In the US dump the only save-memory copy of Makuhita's PID
is its memo entry.

So: **rolled once at the first encounter, written to the save, reused forever.**

Consequences worth stating to anyone using these codes:

* the code must be on **before** the first encounter with each shadow Pokémon
* enabling it afterwards cannot change a PID that is already fixed
* disabling it afterwards does not undo one
* leaving it on is free — it simply stops applying to Pokémon already met

## New structure recorded

**Shadow definition table** at `[r13 - 0x78B4]` (US `r13 = 0x80480820`, pointer
at `0x80478F6C`, read `0x808A7AC4`). `0x38`-byte entries, bounds-checked to
`0x60`. Species `+0x02`, level `+0x08`, memo entry index `+0x0A`. Entry 1 is
Makuhita (`0x014F`, level 30) — matching the WiiRD "0001 = Makuhita" numbering.

## Interaction warning

"Shiny Nation" / all-new-Pokémon-shiny hooks `0x801FA3E4` — the instruction
immediately before this hook. Both would run, and it forces every roll shiny,
defeating the gate. Do not enable both. Noted in the code file.

## Verification

Against the US dump: `0x801FA3E8` holds `38C00000`; `r30` written only at
`0x801FA004` and live at the hook; both branch offsets land on the trailing
`nop`; every encoding round-tripped through the disassembler; the reuse path
confirmed by disassembling `0x801EE8F4` and `0x801EE750`.

**v2 not yet tested in-game.** v1 is retained in the file and remains the
known-good fallback.

## Not done

No PAL equivalent of v2 yet. The conversion should be small — `0x801FA3E8` maps
into `zz_01fe824_` (PAL `0x801FE824`) and only the hook address and the global
change — but it has not been derived or verified.

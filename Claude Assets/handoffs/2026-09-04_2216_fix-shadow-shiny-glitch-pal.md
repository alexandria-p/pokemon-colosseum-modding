# Handoff — 2026-09-04 22:16

**Change:** `fix_shadow_shiny_glitch_US` confirmed working in-game, and
converted to PAL.

## Files

| Path | What |
|---|---|
| `Claude Output/codes/fix_shadow_shiny_glitch_PAL.txt` | new — the PAL conversion |
| `Claude Output/codes/fix_shadow_shiny_glitch_US.txt` | marked confirmed working; cross-links the PAL version |
| `Claude Output/PROJECT_NOTES.md` | §9 gains the PAL counterparts of the hooked functions |

## The PAL code

```
C212811C 00000007
281A0000 4182002C
A19A00D8 280C0000
41820020 3D60804C
616B8268 816B0000
280B0000 4182000C
818B009C 919A0014
BB410008 00000000
```

## Only two things changed

```
hook    US 0x80123FA8  ->  PAL 0x8012811C
global  US 0x8047ADB8  ->  PAL 0x804C8268
          (lis 0x8047 / ori 0xADB8  ->  lis 0x804C / ori 0x8268)
```

Everything else is byte-identical. The record offsets the code uses — `+0xD8`
Shadow Pokémon ID, `+0x14` OT SID/TID, `+0x9C` the player's ID dword — are
save-relative and identical across regions, which the two WiiRD v1.01 tables
already established (they differ only in the base pointer, the in-battle
absolute addresses and the button activator).

`ori` zero-extends, so no sign-extension correction is needed in either region.

## Verified against the PAL MRAM dump

The PAL OT setter at `0x80128064` is instruction-for-instruction identical to
the US one at `0x80123EF0` apart from `bl` targets — same prologue, same
`mr. r26, r3`, same `beq` to the exit, same field indices 113–118, same
`lmw r26, 0x8(r1)` at the exit.

* `0x8012811C` holds `BB410008` — the instruction the code re-emits
* `r26` is the record pointer and is not reloaded until that instruction
* `lis 0x804C` / `ori 0x8268` resolves to `0x804C8268`
* all three branch offsets land exactly on the re-emitted `lmw` (`0x8012814C`)
* the shadow gate discriminates in the PAL dump's opponent array A —
  Duskull `0000`, Spinarak `0000`, Makuhita `0001`
* every encoding round-tripped through the disassembler

`map_convert.py` put `US 80123FA8 -> PAL 8012811C` inside a 95-function
exact-size run.

## The PAL dump happens to demonstrate the glitch

A nice accident: the PAL capture contains exactly the bug this code fixes.

```
shadow Makuhita, PID F4893D62
owner  Trudly  (TID DBB7, SID E829):  xor = FA75  -> not shiny
player Rex     (TID 7002, SID B9EB):  xor = 0002  -> SHINY
```

The PID is genuinely shiny against the player, but the record still carries
Trudly's OT dword (`E829DBB7` at `+0x14`), so the game renders it normally.
With this code the OT becomes `B9EB7002` and it renders shiny. Written into the
PAL code file as a worked example.

## PAL counterparts recorded

| Function | US | PAL |
|---|---|---|
| OT setter | `80123EF0` | `80128064` |
| — its exit (the hook) | `80123FA8` | `8012811C` |
| party builder | `80129F20` | `8012E0E8` |
| battle generator | `801F9F78` | `801FE824` |
| shadow check | `8011FC74` | `80123DE8` |

## Status

US: **confirmed working in-game.**
PAL: verified statically against the PAL dump, **not yet tested in-game.**

## Still open

Unchanged: Strategy Memo pre-seed causality, the u3 scratch struct's constant
`5`, the `saveBase + 0xAF4` money/TID collision.

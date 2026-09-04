# Handoff — 2026-09-05 00:02

**Change:** `force_shadow_shiny_US` v2 confirmed working in-game — including its
shadow-only scope, verified by an independent method — and converted to PAL as
`force_shadow_shiny_PAL`.

## Files

| Path | What |
|---|---|
| `Claude Output/codes/force_shadow_shiny_PAL.txt` | new — the PAL v2 conversion |
| `Claude Output/codes/force_shadow_shiny_US.txt` | v2 marked confirmed; cross-links the PAL build |

## The PAL code

```
C21FEC94 00000006
38C00000 281E0000
41820024 3D60804C
616B8268 816B0000
280B0000 41820010
80EB009C 54E7803E
38C00001 60000000
```

## Only two things changed, again

```
hook    US 0x801FA3E8  ->  PAL 0x801FEC94
global  US 0x8047ADB8  ->  PAL 0x804C8268
          (lis 0x8047 / ori 0xADB8  ->  lis 0x804C / ori 0x8268)
```

Third port in a row where that is the whole diff. The pattern in
`Claude Output/PROJECT_NOTES.md` holds: for a code touching only relative
offsets, a region port is the hook address plus the base pointer.

## How the shadow-only scope was confirmed

Worth recording as a technique. Running `force_all_enemy_ot_to_player_US`
alongside v2 gives *every* generated Pokémon the player's OT — which means any
Pokémon with a player-shiny PID would render shiny. Only the shadow Pokémon did.
That isolates the `r30` gate and proves it discriminates, which watching shadow
Pokémon alone could not have shown.

A deliberately over-broad code used as a test instrument to prove a narrow one.

## Verified against the PAL MRAM dump

The PAL region is instruction-for-instruction identical to the US one apart from
`bl` targets:

```
801FEC44  cmplwi r30, 0
801FEC48  beq    801FEC84      ; not a shadow -> roll
801FEC50  bl     801F3168      ; already has a PID?
801FEC5C  bne    801FEC84      ; no -> roll
801FEC64  bl     801F2FC4      ; yes -> fetch stored PID
801FEC80  b      801FECB4      ; generator skipped
801FEC94  li     r6, 0         ; <- HOOK
801FEC98  bl     80128584      ; the PAL PID generator
```

* `0x801FEC94` holds `38C00000` — the re-emitted instruction
* `r30` written once at `0x801FE8B0` from is-shadow field 19, live at the hook
* both branch offsets land on the trailing `nop` (`0x801FECC0`)
* `lis 0x804C` / `ori 0x8268` resolves to `0x804C8268`
* PAL save `+0x9C` reads `B9EB7002`; `rotlwi 16` → `7002B9EB`
* reuse path `0x801F3168` / `0x801F2FC4` confirmed by disassembly

`map_convert.py`: `US 801FA3E8 -> PAL 801FEC94`, 123-function exact-size run.

Note `0x80128584` — the PAL PID generator the *original* PAL code hooked
directly. v2 sets its arguments at the call site instead, which is what makes
the gate possible.

## Conflict to avoid

`0x801FEC94` is one instruction after `0x801FEC90`, which the PAL
all-new-Pokémon-shiny code hooks. Do not enable both.

## Status

| Code | US | PAL |
|---|---|---|
| `force_shadow_shiny` v1 (all Pokémon) | confirmed | (original PAL code exists) |
| `force_shadow_shiny` v2 (shadow-only) | **confirmed** | statically verified |
| `fix_shadow_shiny_glitch` | confirmed | confirmed |
| `force_all_enemy_ot_to_player` | reported | reported |

PAL v2 is the only untested item.

## Still open

Unchanged: Strategy Memo pre-seed causality, the `u3` scratch struct's constant
`5`, the `saveBase + 0xAF4` money/TID collision.

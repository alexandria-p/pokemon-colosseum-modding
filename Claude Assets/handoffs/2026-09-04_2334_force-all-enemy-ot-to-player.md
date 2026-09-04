# Handoff — 2026-09-04 23:34

**Change:** Two new codes for testing — the OT rewrite with the shadow gate
removed, so every Pokémon built by the trainer-party generator gets the player's
OT. US and PAL.

## Files

| Path | What |
|---|---|
| `Claude Output/codes/force_all_enemy_ot_to_player_US.txt` | new |
| `Claude Output/codes/force_all_enemy_ot_to_player_PAL.txt` | new |

Kept as separate files rather than variants inside the shadow-gated ones,
because they are a different purpose — "force all enemy OT to the player" rather
than "fix the shadow shiny glitch".

## The codes

**US / GC6E01** — hook `0x80123FA8`

```
C2123FA8 00000005
281A0000 41820020
3D608047 616BADB8
816B0000 280B0000
4182000C 818B009C
919A0014 BB410008
```

**PAL / GC6P01** — hook `0x8012811C`

```
C212811C 00000005
281A0000 41820020
3D60804C 616B8268
816B0000 280B0000
4182000C 818B009C
919A0014 BB410008
```

Each is the corresponding `fix_shadow_shiny_glitch` code with three
instructions removed —

```
lhz    r12, 0xD8(r26)    ; Shadow Pokemon ID
cmplwi r12, 0
beq    skip
```

— and the branch offsets and line count adjusted (7 lines → 5, both branches now
`+0x20` / `+0x0C` onto the `lmw` at `+0x24`).

## Scope, stated plainly in both files

This is **not** literally "all enemy Pokémon". It is every Pokémon whose OT is
set through the OT setter. US callers:

```
800097D8   debug-menu path
80129FD0   trainer party generation      <- enemy trainers' Pokemon
801306FC   e-Card / bonus gift Pokemon   (Ageto Celebi, OT ID 31121)
8013080C   e-Card / bonus gift Pokemon
8013092C   e-Card / bonus gift Pokemon
80130A14   e-Card / bonus gift Pokemon
8025CE54   (unidentified)
```

So in normal play: enemy trainers' Pokémon **and** the e-Card / bonus gift
Pokémon, which would lose their distinctive OT IDs while this is on. The
player's own party is not built through this path.

## What it does not do

It rewrites OT SID/TID only — it does not touch the PID. On its own an enemy
Pokémon will look shiny only if its existing PID happens to be shiny against the
player, ~1 in 8192. Both files say so, because "I enabled it and nothing looked
shiny" is the obvious way to misread a test result here.

Also repeated in both files: a shadow's PID is rolled once at the first
encounter and persisted, so a force-shiny code enabled afterwards cannot change
it.

## Verification

Against the respective MRAM dumps: both hooks hold `BB410008`; `r26` is the
record pointer and is not reloaded until the re-emitted instruction; both branch
offsets land exactly on it; `lis`/`ori` resolves to the right global in each
region; every encoding round-tripped through the disassembler.

Derived from builds confirmed working in-game, but **these unconditional builds
are not themselves tested**.

## Conflicts to avoid

Each shares its hook address with the corresponding `fix_shadow_shiny_glitch`
code — enable one or the other, never both.

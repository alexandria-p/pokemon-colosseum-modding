# Handoff — 2026-09-05 01:25

**Change:** New variant — `force_shadow_shiny_1in4_US`. Same shadow-only hook as
v2, but the shiny logic fires on only 1 shadow PID roll in 4.

## File

`Claude Output/codes/force_shadow_shiny_1in4_US.txt` — new. Shares the hook
address `0x801FA3E8` with v2, so it is an alternative to it, not an addition.

## The code

```
C21FA3E8 0000000A
38C00000 281E0000
41820044 3D608048
816B8C94 280B0000
41820034 816B0000
556087BE 28000000
40820024 3D608047
616BADB8 816B0000
280B0000 41820010
80EB009C 54E7803E
38C00001 60000000
```

v2 plus a seed check between the is-shadow gate and the OT load. 10 lines.

## Randomness source — reading the seed, not calling the RNG

`zz_RNG` (`0x801ADCD8`) is a plain LCG:

```
seed = seed * 0x343FD + 0x269EC3
return (seed >> 16) & 0xFFFF
```

Its seed sits behind a **pointer** at `r13 - 0x7B8C = 0x80478C94`
(US `r13 = 0x80480820`). In the dump that pointer held `0x80478C90`, and the
seed there read `0x1E341439`.

The code reads the seed rather than calling the RNG, for two reasons:

* **No `bl`.** At this hook `r3`/`r4`/`r5`/`r7` are already loaded with the PID
  generator's arguments — a call would clobber all four and they would have to
  be rebuilt. Reading needs only `r0` and `r11`, both volatile and dead here.
* **It does not advance the RNG.** Calling would consume a value and shift every
  PID rolled afterwards; reading leaves the sequence exactly as vanilla, so the
  three-in-four non-shiny shadows keep the PIDs they would have had.

Bits 16–17 are used — the low two bits of the high halfword, the same region the
RNG itself returns. An LCG's low-order bits are poor (bit 31 just alternates).

## Two things flagged in the file, because a tester will hit them

**The roll is deterministic for a given game state.** Save-stating right before
an encounter and reloading gives the same result every time — both the gate and
the PID derive from the same seed. Rerolling needs something varied upstream
(input timing, approach, menu path). This is not a property of the code; the PID
has always worked that way.

**A shadow's PID is rolled once and persisted.** So this permanently decides
each shadow's fate at first encounter — three quarters are non-shiny forever,
and changing the code later cannot alter one already rolled.

## Adjustable odds

Only the `rlwinm` mask changes; line count and branch offsets stay the same:

| Odds | Instruction | Word |
|---|---|---|
| 1 in 2 | `rlwinm r0, r11, 16, 31, 31` | `556087FE` |
| 1 in 4 | `rlwinm r0, r11, 16, 30, 31` | `556087BE` |
| 1 in 8 | `rlwinm r0, r11, 16, 29, 31` | `5560877E` |
| 1 in 16 | `rlwinm r0, r11, 16, 28, 31` | `5560873E` |

I first wrote `55608FFE` for the 1-in-2 case in the file; the correct word is
`556087FE`. Caught by generating all four programmatically and disassembling
them rather than hand-deriving — worth doing for any table of encodings.

## Verification

Against the US dump: `0x801FA3E8` holds `38C00000`; `lis 0x8048` /
`lwz 0x8C94` resolves to `0x80478C94` (the displacement sign-extends to
`-0x736C`); the pointer and seed read as above; `r30` live; `r0`/`r11` dead and
volatile while `r3`/`r4`/`r5`/`r7` are untouched; all four branch offsets land
on the trailing `nop` at `0x801FA434`; every encoding round-tripped through the
disassembler.

**Not yet tested in-game.** The always-on v2 it derives from is confirmed, as is
the shadow-only gate it reuses; the seed check is the only new part.

## Not done

No PAL version. The port should be the usual two substitutions plus the seed
pointer — but PAL `r13` has not been read, so the seed-pointer displacement is
unknown and I have not guessed it.

# Handoff — 2026-09-05 01:52

**Change:** New 1-in-4 variant using the CPU timebase instead of the RNG seed —
shorter, simpler, and much more sensitive to real timing. Also taught `ppc.py`
to decode `mftb`/`mfspr`.

## Files

| Path | What |
|---|---|
| `Claude Output/codes/force_shadow_shiny_1in4_timebase_US.txt` | new — the recommended 1-in-4 build |
| `Claude Output/codes/force_shadow_shiny_1in4_US.txt` | cross-linked; kept as the alternative |
| `Claude Assets/tools/ppc.py` | `mftb` / `mfspr` decoding added |
| `Claude Output/colosseum-region-porting.skill` | repackaged with the improved disassembler |

## The code

```
C21FA3E8 00000008
38C00000 281E0000
41820034 7D6C42E6
556007BE 28000000
40820024 3D608047
616BADB8 816B0000
280B0000 41820010
80EB009C 54E7803E
38C00001 60000000
```

8 lines, against 10 for the seed version. `mftb r11` is one instruction with no
pointer and no null check.

## The question that prompted it, answered honestly

Asked whether a 1-in-4 roll could be made non-deterministic for a given game
state — perhaps from save-file play time.

**It cannot, from any in-game source.** A Dolphin save state restores the entire
machine including the timebase register; reload and re-run with identical input
and every readable value is identical. That is emulation, not a limitation of
any particular source.

What a source *can* be is sensitive to real variation. Ranked:

| Source | Rate | Verdict |
|---|---|---|
| **CPU timebase** | ~40 MHz | best — low bits change every ~25 ns |
| RNG seed | per RNG call | coarser, and correlated with the PID rolled from it |
| **save-file play time** | per frame / per second | **worst** — two attempts in the same second give the same value |

So the suggested play-time source would have made results *more* repeatable, not
less. Said plainly in the code file rather than quietly substituting something
better.

In practice the only repeat scenario is a save state taken close to the
encounter plus reproduced input. Reloading the memory-card save and walking back
varies every time.

## Encoding note

`mftb rD` is `mfspr rD, 268` with the SPR field's two 5-bit halves swapped.
Derived it, then cross-checked by generating `mftb r3` and confirming it equals
the well-known `7C6C42E6` before trusting `mftb r11 = 7D6C42E6`. Then added
`mftb`/`mfspr` to `ppc.py` so the block could be round-tripped like every other
code rather than taken on faith.

The odds words differ from the seed version's — there the value is rotated 16
first to reach an LCG's usable high half; here it is not, because the timebase's
low bits are the fastest-changing and perfectly good:

| Odds | Word |
|---|---|
| 1 in 2 | `556007FE` |
| 1 in 4 | `556007BE` |
| 1 in 8 | `5560077E` |
| 1 in 16 | `5560073E` |

## Verification

`0x801FA3E8` holds `38C00000`; `r30` live; `r0`/`r11` volatile and dead while
`r3`/`r4`/`r5`/`r7` are untouched; all three branches land on the trailing `nop`
at `0x801FA424`; every encoding round-tripped.

**Not yet tested in-game.**

## Hook-address collision, now three ways

`0x801FA3E8` is shared by `force_shadow_shiny_US` v2, the seed 1-in-4 build, and
this one. Exactly one may be enabled. Stated in all three files.

## Not done

No PAL version of either 1-in-4 build. The timebase one would port more easily
than the seed one — `mftb` needs no address at all, so it is the usual two
substitutions and nothing more, whereas the seed version would additionally need
PAL's `r13` and seed-pointer displacement.

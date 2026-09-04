# Handoff — 2026-09-05 02:14

**Change:** 1-in-512 timebase variant. One word different from the 1-in-4 build.

## File

`Claude Output/codes/force_shadow_shiny_1in512_timebase_US.txt`

```
C21FA3E8 00000008
38C00000 281E0000
41820034 7D6C42E6
556005FE 28000000
40820024 3D608047
616BADB8 816B0000
280B0000 41820010
80EB009C 54E7803E
38C00001 60000000
```

`rlwinm r0, r11, 0, 23, 31` masks 9 bits (`TB & 0x1FF`) = 1 in 512. Line count
and all three branch offsets are unchanged from the 1-in-4 build — only
`556007BE → 556005FE`.

## The thing worth saying out loud

At 1 in 512, with 48 shadow Pokémon and each PID rolled once and persisted:

| | |
|---|---|
| expected shiny shadows per playthrough | **0.094** |
| chance of at least one | **9%** |
| chance of none | **91%** |

So roughly nine playthroughs in ten contain no shiny shadow at all. That may be
exactly the intent — it makes one genuinely rare — but it is worth being
explicit that this is "probably never", not "shiny hunting". Hunting one
specific shadow by reloading needs ~355 attempts for 50%, ~1180 for 90%.

For context the games' own rate is 1 in 8192, so 1 in 512 is already sixteen
times more generous than vanilla.

The code file carries a full odds table (1 in 2 through 1 in 8192) with the
expected-shinies figure for each, so the tradeoff is visible when picking.

## Testing note recorded

At these odds a test producing no shiny proves nothing about the code. The file
says to validate the mechanism at 1 in 2 or 1 in 4 first, then swap the mask
word — the rest of the block is byte-identical, so a pass at 1 in 4 carries over
completely.

## The pattern, for future adjustments

Halving the odds = subtract 1 from the `rlwinm` MB field = subtract `0x40` from
the word. Nothing else in the block changes, ever. The seed-build equivalents
are the same words plus `0x8000` (that version rotates by 16 first to reach an
LCG's usable high half).

## Verification

`rlwinm r0, r11, 0, 23, 31` confirmed to mask exactly 9 bits; every word in the
odds table generated programmatically and round-tripped through the
disassembler rather than hand-derived — the same check that caught a wrong
1-in-2 word in the seed build earlier. `0x801FA3E8` holds `38C00000`; branches
land on the trailing `nop` at `0x801FA424`.

**Not tested in-game.**

## Hook collision, now five ways

`0x801FA3E8` is shared by `force_shadow_shiny_US` v2, the seed 1-in-4, the
timebase 1-in-4, this, and (one instruction earlier, at `0x801FA3E4`) Shiny
Nation. Exactly one may be enabled. Stated in each file.

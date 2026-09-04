# Handoff — 2026-09-05 02:43

**Change:** A user-configurable-odds build — the shiny chance is a plain decimal
field the user edits. Supersedes the fixed 1-in-N builds for anything but a
power of two.

## File

`Claude Output/codes/force_shadow_shiny_custom_odds_US.txt`

```
C21FA3E8 00000010
38C00000 281E0000
41820074 38000000
6000XXXX 5408073E     <- XXXX is the odds field
5409E73E 540AC73E
540CA73E 1D29000A
1D4A0064 1D8C03E8
7D8C5214 7D8C4A14
7D8C4214 280C0000
4182003C 7D6C42E6
7C0B6396 7C0061D6
7C005850 28000000
40820024 3D608047
616BADB8 816B0000
280B0000 41820010
80EB009C 54E7803E
38C00001 60000000
```

`60000512` → 1 in 512, `60009999` → 1 in 9999, `60000001` → always,
`60000000` → never. 32 instructions, 16 lines.

## Two design decisions worth recording

**Modulo, not a bit mask.** The fixed builds mask bits — compact, but only
powers of two. `1 in 9999` is impossible that way. This computes
`TB - (TB / N) * N` with `divwu` / `mullw` / `subf`, so any N from 1 to 9999 is
exact. Cost is one divide (~20 cycles) once per shadow PID roll.

**The field is decoded as decimal, not hex.** Gecko codes are hex, so a naive
"put your number here" field would read `0512` as `0x512` = 1298 and give
silently wrong odds — undetectable by playing. The code unpacks four BCD digits
and rebuilds the value:

```
rlwinm r8,  r0, 0,  28, 31   ; ones
rlwinm r9,  r0, 28, 28, 31   ; tens      -> mulli 10
rlwinm r10, r0, 24, 28, 31   ; hundreds  -> mulli 100
rlwinm r12, r0, 20, 28, 31   ; thousands -> mulli 1000
```

Twelve extra instructions to make the field mean what a user would assume it
means. Worth it precisely because the failure mode is invisible.

## Safety

`0000` is guarded by `cmplwi r12, 0` / `beq` before the divide, so there is no
divide-by-zero path — it simply never fires. `0001` gives `TB mod 1 == 0`
always, i.e. identical behaviour to v2.

A digit above 9 is misread rather than rejected (`00FF` → 165). Documented.

## Verification

* every encoding round-tripped through the disassembler
* the decimal decode simulated for `0001 0004 0008 0064 0512 1024 8192 9999
  0000` — all produce exactly the intended N
* the modulo sampled over 400,000 uniform 32-bit values at N = 4, 512, 9999 —
  observed rates matched targets within noise
* all four branches land on the trailing `nop` at `0x801FA464`
* `0x801FA3E8` holds `38C00000`; `r30` live; `r0`/`r8`/`r9`/`r10`/`r11`/`r12`
  all volatile and dead here, `r3`/`r4`/`r5` untouched

**Not tested in-game.** Recommended test path is in the file: set `0001`, which
should reproduce v2 exactly (every shadow shiny), then dial in real odds. At long
odds a test producing no shiny proves nothing.

## Tooling

`ppc.py` gained `mullw`, `divwu`, `divw` (and earlier `mftb`/`mfspr`) so the
whole block could be verified rather than hand-checked. Synced to
`Claude Assets/tools/` and repackaged into the shareable skill.

## Note on the older builds

`force_shadow_shiny_1in4_US` (seed), `_1in4_timebase_US` and `_1in512_timebase_US`
are now redundant for most purposes — this build covers their cases and more.
They are smaller (8–10 lines vs 16) and remain valid; kept rather than deleted
since two are the reference points for testing the mechanism cheaply.

All of them share hook `0x801FA3E8` with v2. Exactly one may be enabled.

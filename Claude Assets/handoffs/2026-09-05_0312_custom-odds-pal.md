# Handoff — 2026-09-05 03:12

**Change:** PAL conversion of the user-configurable-odds build.

## File

`Claude Output/codes/force_shadow_shiny_custom_odds_PAL.txt`

```
C21FEC94 00000010
38C00000 281E0000
41820074 38000000
6000XXXX 5408073E
5409E73E 540AC73E
540CA73E 1D29000A
1D4A0064 1D8C03E8
7D8C5214 7D8C4A14
7D8C4214 280C0000
4182003C 7D6C42E6
7C0B6396 7C0061D6
7C005850 28000000
40820024 3D60804C
616B8268 816B0000
280B0000 41820010
80EB009C 54E7803E
38C00001 60000000
```

## Diff from the US build — two words

```
hook    C21FA3E8 -> C21FEC94
global  3D608047 -> 3D60804C     (lis r11, 0x8047 -> 0x804C)
        616BADB8 -> 616B8268     (ori 0xADB8      -> 0x8268)
```

Everything else byte-identical; line count and all four branch offsets unchanged.

Notable: this is the largest code in the set (32 instructions) and still only two
words differ. Nothing else in it refers to an address — `mftb` reads a CPU
register, the decimal decode is pure arithmetic, and the modulo is
`divwu`/`mullw`/`subf`. Only the save-base pointer is region-specific.

Fourth port in a row where the diff is exactly "hook address plus base pointer".

## PAL breakpoints, verified by disassembly

| Purpose | US | PAL |
|---|---|---|
| break here — `r6` = did it fire, `r7` = trainer ID used | `801FA3EC` | **`801FEC98`** (`bl 0x80128584`) |
| step one — `r3` = the rolled PID | `801FA3F0` | `801FEC9C` |
| stored-PID fetch (fires instead if already rolled) | `801FA3B8` | `801FEC64` (`bl 0x801F2FC4`) |
| the hook itself — do NOT break here | `801FA3E8` | `801FEC94` |

Conditional breakpoint `r6 == 1` at `0x801FEC98` for long odds.

## Verification

`0x801FEC94` holds `38C00000`; `lis 0x804C`/`ori 0x8268` resolves to
`0x804C8268`; PAL save base `0x804559E0`, `+0x9C` = `B9EB7002`; `r30` written
once at `0x801FE8B0` and live; all four branches land on the trailing `nop` at
`0x801FED10`; every encoding round-tripped.

The decimal decode and modulo are unchanged from the US build, where they were
simulated across all the example fields and sampled over 400,000 draws.

**Not tested in-game.** Test at `60000001` first — that should reproduce
`force_shadow_shiny_PAL` exactly.

## Still open

Unchanged: Strategy Memo pre-seed causality, the `u3` scratch struct's constant
`5`, the `saveBase + 0xAF4` money/TID collision.

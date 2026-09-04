# Handoff — 2026-09-04 20:19

**Change:** `force_shadow_shiny_US` confirmed working in-game. Marked as such in
the code file. No code changes.

## The working code — US / GC6E01

```
C2124410 00000004
38C00001 3CE08047
60E7ADB8 80E70000
80E7009C 54E7803E
9421FFC0 00000000
```

Prerequisites: the US anti-AR NOP set (`codes/ar_codehandler_nop.txt`) and
Dolphin in JIT64 SC mode.

## What this closes

The original task — convert the PAL "force shadow Pokémon shiny once caught"
Gecko code to US — is done and verified in the actual game, not just statically.

Only two things differed from the PAL original: the hook (`80128584` →
`80124410`) and the save-base global (`804C8268` → `8047ADB8`).

## Method track record — now including a live result

| Stage | How it was checked |
|---|---|
| Hook address | size-sequence map alignment, run 95; corroborated by the PAL author's own US code patching `80124410 + 0x1C` |
| Save-base global | supplied, then NTSC-U WiiRD table, then disassembly of `savedataBiosSetNowSavedataPtr` (`stw r3,-0x5A68(r13)`, `r13 = 0x80480820`) |
| Prologue word `9421FFC0` | read from the US MRAM dump |
| `r6` = shiny argument | `mr r27, r6` at `8012442C` in the dump |
| `+0x9C` = SID:TID, rotate needed | both WiiRD tables plus both dumps |
| **The whole code** | **runs correctly in-game** |

Every address this workspace has translated and later had checked has held.
The confidence tiers in `PROJECT_NOTES.md` §4 stay as they are — a live result
on one code is not a reason to start trusting short alignment runs, and the
tool's false-negative region below `0x80006000` is unchanged.

## Still open (unrelated to this code)

* Whether a Strategy Memo slot's pre-seeded PID *becomes* the next appended
  Pokémon's PID — needs a before/after dump pair.
* Purpose of the u3 global scratch struct and its constant `5`.
* `saveBase + 0xAF4` money/TID collision in the US dump.

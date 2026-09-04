# Handoff — 2026-09-04 18:21

**Change:** Ingested the NTSC-U and PAL WiiRD offset tables. Confirmed the US
save-base pointer independently, corrected a wrong stride in the notes, and
recorded a batch of new US addresses.

## Files changed

| Path | What |
|---|---|
| `PROJECT_NOTES.md` | §1 workspace, §5 save/battle schema (substantially revised), §6 lookup routes |

No code changes — both shipped codes are unaffected and confirmed correct.

## The headline: the base pointer is independently confirmed

`Pokemon_Colosseum_NTSC-U_WiiRD_Offset_Table.txt` opens with

```
48000000 8047ADB8
```

which is exactly the value supplied earlier, from a completely separate source.
The two shipped codes are correct as written.

Method worth remembering: the two tables are the same document per region, so
**`diff` gives every region-varying data address at once**. Recorded as route 0
in `PROJECT_NOTES.md` §6 — check here before touching Dolphin.

## Correction: party/box entry stride is 0x138, not 0x140

The `.skill` playbook's party PID table is wrong. Both WiiRD tables give a
`0x138` stride consistently across 6 party slots and 30 box slots, and the
playbook's *own worked example* proves it: it observed slot 3's PID at
`0x80455CF4` with save base `0x804559E0`, i.e. offset `0x314` — which is
`0xA4 + 2*0x138`, not the `0x324` its table predicts.

Corrected table (offsets from save base):

| Slot | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Entry | 0A0 | 1D8 | 310 | 448 | 580 | 6B8 |
| PID | 0A4 | 1DC | 314 | 44C | 584 | 6BC |

Anything computed from the `0x140` figure — party addresses in old session
notes, memory breakpoints on slots 2–6 — is off and should be recomputed.

## Settled: the trainer ID field layout

`+0x9C` is the **Secret ID** and `+0x9E` is the **Trainer ID**, so the dword at
`+0x9C` is `(SID << 16) | TID`. That is why the shadow-shiny code applies
`rotlwi r7,r7,16` — the PID generator wants `(TID << 16) | SID` — while the
battle-Pokémon generator hook takes the dword raw. Both codes were already
right; now we know *why*.

## New: the "shadow registry" is the Strategy Memo array

The WiiRD tables label `saveBase + 0x82A8` as a Strategy Memo **entry count**,
followed by a 386-entry array at `+0x82AC` with a **12-byte stride** (last entry
at `+0x94B8`), each entry starting with a species number (`| 0x8000` = limited
info).

The playbook's "Shadow Pokémon registry at `+0x82B0`, 12-byte entries, PID1 and
PID2, entry N PID2 = `registry + N*12 + 4`" is geometrically the *same array* —
its PID1/PID2 are that entry's `+0x04` and `+0x08` fields.

**Open question, recorded not resolved:** the playbook observed Makuhita at
index 9, but Makuhita is dex #296, so the array is not dex-ordered. The `+0x82A8`
count field points to an append-as-encountered list. Ordering needs to be
established before any shadow Pokémon's entry address can be computed from its
identity.

## New US battle addresses

| | PAL | US |
|---|---|---|
| Your side, Pokémon 1 | `804BBDA8` | `8046E928` |
| Your side, Pokémon 2 | `804BBEFC` | `8046EA7C` |
| Opponent, Pokémon 1 | `804C0FF0` | `80473B58` |
| Opponent, Pokémon 2 | `804C1144` | `80473CAC` |
| Button activator | `8044F0A8` | `80401C28` |

In-battle entry stride `0x154`; within an opponent entry, `+0xD8` = Shadow
Pokémon Identifier and `+0xDC` = Purification Counter. The `+0xD8` matches the
"is shadow" check the playbook found in the battle struct.

## Killed: the address-shifting heuristic

The PAL→US deltas are close but not equal — `0x4D4B0` for the save-base
pointer, `0x4D480` for your battle side and the button activator, `0x4D498` for
the opponent side. Intervening `.bss` allocations changed size independently.

They are also nothing like the `0x4BE0` `.text` difference the earlier estimate
was built on, which is why that guess (`0x804C3688`) was wrong by ~`0x48A00`.
`PROJECT_NOTES.md` §5 now states the rule: data addresses get looked up
per-variable, never extrapolated.

## Still unverified

Unchanged: the `9421FFC0` prologue word at US `0x80124410`, the `0x547F` guard
halfword at US `0x80129F78`, and the anti-Action-Replay NOP set. None of these
appear in the offset tables — they are code, and the tables cover data only.

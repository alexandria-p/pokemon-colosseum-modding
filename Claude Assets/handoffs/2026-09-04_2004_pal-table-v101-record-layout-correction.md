# Handoff — 2026-09-04 20:04

**Change:** Read the updated PAL WiiRD offset table (now v1.01, matching the
US one). Cross-checking its new fields against my notes exposed an offset error
I had introduced; corrected, and the correction collapses three "different"
record types into one.

## Files changed

| Path | What |
|---|---|
| `PROJECT_NOTES.md` | §1 layout, §5 record-layout table (rewritten, with the correction called out), §6 note on keeping table versions matched, battle section simplified |
| `PID_LIFECYCLE.md` | §1 record-layout paragraph corrected |

## The tables now diff clean

Both files are v1.01. The only differences between regions are the base pointer,
the in-battle absolute addresses, and the button activator. **Every
save-relative offset is identical across regions.**

Worth keeping that way: if the two files are ever at different versions, the
diff fills with spurious entries that look like region differences but are just
revision differences. Noted in §6.

New PAL numbers confirm the battle-entry offsets I had derived from the US dump
— shadow ID `+0xD8`, purification `+0xDC`, Hyper Mode `+0xE8`, status duration
`+0x68`, badly-poison `+0x6A`, all on both sides.

## Correction — an offset error in my own notes

The previous handoff recorded the v1.01 save-entry additions as entry-relative
`+0x178` Shadow Pokémon ID, `+0x17C` Purification, `+0x188` Hyper Mode.

**Those are the WiiRD tables' save-base-relative addresses for Pokémon 1.** The
entry base is `+0xA0`, so the real entry-relative offsets are
**`+0xD8` / `+0xDC` / `+0xE8`** — identical to the battle entry's. Verified
directly: Makuhita's array A record reads `0001` at `+0xD8` and `0BB8` at
`+0xDC`, and zero at the `+0x178`/`+0x188` I had claimed.

The error was invisible in the earlier probe because the PAL party held no
shadow Pokémon, so both the right and wrong offsets read zero.

## What the correction buys — one record type, not three

Comparing Makuhita's array A entry against his array B entry field by field:

```
species +0x00, PID +0x04, EXP +0x5C, status +0x65, status duration +0x68,
move 1 +0x78, HP +0x8A, happiness +0xB0, shadow ID +0xD8,
purification +0xDC, Hyper Mode +0xE8      -- all identical
```

So **the save entry, the battle array A entry and the battle array B entry are
the same record type with the same internal offsets.** The only difference is
the array stride — `0x138` vs `0x154`, i.e. array B leaves `0x1C` bytes more per
slot.

This kills the earlier framing of "the battle entry reuses the save entry's
*head*, then has battle-only fields". There are no battle-only fields. Shadow
ID, purification counter and Hyper Mode live in the save entry too, at the same
offsets — which makes sense, since that is exactly the data that has to survive
being caught.

`PROJECT_NOTES.md` §5 now carries a single record-layout table covering all
three uses, with the correction flagged inline so the wrong offsets are not
reintroduced from an old handoff.

## Still open

Unchanged: the Strategy Memo pre-seed causality question, the purpose of the u3
global scratch struct and its constant `5`, and the `saveBase + 0xAF4`
money/TID collision in the US dump.

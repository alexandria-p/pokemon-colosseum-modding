# Handoff — 2026-09-04 18:36

**Change:** Recorded the US Action Replay code-handler NOP set, closing the last
outstanding address unknown in the workspace. Both regions' sets are now stored
together, and `map_convert.py`'s failure mode in the low-address region is
documented.

## Files changed

| Path | What |
|---|---|
| `codes/ar_codehandler_nop.txt` | New — both regions, plus how each pairing was established |
| `codes/force_shadow_shiny_US.txt` | Anti-AR caveat replaced with a prerequisite pointer |
| `codes/all_new_pokemon_shiny_US.txt` | Same |
| `PROJECT_NOTES.md` | §4 documents the aligner's false-negative region; §10 carries the full anti-AR table |

## The set

```
US / GC6E01                        PAL / GC6P01
04005614 60000000                  04005614 60000000
04005C24 60000000                  04005D1C 60000000
04005D50 60000000                  04005E48 60000000
04036598 60000000                  040387E4 60000000
04036688 60000000                  040388D4 60000000
04036740 60000000                  0403898C 60000000
042663A0 000034E0                  0426AF80 000034E0
042663A4 000034E4                  0426AF84 000034E4
```

## Cross-check against our own derivations

All eight supplied US values agree with what was derived here:

| PAL | Previously called | Supplied | |
|---|---|---|---|
| `80005614` | unresolved | `80005614` | identity — same address in both builds |
| `80005D1C` | unresolved | `80005C24` | `GSgfxResetUpdate − 0x18` in both maps |
| `80005E48` | `80005D50` (likely) | `80005D50` | confirmed |
| `800387E4` | `80036598` (likely) | `80036598` | confirmed |
| `800388D4` | `80036688` (likely) | `80036688` | confirmed |
| `8003898C` | `80036740` (likely) | `80036740` | confirmed |
| `8026AF80/84` | unresolved | `802663A0/A4` | `.text` end + `0x44` / `0x48` |

Every "likely" call from `map_convert.py` (runs of 5–14) held. That is four for
four, alongside the earlier conclusive calls — the confidence rule in
`PROJECT_NOTES.md` §4 is behaving as advertised.

Note the last two lines write **data values**, not instructions, and the values
are identical across regions — only the destination moves. Both sit a fixed
`0x44`/`0x48` past the end of `.text` in their build.

## Tool defect recorded (not fixed)

`map_convert.py` returned "NO ALIGNED COUNTERPART" for `80005614` and
`80005D1C`. Those were **false negatives, not wrong answers**: the containing
functions differ slightly in size between builds —

```
zz_00055e0_   PAL 0xE8    US 0xE4
zz_00057d0_   PAL 0x564   US 0x48C
```

— so the size-sequence aligner won't pair functions that are plainly
counterparts. Below roughly `0x80006000` the builds diverge enough that size
alignment stops working at all.

Documented workaround in `PROJECT_NOTES.md` §4: anchor on a symbol **named in
both maps** and offset by hand. `GSgfxResetUpdate` (PAL `80005D34`,
US `80005C3C`) gives `80005D1C → 80005C24` exactly.

The tool could be hardened to use named-symbol anchors as a fallback when size
alignment fails. Not done — it wasn't asked for, and the manual workaround is
recorded. Worth doing if this region comes up again.

## Status

Every address in the workspace is now resolved. The only things left unverified
are two code words that need a look in Dolphin, unchanged from earlier:

* `9421FFC0` (`stwu r1,-0x40(r1)`) at US `0x80124410`
* the `0x547F` guard halfword at US `0x80129F78`

Neither appears in any table — they are code, and the WiiRD tables cover data.

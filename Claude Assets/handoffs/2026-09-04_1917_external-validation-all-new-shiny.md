# Handoff — 2026-09-04 19:17

**Change:** The PAL code's author supplied their own US conversion of "All new
generated Pokémon are shiny". It is **byte-for-byte identical** to the version
we projected. Recorded as external validation; no code changed.

## Files changed

| Path | What |
|---|---|
| `codes/all_new_pokemon_shiny_US.txt` | New "externally confirmed" block |
| `codes/force_shadow_shiny_US.txt` | Notes the outside corroboration of the `0x80124410` hook address |
| `PROJECT_NOTES.md` | §4 gains a track-record note for the translation method |

## The comparison

All 10 lines match, no differences. Validated independently by that match:

* **All six translated addresses** — the four `04` targets (`80121D44`,
  `8012442C`, `80125408`, `801272CC`), the C2 hook (`C21FA3E4`), and the guard
  fingerprint (`80129F78`). That is `tools/map_convert.py`'s output confirmed
  wholesale.
* **The guard re-target encoding** `A0C69F78` — `lis r6, 0x8013` /
  `lhz r6, 0x9F78(r6)` reaching `0x80129F78`.
* **The sign-extension correction** `3CC08048` / `80C6ADB8`. This is the one
  that could plausibly have gone wrong: `lwz`'s displacement sign-extends, so
  reaching `0x8047ADB8` needs `lis` of high **+1**. Using `lis 0x8047` would
  have produced a pointer `0x10000` off. Their code makes the same correction.
* **The line count** `00000005`.

## Effect on force_shadow_shiny_US

**No new information — that code had no gaps left.** The MRAM dump already
confirmed its hook word (`9421FFC0`), its `r6` = shiny assumption (via the
`mr r27, r6` prologue disassembly), and its global three ways.

One useful cross-check does fall out, though: their code patches `0x8012442C`,
which is `0x80124410 + 0x1C`. That address is only meaningful if the PID
generator's base is `0x80124410` — exactly where our C2 hooks. So the author
independently places the function where we do.

The two codes still differ in *encoding* only: force_shadow_shiny reaches
`0x8047ADB8` via `lis`/`ori` (`3CE08047` / `60E7ADB8`), because that is the form
the PAL original used at that hook; the all-new-shiny code uses `lis`/`lwz` and
therefore needs the +1. Same address, two correct encodings.

## Method track record

Every address this workspace has translated and later had checked has been
right: the four "likely" (run 5–14) anti-AR addresses against an independently
supplied set, and now all six all-new-shiny addresses against the author's own
conversion. Run >= 5 has not yet produced a wrong answer. Noted in
`PROJECT_NOTES.md` §4 — but the confidence tiers stay as they are; two
confirmations are not enough to start trusting short runs.

## Status

Both shipped codes are now confirmed by two independent routes each — static
disassembly of a real US dump, plus (for the all-new-shiny code) the author's
own conversion. Nothing outstanding on either.

Open items elsewhere are unchanged and unaffected: the Strategy Memo pre-seed
causality question, and the `saveBase + 0xAF4` money/TID collision.

# Handoff — 2026-09-04 17:48

**Change:** Converted a second PAL code, "All new generated Pokémon are shiny",
to US, and recorded what it taught us about the save-base pointer.

## Files added / changed

| Path | What |
|---|---|
| `codes/all_new_pokemon_shiny_US.txt` | New — the converted code, disassembly, and what still needs verifying |
| `PROJECT_NOTES.md` | Updated §9 cross-reference table; new §10 note on build-fingerprint guards |

## What the PAL code does

Four `04` writes force a shiny flag to 1 at four sites, and one `C2` at
`801FEC90` (+0x46C into the caller that generates a battle Pokémon from the data
table) replaces the trainer ID in `r7` with the *player's*, read from
`saveBase + 0x9C`.

The C2 is guarded: it reads the halfword at `0x8012E140` — a location inside the
game's own instruction stream — and compares it to `0x547F` (the top half of an
`rlwinm r31, r3, …`). On a build where that doesn't match, it branches past the
pointer dereference and leaves `r7` alone. A build fingerprint, deliberately
placed so the code fails safe rather than crashing on the wrong region.

Also note the C2 uses the trainer ID dword **raw**, where the force-shadow-shiny
code needs the halves swapped (`rotlwi r7,r7,16`). Same save field, two
different consumers.

## What it settled

* **PAL `0x804C8268` is confirmed** as the save-base pointer, and `+0x9C` as the
  player trainer ID — two unrelated codes use the identical global and offset.
  The reading in the previous handoff was correct.
* **`r6` = shiny arg is confirmed.** `041285A0 3B600001` writes `li r27, 1` at
  PID-generator `+0x1C`, i.e. the `r6` argument is parked in `r27` in the
  prologue — matching the annotated symbol
  `zz_generate_pid_gender_r4_nature_r5_shiny_r6_trainer_id_r7`.

## What it did NOT settle

**It gives no information about the US global.** Every address in it is PAL, and
a BSS global's address is only recoverable from a US binary. The blocker from
the previous handoff is unchanged.

## Address translation (all conclusive)

| PAL | US | Where |
|---|---|---|
| `80125EB8` | `80121D44` | +0x12C into a 0x428 fn [run 95] |
| `801285A0` | `8012442C` | +0x1C into the PID generator [run 95] |
| `8012957C` | `80125408` | +0x78 into the in-battle shiny check [run 95] |
| `8012B440` | `801272CC` | +0xEC0 into `zz_battle_pokemon_get_value_with_id_r5` [run 95] |
| `801FEC90` | `801FA3E4` | +0x46C into `zz_gen_battle_pokemon_from_data_table?` [run 123] |
| `8012E140` | `80129F78` | guard fingerprint, +0x58 into a 0x16C fn [run 23] |

## Status

Part 1 (the four `04` writes) is complete and needs no pointer. Part 2 is a
template with the same single blank as `codes/force_shadow_shiny_US.txt`.

Two things to check on US before shipping Part 2: that the halfword at
`0x80129F78` really is `0x547F` (otherwise the guard silently kills the code),
and the save-base global via `0x80128E14 savedataBiosSetNowSavedataPtr`.

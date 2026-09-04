# Handoff — 2026-09-04 22:30

**Change:** `fix_shadow_shiny_glitch_PAL` confirmed working in-game. Both
regions of the shadow shiny glitch fix are now verified in the actual game.
No code changes — status marking only.

## Shipped and confirmed

| Code | Region | Hook | Status |
|---|---|---|---|
| `force_shadow_shiny_US` | US | `80124410` | confirmed in-game |
| `fix_shadow_shiny_glitch_US` | US | `80123FA8` | confirmed in-game |
| `fix_shadow_shiny_glitch_PAL` | PAL | `8012811C` | confirmed in-game |

Together the first two make a shadow Pokémon roll a PID that is shiny against
the player *and* display as shiny while the enemy still owns it — the behaviour
the base game gets wrong.

## What carried the PAL conversion

Two substitutions, nothing else: hook `80123FA8 → 8012811C` and global
`8047ADB8 → 804C8268`. The whole rest of the block was byte-identical, because
the record offsets it uses (`+0xD8`, `+0x14`) and the save offset (`+0x9C`) are
region-independent — established earlier by diffing the two WiiRD v1.01 tables,
and confirmed again here.

That is worth remembering as the general shape: **for a code that only touches
save-relative or record-relative offsets, a region port is just the hook address
and the base pointer.** The expensive part is never the offsets; it is the two
absolute addresses.

## Method track record

Every address this workspace has translated and then had checked in-game or
against an outside source has held:

* four "likely" (run 5–14) anti-AR addresses — confirmed against an
  independently supplied set
* six addresses in the all-new-shiny code — byte-identical to the PAL author's
  own US conversion
* `force_shadow_shiny_US` — confirmed in-game
* `fix_shadow_shiny_glitch_US` — confirmed in-game, including a hook chosen from
  a call-order trace rather than a published reference
* `fix_shadow_shiny_glitch_PAL` — confirmed in-game

The confidence tiers in `Claude Output/PROJECT_NOTES.md` §4 stay as written.
Short alignment runs are still unproven, and the tool's false-negative region
below `0x80006000` is unchanged. A good run of results is not a reason to loosen
the rule that produced them.

## Still open

Unchanged, and none of it blocking:

* whether a Strategy Memo slot's pre-seeded PID *becomes* the next appended
  Pokémon's PID — needs a before/after dump pair
* the purpose of the `u3` global scratch struct and its constant `5`
  (US `804235F4` / PAL `804709F4`)
* the `saveBase + 0xAF4` money/TID collision in the US dump

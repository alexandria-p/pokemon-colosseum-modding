# Handoff — 2026-09-05 00:34

**Change:** `force_all_enemy_ot_to_player` confirmed working in-game on **both**
regions, tested separately. This closes the last soft record. Status marking
only, no code changes.

## Every code, confirmed on both regions

| Code | Hook (US) | Hook (PAL) | Status |
|---|---|---|---|
| `force_shadow_shiny` v2 — shadow-only PID roll | `801FA3E8` | `801FEC94` | ✔ both |
| `fix_shadow_shiny_glitch` — shadow-only OT rewrite | `80123FA8` | `8012811C` | ✔ both |
| `force_all_enemy_ot_to_player` — unconditional OT rewrite | `80123FA8` | `8012811C` | ✔ both |
| `force_shadow_shiny` v1 — all Pokémon (superseded) | `80124410` | — | ✔ US |
| anti-AR codehandler NOPs | — | — | ✔ both |

**Nothing in `Claude Output/codes/` is now unverified.** The bookkeeping gap
noted in the previous handoff — that region coverage for
`force_all_enemy_ot_to_player` was unestablished — is resolved: both were
exercised independently, so neither region's status is an inference from the
other.

## Compatibility

Within a region, `fix_shadow_shiny_glitch` and `force_all_enemy_ot_to_player`
share a hook address (`80123FA8` / `8012811C`) — enable one or the other, never
both. `force_shadow_shiny` v2 hooks a different address and combines with
either.

Useful combinations:

* **v2 + `fix_shadow_shiny_glitch`** — shadow Pokémon roll shiny against you and
  render shiny in battle; nothing else is touched. The intended setup.
* **v2 + `force_all_enemy_ot_to_player`** — the same, but every generated
  Pokémon also carries your OT. This is the pairing that proved v2's shadow-only
  scope, and remains a good diagnostic.

Do not enable `force_shadow_shiny` v1 alongside v2 (v1 forces the flag inside
the shared generator and defeats the gate), nor "Shiny Nation" /
all-new-Pokémon-shiny, which hooks the instruction immediately before v2's hook.

## Method record — final

Every address translated in this project and later checked has held:

* four "likely" (run 5–14) anti-AR addresses — against an independently supplied
  set
* six addresses in the all-new-shiny code — byte-identical to the PAL author's
  own US conversion
* five codes across two regions — confirmed in-game

The confidence tiers in `Claude Output/PROJECT_NOTES.md` §4 stay as written.
Short alignment runs remain unproven and the tool's false-negative region below
`0x80006000` is unchanged; a good run of results is not a reason to loosen the
rule that produced them.

## Still open (research, not blocking)

* whether a Strategy Memo slot's pre-seeded PID *becomes* the next appended
  Pokémon's PID — needs a before/after dump pair
* the purpose of the `u3` global scratch struct and its constant `5`
  (US `804235F4` / PAL `804709F4`)
* the `saveBase + 0xAF4` money/TID collision seen in the US dump

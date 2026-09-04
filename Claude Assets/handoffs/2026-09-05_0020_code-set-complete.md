# Handoff — 2026-09-05 00:20

**Change:** `force_shadow_shiny_PAL` v2 confirmed working in-game. The shadow
shiny code set is complete and confirmed on both regions. Status marking only.

## The finished set

| Code | US | PAL |
|---|---|---|
| `force_shadow_shiny` v2 — shadow-only PID roll | `801FA3E8` ✔ | `801FEC94` ✔ |
| `fix_shadow_shiny_glitch` — shadow-only OT rewrite | `80123FA8` ✔ | `8012811C` ✔ |
| `force_all_enemy_ot_to_player` — unconditional OT rewrite | `80123FA8` ▲ | `8012811C` ▲ |
| `force_shadow_shiny` v1 — all Pokémon (superseded) | `80124410` ✔ | — |
| anti-AR codehandler NOPs | ✔ | ✔ |

✔ confirmed in-game · ▲ reported working, region coverage unconfirmed

Intended pairing, per region: **v2 + the glitch fix + the anti-AR set.** The
first rolls a shadow's PID shiny against the player; the second puts the
player's OT on the record so it renders shiny while the enemy still owns it.

## What the whole job came down to

Starting from one PAL Gecko code and two symbol maps, the work resolved to:

1. **Code addresses** — `.text` function-size alignment between the two maps.
   Every call it made at run ≥ 5 held, across four independent checks.
2. **Data addresses** — not derivable that way. Diffing the two WiiRD tables, or
   reading a DOL/MRAM dump.
3. **Everything else is relative** — record and save offsets are
   region-independent, so a port is *the hook address plus the base pointer*.
   That held for all three ports, exactly.

## Two things worth carrying forward

**A deliberately over-broad code makes a good test instrument.** Running
`force_all_enemy_ot_to_player` alongside v2 meant any Pokémon with a
player-shiny PID would have rendered shiny; only the shadows did. That isolated
the `r30` gate in a way that watching shadow Pokémon alone could not.

**Hook the call site, not the shared function, when scope matters.** v1 hooked
the PID generator and made everything shiny. v2 hooks the argument setup one
instruction before the call, where the game's own is-shadow flag is live in
`r30` — the same register the game branches on itself. Same effect, correct
scope.

## One record still soft

`force_all_enemy_ot_to_player` is marked "reported working" for both regions,
because it was not established which region was actually exercised. The two
differ only in the hook address and the global, and both are statically
verified, so this is a bookkeeping gap rather than a doubt. Worth resolving next
time either is used.

## Still open (research, not blocking)

* whether a Strategy Memo slot's pre-seeded PID *becomes* the next appended
  Pokémon's PID — needs a before/after dump pair
* the purpose of the `u3` global scratch struct and its constant `5`
  (US `804235F4` / PAL `804709F4`)
* the `saveBase + 0xAF4` money/TID collision seen in the US dump

# Handoff — 2026-09-04 21:35

**Change:** New Gecko code — `fix_shadow_shiny_glitch_US`. Gives enemy generated
Pokémon the player's OT Trainer ID / Secret ID, so a PID that is shiny against
the player actually *displays* as shiny during the battle. Designed to run
alongside `force_shadow_shiny_US`.

## Files

| Path | What |
|---|---|
| `Claude Output/codes/fix_shadow_shiny_glitch_US.txt` | new — two variants, full derivation, verification status |
| `Claude Output/PROJECT_NOTES.md` | §9 gains a trainer/record accessor function table |

## The code (shadow-gated — the shipped version)

```
C2123FA8 00000007
281A0000 4182002C
A19A00D8 280C0000
41820020 3D608047
616BADB8 816B0000
280B0000 4182000C
818B009C 919A0014
BB410008 00000000
```

```
cmplwi r26, 0            ; r26 = the record being built
beq    skip
lhz    r12, 0xD8(r26)    ; Shadow Pokemon ID (0 = not a shadow)
cmplwi r12, 0
beq    skip
lis    r11, 0x8047
ori    r11, r11, 0xADB8  ; &saveBasePtr
lwz    r11, 0(r11)
cmplwi r11, 0
beq    skip              ; no save loaded
lwz    r12, 0x9C(r11)    ; player's (SID << 16) | TID
stw    r12, 0x14(r26)    ; record OT SID (+0x14) and OT TID (+0x16)
skip:
lmw    r26, 0x8(r1)      ; overwritten original
```

## The trick that makes it one instruction

The player's ID dword at `saveBase + 0x9C` is `(SID << 16) | TID`, and a Pokémon
record holds OT SID at `+0x14` and OT TID at `+0x16` — **the same halfword
order**. One `lwz`/`stw` pair copies both, no shifting, no masking, no field
indices. Confirmed three ways in the US dump: `save+0x9C` = `8C55208A`,
Makuhita's record `+0x14` = `20D138F5`, and memo entry 9's OT dword = `20D138F5`.

## Why the hook is at the function's *exit*

`0x80123EF0` is the OT setter. Patching its arguments on the way in would be
pointless — the function's own setters run afterwards and would overwrite the
values. `0x80123FA8` (`lmw r26, 0x8(r1)`) is its exit, `r26` still holds the
record, and nothing else touches the OT fields before the caller commits the
record at `0x8012A05C`.

Caller chain: `801F9E84 → 80129F20` (build party into a stack buffer) →
`80129FD0 → 80123EF0` (OT setter, hook inside) → `8012A05C` (commit).

## Key finding: that function sets TID but not SID

`0x80123EF0` takes the OT **Trainer ID** in `r8` and the OT **name** in `r9` —
there is no SID argument. Proof: `r9` is fed to `0x800FA280`
(`zz_get_string_with_msg_id`), and the e-Card callers pass literal TIDs in `r8`
(`li r8, 31121` — Ageto Celebi's known OT ID). The record's OT SID arrives
earlier, in the template copy at `0x80129FB0`.

**That is why Stars' `fixShinyGlitch()` only replaces the TID** — it is all that
function exposes. Writing the whole dword at `record+0x14` sets both halves and
sidesteps the field-index question entirely.

## From Stars' snippet — US addresses now recorded in §9

`fixShinyGlitch()` and `setNPCPokemonShininess()` in
`GoD Tool Package/Reference/Code Snippets CM.swift` are commented-out Swift, but
they carry US addresses that cross-check ours. `shinyLockRAMOffset = 0x801fa3e8`
is exactly the `li r6, 0` we identified independently as the instruction that
wipes any shiny flag set at the caller-side hook.

New entries: `80123EF0` set-OT-info, `80129F20` party builder, `80129280`
trainer_get_data_pointer, `8012A5B0` trainer_get_value_with_index (index 2 =
TID, 1 = OT name msg id), `801254B4` Pokémon set-value-by-index, `801FB1C0`
getter, `800FA280` get_string_with_msg_id, `8011FC74`
battle_pokemon_check_if_shadow, `801FA3E8` shiny lock, `801FA3D8` shadows-only
lock.

> Note: the map calls `801254B4` **`GSmaterialSetTexture`**. That name is wrong
> — it is the Pokémon set-value-by-index setter. Another instance of the map's
> names being less trustworthy than its addresses.

## The shadow gate — verified, after an initial doubt

The gate reads `record+0xD8` (Shadow Pokémon Identifier). I first shipped this
as an unverified variant because I could not show the field was populated that
early. Traced properly, it is:

1. `801F9F78` builds the record, rolls the PID (field 111) and at `801FA418`
   runs shadow setup (`8011FCA4`) — all before the OT setter.
2. `80129F20` copies the whole record verbatim into a stack buffer with
   `8011F5FC` (record ~`0x138` bytes, so `+0xD8` is included).
3. `80129FD0` calls the OT setter on that buffer — our hook.
4. Nothing writes that buffer between the OT setter and the copy-out at
   `8012A018`.

Empirically: opponent array A holds Duskull `+0xD8 = 0000`, Spinarak `0000`,
Makuhita `0001`.

An alternative gate is `bl 0x8011FC74` (`zz_battle_pokemon_check_if_shadow`,
which reads field 194 via `8012640C`). Not used — the direct field read is
cheaper and LR/register juggling is avoided. Noted in the code file as a
fallback if the field read ever proves unreliable.

## Scope

The gated version only rewrites shadow Pokémon's OT, so the e-Card and bonus
Pokémon that also reach `0x80123EF0` keep their distinctive OT IDs. An
unconditional 5-line fallback is kept in the code file for diagnosis.

Note `force_shadow_shiny_US` remains unconditional — it forces every rolled PID
shiny. Gating this code does not narrow that.

## Verification

Confirmed statically: `0x80123FA8` holds `BB410008`; `r26` is the record pointer
and is not reloaded until the instruction we re-emit; the `+0x14`/`+0x9C`
halfword-order match across three records; every encoding round-tripped through
a disassembler; both internal branch offsets land exactly on the re-emitted
`lmw`.

**Not yet tested in-game.**

## Also this session

`Claude Assets/tools/ppc.py` — a small PowerPC disassembler written to read the
dumps. Not yet promoted to a documented tool; it earned its keep here and will
again.

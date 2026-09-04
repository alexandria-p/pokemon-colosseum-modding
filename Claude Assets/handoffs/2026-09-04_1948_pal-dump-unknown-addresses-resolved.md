# Handoff — 2026-09-04 19:48

**Change:** Scraped a PAL MRAM dump (Makuhita on the opponent's side, same
scenario as the earlier US dump), checked the updated NTSC-U WiiRD table v1.01,
and identified all five "unknown_address" locations from the research notes.
Converted the whole lifecycle to US.

## Files added / changed

| Path | What |
|---|---|
| `PID_LIFECYCLE.md` | **New** — the two battle arrays, the five unknowns identified, instruction table, full event trace in both regions |
| `PROJECT_NOTES.md` | §1 layout, §5 save fields from v1.01, battle section rewritten around the two-array model |

## The finding that explains everything: two arrays per side

Scanning both dumps for Pokémon records turned up **two** arrays per side, not
one. The WiiRD tables document only the second.

| | Stride | Order | What |
|---|---|---|---|
| Array A | `0x138` | party order | battle party mirror — same stride **and field layout** as a save entry |
| Array B | `0x154` | send-out order | the WiiRD "In Battle" record |

**`arrayA_base = arrayB_base − 0xAEC`**, holding in both regions and both builds.

| Array | PAL | US |
|---|---|---|
| Your side, A | `804BB2BC` | `8046DE3C` |
| Your side, B | `804BBDA8` | `8046E928` |
| Opponent, A | `804C0504` | `8047306C` |
| Opponent, B | `804C0FF0` | `80473B58` |

Opponent array A held Duskull / Spinarak / Makuhita (party order); array B held
Makuhita / Spinarak / Duskull. Your side's two orders coincided. Don't assume
either.

## The five unknowns

| | PAL | What it is | US |
|---|---|---|---|
| u1 | `8058923C` | PID inside a **heap** battle object | heap — not convertible |
| u2 | `80589D34` | PID field (`record + 4`) of another record | heap — not convertible |
| u3 | `80470A08` | PID slot in a **fixed global** scratch struct | `80423608` |
| u4 | `804C0778` | **opponent array A, slot 3, PID** | `804732E0` |
| u5 | `804BB530` | **your array A, slot 3, PID** | `8046E0B0` |

**u5 is the headline.** `804BB530 = 804BB2BC + 2×0x138 + 4` — it is simply the
battle-side mirror of your **save party slot 3**. That is the whole reason a
caught shadow Pokémon appears there and is then copied to `80455CF4` at battle
end. Not a special "caught Pokémon buffer".

Likewise u4 is opponent array A slot 3 — Makuhita is Trudly's third party
member.

> **Trap recorded.** The `0x87C` gap between u4 and opponent array B slot 1 is a
> coincidence of *this fight*: Makuhita happens to be party slot 3 and battle
> slot 1 simultaneously. It is not a rule. Compute from the array A base.

**u1/u2 are heap and cannot be translated.** Both live in a per-field-Pokémon
object laid out `FFFF0000 / 00000000 / pointer to its array A entry / record`,
PID at `object + 0x10`. The object sat at PAL `8058922C` holding **Duskull**,
and US `8053BCAC` holding **Makuhita** — different address, different occupant,
no delta matching any of our region deltas. Find it by scanning for the
`FFFF0000 / 00000000 / <0x804xxxxx pointer>` signature each session.

**u3 is a fixed global**, identical relative layout in both builds: struct start
= PID − `0x14`, with `1` at `+0x00`, the newest PID at `+0x14`, constant `5` at
`+0x18`. PAL `804709F4` / US `804235F4`. Purpose still undetermined.

## New instruction addresses

`801B204C` → US `801ADCD8`, and the US map names it **`zz_RNG`**. That confirms
the notes' reading of `801B207C` (US `801ADD08`): it is the RNG returning one
16-bit half per call, so the PID is built from two calls — standard Gen-3
construction. The halves are combined at `801285D4`/`801285D8` →
US `80124460`/`80124464`, inside the PID generator.

## Corrections to the source notes

* `80589D30` is labelled "Shadow pokemon identifier". By the record layout it is
  the **species field** (u16 species + u16), so `stw r4, 0x4(r3)` at `80121FC4`
  is a generic "store PID into `record + 4`".
* The notes say "my save base is `0x80455CF4`" and then "Save base =
  `0x804559E0`". The second is right; `80455CF4` is party slot 3's PID field.
  The dump reads `804559E0`, trainer "REX", TID `0x7002`, SID `0xB9EB` —
  matching the playbook's stated TID/SID.
* "Shadow Registry" remains the **Strategy Memo**, and its "PID1" is the owner's
  OT ID dword. Both dumps agree. Geometry is unaffected — memo entry 9's PID
  really is at `saveBase + 0x8320` (PAL `8045DD00`).

## WiiRD NTSC-U table v1.01

Genuinely new content, now folded into `PROJECT_NOTES.md` §5:

* **Hyper Mode** — save entry `+0x188` (`0000` no, `003E` yes), battle entry
  `+0xE8`.
* Status Duration (`+0x68` save, `+0xD0`… see notes), Badly-Poison damage
  counter, Pokérus counter.
* Shadow ID and Purification Counter now documented on the **self** side too, at
  `+0xD8`/`+0xDC` — matching what I had already derived from the US dump.
* "Money" renamed "PokeDollars".

The old NTSC-U file was replaced rather than kept alongside, so the v1.00 →
v1.01 delta above was reconstructed by diffing against the PAL table.

## Still open

* Whether a Strategy Memo slot's pre-seeded PID *becomes* the next appended
  Pokémon's PID. Unchanged — needs a before/after dump pair.
* The purpose of the u3 global scratch struct and its constant `5`.
* `saveBase + 0xAF4` money/TID collision in the US dump. Note the PAL dump gives
  a clean way to settle it if it recurs.

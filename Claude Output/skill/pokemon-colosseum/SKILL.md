---
name: pokemon-colosseum
description: "Debugging and Gecko/AR code creation for Pokémon Colosseum on GameCube, both US (GC6E01) and PAL (GC6P01)"
---

# Pokémon Colosseum Debugging Reference

Covers **US (GC6E01)** and **PAL (GC6P01)**. Dolphin 2603.

Addresses are given as `US / PAL` throughout. **Never reuse an address across
regions** — PAL `.text` is 0x4BE0 bytes larger and every address past the first
divergence differs.

Verified against MRAM dumps of both builds and against the WiiRD offset tables
v1.01 for both regions.

---

## 1. Get the current save base each session

The save base pointer changes every session. Always start here.

| | US | PAL |
|---|---|---|
| Save-base pointer global | `0x8047ADB8` | `0x804C8268` |

Open the Memory panel in Dolphin and read the **big-endian 32-bit word at that
address**. That word is the save base. (Example values seen: US `0x804085E0`,
PAL `0x804559E0` — they will differ for you.)

Recalculate every save-relative address below from the base you just read.

---

## 2. Save data layout (offsets from the save base — identical in both regions)

| Offset | Field |
|---|---|
| `+0x70` | Trainer name, UTF-16BE, one u16 per character |
| `+0x9C` | Trainer **Secret ID** (u16) |
| `+0x9E` | Trainer **ID** (u16) |
| `+0xA0` | Party slot 1 entry — **stride `0x138`** |
| `+0xAF4` | PokéDollars |
| `+0xAF8` | PokéCoupons |
| `+0xB9C` | Box 1 slot 1 entry, same `0x138` stride, 30 per box |
| `+0x82A8` | Strategy Memo entry count (u16) |
| `+0x82AC` | Strategy Memo array — **12 bytes per entry, 386 entries** |

The dword at `+0x9C` is therefore `(SID << 16) | TID`.

### Party slot addresses

**Stride is `0x138`, not `0x140`.**

| Slot | Entry | PID (`entry + 4`) |
|---|---|---|
| 1 | base + 0x0A0 | base + 0x0A4 |
| 2 | base + 0x1D8 | base + 0x1DC |
| 3 | base + 0x310 | base + 0x314 |
| 4 | base + 0x448 | base + 0x44C |
| 5 | base + 0x580 | base + 0x584 |
| 6 | base + 0x6B8 | base + 0x6BC |

### The Pokémon record — one layout, used everywhere

The save entry, and both in-battle arrays, are the **same record type** with the
same internal offsets. Only the array stride differs.

| Off | Field | | Off | Field |
|---|---|---|---|---|
| `+0x00` | species (Gen-3 **internal** index) | | `+0x78` | move 1, then PP (×4) |
| `+0x04` | **PID** | | `+0x88` | held item |
| `+0x07` | gender | | `+0x8A` | HP actual / max / stats |
| `+0x08` | came from (`0B` = Colosseum/XD) | | `+0x98` | EVs (6 × u16) |
| `+0x0A` / `+0x0B` | original / actual font | | `+0xB0` | happiness |
| `+0x0E` | level met | | `+0xD0` | Pokérus counter |
| `+0x0F` | ball | | `+0xD8` | **Shadow Pokémon ID** |
| `+0x14` / `+0x16` | OT SID / OT TID | | `+0xDC` | **Purification counter** |
| `+0x18` | OT name (UTF-16BE) | | `+0xE8` | **Hyper Mode** (`003E` = yes) |
| `+0x2E` | nickname | | `+0xFB` | obedient |
| `+0x44` | original name | | | |
| `+0x5C` | EXP | `+0x60` level | `+0x65` status | `+0x68` status duration |

> Species numbers are **Gen-3 internal indices**, not National Dex numbers. They
> match for #1–251 and diverge above it — Makuhita is `0x14F` (335), not 296.

---

## 3. Shiny mechanics

Gen-3 test: `(TID ^ SID ^ PID_high ^ PID_low) < 8`.

To force shiny for a given save: `PID_LOW = PID_HIGH ^ (TID ^ SID)` → xor
result 0. **`TID ^ SID` is save-file specific — recompute it, never reuse a
constant from an old session.**

Shadow Pokémon specifics:

* The PID is **rolled once, at first encounter**, then locked into save data.
  Catching does **not** re-roll it.
* While the AI trainer owns it, the shiny *display* uses the **AI trainer's**
  TID/SID; after you catch it, your own. So a Pokémon that will be shiny for you
  may look non-shiny during the battle. **That is expected, not a failed patch.**

---

## 4. The two in-battle arrays

Each side has **two** arrays of Pokémon records. The WiiRD tables document only
the second.

| | Stride | Order |
|---|---|---|
| **Array A** — battle party mirror | `0x138` | party order |
| **Array B** — WiiRD "In Battle" table | `0x154` | send-out order |

**`arrayA_base = arrayB_base − 0xAEC`.**

| Array | US | PAL |
|---|---|---|
| Your side, A | `8046DE3C` | `804BB2BC` |
| Your side, B | `8046E928` | `804BBDA8` |
| Opponent, A | `8047306C` | `804C0504` |
| Opponent, B | `80473B58` | `804C0FF0` |

Array A is the battle-side mirror of the party, so **a caught shadow Pokémon
lands in your array A slot 3** (`arrayA + 2*0x138`) and is copied to save party
slot 3 at battle end.

---

## 5. The Strategy Memo (NOT a "shadow registry")

`saveBase + 0x82AC`, 12 bytes per entry, 386 entries, count at `+0x82A8`.

| Off | Field |
|---|---|
| `+0x00` | species (`\| 0x8000` = limited info) |
| `+0x02` | (zero in every entry observed) |
| `+0x04` | **owner's OT ID dword** — `(SID << 16) \| TID` |
| `+0x08` | **PID** |

Two things to be careful about:

* `+0x04` is **not** a PID. It is the OT trainer dword. (Proof: your own
  starters' entries hold your own OT dword there, byte for byte.)
* The array is **append-as-encountered**, not indexed by species, dex number or
  shadow ID. An entry's address **cannot** be computed from a Pokémon's
  identity — scan the array for a matching species or PID.

Every slot past the count holds `species = 0`, `otID = 0` and a **non-zero
pre-seeded PID**. Whether that pre-seed *becomes* the next appended Pokémon's
PID, or is simply overwritten, is unresolved.

---

## 6. Useful breakpoints

| Purpose | US | PAL |
|---|---|---|
| **PID roll/reroll** (`r6` shiny, `r7` trainer ID) | `80124410` | `80128584` |
| — `mr r27, r6`, the real shiny flag | `8012442C` | `801285A0` |
| — PID halves combined into `r31` | `80124460` / `80124464` | `801285D4` / `801285D8` |
| **RNG** (one 16-bit half per call) | `801ADCD8` | `801B204C` |
| Store PID into `record + 4` (`stw r4, 4(r3)`) | `8011DFE8` | `80121FC4` |
| Shadow caught mid-battle (`stwu r0, 8(r5)`) | `8011F628` | `8012379C` |
| Battle end → party slot (`stwu r0, 8(r5)`) | `8012AC90` | `8012EEBC` |
| Shiny check when drawn on screen | `801253D8` | `8012954C` |
| Fires once during the battle-start swirl | `801EE80C` | `801F3080` |

The PID generator's prologue parks its arguments:
`mr r24,r3 / mr r25,r4 (gender) / mr r26,r5 (nature) / mr r27,r6 (shiny)`.

---

## 7. PID lifecycle for a shadow Pokémon

```
Battle begins (swirl)  →  old PID copied from the Strategy Memo entry
PID generated          →  RNG called twice, halves combined
first store            →  into a record's PID field (record + 4)
                       →  global scratch struct (US 80423608 / PAL 80470A08)
                       →  opponent array A slot, and a heap battle object
Thrown onto the field  →  written back to the Strategy Memo entry
Caught mid-battle      →  written to YOUR array A slot 3
Battle ends            →  copied to save party slot 3 — now permanent
```

The heap battle object is laid out
`FFFF0000 / 00000000 / pointer to its array A entry / the record`, so its PID is
at `object + 0x10`. **Its address is heap-dependent** — it moves between
sessions and builds, and which Pokémon occupies it varies. Find it by scanning
for the `FFFF0000 / 00000000 / <0x804xxxxx pointer>` signature; never hardcode it.

---

## 8. Writing Gecko codes

```
C2<addr without leading 8> <number of 8-byte lines>
<instruction> <instruction>
...
```

* The C2 branch **overwrites** the instruction at the hook address, and it is
  *not* re-executed for you — **re-emit it as the last instruction of the
  block.** For a hook on a function's first instruction that is the prologue
  `stwu r1,-N(r1)`.
* Pad to a whole number of 8-byte lines with `00000000`. The count is **lines,
  not instructions** — count them, don't guess.
* Hooking a function's *first* instruction is the safe place to overwrite
  argument registers `r3`–`r10`; the callee has not read them yet. Do **not**
  clobber `LR` there — it still holds the return address and has not been
  spilled, so a `bl` corrupts the return unless you save and restore it.
* **Check what runs between a caller-side hook and the call.** Example: a hook
  at US `801FA3E4` is followed by `li r6, 0`, which wipes any shiny flag set at
  the hook. Set `r7` there and force the flag inside the callee instead.
* `ori` **zero-extends**; `lwz`/`stw`/`addi` displacements **sign-extend**. To
  reach `0x8047ADB8`: `lis 0x8047` + `ori 0xADB8`, but `lis 0x8048` +
  `lwz 0xADB8`. Getting this wrong puts the pointer `0x10000` off.
* **Build-fingerprint guard** — worth copying. Read a halfword out of the game's
  own code and compare, so a region-specific code fails safe instead of
  dereferencing garbage:

  ```
  lis    r6, 0x8013
  lhz    r6, 0x9F78(r6)   ; US 0x80129F78 (PAL 0x8012E140)
  cmplwi r6, 0x547F
  bne    skip
  ```

  Pick a fingerprint word from an instruction with **no relocation** (`rlwinm`,
  `li`, arithmetic) so it survives the region port.

### Display shiny vs actual shiny

Four write-patches are commonly used for "all Pokémon shiny". Three of them —
US `80121D44`, `80125408`, `801272CC` — are **display only**. The one that
actually changes the rolled PID is US `8012442C` (`mr r27, r6` in the
generator). If a Pokémon looks shiny but isn't, that is why.

---

## 9. Required: Action Replay codehandler NOP patches

Needed or Colosseum detects the code handler. Use **JIT64 SC** mode, not Cached
Interpreter.

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

---

## 10. Dolphin workflow rules

* **Never do an in-Dolphin memory *value search*** — it hangs Dolphin. Instead
  ask for `Memory → Export → Dump MRAM` and analyse the `.raw` (the path is
  under `Options → Configuration → Paths → Dump Path`).
* **Always request a fresh dump.** Never reason from an old one.
* Re-read the save-base pointer at the start of every session and recompute
  everything from it.
* PkHeX check: set `Options → GameCube → Device Settings → Slot A` to *GCI
  Folder*; save at an in-game PC to the Slot A card; in Dolphin
  `Tools → Memory Card Manager` open the card, delete any existing Colosseum
  save, `Import` the latest `.gci`; then open the memory-card file in PkHeX.

---

## 11. Region conversion

* **Code addresses** — align the two symbol maps by their `.text` function-size
  sequences; long runs of identical sizes give an exact mapping. Below roughly
  `0x80006000` the builds diverge too much for this; anchor on a symbol named in
  both maps instead.
* **Data / BSS addresses** — cannot be derived that way and **must not be
  extrapolated**; observed PAL→US deltas vary per variable (`0x4D480`,
  `0x4D498`, `0x4D4B0`) and bear no relation to the `.text` size difference.
  Diff the two WiiRD offset tables, or read the address out of a dump.
* Published code archives that carry both regions give the mapping of every
  address a code touches, for free.

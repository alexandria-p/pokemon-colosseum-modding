# Shadow Pokémon PID Lifecycle — PAL and US

Derived from two MRAM dumps of the same scenario (Makuhita, first shadow
encounter, opponent's side of the field): `mem1 - makuhita on opponent side of
field PAL.raw` and `mem1 - US shadow mak mid-battle.raw`. Every address below
was read out of one of those dumps unless marked otherwise.

---

## 1. The two battle arrays — this is the key to everything

Each side of a battle has **two** arrays of Pokémon records, not one. The WiiRD
tables document only the second.

| | Stride | Order | What it is |
|---|---|---|---|
| **Array A** — battle party mirror | **`0x138`** | party order | the party as it exists during battle; same stride *and* field layout as a save entry |
| **Array B** — WiiRD "In Battle" table | **`0x154`** | send-out order | the battle-display record |

**`arrayA_base = arrayB_base − 0xAEC`**, confirmed in both regions and both
builds.

| Array | PAL | US |
|---|---|---|
| Your side, A | `804BB2BC` | `8046DE3C` |
| Your side, B | `804BBDA8` | `8046E928` |
| Opponent, A | `804C0504` | `8047306C` |
| Opponent, B | `804C0FF0` | `80473B58` |

Verified contents (PAL / US): your side A and B both held Umbreon then Espeon.
Opponent A held Duskull, Spinarak, Makuhita — party order. Opponent B held
Makuhita, Spinarak, Duskull — the reverse. The two orders coincided for the
player and were reversed for Trudly in this fight; do not assume either.

**Both arrays hold the same record type as a save entry**, with identical
internal offsets — species `+0x00`, PID `+0x04`, OT SID/TID `+0x14`/`+0x16`,
OT name `+0x18`, nickname `+0x2E`, shadow ID `+0xD8`, purification `+0xDC`,
Hyper Mode `+0xE8`. Only the array stride differs. Verified field by field
across both dumps; full layout in `Claude Output/PROJECT_NOTES.md` §5.

---

## 2. The five unknown addresses, identified

| | PAL | What it actually is | US |
|---|---|---|---|
| `unknown_address_1` | `8058923C` | PID field of a record inside a **heap** battle object | **heap — see below** |
| `unknown_address_2` | `80589D34` | PID field (`record + 4`) of another such record | **heap — see below** |
| `unknown_address_3` | `80470A08` | PID slot in a **fixed global** scratch struct | `80423608` |
| `unknown_address_4` | `804C0778` | **opponent array A, slot 3, PID** | `804732E0` |
| `unknown_address_5` | `804BB530` | **your array A, slot 3, PID** | `8046E0B0` |

### u4 and u5 — the important ones

`804C0778 = 804C0504 + 2×0x138 + 4` — opponent array A **slot 3**. Makuhita is
Trudly's third party member.

`804BB530 = 804BB2BC + 2×0x138 + 4` — your array A **slot 3**. This is simply
**the battle-side mirror of your save party slot 3**, which is why a caught
shadow Pokémon appears there and is copied to save party slot 3
(`saveBase + 0x314`, PAL `80455CF4`) when the battle ends. It is not a special
"caught Pokémon buffer"; it was empty in the PAL dump because nothing had been
caught yet and the party held only two Pokémon.

> **Caveat.** The `0x87C` gap between `804C0778` (u4) and opponent array B slot 1
> is a **coincidence of this particular fight** — Makuhita happens to be party
> slot 3 *and* battle slot 1. It is not a general rule. Always compute from the
> array A base.

### u3 — a fixed global

Identical relative layout in both builds. Struct start = PID − `0x14`:

```
+0x00  00000001
+0x04  00000000  ×4
+0x14  <most recently generated PID>
+0x18  00000005
```

PAL struct `804709F4`, US struct `804235F4`. Purpose not determined — it is the
"staging area" of the original notes. The `5` was constant across both dumps.

### u1 and u2 — heap, and NOT convertible

Both are inside a heap-allocated per-field-Pokémon battle object:

```
+0x00  FFFF0000
+0x04  00000000
+0x08  pointer to this Pokémon's array A entry
+0x0C  the Pokémon record   (species +0x00, PID +0x04, ...)
```

so the PID sits at `object + 0x10`.

| | PAL dump | US dump |
|---|---|---|
| object | `8058922C` | `8053BCAC` |
| → array A entry | `804C0504` (Duskull) | `804732DC` (Makuhita) |
| PID field | `8058923C` ( = u1) | `8053BCBC` |

The object address differs between builds by no rule that matches any of our
region deltas, and **which Pokémon occupies it varies** — Duskull in the PAL
dump, Makuhita in the US dump. **u1 and u2 must be re-found every session and
cannot be translated PAL→US statically.** Find them by scanning for the
`FFFF0000 / 00000000 / <0x804xxxxx pointer>` signature.

> **Correction.** The notes label `80589D30` "Shadow pokemon identifier". By the
> record layout it is the **species field** (u16 species + u16). The instruction
> `stw r4, 0x4(r3)` at `80121FC4` therefore writes the PID into `record + 4` —
> a generic "store PID into a Pokémon record", which is exactly what it looks
> like.

---

## 3. Instruction addresses

| Purpose | PAL | US | Confidence |
|---|---|---|---|
| PID roll / reroll function (`r6` shiny, `r7` trainer ID) | `80128584` | `80124410` | conclusive [95] |
| — PID halves combined into `r31` | `801285D4` / `801285D8` | `80124460` / `80124464` | conclusive [95] |
| **RNG** — US symbol `zz_RNG` | `801B204C` | `801ADCD8` | conclusive [123] |
| — the return the notes observed | `801B207C` | `801ADD08` | conclusive [123] |
| Store PID into record+4 (`stw r4, 4(r3)`) | `80121FC4` | `8011DFE8` | conclusive [32] |
| Shadow caught mid-battle (`stwu r0, 8(r5)`) | `8012379C` | `8011F628` | conclusive [95] |
| Battle end → party slot (`stwu r0, 8(r5)`) | `8012EEBC` | `8012AC90` | conclusive [54] |
| Shiny check when drawn on screen | `8012954C` | `801253D8` | conclusive [95] |
| Fires once during battle-start swirl | `801F3080` | `801EE80C` | conclusive [101] |

The PAL function at `801B204C` maps to a US symbol literally named `zz_RNG`,
which confirms the notes' reading of `801B207C`: it is the RNG returning one
16-bit half per call, so the PID is built from **two** calls — standard Gen-3
construction.

---

## 4. The event trace, both regions

```
Battle begins (swirl animation)
  │  old PID copied: Strategy Memo entry ──► heap battle object record
  │      PAL memo entry 9 PID 8045DD00 ──► 8058923C (u1)
  ▼
PID is generated
  │  RNG called twice           PAL 801B207C          US 801ADD08
  │  halves combined into r31   PAL 801285D4/D8       US 80124460/64
  ▼
first store — into a record's PID field (record + 4)
  │  PAL instr 80121FC4  stw r4, 4(r3)      US instr 8011DFE8
  │  PAL 80589D34 (u2)                      US heap equivalent
  ▼
written to the global scratch struct
  │  PAL 80470A08 (u3)                      US 80423608
  ▼
written to the heap object record and to opponent array A slot 3
  │  PAL 8058923C (u1) and 804C0778 (u4)    US 804732E0
  ▼
Shadow Pokémon thrown onto the field
  │  written back to the Strategy Memo entry
  │  PAL 8045DD00                           US saveBase + 0x8320
  ▼
Shadow Pokémon caught mid-battle
  │  PAL instr 8012379C  stwu r0, 8(r5)     US instr 8011F628
  │  written to YOUR array A slot 3
  │  PAL 804BB530 (u5)                      US 8046E0B0
  ▼
Battle ends with it caught
  │  PAL instr 8012EEBC  stwu r0, 8(r5)     US instr 8012AC90
  │  copied to save party slot 3
  │  PAL 80455CF4                           US saveBase + 0x314
  ▼
done — the PID is now permanent
```

---

## 5. Two notes on the source material

* The original notes say "my save base is `0x80455CF4`" and then
  "Save base = `0x804559E0`". The second is right; `80455CF4` is party slot 3's
  PID field. The PAL dump reads `804559E0`, trainer "REX", TID `0x7002`,
  SID `0xB9EB` — matching the playbook's stated TID/SID.
* What the notes call the "Shadow Registry" is the **Strategy Memo**, and its
  "PID1" is the **owner's OT ID dword**, not a PID. Both dumps confirm this.
  The geometry is unaffected: memo entry 9's PID really is at
  `saveBase + 0x8320`. See `Claude Output/PROJECT_NOTES.md` §5.

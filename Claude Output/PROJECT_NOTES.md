# Pokémon Colosseum Modding — Project Schema & Rules

Living reference for this workspace. Last updated 2026-09-04.

---

## 1. Workspace layout

```
E:\Pokemon Colosseum Modding\
│
├── Claude Assets\                    <- working material for Claude
│   ├── handoffs\                     dated write-up per major change (§13)
│   └── tools\map_convert.py          PAL <-> US address translator (§4)
│
├── Claude Output\                    <- deliverables
│   ├── PROJECT_NOTES.md               this file
│   ├── PID_LIFECYCLE.md               shadow PID lifecycle, both regions
│   └── codes\                        finished Gecko / AR codes
│
├── Pokemon Colosseum - Offsets and Maps\
│   ├── GC6E01 annotated.map           US symbol map (annotated — the good one)
│   ├── GC6P01.map                     PAL symbol map (mostly zz_ stubs)
│   ├── Pokemon_Colosseum_NTSC-U_WiiRD_Offset_Table\   v1.01
│   ├── Pokemon_Colosseum_PAL_WiiRD_Offset_Table\      v1.01  (diff these, §6)
│   └── Pokemon_Colosseum_NTSC-U_AR_Offset_Table\      AR dialect of the same
│
├── Existing Gecko and AR codes by Ralf\   ~460-476 published codes per file,
│                                           US and PAL, Gecko and AR (§6)
├── GoD-Tool by Stars\                 file-format / FSYS reference (§12)
├── pokemon-colosseum.skill         PAL Dolphin debugging playbook — a copy of
│                                   the INSTALLED skill of the same name.
│                                   Contains known errors; see §5 and the
│                                   warning below.
└── OBSOLETE - Original Attempt & Knowledge - PAL Gecko shiny hunting.zip
                                    superseded PAL research and codes.
                                    Do not use as a source.
```

> **Placement rule.** Anything generated in a chat session goes in
> **`Claude Assets\`** (working material — tools, handoffs, process records) or
> **`Claude Output\`** (deliverables — codes and documentation). Never write to
> the source folders: the maps, offset tables, Ralf's code archive and GoD-Tool
> are inputs and stay untouched.
>
> A name prefixed **`OBSOLETE`** means superseded — do not read it as a source
> or cite it. Currently: the original-attempt zip.

> **Warning — the installed `pokemon-colosseum` skill carries known errors.**
> The `.skill` file at the root is a copy of a skill that is *installed and
> live*, so any session that loads it inherits its mistakes. Three are confirmed
> wrong by both WiiRD tables and both MRAM dumps:
>
> * party/box slot stride given as `0x140` — it is **`0x138`** (§5)
> * the `+0x82AC` array called a "Shadow Registry" — it is the **Strategy
>   Memo**, append-ordered, 386 entries (§5)
> * its "PID1" field — that is the owner's **OT ID dword**, not a PID (§5)
>
> Its breakpoint list, event trace and Dolphin workflow rules are sound and are
> reflected in `Claude Output/PID_LIFECYCLE.md` §11. **Fixing the installed
> skill is worth doing** — until then, treat these notes as authoritative where
> the two disagree.

## 2. The two builds — never mix them up

| | US | PAL |
|---|---|---|
| Game ID | **GC6E01** | **GC6P01** |
| Map file | `GC6E01 annotated.map` | `GC6P01.map` |
| Symbol quality | Real Colosseum symbols (`hero.a`, `memcard.a`, `fight.a`, …) plus hand annotations | Almost entirely `zz_<addr>_` placeholders |
| `.text` end | `0x8026635C` | `0x8026AF3C` |

PAL `.text` is **0x4BE0 bytes larger** than US. Every address past the first
divergence differs, so *no* PAL address may be reused on US without translation.

JP is `GC6J01`; GoD-Tool knows all three IDs
(`Sources/Shared/Core/Engines/Colosseum/ColosseumEngine.swift`).

## 3. Map file format and its quirks

Line format (whitespace-separated):

```
<addr8hex> <size8hex> <vaddr8hex> <align> <symbol> [<archive.a> <object.o>] [# was: <old name>]
```

Quirks that bit us and will bite again:

* Only the `.text section layout` block is meaningful. The `.data section layout`
  block at the bottom holds a single stray line in each file — **there are no
  data/BSS symbols in either map.** Globals must be found another way (§6).
* The tail of the `.text` list appends unrelated high-memory blobs
  (US `0x809F…`–`0x809FF…`, PAL `0x810A…`–`0x810C…`). Filter to `< 0x80400000`
  when treating the list as the code segment.
* A few early entries have `size` fields that overlap the next symbol's address
  (e.g. US `80005544` claims `0x180` but the next symbol starts `0x9C` later).
  Below roughly `0x80006000`, treat `size` as a hint, not gospel.
* `# was:` comments record where the original name dump was misaligned and the
  annotator corrected it. Symbol *names* in these maps are therefore only
  moderately trustworthy; symbol *addresses and sizes* are reliable.

## 4. Rule: how to translate an address between builds

Use `Claude Assets/tools/map_convert.py`. It finds the two symbol maps by
searching upward from itself for filenames containing `GC6P01` / `GC6E01`, so
moving files around does not break it (this already happened once). Method: both
builds are the same source, so the
**sequence of function sizes** in `.text` is nearly identical. A `difflib`
sequence alignment over those size sequences produces long runs of exactly
corresponding functions; inside a run,

```
us_addr = us_func_start + (pal_addr - pal_func_start)
```

```bash
python "Claude Assets/tools/map_convert.py" 0x80128584
```

```bash
python "Claude Assets/tools/map_convert.py" --us2pal 0x80124410
```

**Track record.** Every call this method has made has since been confirmed:
the four "likely" (run 5–14) anti-AR addresses against an independently
supplied set, and all six addresses in the all-new-shiny code against the PAL
author's own US conversion, which came back byte-for-byte identical to ours.
Code addresses translated at run >= 5 have not yet been wrong.

**Confidence rule — read the reported run length:**

| Matched run | Meaning |
|---|---|
| >= 20 consecutive functions | Conclusive. Ship it. |
| 5–19 | Likely. Sanity-check the opcode in Dolphin before shipping. |
| 1–4, or "NO ALIGNED COUNTERPART" | Guess. Must be verified against the real DOL. |

Limits: **code only**. Data and BSS globals are not in the maps and this method
cannot translate them.

**Known false negatives below ~`0x80006000`.** The two builds diverge enough
there that some counterpart functions differ in size and the aligner refuses to
pair them — e.g. `zz_00055e0_` is `0xE8` PAL / `0xE4` US, `zz_00057d0_` is
`0x564` / `0x48C`. "NO ALIGNED COUNTERPART" in that region means *the tool
can't tell*, not *no counterpart exists*. Fall back to anchoring on a symbol
that is **named in both maps** and offsetting by hand: `GSgfxResetUpdate`
(PAL `80005D34`, US `80005C3C`) correctly gives `80005D1C → 80005C24`. Both
anti-AR addresses the tool missed were recovered this way and later confirmed.

## 5. Colosseum runtime memory schema (PAL values unless marked)

### Save data
* **Save-base pointer** — PAL `0x804C8268`, US `0x8047ADB8`. A global holding
  the pointer to the live save struct. **Re-read every session; the save base
  moves.** Session examples: PAL `0x804559E0`, US `0x804085E0`.

  The US address is confirmed three ways: the NTSC-U WiiRD table, and in the
  dump `savedataBiosSetNowSavedataPtr` at `0x80128E14`, which disassembles to

  ```
  cmplwi r3, 0
  beqlr                    ; ignore a null pointer
  stw    r3, -0x5A68(r13)
  blr
  ```

  with `r13 = 0x80480820`, giving `0x80480820 - 0x5A68 = 0x8047ADB8`.

* **US SDA bases** (from `__init_registers`, `0x80003324`–`0x80003338`):
  `r13 = 0x80480820`, `r2 = 0x804836A0`, initial `r1 = 0x8048E738`. Useful when
  a global is reached as `lwz rX, off(r13)` rather than `lis`/`ori`.
* `saveBase + 0x70` — trainer name, **UTF-16BE**, one u16 per character
  (dump read `"WES"`).
* `saveBase + 0x9C` — **Trainer Secret ID** (u16); `+0x9E` — **Trainer ID**
  (u16). So the dword at `+0x9C` is `(SID << 16) | TID`. The PID generator
  wants `(TID << 16) | SID`, hence the `rotlwi rX,rX,16` in the shadow-shiny
  code; the battle-Pokémon generator hook takes the dword raw.
* `saveBase + 0xA0` — party slot 1 entry. **Entry stride `0x138`** (party and
  boxes alike). PID is at `+0x04` into the entry, i.e. `base + 0xA4` for slot 1.

  | Slot | Entry | PID |
  |---|---|---|
  | 1 | base + 0x0A0 | base + 0x0A4 |
  | 2 | base + 0x1D8 | base + 0x1DC |
  | 3 | base + 0x310 | base + 0x314 |
  | 4 | base + 0x448 | base + 0x44C |
  | 5 | base + 0x580 | base + 0x584 |
  | 6 | base + 0x6B8 | base + 0x6BC |

  > **Correction.** The `.skill` playbook lists this stride as `0x140`
  > (slot 2 PID `0x1E4`, slot 3 `0x324`, …). That is wrong. Both WiiRD tables
  > give `0x138` consistently across 6 party and 30 box slots, and the
  > playbook's own worked example proves it: it observed slot 3's PID at
  > `0x80455CF4` with base `0x804559E0`, i.e. offset `0x314` — the `0x138`
  > value, not `0x324`.

* **The Pokémon record — one layout, used everywhere.** The save entry, the
  battle array A entry and the battle array B entry are the same record type
  with identical internal offsets; only the array stride differs (`0x138`
  vs `0x154`). Verified field by field against both dumps. Offsets are
  **relative to the entry start**:

  | Off | Field | | Off | Field |
  |---|---|---|---|---|
  | `+0x00` | species (internal index) | | `+0x78` | move 1 (then PP, ×4) |
  | `+0x04` | PID | | `+0x88` | held item |
  | `+0x07` | gender | | `+0x8A` | HP actual / max / stats |
  | `+0x08` | came from | | `+0x98` | EVs (6 × u16) |
  | `+0x0A`/`+0x0B` | original / actual font | | `+0xA5`… | DVs (odd bytes) |
  | `+0x0C` | location caught | | `+0xB0` | happiness |
  | `+0x0E` | level met | | `+0xB2`… | contest values, ribbons |
  | `+0x0F` | ball | | `+0xCA` | Pokérus |
  | `+0x10` | OT gender | | `+0xCC` | ability used |
  | `+0x14`/`+0x16` | OT SID / OT TID | | `+0xCF` | marks |
  | `+0x18` | OT name (UTF-16BE) | | `+0xD0` | Pokérus counter |
  | `+0x2E` | nickname | | **`+0xD8`** | **Shadow Pokémon ID** |
  | `+0x44` | original name | | **`+0xDC`** | **Purification counter** |
  | `+0x5C` | EXP | | **`+0xE8`** | **Hyper Mode** (`0000` no, `003E` yes) |
  | `+0x60` | level | | `+0xFB` | obedient |
  | `+0x65` | status | | | |
  | `+0x68`/`+0x6A` | status duration / badly-poison counter | | | |

  > **Correction.** An earlier revision of these notes listed shadow ID /
  > purification / Hyper Mode as entry-relative `+0x178` / `+0x17C` / `+0x188`.
  > Those are the WiiRD tables' **save-base-relative** addresses for Pokémon 1;
  > subtract the `+0xA0` entry base to get the real entry offsets above.

  v1.01 also renames Money to PokeDollars.
* Box 1 slot 1 entry — `base + 0xB9C`, same `0x138` stride, 30 per box.
* `saveBase + 0xAF4` — Money; `+0xAF8` — PokéCoupons.
* `saveBase + 0x7974` — PC item slot 1 (u16 item, u16 quantity, 4-byte stride).
* `saveBase + 0x82A8` — **Strategy Memo**. u16 entry count, then an entry array
  at `+0x82AC`, **12 bytes per entry**, 386 entries (last at `+0x94B8`).
  Verified against a US MRAM dump. Entry layout:

  | Off | Size | Field |
  |---|---|---|
  | `+0x00` | u16 | species, internal index (`\| 0x8000` = limited info) |
  | `+0x02` | u16 | (zero in every entry observed) |
  | `+0x04` | u32 | **owner's OT ID dword** — `(SID << 16) \| TID` |
  | `+0x08` | u32 | **PID** |

  > **Correction — this is not a "shadow registry".** The playbook describes it
  > as 48 shadow entries with a "PID1" and a "PID2", where
  > `entry N PID2 = registry + N*12 + 4`. The geometry is right but the fields
  > are misnamed: what it calls PID1 is the **OT trainer-ID dword**, and only
  > PID2 is a PID. Confirmed in the dump — memo entries 0 and 1 are the
  > player's own Umbreon and Espeon, and their "PID1" is `8C55208A`, byte-for-
  > byte the player's own OT dword from `+0x9C`.

  > **Ordering — resolved: append-as-encountered, not indexed by identity.**
  > The dump had count = 10 with entries 0–9 populated: the player's two
  > starters at 0–1, and the just-encountered shadow Makuhita last at index 9
  > (species `0x14F`, OT `20D138F5` = the AI trainer Trudly). Makuhita's dex
  > number is 296 and its shadow ID is 1, so index 9 is neither. **A Pokémon's
  > entry address cannot be computed from its identity** — scan the array for a
  > matching species or PID instead.

  > **All 386 PID fields are pre-seeded.** Every slot past the count has
  > `species = 0` and `otID = 0` but a **non-zero, random-looking PID**
  > (376 of 376). So the game does write PID-shaped values into the whole array
  > up front, which is what the playbook saw as "pre-generated PIDs". Whether a
  > slot's pre-seed *becomes* the PID of the next Pokémon appended there, or is
  > simply overwritten by an independently rolled one, is **not determinable
  > from a single post-encounter dump**. To settle it: dump before an encounter,
  > note the PID in slot `[count]`, encounter something, dump again, compare.
  > (A naive Gen-3 LCG test on these values does not discriminate — random
  > dwords pass it at the same rate.)

### Battle (absolute addresses — these are NOT save-relative)

| | PAL | US |
|---|---|---|
| Your side, Pokémon 1 | `804BBDA8` | `8046E928` |
| Opponent, Pokémon 1 | `804C0FF0` | `80473B58` |
| Button activator (`28…`) | `8044F0A8` | `80401C28` |

**There are TWO arrays per side.** The WiiRD tables document only the second.
Full treatment in `Claude Output/PID_LIFECYCLE.md` §1.

| | Stride | Order | What |
|---|---|---|---|
| Array A — battle party mirror | `0x138` | party order | the party during battle; **same stride and field layout as a save entry** |
| Array B — the WiiRD "In Battle" table | `0x154` | send-out order | the battle-display record |

**`arrayA_base = arrayB_base − 0xAEC`** in both regions and both builds.

| Array | PAL | US |
|---|---|---|
| Your side, A | `804BB2BC` | `8046DE3C` |
| Your side, B | `804BBDA8` | `8046E928` |
| Opponent, A | `804C0504` | `8047306C` |
| Opponent, B | `804C0FF0` | `80473B58` |

Array A is where a caught shadow Pokémon lands (your slot 3 =
`arrayA + 2*0x138`), and it is copied to the save party at battle end. Six slots
per side in array B; US self `8046E928 … 8046EFCC`, opponent
`80473B58 … 804741FC`.

**The in-battle entry is the save entry.** Same record type, same offsets
throughout — see the layout table in §5. There are no battle-only fields: shadow
ID `+0xD8`, purification `+0xDC` and Hyper Mode `+0xE8` exist in the save entry
too, at the same offsets. The playbook's "shadow check at battle struct `+0xD8`"
is that field. WiiRD v1.01 documents `+0xD8`/`+0xDC` on **both** sides, matching
the dumps.

**Heap battle object.** One per active field Pokémon, layout
`FFFF0000 / 00000000 / pointer to its array A entry / the Pokémon record`, so
its PID sits at `object + 0x10`. Observed at PAL `8058922C` (holding Duskull)
and US `8053BCAC` (holding Makuhita). **Heap-allocated: the address is not
stable between builds or sessions, and which Pokémon occupies it varies.** Find
it by scanning for the `FFFF0000 / 00000000 / <0x804xxxxx pointer>` signature —
never by a static PAL→US conversion.

**Global PID scratch struct.** PAL `804709F4`, US `804235F4`; `1` at `+0x00`,
the most recently generated PID at `+0x14`, constant `5` at `+0x18`. Fixed
addresses, verified in both dumps.

A further PID copy sat in a display/model struct — PAL `80A67AD0`,
US `809C8210`.

### Species numbering

The "Pokemon Modifier" field is a **Gen-3 internal species index**, not a
National Dex number. They coincide for #1–251 and diverge above it: the dump's
Makuhita reads `0x014F` = 335 (dex 296), while Umbreon/Espeon read `0x00C5`/
`0x00C4` = 197/196, matching their dex numbers.

### Rule: never extrapolate a data address between regions

The PAL→US deltas for globals are close but **not equal**, because the
intervening `.bss` allocations changed size independently:

| Global | Delta |
|---|---|
| Save-base pointer | `0x4D4B0` |
| Battle, your side | `0x4D480` |
| Battle, opponent | `0x4D498` |
| Button activator | `0x4D480` |

They are also nothing like the `0x4BE0` `.text` size difference — an earlier
estimate built on that heuristic was off by ~`0x48A00`. Data addresses must be
looked up per-variable, never shifted.

## 6. Rule: finding a data/BSS global on the other build

The maps can't do it. Three working routes, cheapest first:

0. **Check the WiiRD offset tables.** `Pokemon Colosseum - Offsets and Maps/Pokemon_Colosseum_NTSC-U_WiiRD_Offset_Table/`
   and `Pokemon Colosseum - Offsets and Maps/Pokemon_Colosseum_PAL_WiiRD_Offset_Table/` are the same document per
   region. Diffing them gives every region-varying address for free — that is
   how the US save-base pointer was confirmed. **Always look here first.**

   Both are at **v1.01** and the diff is now clean: the *only* differences are
   the base pointer, the in-battle absolute addresses, and the button activator.
   Every save-relative offset is identical across regions. Keep the two files at
   the same version — a version mismatch makes the diff show spurious entries.

Then:

1. **Symbol-guided (preferred, exact).** Find the accessor function in the
   annotated US map and read its instructions. Example: US
   `0x80128E14 savedataBiosSetNowSavedataPtr  memcard.a savedataBios.o` is a
   16-byte function — its single `stw` names the save-base global outright
   (an `lis`/`stw` pair, or `stw rX, off(r13)` against the SDA base).
   Neighbour: `0x80128E04 gamedataBiosGetGamedataAtttestPtr`.
2. **MRAM dump.** Run the game with a save loaded, dump MRAM, then scan the dump
   for a big-endian word equal to the known save-base address; where it is found
   is the global.

Resolved so far: save-base pointer, PAL `0x804C8268` → US `0x8047ADB8`.

**Route 0b — Ralf's published code archive.** `Existing Gecko and AR codes by
Ralf/` holds ~460-476 codes per file, in four files: US/PAL x Gecko/AR. Since
the same code is published for both regions, **finding a code in both files
gives the PAL->US mapping of every address it touches, for free.** It is also
the fastest way to check whether something already exists before building it.
(No force-shadow-shiny code in there — ours is original.)

**The AR offset table dialect.** `Pokemon_Colosseum_NTSC-U_AR_Offset_Table/` is
the same data as the WiiRD table in Action Replay form: `42<pointer>` followed
by a **halfword index**, not a byte offset. So `4247ADB8 004Exxxx` is
`saveBase + 0x4E*2 = +0x9C` = Trainer Secret ID. Double the index to get the
byte offset used everywhere else in these notes.

### Encoding a global into a code — the sign-extension trap

`ori` **zero-extends** its immediate; `lwz`/`stw`/`addi` displacements
**sign-extend**. So the same global splits two different ways:

| Form | `0x8047ADB8` (US) | `0x804C8268` (PAL) |
|---|---|---|
| `lis rX, H` + `ori rX, rX, L` | `lis 0x8047` / `ori 0xADB8` | `lis 0x804C` / `ori 0x8268` |
| `lis rX, H` + `lwz rX, L(rX)` | `lis 0x8048` / `lwz 0xADB8` | `lis 0x804D` / `lwz 0x8268` |

Rule: for the `lwz`/`stw` form, if the low halfword is ≥ `0x8000`, the `lis`
must carry **high + 1**. Both existing codes rely on this — one uses each form.

## 7. How shininess works in Colosseum (game rules, not code)

* Gen-3 shiny test: `(TID ^ SID ^ PID_high ^ PID_low) < 8`.
* A shadow Pokémon's PID is **rolled once, at first encounter**, and locked into
  save data. Catching it does **not** re-roll it.
* While the AI trainer owns it, the shiny *display* uses the **AI trainer's**
  TID/SID. After you catch it, display uses **your** TID/SID. So a Pokémon that
  will be shiny for you may look non-shiny during the battle. Expected, not a bug.
* Forced-shiny PID construction: `PID_LOW = PID_HIGH ^ (TID ^ SID)` → xor result 0.
* For the PAL test save (TID 28674 = `0x7002`, SID 47595 = `0xB9EB`),
  `TID ^ SID = 0xC9E9`. **Save-file specific** — recompute for any other save.

## 8. PID lifecycle (PAL trace; US equivalents in §9)

```
Battle begins (swirl)
  └─ old PID copied: Shadow Registry slot ──► battle struct (0x8058923C)
PID is generated                                  ← the hook point
  └─ first store: 0x80589D34   (PAL instr 0x80121FC4  stw r4,4(r3))
  └─ staging:     0x80470A08
  └─ ──► battle struct 0x8058923C and 0x804C0778
Shadow Pokémon thrown onto the field
  └─ battle struct ──► Shadow Registry PID2 slot
Shadow Pokémon caught mid-battle    (PAL instr 0x8012379C  stwu r0,8(r5))
  └─ ──► caught-Pokémon battle buffer 0x804BB530
Battle ends with it caught          (PAL instr 0x8012EEBC  stwu r0,8(r5))
  └─ battle buffer ──► permanent party slot
```

## 9. Function / breakpoint cross-reference

Derived with `Claude Assets/tools/map_convert.py`; matched-run length in brackets.

| Purpose | PAL | US | Confidence |
|---|---|---|---|
| **PID generator** `(…, r4=gender, r5=nature, r6=shiny, r7=trainerID)`, size 0x4B4 | `80128584` | **`80124410`** | conclusive [95] |
| Shiny check when a Pokémon is drawn in battle | `8012954C` | `801253D8` | conclusive [95] |
| First PID store — `stw r4, 4(r3)` | `80121FC4` | `8011DFE8` | conclusive [32] |
| Shadow caught mid-battle — `stwu r0, 8(r5)` | `8012379C` | `8011F628` | conclusive [95] |
| Battle end, PID → party slot — `stwu r0, 8(r5)` | `8012EEBC` | `8012AC90` | conclusive [54] |
| Fires once during battle-start swirl | `801F3080` | `801EE80C` | conclusive [101] |
| `mainAntiActionReplay` (function start) | `80005DDC` | `80005CE4` | conclusive |
| Save-base pointer **setter** | — | `80128E14` `savedataBiosSetNowSavedataPtr` | named symbol |
| Shiny flag site (`li r5,1`) | `80125EB8` | `80121D44` | conclusive [95] |
| Shiny flag site — PID generator +0x1C (`li r27,1`) | `801285A0` | `8012442C` | conclusive [95] |
| Shiny flag site — in-battle check (`li r3,1`) | `8012957C` | `80125408` | conclusive [95] |
| Shiny flag site — `battle_pokemon_get_value_with_id` (`li r0,1`) | `8012B440` | `801272CC` | conclusive [95] |
| Trainer-ID override hook, +0x46C into `zz_gen_battle_pokemon_from_data_table?` | `801FEC90` | `801FA3E4` | conclusive [123] |
| Build-fingerprint halfword (value `0x547F`) | `8012E140` | `80129F78` | conclusive [23] |

### Verified against the US MRAM dump

The PID generator's identity and argument registers are now proven, not
inferred. `0x80124410` disassembles to

```
80124410  stwu   r1, -0x40(r1)      ; the word both C2 codes re-emit
80124414  mflr   r0
80124418  stw    r0, 0x44(r1)
8012441C  stmw   r21, 0x14(r1)
80124420  mr.    r24, r3
80124424  mr     r25, r4            ; gender
80124428  mr     r26, r5            ; nature
8012442C  mr     r27, r6            ; shiny  <-- code 2 patches this to li r27,1
80124430  bne    +0x468
```

matching `zz_generate_pid_gender_r4_nature_r5_shiny_r6_trainer_id_r7` argument
for argument. And the caller confirms the link:

```
801FA3E4  mr     r7, r25            ; <-- code 2's C2 hook site
801FA3E8  li     r6, 0              ; shiny flag off
801FA3EC  bl     0x80124410         ; -> the PID generator
```

**Which write does what.** Ralf publishes a toggle version, "All Pokemon Are
Shiny On/Off", that uses only three of the four writes — `80121D44`, `80125408`,
`801272CC` — and labels it **"GFX only"**. So those three are the *display*
shiny checks, and **`8012442C` (the `mr r27, r6` inside the PID generator) is
the one that actually changes the rolled PID.** If you want a Pokémon that is
genuinely shiny rather than merely drawn shiny, `8012442C` is the write that
matters.

The three display sites share one idiom — `xor` / `cntlzw` / `slw` then
`rlwinm rX, r0, 1, 31, 31` to land the boolean in a register. The patch replaces
that final extract with `li rX, 1`:

| Address | Currently | Patched to |
|---|---|---|
| `80121D44` | `rlwinm r5, r0, 1, 31, 31` | `li r5, 1` |
| `80125408` | `rlwinm r3, r0, 1, 31, 31` | `li r3, 1` |
| `801272CC` | `rlwinm r0, r0, 1, 31, 31` | `li r0, 1` |

### Corroboration from Ralf's archive (US)

| Ralf code | Writes | What it confirms |
|---|---|---|
| "Shiny Nation" | the exact 10 lines of our all-new-shiny code | our conversion, third independent source |
| "Female Nation" | `04124424 3B200001` = `li r25, 1` | `80124424` is `mr r25, r4`, so **`r4` = gender** — the prologue reading is right |
| "Shiny Starter Pokemon" | `04130B24` / `04130C4C` = `li r6, 1` | two starter-generation **call sites** that pass the shiny flag in `r6` |
| "All Pokemon Are Shiny On/Off" | 3 of the 4 writes, "GFX only" | separates display sites from the real PID site (above) |
| "Complete Strategy Memo" | `120082A8 00000182`, then fills at step `0x0C` | **count at `+0x82A8` = 386 entries, 12-byte stride** — our memo model exactly |

### Trainer / record accessor functions (US)

| Address | Symbol / role |
|---|---|
| `80123EF0` | **set OT info** — `(r3=record, r4=f113, r5=f114, r6=f115, r7=f116, r8=OT TID, r9=OT name string)`. Sets **TID but not SID**. Exit at `80123FA8`. |
| `80129F20` | builds a trainer's party into a stack buffer, then calls the above |
| `80129280` | `zz_trainer_get_data_pointer` — `(r3=trainer index, r4=2)`; index 0 = the player |
| `8012A5B0` | `zz_trainer_get_value_with_index` — index **1** = OT name msg id, **2** = **TID**, 11 = a byte |
| `801254B4` | **Pokémon set-value-by-index** `(r3=record, r5=index, r7=value)`. The map calls this `GSmaterialSetTexture` — **that name is wrong.** |
| `801FB1C0` | `zz_pokemon_data_get_value_with_index_r5` (the getter) |
| `800FA280` | `zz_get_string_with_msg_id` |
| `8011FC74` | `zz_battle_pokemon_check_if_shadow` |
| `801FA3E8` | the `li r6, 0` Stars calls the **shiny lock** |
| `801FA3D8` | Stars' `shadowsOnlyLock` hook point |

PAL counterparts of the ones we hook: OT setter `80123EF0` → **`80128064`**
(exit `80123FA8` → **`8012811C`**), party builder `80129F20` → `8012E0E8`,
battle generator `801F9F78` → `801FE824`, shadow check `8011FC74` → `80123DE8`.
The OT setter is instruction-for-instruction identical between builds apart from
`bl` targets.

Field indices used by `801254B4` / read by `8012640C`
(`zz_battle_pokemon_get_value_with_id_r5`):

| Index | Field |
|---|---|
| 111 | **PID** (stored right after the generator returns, `801FA3FC`) |
| 113–118 | the OT block — **117 = OT TID**, **118 = OT name string** |
| 122 | read during party build |
| **194** | **is-shadow** — what `zz_battle_pokemon_check_if_shadow` reads |
| 195, 197, 198, 199 | written by the shadow setup at `8011FCA4`; 200 read |
| 201 | set during trainer generation (`801F9E50`) |

Battle-Pokémon generation order, which matters when choosing a hook:

```
801F9F78  gen_battle_pokemon_from_data_table
  801FA3EC  bl PID generator        -> field 111 = PID
  801FA418  bl 8011FCA4             -> shadow setup
801F9E84  bl 80129F20               (party builder)
  80129FB0  bl 8011F5FC             -> verbatim record copy into a stack buffer
  80129FD0  bl 80123EF0             -> OT setter (TID + name only, no SID)
  8012A018  bl 8011F5FC             -> copy out to the trainer's party slot
```

So by the time the OT setter runs, the PID and the shadow fields are already on
the record — which is what makes a shadow-gated hook at the OT setter's exit
(`80123FA8`) viable.

### A shadow's PID is rolled ONCE and then persisted

`zz_gen_battle_pokemon_from_data_table?` decides between rolling and reusing:

```
801FA398  cmplwi r30, 0          ; r30 = is-shadow (loaded once at 801FA004,
801FA39C  beq    801FA3D8        ;        from pokemon-data field 19)
801FA3A4  bl     801EE8F4        ; does this shadow already have a PID?
801FA3B0  bne    801FA3D8        ; no  -> roll
801FA3B8  bl     801EE750        ; yes -> fetch the stored PID
801FA3D0  bl     set field 111
801FA3D4  b      801FA408        ;        generator skipped entirely
801FA3D8  ...    li r6, 0 ; bl 80124410   ; roll a new PID
```

`801EE750` reads it as `base + index*12 + 8` where `base` comes from
`trainer_get_data_pointer(0, 15)` — the same 12-byte stride and PID-at-`+0x08`
as the Strategy Memo, and in the dump the only save-memory copy of a shadow's
PID is its memo entry. **So the PID is rolled at the first encounter, saved, and
reused for good.**

Consequence for any force-shiny code: it must be enabled *before* the first
encounter with a given shadow Pokémon. Enabling it later cannot change a PID
that has already been fixed, and disabling it later does not undo one.

**Shadow definition table** — `[r13 - 0x78B4]` (US `r13 = 0x80480820`, so the
pointer sits at `0x80478F6C`; it read `0x808A7AC4`). `0x38`-byte entries,
bounds-checked to `0x60`: species at `+0x02`, level at `+0x08`, memo entry index
at `+0x0A`. Entry 1 is Makuhita (`0x014F`, level 30).

Useful US-only named symbols found while working:

| Address | Symbol |
|---|---|
| `801240C4` | `zz_generate_pokemon_with_species_and_level` |
| `80124410` | `zz_generate_pid_gender_r4_nature_r5_shiny_r6_trainer_id_r7` |
| `801249F8` | `zz_init_pokemon_at_r3_number_of_mons_r4` |
| `80124A60` | `zz_battle_pokemon_init` |
| `80129280` | `zz_trainer_get_data_pointer` |
| `8012AC08` | `heroBiosGetPokemonPtr` |
| `80135168` | `zz_save_data_get_value_with_index` |
| `80113FE8` | `zz_load_spawn_position_from_save_data?` |

## 10. Code-writing rules

### Gecko C2 ("insert ASM")

```
C2<addr without leading 8> <number of 8-byte lines>
<instruction> <instruction>
...
```

* The address is written **without** the leading `8` (`0x80124410` → `C2124410`).
* The C2 branch **overwrites** the instruction at the hook address, and that
  instruction is *not* re-executed for you — **re-emit it as the last
  instruction of the block**. All our hooks sit on a function's first
  instruction, so that word is the prologue `stwu r1,-N(r1)`.
* Pad to a whole number of 8-byte lines with `00000000`; the line count counts
  8-byte lines, not instructions.
* Hooking a function's *first* instruction is the safe place to overwrite
  argument registers (`r3`–`r10`) — the callee has not read them yet. Do not
  clobber `LR` there: it still holds the caller's return address and has not
  been spilled, so a `bl` from that point corrupts the return unless you save
  and restore LR yourself.
* **Check what runs between a caller-side hook and the call.** Code 2 hooks
  `801FA3E4` (`mr r7, r25`) but the very next instruction is `li r6, 0`, which
  would wipe any shiny flag the hook wrote. That is exactly why the code sets
  only `r7` there and forces the flag with a separate `04` write *inside* the
  callee at `8012442C`. Setting `r6` at the hook site would silently do nothing.

### Build-fingerprint guards

An existing PAL code guards its hardcoded global like this:

```
lis    r6, 0x8013
lhz    r6, -0x1EC0(r6)   ; halfword at 0x8012E140 — inside the game's own code
cmplwi r6, 0x547F        ; top half of an rlwinm r31, r3, ...
bne    skip              ; wrong build -> never touch the pointer
```

Worth copying. It makes a region-specific code fail safe instead of
dereferencing garbage on the wrong build. Pick a fingerprint word from an
instruction with **no relocation** (`rlwinm`, `li`, arithmetic) so it survives
the region port unchanged; a `lis`/`bl`/`lwz` word will differ between builds.
PAL `0x8012E140` corresponds to US `0x80129F78`.

### The trainer ID dword is consumed two ways

`saveBase + 0x9C` feeds both hooks, but the PID generator wants the halves
swapped (`rotlwi r7,r7,16`) while the battle-Pokémon generator wants it raw.
Don't copy one hook's loading sequence into the other.

### Dolphin requirements — prerequisite for every Gecko code here

* Anti-Action-Replay checks must be NOP'd or the code handler is detected.
  Full set for both regions in `Claude Output/codes/ar_codehandler_nop.txt`:

  | | PAL | US | established by |
  |---|---|---|---|
  | nop | `80005614` | `80005614` | identity |
  | nop | `80005D1C` | `80005C24` | `GSgfxResetUpdate − 0x18` |
  | nop | `80005E48` | `80005D50` | `mainAntiActionReplay + 0x6C` |
  | nop | `800387E4` | `80036598` | map_convert [14] |
  | nop | `800388D4` | `80036688` | map_convert [14] |
  | nop | `8003898C` | `80036740` | map_convert [14] |
  | `000034E0` | `8026AF80` | `802663A0` | `.text` end + 0x44 |
  | `000034E4` | `8026AF84` | `802663A4` | `.text` end + 0x48 |

  The last two write data values, not instructions — the values are identical
  in both regions, only the destination moves.
* Use **JIT64 SC** mode, not Cached Interpreter.

## 11. Dolphin workflow rules (working agreement)

* **Never** ask for an in-Dolphin memory *value search* — it hangs Dolphin.
  Instead: `Memory → Export → Dump MRAM`, then hand over the `.raw`
  (path is under `Options → Configuration → Paths → Dump Path`).
* **Always request a fresh MRAM dump.** Never reason from an older one.
* Re-read the save-base pointer at the start of every session; recompute all
  party and registry addresses from it.
* PkHeX check procedure: set `Options → GameCube → Device Settings → Slot A` to
  *GCI Folder*; save at an in-game PC to the Slot A card; in Dolphin
  `Tools → Memory Card Manager`, open the card, delete any existing Colosseum
  save, `Import` the latest `.gci`; then open the memory-card file in PkHeX.

## 12. GoD-Tool as a reference

`GoD-Tool/` is StarsMmd's rewrite of the legacy Pokémon XD/Colosseum tool
(executable `GODDESS`, Swift 5.7+ / macOS 13+, SwiftPM). Philosophy:
**export → edit → rebuild**, never in-place ROM byte patching; game knowledge
lives in JSON struct/enum definitions rather than Swift code.

Use it for: FSYS handling, ISO dump/rebuild, file formats, struct/enum
definitions (`Sources/Shared/Core/Engines/…`), and worked assembly-patch
examples in `GoD Tool Package/Reference/Code Snippets CM.swift` (Colosseum) and
`Code snippets XD.swift`.

Note that the snippet files use **US** RAM offsets written without the
`0x80000000` base (e.g. `0x11e3b4` = `0x8011E3B4`), and show the idiom for
SDA-relative global access (`lwz r31, -0x7890(r13)`).

## 13. Handoff convention

Every major change gets a file in `handoffs/` named
`YYYY-MM-DD_HHMM_<short-slug>.md`, stating date/time, what changed, why, and
anything left unverified.

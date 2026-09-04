---
name: colosseum-region-porting
description: "Convert Pokémon Colosseum (GameCube) Gecko/Action Replay codes between the US (GC6E01) and PAL (GC6P01) builds — address translation, save-base pointers, record offsets, and the verification workflow"
---

# Porting Pokémon Colosseum codes between US and PAL

Everything here was derived and then **confirmed in-game** on both regions while
porting a set of shiny-related Gecko codes. Method notes, not theory.

Companion scripts in this skill:

* `scripts/map_convert.py` — translates **code** addresses between builds
* `scripts/ppc.py` — a small PowerPC disassembler for reading MRAM dumps

---

## 0. The one-paragraph version

Split every address in a code into **code addresses** (hook points, branch
targets) and **data addresses** (globals). Code addresses translate mechanically
by aligning the two symbol maps' `.text` function-size sequences. Data addresses
**cannot** be extrapolated and must be looked up. Everything else in a typical
code — record offsets, save offsets — is region-independent. In practice a port
is **the hook address plus the base pointer, and nothing else.** That held
exactly for three separate codes.

---

## 1. The two builds

| | US | PAL |
|---|---|---|
| Game ID | **GC6E01** | **GC6P01** |
| `.text` end | `0x8026635C` | `0x8026AF3C` |
| **Save-base pointer global** | **`0x8047ADB8`** | **`0x804C8268`** |
| `r13` (SDA base) | `0x80480820` | — |
| `r2` (SDA2 base) | `0x804836A0` | — |

PAL `.text` is **`0x4BE0` bytes larger**. Every address past the first
divergence differs, so no PAL address may ever be reused on US untranslated.

JP is `GC6J01` (not covered here).

**The save-base pointer is a pointer, not the save.** Read the big-endian word
at that address to get the live save base; it moves every session. Session
examples seen: US `0x804085E0`, PAL `0x804559E0`.

The US value is independently confirmed three ways: the NTSC-U WiiRD table, an
MRAM dump, and by disassembling `savedataBiosSetNowSavedataPtr` at `0x80128E14`:

```
cmplwi r3, 0
beqlr
stw    r3, -0x5A68(r13)   ; r13 = 0x80480820 -> 0x8047ADB8
blr
```

---

## 2. What you need

| File | Where |
|---|---|
| `GC6E01` and `GC6P01` symbol maps | github.com/StarsMmd/Colo-XD-PBR-symbol-maps (may be outdated but addresses/sizes are sound) |
| WiiRD offset tables, both regions | Ralf's posts at gc-forever (via the Wayback Machine) — get **the same version** for both regions |
| Published code archives, both regions | Ralf, same source — US/PAL × Gecko/AR |
| An MRAM dump | Dolphin: `Memory → Export → Dump MRAM` |

---

## 3. Translating a CODE address

Both builds are the same source compiled per region, so the **sequence of
function sizes** in `.text` is nearly identical. Align those sequences with
`difflib`, and inside a matched run:

```
us_addr = us_func_start + (pal_addr - pal_func_start)
```

```bash
python scripts/map_convert.py 0x80128584          # PAL -> US
python scripts/map_convert.py --us2pal 0x80124410 # US  -> PAL
```

It finds the maps by searching upward from itself for filenames containing
`GC6P01` / `GC6E01`, so layout does not matter.

**Read the reported run length — that is the confidence signal:**

| Matched run | Meaning |
|---|---|
| ≥ 20 consecutive functions | Conclusive. Ship it. |
| 5–19 | Likely. Check the opcode in a dump before shipping. |
| 1–4, or "NO ALIGNED COUNTERPART" | Guess. Verify against a real dump. |

Track record: every call at run ≥ 5 has held, across four independent checks
including in-game confirmation of five codes.

### The known blind spot

Below roughly `0x80006000` the builds diverge enough that counterpart functions
differ in *size*, and the aligner refuses to pair them — e.g. one function is
`0xE8` in PAL and `0xE4` in US. **"NO ALIGNED COUNTERPART" there means the tool
cannot tell, not that no counterpart exists.**

Fall back to anchoring on a symbol **named in both maps** and offsetting by hand.
`GSgfxResetUpdate` (PAL `0x80005D34`, US `0x80005C3C`) correctly gives
`80005D1C → 80005C24`. Two anti-AR addresses were recovered this way and later
confirmed.

### Symbol names are less trustworthy than addresses

The maps carry mislabelled names — e.g. `0x801254B4` is listed as
`GSmaterialSetTexture` but is actually the Pokémon set-value-by-index setter.
Trust addresses and sizes; treat names as hints.

---

## 4. Translating a DATA address — you can't

Neither map contains data or BSS symbols. And the deltas **are not constant**:

| Global | PAL → US delta |
|---|---|
| save-base pointer | `0x4D4B0` |
| battle array, your side | `0x4D480` |
| battle array, opponent | `0x4D498` |
| button activator | `0x4D480` |

They are also nothing like the `0x4BE0` `.text` difference. An early estimate
built on that heuristic was wrong by ~`0x48A00`. **Look data addresses up
per-variable. Never shift them.**

### Route 1 — diff the two WiiRD tables (fastest)

They are the same document per region. `diff` them and the *only* differences
are the base pointer, the in-battle absolute addresses, and the button
activator. That hands you every region-varying data address at once.

Keep both files at the **same version** — a version mismatch fills the diff with
spurious entries that look like region differences but aren't.

### Route 2 — diff a published code that exists for both regions

Ralf's archive publishes the same code for US and PAL. Finding one in both files
gives the mapping of every address it touches, for free. Also the fastest way to
check whether something already exists before building it.

### Route 3 — disassemble the accessor

Find a named accessor in the map and read its instructions. The
`savedataBiosSetNowSavedataPtr` example in §1 is the model.

### Route 4 — MRAM dump

Dump with a save loaded and scan for a big-endian word equal to a known value.

---

## 5. What does NOT change between regions

This is the part that makes ports cheap. **All of these are identical in both
builds:**

* every save-relative offset
* every Pokémon-record-relative offset
* every field index used by the get/set-value-by-index functions

### Save layout (offsets from the save base)

| Offset | Field |
|---|---|
| `+0x70` | trainer name, UTF-16BE |
| `+0x9C` | Trainer **Secret ID** (u16) |
| `+0x9E` | Trainer **ID** (u16) |
| `+0xA0` | party slot 1 entry — **stride `0x138`** |
| `+0xAF4` | PokéDollars |
| `+0xB9C` | box 1 slot 1, same `0x138` stride |
| `+0x82A8` | Strategy Memo entry count |
| `+0x82AC` | Strategy Memo array, **12 bytes/entry**, 386 entries |

So the dword at `+0x9C` is `(SID << 16) | TID`.

### The Pokémon record — one layout everywhere

The save entry and both in-battle arrays are the **same record type** with the
same internal offsets; only the array stride differs.

| Off | Field | | Off | Field |
|---|---|---|---|---|
| `+0x00` | species (Gen-3 **internal** index) | | `+0x5C` | EXP |
| `+0x04` | **PID** | | `+0x60` | level |
| `+0x08` | came from (`0B` = Colosseum/XD) | | `+0x65` | status |
| `+0x0E` | level met | | `+0x78` | move 1, then PP ×4 |
| `+0x14` | **OT Secret ID** (u16) | | `+0xB0` | happiness |
| `+0x16` | **OT Trainer ID** (u16) | | `+0xD8` | **Shadow Pokémon ID** |
| `+0x18` | OT name, UTF-16BE | | `+0xDC` | purification counter |
| `+0x2E` | nickname | | `+0xE8` | Hyper Mode (`003E` = yes) |

> Species numbers are **Gen-3 internal indices**, not National Dex numbers. They
> agree for #1–251 and diverge above — Makuhita is `0x14F` (335), not 296.

**A useful consequence:** `saveBase + 0x9C` is `(SID << 16) | TID` and the
record holds OT SID at `+0x14` / OT TID at `+0x16` — the *same halfword order*.
So one `lwz`/`stw` pair copies the player's whole OT onto a record, no shifting
or masking. That single fact carried an entire code.

---

## 6. Writing the Gecko block

```
C2<addr without leading 8> <number of 8-byte LINES>
<instruction> <instruction>
...
```

Rules that actually bite:

* **The C2 branch overwrites the instruction at the hook, and it is not
  re-executed for you. Re-emit it yourself** — usually as the last instruction
  of the block.
* The count is **8-byte lines, not instructions**. Count them.
* Pad to a whole line with `00000000`.
* **Branches inside the block are PC-relative and stay correct** wherever the
  codehandler copies it. Point them at a real instruction — the re-emitted
  original, or a trailing `nop` — never at the padding word.
* Hooking a function's *first* instruction is the safe place to overwrite
  argument registers `r3`–`r10`; the callee has not read them yet. But do **not**
  clobber `LR` there — it still holds the return address and has not been
  spilled.
* **Check what runs between a caller-side hook and the call.** In one case a
  hook was immediately followed by `li r6, 0`, which wiped the flag the hook had
  just set.
* Volatile scratch: `r11` / `r12` are safe to clobber almost anywhere.

### The sign-extension trap

`ori` **zero-extends**; `lwz` / `stw` / `addi` displacements **sign-extend**. So
the same global splits two different ways:

| Form | US `0x8047ADB8` | PAL `0x804C8268` |
|---|---|---|
| `lis rX, H` + `ori rX, rX, L` | `lis 0x8047` / `ori 0xADB8` | `lis 0x804C` / `ori 0x8268` |
| `lis rX, H` + `lwz rX, L(rX)` | `lis 0x8048` / `lwz 0xADB8` | `lis 0x804D` / `lwz 0x8268` |

**Rule:** for the `lwz`/`stw` form, if the low halfword is ≥ `0x8000` the `lis`
must carry **high + 1**. Getting this wrong puts the pointer `0x10000` off.

### Build-fingerprint guard (worth copying)

Make a region-specific code fail safe instead of dereferencing garbage on the
wrong build:

```
lis    r6, 0x8013
lhz    r6, 0x9F78(r6)   ; halfword at US 0x80129F78 (PAL 0x8012E140)
cmplwi r6, 0x547F       ; the top half of an rlwinm r31, r3, ...
bne    skip             ; wrong build -> never touch the hardcoded pointer
```

Pick a fingerprint word from an instruction with **no relocation** (`rlwinm`,
`li`, arithmetic) so it survives the port unchanged. A `lis`/`bl`/`lwz` word
will differ between builds.

---

## 7. Verification workflow

Before shipping any ported code:

1. **The re-emitted instruction.** Read the hook address in an MRAM dump and
   confirm it holds exactly the word your block re-emits. This catches a wrong
   hook immediately.
2. **The global.** Confirm your `lis`/`ori` or `lis`/`lwz` pair resolves to the
   intended address, and that the address contains something plausible.
3. **Register liveness.** If you use a non-volatile register the caller set
   (e.g. a flag in `r30`), confirm it is written once and not rewritten before
   your hook.
4. **Branch targets.** Confirm each internal branch lands on a real instruction.
5. **Round-trip every encoding** through a disassembler — `scripts/ppc.py`
   does this. Hand-assembled words are where mistakes hide.

Reading a dump (24 MB MEM1, base `0x80000000`):

```python
import struct
DATA = open('mem1.raw','rb').read()
u32 = lambda a: struct.unpack_from('>I', DATA, a - 0x80000000)[0]

import ppc
print(ppc.dis(u32(0x80123FA8), 0x80123FA8))
```

---

## 8. Dolphin requirements

**Anti-Action-Replay checks must be NOP'd** or Colosseum detects the code
handler:

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

Use **JIT64 SC**, not Cached Interpreter.

**Never run an in-Dolphin memory value search** — it hangs. Dump MRAM and
analyse the `.raw` instead. Always use a fresh dump.

---

## 9. Worked example

The original PAL code — force a shadow Pokémon's PID to roll shiny against the
player:

```
C2128584 00000004
38C00001 3CE0804C
60E78268 80E70000
80E7009C 54E7803E
9421FFC0 00000000
```

```
li     r6, 1            ; shiny flag argument
lis    r7, 0x804C
ori    r7, r7, 0x8268   ; r7 = &saveBasePtr (PAL)
lwz    r7, 0(r7)        ; save base
lwz    r7, 0x9C(r7)     ; (SID << 16) | TID
rotlwi r7, r7, 16       ; -> (TID << 16) | SID
stwu   r1, -0x40(r1)    ; the overwritten prologue instruction
```

Porting it:

1. **Hook** — `map_convert.py 0x80128584` → US `0x80124410`, run 95,
   conclusive. Bonus: the US map names that function
   `zz_generate_pid_gender_r4_nature_r5_shiny_r6_trainer_id_r7`, independently
   confirming `r6` = shiny and `r7` = trainer ID.
2. **Global** — `0x804C8268 → 0x8047ADB8`, from the WiiRD table diff.
3. **Everything else** — `+0x9C` and the `rotlwi` are region-independent.
   Unchanged.
4. **Verify** — `0x80124410` holds `9421FFC0`, matching the re-emitted word.

Result:

```
C2124410 00000004
38C00001 3CE08047
60E7ADB8 80E70000
80E7009C 54E7803E
9421FFC0 00000000
```

Two substitutions. Confirmed working in-game.

---

## 10. Confirmed address pairs

Free reference — all verified, most confirmed in-game.

| Purpose | US | PAL |
|---|---|---|
| PID generator (`r6` shiny, `r7` trainer ID) | `80124410` | `80128584` |
| — `mr r27, r6`, the real shiny flag | `8012442C` | `801285A0` |
| Battle-Pokémon generator | `801F9F78` | `801FE824` |
| — shiny-flag argument at the call site | `801FA3E8` | `801FEC94` |
| — is-shadow flag loaded into `r30` | `801FA004` | `801FE8B0` |
| OT setter (sets TID + OT name, **not SID**) | `80123EF0` | `80128064` |
| — its exit, record still in `r26` | `80123FA8` | `8012811C` |
| Trainer-party builder | `80129F20` | `8012E0E8` |
| `battle_pokemon_check_if_shadow` | `8011FC74` | `80123DE8` |
| RNG (one 16-bit half per call) | `801ADCD8` | `801B204C` |
| Stored-PID getter | `801EE750` | `801F2FC4` |
| Has-stored-PID check | `801EE8F4` | `801F3168` |
| Shiny check when drawn on screen | `801253D8` | `8012954C` |
| Build-fingerprint word (`0x547F`) | `80129F78` | `8012E140` |
| `mainAntiActionReplay` | `80005CE4` | `80005DDC` |

Useful US-only symbol names: `80129280 zz_trainer_get_data_pointer`,
`8012A5B0 zz_trainer_get_value_with_index` (index 2 = TID, 1 = OT name msg id),
`801254B4` Pokémon set-value-by-index, `801FB1C0` the getter,
`800FA280 zz_get_string_with_msg_id`.

---

## 11. One Colosseum-specific gotcha

A shadow Pokémon's PID is **rolled once, at the first encounter, then persisted
in the save** and reused forever. The generator is skipped on later encounters:

```
cmplwi r30, 0        ; is-shadow?
beq    roll
bl     <has PID?>
bne    roll
bl     <fetch stored PID>
b      done          ; generator never called
roll:
li     r6, 0
bl     <PID generator>
```

So any force-shiny code must be enabled **before** the first encounter with each
shadow Pokémon. Enabling it later cannot change a PID already fixed; disabling
it later does not undo one.

More generally: before hooking, trace whether your target is even reached on the
path you care about. Two codes in this project were redesigned once the call
order was actually read.

# Handoff — 2026-09-04 19:03

**Change:** Scraped a US (GC6E01) MEM1 dump taken mid-battle with a shadow
Makuhita on the field under the opposing trainer's control. Both shipped codes
are now verified against real code. Two playbook errors corrected, one open
question resolved, several new schema facts added.

Dump: `mem1 - US shadow mak mid-battle.raw`, 24 MB, base `0x80000000`.
Session save base `0x804085E0`; player "WES", TID `0x208A`, SID `0x8C55`.

## Files changed

| Path | What |
|---|---|
| `PROJECT_NOTES.md` | §5 save/battle/memo schema substantially revised; §9 gains a verified-disassembly block; §10 gains a caller-side-hook rule |
| `codes/force_shadow_shiny_US.txt` | "Still unverified" replaced with verified findings |
| `codes/all_new_pokemon_shiny_US.txt` | Same |

## Both codes verified — nothing left outstanding

* `0x80124410` reads **`9421FFC0`** (`stwu r1,-0x40(r1)`). Code 1's re-emitted
  prologue word is correct.
* `0x80129F78` reads **`547F063E`** (`rlwinm r31, r3, 0, 24, 31`). The guard
  halfword is `0x547F`, so code 2's `cmplwi` matches and the guard passes.
* `0x801FA3E4` reads **`7F27CB78`** (`mr r7, r25`) — exactly the instruction
  code 2 re-emits as its first line.
* All four `04` targets hold the boolean-producing instruction each write
  replaces: `rlwinm r5/r3/r0, r0, 1, 31, 31` at `80121D44` / `80125408` /
  `801272CC`, and `mr r27, r6` at `8012442C`.

## The save-base pointer, now derived rather than taken on trust

`savedataBiosSetNowSavedataPtr` (`0x80128E14`) disassembles to

```
cmplwi r3, 0
beqlr
stw    r3, -0x5A68(r13)
blr
```

and `__init_registers` sets `r13 = 0x80480820` (`3DA08048` / `61AD0820` at
`0x80003334`). `0x80480820 - 0x5A68 = 0x8047ADB8`. Independent of both the
supplied value and the WiiRD table.

Also recovered: **US SDA bases** `r13 = 0x80480820`, `r2 = 0x804836A0`, initial
`r1 = 0x8048E738`. Worth having when a global is reached `off(r13)`.

## The PID generator is proven, not inferred

```
80124410  stwu r1,-0x40(r1) / mflr r0 / stw r0,0x44(r1) / stmw r21,0x14(r1)
80124420  mr. r24,r3 / mr r25,r4 / mr r26,r5 / mr r27,r6
```

r4 = gender, r5 = nature, r6 = shiny — the annotated symbol name is accurate
argument for argument. And the caller closes the loop:

```
801FA3E4  mr   r7, r25          <-- code 2's C2 hook
801FA3E8  li   r6, 0
801FA3EC  bl   0x80124410       <-- decoded branch target = the PID generator
```

**New rule recorded (§10):** the `li r6, 0` sitting between the hook and the
call would wipe any shiny flag set from that C2. That is precisely why the
original code sets only `r7` there and forces the flag with a separate `04`
write *inside* the callee. Anyone extending that hook needs to know this.

## Correction 1 — party stride 0x138, now beyond argument

Reading the party at `0x138` gives slots 1 and 2 as species 197 and 196,
**Umbreon and Espeon** — the Colosseum starter pair, with PIDs matching the
Strategy Memo's first two entries. Reading at the playbook's `0x140` gives
species 2819 and 512, i.e. garbage. Settled.

## Correction 2 — the "shadow registry" is the Strategy Memo, and its fields were misread

Entry layout, 12 bytes, array at `saveBase + 0x82AC`, count u16 at `+0x82A8`:

| Off | Size | Field |
|---|---|---|
| `+0x00` | u16 | species, internal index (`\| 0x8000` = limited info) |
| `+0x02` | u16 | zero in every entry observed |
| `+0x04` | u32 | **owner's OT ID dword** — `(SID << 16) \| TID` |
| `+0x08` | u32 | **PID** |

The playbook calls `+0x04` and `+0x08` "PID1" and "PID2". `+0x04` is not a PID —
it is the OT trainer dword. Proof: memo entries 0 and 1 are the player's own
Umbreon and Espeon and their `+0x04` is `8C55208A`, byte-for-byte the player's
OT dword from `saveBase + 0x9C`.

## Resolved — memo ordering is append-as-encountered

Count was 10, entries 0–9 populated. Entry 9 is the shadow Makuhita: species
`0x14F`, OT `20D138F5` = Trudly, PID `4F662AD2`, matching the battle struct
exactly. Makuhita's dex number is 296 and its shadow ID is 1, so **index 9 is
neither** — an entry's address cannot be computed from the Pokémon's identity.
Scan for species or PID instead.

(Entries 7/8/9 are Trudly's three Pokémon — species 361, 167, 335 — appended in
the reverse of their battle-slot order. The precise append rule is not pinned
down and does not matter for addressing.)

## Partly resolved — the pre-seeded PIDs

Every one of the 376 slots past the count has `species = 0`, `otID = 0`, and a
**non-zero random-looking PID**. So the game does seed PID-shaped values across
the whole 386-entry array up front; that is what the playbook saw. But whether a
slot's pre-seed *becomes* the PID of the next Pokémon appended there, or is
simply overwritten by an independently rolled one, **cannot be determined from a
single post-encounter dump**.

Test that would settle it: dump before an encounter, note the PID in slot
`[count]`, encounter something, dump again, compare. (I tried a Gen-3 LCG
consistency check on these values; it is worthless here — random dwords pass it
at the same rate. Recorded so nobody repeats it.)

## New schema facts

* **Species numbers are Gen-3 internal indices, not dex numbers.** Makuhita
  reads `0x014F` = 335 (dex 296); Umbreon/Espeon read 197/196, which happen to
  match because the two numberings coincide below 252.
* **Six battle slots per side**, stride `0x154` — US self `8046E928…8046EFCC`,
  opponent `80473B58…804741FC`. The WiiRD tables document only the first two.
* **The in-battle entry reuses the save entry's field layout** for its whole
  head (species, PID, came-from, fonts, level met, OT gender/SID/TID, OT name,
  nickname, original name), then adds `+0xD8` shadow ID and `+0xDC` purification
  counter. The playbook's "shadow check at battle struct `+0xD8`" is that field.
* **The battle record is triplicated**: `80473B58` (documented slot),
  `804732DC` (parallel copy `0x87C` earlier, behind a 12-byte header), and
  `8053BCB8` (third copy, with a pointer to `804732DC` at `8053BCB4`). A fourth
  PID copy sits at `809C8210` in what looks like a display/model struct.
  `8053BCB8` is in a session-dependent region — observed, not fixed.
* `saveBase + 0x70` — trainer name in **UTF-16BE**, one u16 per character.

## The observed Makuhita is not shiny either way

PID `4F662AD2`. Against Trudly (`TID 38F5`, `SID 20D1`) the xor is `0x7D90`;
against Wes (`TID 208A`, `SID 8C55`) it is `0xC96B`. Neither is < 8. Expected —
the dump was taken without the codes active, and the PID was already rolled.

## One loose thread

`saveBase + 0xAF4`, which the WiiRD tables label Money, reads **8330** — which
is exactly the player's TID (`0x208A`). The field is isolated (zeros either
side) and sits where the table says, so it is probably genuine, but an exact
collision with the TID is a ~1-in-10-million coincidence. Worth one glance at
the in-game money total to rule out a misread. Affects nothing we ship.

# Handoff — 2026-09-04 18:02

**Change:** The US save-base pointer global was supplied as **`0x8047ADB8`**
(PAL `0x804C8268`). Both blocked codes are now complete.

## Files changed

| Path | What |
|---|---|
| `codes/force_shadow_shiny_US.txt` | Rewritten — final US code, placeholders gone |
| `codes/all_new_pokemon_shiny_US.txt` | Part 2 filled in; final US code |
| `PROJECT_NOTES.md` | §5 records the US global; §6 adds the sign-extension encoding rule |

## Final codes

**Force shadow Pokémon shiny once caught (US / GC6E01)**

```
C2124410 00000004
38C00001 3CE08047
60E7ADB8 80E70000
80E7009C 54E7803E
9421FFC0 00000000
```

**All newly generated Pokémon are shiny (US / GC6E01)**

```
04121D44 38A00001
0412442C 3B600001
04125408 38600001
041272CC 38000001
C21FA3E4 00000005
7F27CB78 3CC08013
A0C69F78 2806547F
40820010 3CC08048
80C6ADB8 80E6009C
60000000 00000000
```

## The one subtlety worth recording

The two codes reach the same global through different instruction forms, and
they encode it differently:

* Code 1 uses `lis` + **`ori`**. `ori` zero-extends, so the split is plain:
  `lis 0x8047` / `ori 0xADB8`.
* Code 2 uses `lis` + **`lwz`**. `lwz`'s displacement sign-extends, and
  `0xADB8` ≥ `0x8000` sign-extends to `-0x5248`, so the `lis` must carry
  high **+1**: `lis 0x8048` / `lwz 0xADB8` → `0x80480000 - 0x5248` =
  `0x8047ADB8`. This is the same correction the PAL original makes with
  `804D` / `8268` for `0x804C8268` — easy to miss when copying between codes.

Recorded as a table in `PROJECT_NOTES.md` §6.

## Still unverified

* **`9421FFC0` at US `0x80124410`.** Code 1's last line re-emits the prologue
  instruction the C2 branch overwrites. Both functions are 0x4B4 bytes so the
  frame size should match, but this is one glance at Dolphin's code view and
  worth doing before a long test session.
* **The `0x547F` guard word at US `0x80129F78`.** If the halfword there isn't
  `0x547F`, code 2's C2 branches past the pointer read every time and Part 2
  silently does nothing — Part 1 would still work, so the failure looks like
  "shiny but wrong TID" rather than a crash. Same one glance.
* **Anti-Action-Replay NOP set.** Unchanged from the first handoff: four US
  addresses at "likely" confidence, three PAL entries with no aligned
  counterpart.

#!/usr/bin/env python3
"""
map_convert.py -- Translate Pokemon Colosseum code addresses between the
PAL (GC6P01) and US (GC6E01) builds.

Method
------
Both symbol maps list every .text function in address order with its size.
The two builds are the same source compiled for different regions, so the
*sequence of function sizes* is almost identical; only region-specific
functions are inserted/removed. Running a difflib sequence alignment over
those size sequences yields long runs of exactly-corresponding functions.
An address is translated as:

    us_addr = us_func_start + (pal_addr - pal_func_start)

The reported "run" length is the number of consecutive functions whose sizes
matched around the hit. A run in the dozens is effectively conclusive; a run
of 1-2 should be treated as a guess and verified in a debugger.

This only works for .text (code). Data / BSS globals are NOT in these maps
and must be found another way (see Claude Output/PROJECT_NOTES.md).

Usage
-----
    python "Claude Assets/tools/map_convert.py" 0x80128584    # PAL -> US
    python "Claude Assets/tools/map_convert.py" --us2pal 0x80124410

The two symbol maps are located automatically by searching upward from this
script for filenames containing GC6P01 / GC6E01, so moving things around does
not break it.
"""
import re, sys, difflib, os

def _find_maps():
    """Locate the two symbol maps without assuming a directory layout.

    Walks up from this script looking for a directory that contains both maps
    somewhere beneath it, matching on the game IDs in the filenames. This
    survives the files being moved or renamed, which has already happened once.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    for _ in range(6):
        pal = us = None
        for root, dirs, files in os.walk(here):
            dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
            for f in files:
                if not f.lower().endswith(".map"):
                    continue
                if "GC6P01" in f and pal is None:
                    pal = os.path.join(root, f)
                elif "GC6E01" in f and us is None:
                    us = os.path.join(root, f)
        if pal and us:
            return pal, us
        parent = os.path.dirname(here)
        if parent == here:
            break
        here = parent
    raise SystemExit(
        "map_convert: could not find GC6P01*.map and GC6E01*.map. "
        "Searched upward from " + os.path.dirname(os.path.abspath(__file__)))


PAL_MAP, US_MAP = _find_maps()

# The maps tack a few unrelated high-memory blobs (0x809f.../0x810a...) onto
# the end of the .text listing; ignore anything above the real code segment.
CODE_LIMIT = 0x80400000


def parse(path):
    syms, sec = [], None
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if "section layout" in line:
                sec = line.strip().split()[0]
                continue
            p = line.split()
            if len(p) >= 5 and re.fullmatch(r"[0-9a-fA-F]{8}", p[0]):
                addr, size = int(p[0], 16), int(p[1], 16)
                if sec == ".text" and addr < CODE_LIMIT:
                    syms.append(dict(addr=addr, size=size, name=p[4],
                                     lib=" ".join(p[5:])))
    return syms


def build_alignment(src, dst):
    a = [s["size"] for s in src]
    b = [s["size"] for s in dst]
    return difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks()


def translate(addr, src, dst, blocks):
    idx = next((i for i, s in enumerate(src)
                if s["addr"] <= addr < s["addr"] + s["size"]), None)
    if idx is None:
        return None
    off = addr - src[idx]["addr"]
    for bl in blocks:
        if bl.a <= idx < bl.a + bl.size:
            j = bl.b + (idx - bl.a)
            return dict(src=src[idx], dst=dst[j], off=off,
                        addr=dst[j]["addr"] + off, run=bl.size)
    return dict(src=src[idx], dst=None, off=off, addr=None, run=0)


def main(argv):
    us2pal = "--us2pal" in argv
    args = [a for a in argv if not a.startswith("--")]
    pal, us = parse(PAL_MAP), parse(US_MAP)
    src, dst = (us, pal) if us2pal else (pal, us)
    slbl, dlbl = ("US", "PAL") if us2pal else ("PAL", "US")
    blocks = build_alignment(src, dst)
    for arg in args:
        a = int(arg, 16)
        r = translate(a, src, dst, blocks)
        if r is None:
            print(f"{slbl} {a:08X} -> not inside any known function"); continue
        if r["dst"] is None:
            print(f"{slbl} {a:08X} ({r['src']['name']}) -> NO ALIGNED COUNTERPART"); continue
        conf = "conclusive" if r["run"] >= 20 else ("likely" if r["run"] >= 5 else "GUESS - verify")
        print(f"{slbl} {a:08X} -> {dlbl} {r['addr']:08X}   (+0x{r['off']:X} into function)")
        print(f"    {slbl:<3} sym: {r['src']['addr']:08X} size 0x{r['src']['size']:X}  {r['src']['name']} {r['src']['lib']}")
        print(f"    {dlbl:<3} sym: {r['dst']['addr']:08X} size 0x{r['dst']['size']:X}  {r['dst']['name']} {r['dst']['lib']}")
        print(f"    matched run: {r['run']} consecutive functions  [{conf}]")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    main(sys.argv[1:])

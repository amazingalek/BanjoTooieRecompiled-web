#!/usr/bin/env python3
"""Writes tools/shader_plan.json and tools/play_plan.json, the plans N64Recomp-browser's tools/record_shaders.mjs and
play_page.mjs follow (src/rt64_shaders.txt's header says how the list was recorded with the first). Both reach the game the
same way: the launcher, Start Game, the title for 25 s, Start (Enter) to the file select, A (Space) on Game 1, which on a
new profile starts a new game, and its opening cutscene; then tools/shader_survey.js warps to each world's maps, and in each
the camera turns (the C buttons, the arrow keys) and Banjo walks (W) for a few seconds. Run it again after changing WORLDS.

The play plan doesn't walk: in each world Banjo jumps and attacks where he lands while the camera turns. A blind walk
from an entrance, which way the entrance faces unknown, carried him off Hailfire Peaks' and Cloud Cuckooland's ledges,
or through a world's exit: a laptop's three runs of a 2.5 s walk ended black after Cauldron Keep's, which the page
draws in Chrome and Firefox at 1256x645 and 1920x945, Chrome's page thread throttled 3 times too, and with a walk out and
back the game began a change of map of its own in Hailfire Peaks (its jigsaw wipe), after which every world warped to
drew black in Chrome, though each warp reached its map. tools/shader_survey.js's warp now waits for such a change to
end."""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))

# A section a world: its maps, by the game's map numbers, the first where a player enters it.
WORLDS = [
    ("isle", "Isle o' Hags", [0x142, 0x143, 0x14F, 0x152, 0x154, 0x155, 0x15A, 0x15C, 0xAF]),
    ("mayahem", "Mayahem Temple", [0xB8, 0xB9, 0xC4, 0x177]),
    ("glitter", "Glitter Gulch Mine", [0xC7, 0xD2, 0xD7, 0xDC]),
    ("witchy", "Witchyworld", [0xD6, 0xE1, 0xF9, 0xEA]),
    ("jolly", "Jolly Roger's Lagoon", [0x1A7, 0xED, 0x1A8, 0x1A9]),
    ("terry", "Terrydactyland", [0x112, 0x116, 0x11A, 0x119]),
    ("grunty", "Grunty Industries", [0x100, 0x101, 0x106, 0x10B]),
    ("hailfire", "Hailfire Peaks", [0x127, 0x128, 0x132, 0x133]),
    ("cloud", "Cloud Cuckooland", [0x136, 0x13A, 0x137]),
    ("cauldron", "Cauldron Keep", [0x15D, 0x15E]),
]

def key(name, code, ms):
    return ["hold", name, name if len(name) > 1 else name.lower(), code, ms]

LOOK = [key("ArrowLeft", 37, 2000), key("KeyW", 87, 2500), key("ArrowRight", 39, 2000), ["wait", 1500]]
for step in LOOK:
    if step[1] == "KeyW":
        step[2] = "w"

def visit(m):
    return [["eval", f"warp(0x{m:X})"], ["wait", 4000], *LOOK]

PLAY_LOOK = [key("ArrowLeft", 37, 2000), ["hold", "Space", " ", 32, 200], ["wait", 1200],
             ["hold", "ShiftLeft", "Shift", 16, 200], ["wait", 1000], key("ArrowRight", 39, 2000), ["wait", 1500]]

def play_visit(m):
    return [["eval", f"warp(0x{m:X})"], ["wait", 4000], *PLAY_LOOK]

LOAD = [["until", "Device Name", 30000], ["wait", 9000]]
SETUP = [["rom", 1042, 478], ["wait", 4000]]
START = [["click", 1042, 478], ["wait", 25000],
         ["hold", "Enter", "Enter", 13, 300], ["wait", 5000],
         ["hold", "Space", " ", 32, 300], ["wait", 4000],
         ["evalFile", "shader_survey.js"], ["eval", "waitMap(0xA1, 30000)"], ["wait", 4000]]

shader_plan = {
    "header": [
        "Banjo-Tooie's shader plan for N64Recomp-browser's tools/record_shaders.mjs, written by tools/make_plans.py (its",
        "docstring says how it plays): the boot is the launcher, the logos, the title, the file select and a new game's",
        "opening; each section after it a world, its maps reached by tools/shader_survey.js."],
    "page": "BanjoTooieRecompiled.html",
    "load": LOAD, "setup": SETUP, "start": START,
    "sections": [{"name": name, "steps": [s for m in maps for s in visit(m)]} for name, _, maps in WORLDS],
}
play_plan = {
    "header": [
        "Banjo-Tooie's play plan for N64Recomp-browser's tools/play_page.mjs, written by tools/make_plans.py: the boot as",
        "the shader plan's, then the first map of every world in turn, Banjo jumping and attacking where he lands in each",
        "while the camera turns (make_plans.py's docstring says why he doesn't walk)."],
    "page": "BanjoTooieRecompiled.html",
    "load": LOAD, "setup": SETUP, "start": START,
    "play": [s for _, _, maps in WORLDS for s in play_visit(maps[0])],
}
for name, plan in (("shader_plan.json", shader_plan), ("play_plan.json", play_plan)):
    with open(os.path.join(HERE, name), "w", newline="\n") as f:
        json.dump(plan, f, indent=1)
        f.write("\n")

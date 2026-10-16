# Building the web page

This fork's `main` branch builds the game with [Emscripten](https://emscripten.org) into a page,
`BanjoTooieRecompiled.html`, that draws through WebGPU. The desktop build is upstream's and unchanged: README.md's
Building section.

`lib/rt64`, `lib/N64ModernRuntime`, `lib/RecompFrontend` and `lib/N64Recomp` are upstream's, at the same commits, and
patched by `patches/` as upstream patches them (`tools/setup_deps.py`).
[N64Recomp-browser](https://github.com/amazingalek/N64Recomp-browser) (`lib/N64Recomp-browser`) puts the web support
on top of those (its `patches/apply.cmake`) and makes the game a page (its `frontend/`). Where the two change the same
code, `tools/build_web.sh` leaves N64Recomp-browser's change out of that file: `thread_queue_remove`, which upstream's
runtime patch fixes too, and the recompiler's jump tables in another section, whose analysis upstream's N64Recomp
patch rewrites.

The page needs recompiled code of its own: the committed `RecompiledFuncs/` is C from upstream's N64Recomp, and the
page's comes from the web-patched one, which writes a tail call as a `return_call` and keeps the FPU's rounding mode
for float-to-int conversions (WebAssembly's own instructions only round to nearest). So `tools/build_web.sh` makes it
from your ROM into `build/RecompiledFuncs-web`, as `tools/autostub.py` makes upstream's.

Mods a player adds are off on the page (the live recompiler writes machine code, which a page can't load), so are
Exit (it would leave the page dead) and RT64's render to RAM (`src/main.cpp` says why).

## What it needs

- The US ROM of Banjo-Tooie, once: `build/decompressed.us.z64` is made from it and kept.
- The [Emscripten SDK](https://emscripten.org/docs/getting_started/downloads.html), installed and activated
  (`source emsdk_env.sh`).
- [naga](https://github.com/gfx-rs/wgpu/tree/trunk/naga) on `PATH` (`cargo install naga-cli`), which turns the shaders
  into WGSL, and `spirv-opt` ([SPIRV-Tools](https://github.com/KhronosGroup/SPIRV-Tools)), without which the shaders
  come out about twice the size.
- A host clang and clang++ for the recompiler (`HOST_CC` and `HOST_CXX` pick others), CMake 3.20+, Ninja, git and
  Python 3 with `venv` (the script installs rabbitizer into `build/venv`).
- [ccache](https://ccache.dev) on `PATH`, optional: a second build dir, or another checkout with `build-web` inside it,
  then compiles nothing that was compiled before.

It was built on Linux, in the Docker image N64Recomp-browser's README describes.

## Building

```bash
git clone --recursive https://github.com/amazingalek/BanjoTooieRecompiled-web
cd BanjoTooieRecompiled-web
tools/build_web.sh "path/to/Banjo-Tooie (USA).z64"
```

Run again after a pull, without the ROM: each step skips what is done. `WEB_CMAKE_ARGS` goes to the configure
(`-DN64RECOMP_BROWSER_FAST_LINK=ON` for a quick link while trying something, never for a page people play).

`build-web` then holds `BanjoTooieRecompiled.html`, `.js`, `.wasm`, `.data` and `coi_serviceworker.js`. The page must
be cross-origin isolated: serve the folder with `Cross-Origin-Opener-Policy: same-origin` and
`Cross-Origin-Embedder-Policy: require-corp`, or on a host that can't set headers (GitHub Pages), as is, and
`coi_serviceworker.js` sets them after one reload. The player picks their ROM in the launcher; it, the settings and the
saves are kept in the browser's IndexedDB for that origin.

## The shaders

The page builds the game's shaders from `src/rt64_shaders.txt` (`RT64_PREBUILT_SHADER_LIST` in `CMakeLists.txt`), in
sections, one a world. In Chrome they are built behind the game from its first frame, and the game waits only when a
frame wants 4 or more that aren't built yet, under a small "Preparing graphics" indicator in a corner; Chrome keeps
them for the visits after. Firefox builds a pipeline in line with the rest of its GPU work, so there the game waits
instead: on its first frame for the list's boot, and for a world's section when a frame first wants 4 of its shaders.
Without them RT64 would draw with its ubershader meanwhile, which integrated graphics can't keep up with. A shader the
list missed is built behind the game, and the page remembers it and builds it with the rest on the next visit.

The list is recorded by code, not by hand: `tools/shader_plan.json` (written by `tools/make_plans.py`) is a plan for
N64Recomp-browser's `tools/record_shaders.mjs`, which boots the page, starts a new game and, for each section, sends
Banjo to the maps of one world with `tools/shader_survey.js`, looking around on each. That script needs no change to
the game: a map change is a request the game's own code leaves in RAM, and the survey leaves the same one (its header
says where). To record again:

```bash
python3 tools/make_plans.py
node lib/N64Recomp-browser/tools/record_shaders.mjs tools/shader_plan.json build-web <rom> src/rt64_shaders.txt
```

then put back the list's header. The list's header says what was played.

## How it plays

The desktop build (upstream's release, Windows, RTX 2070), game frames a second at the first map of each world: Jinjo
Village, Glitter Gulch Mine, Ordnance Storage, Mayahem Temple and Cloud Cuckooland 30, Terrydactyland 12, Hailfire
Peaks 10. Entering Ordnance Storage and Mayahem Temple didn't crash there.

The page from Pages (main c829a51, gh-pages 7751c2a, N64Recomp-browser 7277a2e) on 2026-10-15, RTX 2070, 1256x645, a
fresh profile each, the host's every core busy with other work, by `tools/play_plan.json` (the boot, a new game's
opening, then the first map of every world, about 12 s each) with N64Recomp-browser's `tools/play_page.mjs`:

- Headless Chrome 155 waited 2.0 s for 18 of the boot's shaders and had built all 160 pipelines 24 s in; Firefox 158
  waited 4.0 s for the boot's 59 and then up to 1.6 s for a world's. Through the menus, the opening and the worlds up
  to Jolly Roger's Lagoon Chrome drew 59 presents a second, Firefox 49-58 with its waits for each world in it (49.2
  and 53.6, the medians of the whole run).
- In Terrydactyland, Grunty Industries, Hailfire Peaks, Cloud Cuckooland and Cauldron Keep both drew 12-45: the game's
  own rate there, which the desktop shares. RT64 paces its presents there (`presents paced to the game's frames`), one
  a game frame, 12-14 a second in Hailfire Peaks: the game's frames come unevenly, while the GPU is 30-39% busy.
- No sound short after the boot's wait, and no WebGPU errors. Firefox's one exception is the first load's wasm fetch,
  cut off by `coi_serviceworker.js`'s reload.
- At 3840x2000, about 7 times a laptop window's pixels (`--size 3840x2000 --play 25`), Chrome drew 59.4 presents a
  second and Firefox 59.2 after the boot's wait, the GPU 37-38% busy, no sound short.
- From Pages, built on N64Recomp-browser v0.43.0 (main 4ca79dc), on 2026-10-15, RTX 2070, 1256x645, a fresh profile
  each, one page at a time, the plan's first 60 s: headless Chrome 155 waited 2.1 s for 18 and drew 59.4 presents a
  second (median), Firefox 158 waited 4.1 s for the boot's 59 and drew 58.7, no sound short after the waits, no WebGPU
  errors.
- On N64Recomp-browser v0.46.0 (main 25f69f8 built with its pin moved there, served locally) on 2026-10-15, RTX 2070, a
  fresh profile each, one page at a time, a host 14-27% busy, the plan's first 120 s: headless Chrome 155 waited 1.7 s
  for 18 and drew 58.4 presents a second (median), Firefox 158 waited 3.9 s for the boot's 59 and up to 1.6 s a world
  and drew 57.8; at 3840x2000 (`--play 25`) Chrome waited 1.7 s and drew 59.6, Firefox 3.8 s and 59.2. No sound short,
  no WebGPU errors.

Played on N64Recomp-browser v0.50.0 (main 0afb26f built with its pin moved there, served locally) on 2026-10-16, RTX
2070, a fresh profile each, one page at a time, a quiet host, by `tools/play_plan.json` with `play_page.mjs`: at
1256x645 headless Chrome 155 waited 1.4 s and drew 55.2 presents a second (median; headless Chrome drew about 56 frames
a second that night: four games played from Pages beside their builds, as a control, read 54.8-55.6 too), Firefox 158
waited 7.3 s and drew 58.0, both at the game's own rate in the later worlds as before; uncapped at 3840x2000
(`--uncapped --play 25`, the first such run) Chrome drew 335.1 after 1.4 s and Firefox 123.6 after 4.1 s. No sound short
and no WebGPU errors.

Render to RAM is off on the page: on, the same 200 s in Jinjo Village and Terrydactyland drew 48.6 presents a second
with the sound about 10,000 frames short, against 59.0 and none off (headless Chrome 155). With it off, RT64 made every
tile copy a new texture until rt64-web 8bea892: the game makes 4 a frame, and the page had 16,690 textures and 2.7 GB
of video memory after those 200 s, its frame rate falling. Now it keeps 4 copies and about 300 textures, 53 MB, flat.

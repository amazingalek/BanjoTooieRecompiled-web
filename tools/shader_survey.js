// Evaluated in the page by N64Recomp-browser's tools/record_shaders.mjs and play_page.mjs (tools/shader_plan.json,
// tools/play_plan.json), to reach any map by code, without anyone playing. It needs no change to the game: a map
// change is a request the game's own code leaves in the block at 0x80127630 and its main loop acts on, and this
// leaves the same request (func_800A7A6C, func_800A7A90 and func_800A7B18 write it, in that order):
//
//   +0x10 (halfword) the map, +0x13 the entrance, +0x14 the transition (0: a cut, no fade), +0x15 what +0x18 held,
//   +0x16, +0x17 and +0x18 cleared, then +0x12 set to 1, the request itself.
//
// The map the game is on is the halfword at 0x80132DC2 (func_800EA05C gives it), and the byte at 0x801275C0 is set while
// a change is under way (gcgoto_entrypoint_14), which the game's own requests also set. warp first waits for one the game
// began itself to end (up to 15 s): cut in during its fade, the fade stayed black. warp(map, exit) resolves once that has changed to the map asked
// for, or with false after 30 s; map() gives it, and waitMap(id, ms) waits for one. RDRAM is found as page_driver.mjs's
// n64r finds it; bytes and halfwords sit at the address XOR 3 and XOR 2 in its little-endian words.
(() => {
  if (!window.__rdram) {
    const h = HEAPU32;
    for (let i = 2; i < h.length - 8; i++) {
      if (h[i] === 0xB0000000 && h[i - 2] <= 2 && (h[i + 4] === 0x400000 || h[i + 4] === 0x800000)) {
        window.__rdram = i * 4 - 0x308;
        break;
      }
    }
  }
  const base = window.__rdram;
  const off = (a) => base + (a - 0x80000000);
  const w8 = (a, v) => { HEAPU8[off(a) ^ 3] = v; };
  const w16 = (a, v) => { HEAPU16[(off(a) ^ 2) >>> 1] = v; };
  const r8 = (a) => HEAPU8[off(a) ^ 3];
  const r16 = (a) => HEAPU16[(off(a) ^ 2) >>> 1];
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const MAP = 0x80127630;
  const CURRENT = 0x80132DC2;
  window.map = () => r16(CURRENT);
  window.waitMap = async (id, ms = 120000) => {
    for (let t = 0; t < ms; t += 100) { if (r16(CURRENT) === id) return true; await sleep(100); }
    return false;
  };
  window.warp = async (id, exit = 0) => {
    for (let t = 0; t < 15000 && r8(0x801275C0); t += 100) await sleep(100);
    w16(MAP + 0x10, id);
    w8(MAP + 0x13, exit);
    w8(MAP + 0x16, 0);
    w8(MAP + 0x15, r8(MAP + 0x18));
    w8(MAP + 0x18, 0);
    w8(MAP + 0x14, 0);
    w8(MAP + 0x17, 0);
    w8(MAP + 0x12, 1);
    w8(0x801275C0, 1);
    return window.waitMap(id, 30000);
  };
  return true;
})()

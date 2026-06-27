# Worklog — v0.26.0

Batch of roster/archetype fixes and additions. Status of each item below.

## Status legend
- [x] done  · [~] in progress · [ ] todo

## Items
- [x] **A1. GL rings** — ring moved from `prop` into `costume` (always shown) for
  Arisia Rrab, Jessica Cruz, Katma Tui, Star Sapphire. (Jade keeps energy construct.)
- [x] **A2. Harley Quinn (SS)** — pale white face, club makeup, bold eyeshadow,
  winged liner, false lashes, deep-red manic grin; blonde high pigtails dip-dyed
  pink/blue at tips; white crop top, tattered red/blue shorts over ripped fishnets,
  studded choker; baseball-bat prop (replaces mallet).
- [x] **A3. Harley Quinn (Classic Jester)** — NEW. BTAS red/black harlequin catsuit,
  jester hood, black domino mask, chalk-white face + red grin; optional mallet prop.
- [x] **A4. Booster Gold** — late-1980s suit, gold star emblem, yellow visor, blue
  sweeping around sides/back/top of head; face/hair exposed.
- [x] **A5. Blue Beetle** — renamed existing → `Blue Beetle (Jaime Reyes)`; added
  `Blue Beetle (Ted Kord)` (classic late-80s, cowl + goggles, face exposed).
- [x] **A6. Astro Boy** — deleted entry entirely.
- [x] **B. Engine** — `nodes/identity_forge.py`: locked Makeup-group fields survive a
  gender override (`_GENDER_FLEXIBLE_GROUPS`). Fixes male drag makeup. Two existing
  tests that pinned the old (drop) behavior were updated to assert the new behavior;
  random men still default bare-faced (`test_male_random_never_feminine`).
- [x] **C1. Drag Performer** — enriched with eye_makeup / eyeliner / lashes.
- [x] **C2. Era archetypes** — added 1950s Sock Hop, 1960s Hippie, 1990s Goth,
  1980s Preppy, 1980s New Wave (ARCHETYPES + _COSTUMES). 128 archetypes total.
- [x] **E1. Version** — pyproject.toml 0.25.0 → 0.26.0.
- [x] **E2. Docs** — architecture.md roster count is approximate (~840) and still
  valid (net +1); no hardcoded exact count to change.
- [x] **QA** — `validate_data.py` PASSED (128 archetypes, 844 cosplayers); 186
  unittests OK; manual checks confirm male drag keeps glam, Arisia ring in costume,
  Astro Boy removed, Beetle/Harley keys present.
- [x] **Commit + push.** Pushed as `3ddaddf` on `main`.

## Deferred (out of scope)
- Per-archetype `{color}` slot sweep beyond existing usage.
- A `covers_hair` flag for hooded characters (BTAS Harley, Ted Kord) — randomized
  hair under the hood is accepted for now.

## Notes
- Harley's two-tone pigtail tips are encoded in `costume` text (no structured
  two-tone hair field exists).

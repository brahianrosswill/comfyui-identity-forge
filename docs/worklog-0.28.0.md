# Worklog — v0.28.0

Body-paint colour-anchor bug fix, a non-human-face mask sweep, and content additions
(10 archetypes, 2 cyborg creatures). No breaking changes (all additive).

## Status legend
- [x] done · [~] in progress · [ ] todo

## Items

### Bug fix — body-paint white-face (the primary report)
Root cause: face-visible body-paint characters suppress `skin_tone`/`complexion` (correct, to
stop a *human* tone), which left the **opening sentence with no skin colour at all**, so t2i
defaulted the high-attention face to a human tone (Poison Ivy white face; Raphael "pale white guy's
face"). Identical in *Costume only* / *Full character*; "set all to none" only made it worse.
- [x] **Builder colour anchor** (`nodes/identity_forge_cosplayer.py`) — after body-paint
  suppression, re-inject the colour into `skin_tone` so the lead sentence reads "…and vivid green
  skin". Auto-derived from the `coat of <colour> <material>` clause (`_BODY_PAINT_COLOR_RE` /
  `_body_paint_skin_color`); explicit free-text **`skin` key** wins (mirrors `eyes`).
- [x] **Prose guard** (`nodes/identity_forge.py`) — don't append `" skin"` when the value already
  ends in skin/fur/scales/hide ("dark blue scaled-skin", not "…scaled-skin skin").
- [x] **`skin` key on the 4 non-auto entries** — Maui (`warm brown`), Iceman (`icy pale-blue`),
  D'Vorah (`pale yellow-green`), Bib Fortuna (`pale waxy`). Maui's old suppressed `physique.skin_tone`
  moved to the always-on anchor.
- [x] **`validate_data`** allows the optional `skin` key (non-empty; not also pinned in skin_tone).
- Anchor is a wired value → survives both look levels **and** "set all to none" (tested).

### Pattern A masks — non-human faces (decided: add masks)
- [x] **TMNT turtles ×4** (Leonardo/Raphael/Donatello/Michelangelo) → `covers_face` + `mask`
  (green turtle face + beak + coloured bandana); body keeps the green skin anchor.
- [x] **King Shark, Abe Sapien, Jar Jar Binks, Despero** → `covers_face` + `mask` (shark / amphibian
  / Gungan / pink-red alien head). Humanoid coloured characters (She-Hulk, Mystique, Gamora, …)
  stay face-visible and rely on the anchor.

### Content — archetypes (decided: all 10)
- [x] `data/templates.py` (+ `_COSTUMES`): **Tennis Player, Gymnast, Baker, Florist, Plumber,
  Retail Cashier, Rancher, Navy Sailor, Pin-up Model, Streamer.** Gender-neutral unless strongly
  coded (Pin-up Female). All field values verified valid; uniform random pick → no overweighting.

### Content — cyborg creatures (decided: the two listed)
- [x] `data/creatures.py`: **porcelain cyborg** (porcelain panels + black linework + blob
  cybernetics + glowing nonstandard eyes, neon `palette_pool`) and **chrome-flesh cyborg**
  (organic/chrome hybrid). Class `Aliens`; uniform `rng.choice` over 131 names → cyborgs stay
  ~1/131, nothing overweighted; palette draw stays last so existing seeds keep their creature.

### onebuttonprompt (decided: no changes, document for later)
- [x] **`docs/onebuttonprompt-findings.md`** — inventory of useful OBP `csvfiles` + a safe-addition
  strategy (route batches through presets / weighted families / density-gating / scoped controls;
  never bare flat-field appends) so a large future pass won't overweight any concept. No field,
  weight, or pool changed from OBP in this release.

### Docs / version
- [x] `pyproject.toml` 0.27.0 → 0.28.0.
- [x] `docs/architecture.md` — skin-anchor + `skin`-override convention, Pattern-A note, optional
  cosplayer keys updated.
- [x] `docs/worklog-0.28.0.md` — this file.

## QA
- [x] `python tests/validate_data.py` → PASSED (138 archetypes, 131 creatures, 844 cosplayers).
- [x] `python -m unittest discover -s tests` → 201 OK (new `SkinColorAnchorTests`; updated
  body-paint tests now assert the colour anchor, not an empty slot).
- [x] Node-path spot-checks: Ivy/She-Hulk/Mystique/King Shark open with "…and <colour> skin" in both
  look levels and under "set all to none"; turtles & fish-faces drop the human face and render the
  mask; new archetypes and both cyborgs render.
- [x] Commit + push.

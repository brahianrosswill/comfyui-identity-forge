# Worklog — v0.27.0

Likeness-coherence batch: a new `covers_hair` flag, an alien/droid likeness sweep, a Poison Ivy
rework, and a root-cause engine fix for suppression locks that were silently dropped through the
node path. No breaking changes (all additive; existing pure-human entries unchanged).

## Status legend
- [x] done · [~] in progress · [ ] todo

## Items

### Engine (`nodes/identity_forge.py`)
- [x] **E1. `covers_hair` flag.** New `_COVERS_HAIR_KEY` + `_CONCEALED_HAIR_GROUPS = {"Hair"}`;
  parsed from `_meta`, popped in `execute`, threaded as `generate_character(..., covers_hair=...)`.
  Drops the Hair group only (keeps Face/Makeup) — narrower than `covers_face`.
- [x] **E2. Fully-encased skin-tone fix.** When `covers_face` **and** a full hard shell
  (`covers_body`/`_FULL_COVER_RE`), the leaking Body-group `skin_tone` is dropped
  (`_CONCEALED_SHELL_SKIN_FIELDS`). Fixes 2-1B and the Iron Man / 4-LOM class (stray human skin
  under armour/plating). Respects an explicit user `skin_tone` lock.
- [x] **E3. ROOT CAUSE — wired `"None"` omits now survive the node.** `execute`'s
  `archetype_locked` excluded `"None"`, so the builder's body-paint / bald / eye-lock
  suppressions were re-randomized by the default `"Random"` widget (She-Hulk showed a human skin
  tone under her green; bald characters grew hair). Changed the filter to keep every wired value
  `!= "Random"`; a concrete widget choice still overrides. This is the real fix for the Poison Ivy
  "pale face" report and a whole class of body-paint/bald characters.

### Builder (`nodes/identity_forge_cosplayer.py`)
- [x] **B1.** Reads `covers_hair` from the entry and emits it in `_meta` (next to `covers_body`).

### Data (`data/cosplayers.py`)
- [x] **D1. Poison Ivy.** Costume reworded to lead with the all-over green coat covering the face;
  `lip_color: "red"` added (Face group, survives body-paint makeup suppression → red lips);
  `body_type: voluptuous` (applies in Full-character mode). Combined with E3 she no longer renders
  a pale human face under the green.
- [x] **D2. Alien sweep — Pattern A** (`covers_face` + `mask` + `body_paint: True`, eyes folded
  into the mask): Max Rebo, Greedo, Admiral Ackbar, Ithorian, Jawa, Nute Gunray, Kuiil. The
  non-human face is now a mask (no random human face/hair) and the body's skin tone is suppressed.
- [x] **D3. Alien sweep — Pattern B** (face kept): Bib Fortuna gets `body_paint: True` (pale waxy
  skin → no contradicting skin tone) + `covers_hair: True` (lekku, no scalp hair).
- [x] **D4. 2-1B Droid.** No entry edit — already `covers_face` + auto-detected droid shell, so
  E2 drops its stray skin tone.
- [x] **D5. `covers_hair` hood sweep.** Reviewed every cowl/hood. Applied to Harley Quinn
  (Classic Jester) and Blue Beetle (Ted Kord) — the only face-visible, scalp-enclosing entries with
  no signature hair. All other hooded characters are already `covers_face` (Ghostface, Batman,
  Flash, Scorpion) or carry an iconic-hair signature lock that must show (Batgirl, Catwoman,
  Captain America, Sheik, Deku, Morrigan), so they were left untouched.
- [x] **D6.** Fixed pre-existing-in-working-tree invalid value: Harley Quinn `eyeliner` →
  `"dramatic winged"` (a user edit had left `"dramatic"`, not a valid option).

### Tests (`tests/test_engine.py`)
- [x] `CoversHairTests` — drops Hair, keeps Face; round-trips through `_meta` (Ted Kord).
- [x] `ShellSkinToneTests` — masked droid drops `skin_tone`; masked-only keeps it; locked tone
  survives; 2-1B end-to-end.
- [x] `SuppressionLockSurvivalTests` — body-paint + bald suppression survives the **node path**
  (`resolve_locked_fields`), and a concrete widget still overrides. Guards E3.
- [x] `BodyPaintLipColorTests` — Poison Ivy keeps red lips while skin tone stays suppressed.
- [x] Added `_node_locked` helper so suppression tests exercise the real node flow, not the
  flat-dict shortcut that hid the E3 bug.

### Docs / version
- [x] `pyproject.toml` 0.26.0 → 0.27.0 (minor).
- [x] `docs/architecture.md` — `covers_hair` convention, fully-encased skin-tone drop, and the
  wired-`"None"`-omit gotcha.
- [x] `docs/worklog-0.26.0.md` — deferred `covers_hair` marked done; two-tone-hair decision recorded.
- [x] `docs/worklog-0.27.0.md` — this file.

## Decisions / out of scope
- **Two-tone hair field: not implemented** — disproportionate (fields.py + JS `GENDER_POOLS` +
  constraints sync). Harley's pigtail tips stay in costume text.
- Non-Star-Wars aliens with the same latent random-hair/skin issue can reuse the Pattern A/B
  recipes; not swept in this batch.

## QA
- [x] `python tests/validate_data.py` → PASSED.
- [x] `python -m unittest discover -s tests` → 197 tests OK.
- [x] Manual node-path spot-checks: Poison Ivy (no skin tone, red lips), She-Hulk / bald (E3),
  Pattern-A aliens (masked, no human face/hair/skin), 2-1B (no skin tone), Harley Jester & Ted
  Kord (no hair line, face intact).
- [x] Commit + push.

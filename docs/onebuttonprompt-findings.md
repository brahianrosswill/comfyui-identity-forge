# OneButtonPrompt — content inventory & safe-addition strategy

A scouting doc for a **future** pass that mines `OneButtonPrompt` (and similar wildcard packs
like `cornflakes`) for more variety. **Nothing here is implemented yet** — the point is to land
large additions later *without* overweighting any concept (or cluster of similar concepts) during
randomization. Source is read-only: `D:\comfy\custom_nodes\onebuttonprompt\csvfiles\` and
`D:\SDshared\wildcards\`.

## The overweighting problem (why we can't just append)
Most IdentityForge fields are **flat pools** picked with a uniform `rng.choice`. Two failure modes:

1. **Single-field inflation.** Adding N options to a flat field changes every *other* option's odds
   (documented gotcha in `architecture.md`). Adding 30 hairstyles makes any one hairstyle rarer and
   the *category* "unusual hair" much more common.
2. **Cluster inflation.** Even one-at-a-time additions tilt the *distribution of concepts* if they
   cluster. Adding "cyberpunk street", "neon alley", "holographic market", "rain-slicked megacity"
   as four separate `location` options quadruples the odds a random portrait is cyberpunk-themed,
   crowding out everything else — the exact thing to avoid.

## Existing mechanisms that already solve this (reuse these)
- **Uniform name pick over presets** — Archetype/Cosplayer/Creature random picks one *name*
  uniformly. Adding a whole *themed look* as one archetype/creature adds exactly one unit of weight,
  no matter how many descriptive tokens it carries. **This is the safest channel for big batches.**
  (This round's 10 archetypes + 2 cyborgs went here.)
- **Weighted families** — `HAIR_STYLE_FAMILIES` (`data/fields.py`, `_pick_hair_style`): a family is
  drawn by a frozen weight, then a variant uniformly *within* it. Adding variants subdivides a
  family's share instead of inflating it (3 ponytails still total what 2 did). **The template for
  enlarging any flat field without shifting its top-level distribution** — generalize this to
  `location`, `expression`, etc. before bulk-adding.
- **Density-gated extras** — `_EXTRA_ABSENCE` (`nodes/identity_forge.py`): variety can grow while
  frequency stays pinned by the `accessory_density` control. Good for accessory-like fields.
- **Control fields / scoping** — `location_setting`, `random_scope`, `Random - <class>` narrow the
  pool deliberately rather than by accident.

## OBP csvfiles worth mining (by target, with the safe channel)
| OBP list(s) | Maps to | Safe channel |
|---|---|---|
| `jobs.csv`, `rpgclasses.csv`, `charactertypes.csv` | new **archetypes** | uniform preset name pick |
| `humanoids.csv`, `animals.csv`, `space.csv` | new **creatures** | uniform preset name pick |
| `settings.csv`, `locations.csv`, `backgrounds.csv`, `minilocations.csv`, `waterlocations.csv` | `location` field | **family-weighted** sub-grouping (Indoor/Urban/Nature/Studio/Fantasy) before adding |
| `moods.csv`, `humanexpressions.csv` | `expression`, `mood` | family-weighted, or small curated adds |
| `poses.csv`, `shotsizes*.csv`, `directions*.csv` | `shot_type` / a future `pose` field | family-weighted |
| `lighting*.csv` | `lighting` | family-weighted (Daylight/Indoor/Dramatic/Neon) |
| `haircolors.csv`, `hairstyles*.csv` | hair fields | extend `HAIR_STYLE_FAMILIES`; gate fantasy colours behind `hair_color_scope` |
| `eyecolors.csv` | `eye_color` | keep believable in the pool; exotic via the cosplayer `eyes` free-text override |
| `outfits*.csv`, `materials.csv`, `patterns.csv` | archetype `_COSTUMES` `{slot}` pools | add to `COSTUME_SLOTS` (already family-like) |
| `objectstohold.csv` | `held_item` (hidden) / cosplayer `prop` | per-preset, not a flat field |

## Recommended approach for the future pass
1. **Prefer presets.** Route most new *concepts* through new archetypes/creatures (one unit of
   weight each) rather than flat-field options.
2. **Family-weight before bulk-adding to a flat field.** Generalize the `HAIR_STYLE_FAMILIES`
   pattern to `location`/`lighting`/`expression`/`pose`: define sub-families with frozen weights so
   adding variants subdivides a share. Add a `validate_data` partition check (as hair styles have).
3. **Gate themed clusters** behind a control field (e.g. a `location_setting` theme) so a cyberpunk
   batch only appears when asked, never crowding the default mix.
4. **De-duplicate against the current pools** first (many OBP entries already exist here).
5. **Keep it ASCII / believable** per the existing conventions; exotic values go through overrides
   (`eyes`, `skin`) or scoped controls, not the main believable-people dropdowns.

## Status
Captured for a later, deliberate pass. No fields, weights, or pools changed in v0.28.0 from OBP.

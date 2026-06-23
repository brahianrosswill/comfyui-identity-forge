"""IdentityForgeVaultSave node — save a generated character to the local vault.

A small terminal node, used like **Save Image**: branch the ``prompt_json`` output of
an :class:`~nodes.identity_forge.IdentityForge` node into it (and, if you want a
thumbnail, the rendered ``image``). That's it — one required wire. It writes a
self-contained vault entry you can recall later with
:class:`~nodes.identity_forge_vault_load.IdentityForgeVaultLoad`. Mute the node
(Ctrl+M) to skip saving without rewiring.

Why ``prompt_json`` is all it needs: by the time IdentityForge emits it, any wired
Cosplayer / Archetype / Modifier preset has already been baked into the document
(``_meta.cosplay_of``, the ``_modifiers`` section, every resolved field value). So a
single saved document captures the whole character regardless of how the graph was
wired, and recall feeds it straight back through IdentityForge's ``archetype_json``
string input — no fragile per-widget round-trip. (The prose is regenerated from the
same fields on reload, so it isn't required here.)

Storage lives under ComfyUI's *user* directory (``user/identity_forge/characters/``),
which survives node-pack reinstalls and is never touched when you clear ``output/``.
Each character is one folder containing ``character.json`` (the pristine resolved
document), ``preview.png`` (a thumbnail, when an image is wired) and ``meta.json``
(sidecar metadata kept *out* of ``character.json`` so recall stays a clean round-trip).

The storage engine (:func:`save_character` and friends) is pure and testable without
ComfyUI — it takes an explicit ``vault_root`` and an optional already-decoded PIL
thumbnail, keeping torch / numpy / folder_paths out of the tested core.
"""
from __future__ import annotations

import datetime as _dt
import json
import re
import shutil
from collections import OrderedDict
from pathlib import Path
from typing import Any

try:
    from comfy_api.latest import io  # type: ignore[import-not-found]
    _COMFY_AVAILABLE: bool = True
except ImportError:  # pragma: no cover — exercised only outside ComfyUI
    _COMFY_AVAILABLE = False

#: Bumped only if the on-disk layout changes in a way recall must branch on.
SCHEMA_VERSION = 1

#: Largest edge of the stored preview thumbnail, in pixels.
_THUMBNAIL_MAX = 512

#: ``on_existing`` collision policy.
_OVERWRITE = "Overwrite"
_KEEP_BOTH = "Keep both (suffix)"
_SKIP = "Skip"

#: Standard entry filenames.
_CHARACTER_FILE = "character.json"
_PROMPT_FILE = "prompt.txt"
_PREVIEW_FILE = "preview.png"
_META_FILE = "meta.json"

#: Characters never allowed in a folder name (filesystem-illegal + separators).
_ILLEGAL = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_name(raw: str) -> str:
    """Return ``raw`` reduced to a safe single-segment folder name, or ``""``.

    Strips filesystem-illegal characters and path separators, collapses runs of
    whitespace, trims trailing dots/spaces (Windows-hostile), and caps the length.
    Returns ``""`` when nothing usable remains, so callers can fall back.
    """
    name = _ILLEGAL.sub(" ", str(raw or ""))
    name = re.sub(r"\s+", " ", name).strip().strip(".").strip()
    if name in {"", ".", ".."}:
        return ""
    return name[:120].strip()


def _source_label(character_json: str) -> str:
    """Best-effort cosplay/archetype label from a resolved document's ``_meta``."""
    try:
        meta = json.loads(character_json).get("_meta", {})
    except (ValueError, TypeError, AttributeError):
        return ""
    return str(meta.get("cosplay_of") or meta.get("archetype") or "")


def _derive_name(custom_name: str, character_json: str, fallback: Any) -> str:
    """Pick a folder name: sanitized custom name, else cosplay label, else fallback."""
    return (
        sanitize_name(custom_name)
        or sanitize_name(_source_label(character_json))
        or str(fallback)
    )


def _timestamp_name() -> str:
    """A readable, reasonably-unique default name when nothing else is available."""
    return _dt.datetime.now().strftime("character-%Y%m%d-%H%M%S")


def _entry_dir(vault_root: Path, name: str) -> Path:
    """Resolve ``vault_root/<sanitized name>`` and guard against escaping the root.

    Raises ``ValueError`` if the name sanitizes to nothing or if the resolved path
    is not a direct child of ``vault_root`` (defends the write/rename/delete APIs
    against ``..`` and absolute-path tricks).
    """
    safe = sanitize_name(name)
    if not safe:
        raise ValueError(f"Unusable character name: {name!r}")
    root = Path(vault_root).resolve()
    entry = (root / safe).resolve()
    if entry.parent != root:
        raise ValueError(f"Refusing path outside the vault: {name!r}")
    return entry


def _unique_dir(vault_root: Path, name: str) -> Path:
    """Return an entry dir for ``name``, appending ``-2``, ``-3`` … if it exists."""
    base = _entry_dir(vault_root, name)
    if not base.exists():
        return base
    safe = base.name
    for n in range(2, 1000):
        candidate = _entry_dir(vault_root, f"{safe}-{n}")
        if not candidate.exists():
            return candidate
    raise ValueError(f"Too many entries named like {name!r}")


def save_character(
    vault_root: Path | str,
    name: str,
    character_json: str,
    prompt_text: str = "",
    on_existing: str = _OVERWRITE,
    thumbnail: Any = None,
    pack_version: str = "",
) -> str:
    """Write one vault entry and return the folder name actually used.

    ``thumbnail`` is an optional PIL image (already decoded by the node, so this
    function stays torch/numpy-free); it is copied, downscaled to
    :data:`_THUMBNAIL_MAX` and saved as ``preview.png``. ``character_json`` is
    stored verbatim so recall round-trips cleanly. ``prompt_text`` is written only
    when non-empty. ``on_existing`` selects the collision policy: overwrite,
    keep-both (suffix), or skip.
    """
    root = Path(vault_root)
    target = _entry_dir(root, name)

    if target.exists():
        if on_existing == _SKIP:
            return target.name
        if on_existing == _KEEP_BOTH:
            target = _unique_dir(root, name)
        else:  # Overwrite — clear stale files (e.g. an old preview)
            shutil.rmtree(target, ignore_errors=True)
    target.mkdir(parents=True, exist_ok=True)

    (target / _CHARACTER_FILE).write_text(character_json or "{}", encoding="utf-8")
    if prompt_text:
        (target / _PROMPT_FILE).write_text(prompt_text, encoding="utf-8")

    if thumbnail is not None:
        thumb = thumbnail.copy()
        thumb.thumbnail((_THUMBNAIL_MAX, _THUMBNAIL_MAX))
        thumb.save(target / _PREVIEW_FILE)

    meta = OrderedDict([
        ("display_name", target.name),
        ("created", _dt.datetime.now().isoformat(timespec="seconds")),
        ("source_label", _source_label(character_json)),
        ("schema_version", SCHEMA_VERSION),
        ("pack_version", pack_version),
    ])
    (target / _META_FILE).write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return target.name


if _COMFY_AVAILABLE:

    def _vault_root() -> Path:
        """Vault root under ComfyUI's user dir; created on first use."""
        import folder_paths  # type: ignore[import-not-found]

        root = Path(folder_paths.get_user_directory()) / "identity_forge" / "characters"
        root.mkdir(parents=True, exist_ok=True)
        return root

    def _tensor_to_pil(image: Any) -> Any:
        """First frame of an ``(B,H,W,C)`` float[0,1] tensor → an RGB PIL image."""
        import numpy as np
        from PIL import Image as PILImage

        frame = image[0]
        arr = frame.detach().cpu().numpy() if hasattr(frame, "detach") else np.asarray(frame)
        arr = (np.clip(arr, 0.0, 1.0) * 255.0).round().astype("uint8")
        pil = PILImage.fromarray(arr)
        return pil if pil.mode == "RGB" else pil.convert("RGB")

    class IdentityForgeVaultSave(io.ComfyNode):  # type: ignore[misc, valid-type]
        """Save a generated character to the local vault (terminal node)."""

        @classmethod
        def define_schema(cls) -> "io.Schema":
            return io.Schema(
                node_id="IdentityForgeVaultSave",
                display_name="Identity Forge Vault Save",
                category="conditioning/character",
                description=(
                    "Save the generated character so you can recall it later with Identity "
                    "Forge Vault Load. Wire Identity Forge's 'prompt_json' in (that's all it "
                    "needs); add the rendered 'image' for a thumbnail. Mute the node (Ctrl+M) "
                    "to skip saving. Stored under ComfyUI/user/identity_forge/characters/, "
                    "which survives updates and isn't cleared with your image output."
                ),
                inputs=[
                    io.String.Input(
                        "prompt_json",
                        force_input=True,
                        tooltip="Wire Identity Forge's 'prompt_json' here — the character to "
                                "save. Any wired Cosplayer/Archetype/Modifier is already "
                                "baked into it.",
                    ),
                    io.Image.Input(
                        "image",
                        optional=True,
                        tooltip="Optional: the rendered image. Its first frame is stored as "
                                "a thumbnail for the visual recall gallery.",
                    ),
                    io.String.Input(
                        "name",
                        default="",
                        tooltip="Name for this character. Leave blank to use the cosplay / "
                                "archetype label if present, otherwise a timestamp.",
                    ),
                    io.Combo.Input(
                        "on_existing",
                        options=[_OVERWRITE, _KEEP_BOTH, _SKIP],
                        default=_OVERWRITE,
                        tooltip="What to do if a character with this name already exists.",
                    ),
                ],
                outputs=[],
                is_output_node=True,
            )

        @classmethod
        def execute(cls, **kwargs: Any) -> "io.NodeOutput":
            prompt_json = kwargs.get("prompt_json", "")
            name = _derive_name(kwargs.get("name", ""), prompt_json, _timestamp_name())

            thumbnail = None
            image = kwargs.get("image")
            if image is not None:
                try:
                    thumbnail = _tensor_to_pil(image)
                except Exception as exc:  # noqa: BLE001 — a bad image must not block saving
                    print(f"[IdentityForgeVaultSave] Could not build thumbnail: {exc}")

            try:
                saved_as = save_character(
                    _vault_root(), name, prompt_json,
                    on_existing=kwargs.get("on_existing", _OVERWRITE),
                    thumbnail=thumbnail,
                )
                print(f"[IdentityForgeVaultSave] Saved character '{saved_as}'.")
            except Exception as exc:  # noqa: BLE001 — saving must never break a run
                print(f"[IdentityForgeVaultSave] Save failed: {exc}")

            return io.NodeOutput()

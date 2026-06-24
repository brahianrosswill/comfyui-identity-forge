import { app } from "../../scripts/app.js";

/*
 * IdentityForgeCreature frontend extension.
 *
 * Keeps the node compact: the headline widgets (creature / form / seed) stay
 * visible, while the per-slot hybrid overrides and the detail dropdowns live in
 * collapsed-by-default sections (the same zero-height collapse trick the main
 * IdentityForge node uses for its 70+ fields). Collapsing only changes how a
 * widget is *drawn* — it stays in node.widgets, so its value is still serialized
 * and passed to the backend (exactly how the main node's collapsed locks work).
 *
 * The multiline `more_features` box is a DOM-backed <textarea>. ComfyUI positions
 * DOM widgets by accumulating the heights of the widgets *above* them, so a textarea
 * placed *below* the collapsible groups desyncs on first paint (it overlaps the last
 * collapsed widget until a relayout). The fix is to anchor it to the stable headline
 * widgets only — it is placed directly after creature/form/seed, with the collapsible
 * groups below it, so collapsing/expanding anything can never push a group under it.
 * A deferred relayout (next frame) makes the initial DOM position correct too.
 *
 * Collapsing only changes how a widget is *drawn* — it stays in node.widgets, so its
 * value is still serialized and passed to the backend (exactly how the main node's
 * collapsed locks work).
 *
 * Degrades gracefully — any failure is caught so the node still works headless.
 * The widget *names* below must match the Python schema's input names.
 */

const GROUPS = [
  ["Hybrid slots", ["head", "eyes", "integument", "arms", "hands", "legs_feet", "tail", "wings"]],
  ["Detail", ["integument_finish", "palette", "size_scale"]],
];

const GROUPED_NAMES = new Set(GROUPS.flatMap(([, names]) => names));

// Multiline DOM widget(s): kept out of the collapse machinery and anchored to the
// stable headline (placed right after it, above the collapsible groups).
const MULTILINE_AFTER_HEADLINE = ["more_features"];

// --- collapse helpers (hide a widget without losing its type) -------------
function hideWidget(w) {
  if (w.__hidden) return;
  w.__hidden = true;
  w.__origType = w.type;
  w.__origComputeSize = w.computeSize;
  w.type = "if_creature_hidden";
  w.computeSize = () => [0, -4];
}

function showWidget(w) {
  if (!w.__hidden) return;
  w.__hidden = false;
  w.type = w.__origType;
  w.computeSize = w.__origComputeSize;
  w.__origType = null;
  w.__origComputeSize = null;
}

function resize(node) {
  if (typeof node.computeSize === "function") {
    const sz = node.computeSize();
    node.setSize([Math.max(node.size[0], sz[0]), sz[1]]);
  }
  node.setDirtyCanvas(true, true);
}

function setupCreature(node) {
  const original = node.widgets ? node.widgets.slice() : [];
  if (!original.length) return;

  const byName = new Map(original.map((w) => [w.name, w]));
  const multiline = new Set(MULTILINE_AFTER_HEADLINE);
  // Headline = everything that isn't grouped or a pinned multiline, kept in schema
  // order. Using "not grouped" (rather than a name allow-list) means a linked/auto
  // widget like control_after_generate is never accidentally dropped.
  const headline = original.filter((w) => !GROUPED_NAMES.has(w.name) && !multiline.has(w.name));

  // The multiline DOM box(es) go right after the headline so their position depends
  // only on stable widgets above them — never on a collapsed group.
  const ordered = [...headline];
  for (const name of MULTILINE_AFTER_HEADLINE) {
    const w = byName.get(name);
    if (w) ordered.push(w);
  }

  for (const [title, names] of GROUPS) {
    const widgets = names.map((n) => byName.get(n)).filter(Boolean);
    if (!widgets.length) continue;
    const state = { collapsed: true }; // collapsed by default — keep the node small
    const header = node.addWidget("button", "▸ " + title, null, () => {
      state.collapsed = !state.collapsed;
      header.name = (state.collapsed ? "▸ " : "▾ ") + title;
      for (const w of widgets) (state.collapsed ? hideWidget : showWidget)(w);
      resize(node);
    }, { serialize: false });
    for (const w of widgets) hideWidget(w); // start collapsed
    ordered.push(header, ...widgets);
  }

  // Safety net: append any widget we didn't explicitly place so a future
  // auto-added widget can never silently disappear.
  const placed = new Set(ordered);
  for (const w of original) if (!placed.has(w)) ordered.push(w);

  node.widgets = ordered.filter((w, i) => ordered.indexOf(w) === i);
  resize(node);
  // The DOM textarea caches its position on first layout; nudge a relayout next
  // frame so it lands correctly even before any user interaction.
  requestAnimationFrame(() => resize(node));
}

app.registerExtension({
  name: "identity_forge.creature.ui",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "IdentityForgeCreature") return;
    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      const result = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
      try {
        setupCreature(this);
      } catch (err) {
        console.error("[IdentityForgeCreature] frontend setup failed:", err);
      }
      return result;
    };
  },
});

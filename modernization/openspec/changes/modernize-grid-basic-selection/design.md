## Context

Legacy: `Grid/BasicSelection.aspx.cs`, `BindDataSource()` generates 48 rows (8 loop
iterations × 6 hand-coded rows — one more row per iteration than the first capability's
40). Same environment constraints as before: Node.js/npm available, no .NET SDK. This
time `modern/OrdersApi` and the `json-server` dev dependency already exist from the first
capability — genuinely reusable, not re-created.

The legacy page also has a selection-type dropdown (Single/Multiple), a selection-mode
dropdown (Row/Cell/Column), and an enable-toggle checkbox that reconfigure the grid live
via client-side JS. This design deliberately does not port that configurability — see
Non-Goals.

## Goals / Non-Goals

**Goals:**
- Byte-identical data to `BindDataSource()` (48 rows).
- Core interaction: clicking anywhere on a row toggles its selected state; multiple rows
  independently selectable; paging.
- Genuinely browser-tested in this session, same standard as the first capability.

**Non-Goals:**
- Porting the selection-type/selection-mode/enable-toggle property panel — that's
  reconfiguring the *demo itself* for showcase purposes, not a requirement of the
  underlying business capability (an Orders grid with selectable rows). Out of scope here;
  could be a follow-up capability if there's a real need for runtime-configurable
  selection behavior in the target app.
- Persisting selection anywhere beyond component state (same as the legacy page, which
  doesn't persist it either).

## Decisions

- **Click-anywhere-on-row toggle, not a checkbox column.** This is the entire point of
  picking this capability second — matching the legacy `ej:Grid`'s actual interaction
  (`AllowSelection="True"`, `SelectionSettings EnableToggle="true"`, no checkbox column in
  markup) rather than defaulting to the same UI pattern as the first capability.
- **Reuse `modern/OrdersApi` and the existing `json-server` devDependency**, not new
  ones — same reasoning as the first capability's sibling-capability decision, and this
  time it's a genuine reuse of an already-built project rather than a forward-looking
  placeholder.
- **Don't port the selection-type/mode dropdowns.** Alternative considered: port them for
  full fidelity. Rejected — they reconfigure the Syncfusion demo's *showcase* behavior
  (letting a visitor try different EJ1 grid options), not a requirement of the Orders-grid
  business capability itself. Porting demo-chrome controls would inflate scope without
  adding real capability value.

## Risks / Trade-offs

- **[Risk]** Skipping the selection-type/mode dropdowns means this port isn't
  *feature-complete* against the legacy page, only *capability-complete* against its core
  selection behavior → **[Mitigation]** Explicitly stated in Non-Goals and here — anyone
  comparing page-for-page will notice the missing property panel; it's a deliberate,
  documented scope cut, not an oversight.
- **[Risk]** Same as the first capability: backend not compiled here (no .NET SDK) →
  **[Mitigation]** Same discipline — authored to the same standard, deferred verification
  task, not archived until actually run.

## Migration Plan

Additive, parallel to the untouched legacy page — no deployment/rollback concerns.
Frontend + mock verified live in this session; real backend deferred to whoever has a
.NET SDK, same as the first capability.

## Open Questions

- If a real need for the selection-type/mode configurability surfaces later, is it its own
  capability or an addition to this one? Not a blocker now — revisit if it comes up.

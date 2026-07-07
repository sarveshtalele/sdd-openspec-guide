## Why

`Grid/BasicSelection.aspx` (legacy code-behind class `Grid.BasicSelection`) demonstrates
click-anywhere-on-row toggle multi-selection with paging, using the Syncfusion EJ1
`ej:Grid` control on an in-process Orders list. This is the third capability tackled in
this workspace and the second one built fully end-to-end — chosen specifically because it
exercises a genuinely different interaction model than the first
(`modernize-grid-checkbox-selection`'s checkbox column): here, clicking anywhere on a row
toggles its selection state, with no checkbox UI at all. Proving the modernization
pattern handles two distinct selection UX models (not just repeating the same one) is the
point of doing a second capability rather than stopping at one.

## What Changes

- Add `GET /api/basic-selection-orders` to the existing `modern/OrdersApi` project
  (created for the first capability — this time genuinely "reuse the existing project,"
  not a fresh one, since it already exists in this workspace).
- Add a `BasicSelectionGrid` React/TypeScript component rendering the same six data
  columns, with click-anywhere-on-row toggle selection (no checkbox column) and paging.
- Reuse the same local-mock-API pattern established for the first capability
  (`json-server`, already installed as a dev dependency) for genuine browser verification
  without the .NET SDK.
- Legacy `Grid/BasicSelection.aspx` is left untouched. **Not BREAKING**.

## Capabilities

### New Capabilities
- `basic-selection-grid-api`: A modern ASP.NET Core Web API + React/TypeScript
  reimplementation of the legacy click-toggle Orders grid, functionally equivalent to
  `Grid/BasicSelection.aspx`'s core selection behavior (not its full selection-type/
  selection-mode property panel — see design.md's Non-Goals), genuinely browser-verified.

### Modified Capabilities
(none — legacy code untouched; sibling capability to `checkbox-selection-grid-api`,
sharing the same API project by the same reasoning as before)

## Impact

- **New files, backend**: `modern/OrdersApi/Controllers/BasicSelectionController.cs`,
  `modern/OrdersApi/Data/BasicSelectionOrdersRepository.cs` (reuses the existing
  `Models/Order.cs`).
- **New files, frontend**: `modern/orders-grid-web/src/components/BasicSelectionGrid.tsx`,
  matching typed client, a second mock dataset file.
- **Dependencies**: none new — `json-server` already installed from the first capability.
- **No impact to legacy app or to the first capability's shipped code.**

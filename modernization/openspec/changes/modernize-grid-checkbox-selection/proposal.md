## Why

`Grid/CheckboxSelection.aspx` (legacy code-behind class `Grid.DefaultPaging`) demonstrates
checkbox-column multi-row selection with paging on an in-process Orders list, using the
Syncfusion EJ1 `ej:Grid` control. Like every other Web Forms page in this repo, markup and
data are welded to one page — no API, no reuse outside the ASP.NET runtime, and the UI
framework choice (`ej:Grid`) is baked into the page rather than swappable. This is the
second capability proven end-to-end (after `modernize-grid-basic-selection`), picked this
time using corrected analyzer output: an earlier version of the aspx-analyzer skill's
control-tag regex only matched `<asp:*>` tags and was blind to `<ej:*>` (Syncfusion's own
prefix), so it reported 0 pages with a grid control. After fixing that, 107 pages
correctly show a grid control, and this page surfaced as a clean, zero-SQL, zero-AJAX
candidate — auth `unknown` (no `[Authorize]`/role check present, consistent with the rest
of this public-facing demo repo).

## What Changes

- Add `GET /api/checkbox-selection-orders` to the same ASP.NET Core Web API used for the
  first capability (`modern/OrdersApi`), returning the exact same Orders data
  `Grid/CheckboxSelection.aspx.cs`'s `BindDataSource()` generates (40 rows: 8 loop
  iterations × 5 hand-coded rows — fewer per-iteration rows than the first capability's
  page, same columns).
- Add a `CheckboxSelectionGrid` component to the existing React/TypeScript frontend
  (`modern/orders-grid-web`) rendering the same six data columns plus a checkbox selection
  column, with paging.
- **Genuinely browser-testable in this environment**: point the frontend's dev build at a
  local mock API (`json-server`, seeded with the exact `BindDataSource()` values) instead
  of the real ASP.NET Core API, since this environment has no .NET SDK to run the real
  backend. This is a documented stand-in for local verification only — see design.md.
- Legacy `Grid/CheckboxSelection.aspx` is left untouched and running — additive, parallel
  build, same as the first capability. **Not BREAKING**.

## Capabilities

### New Capabilities
- `checkbox-selection-grid-api`: A modern ASP.NET Core Web API + React/TypeScript
  reimplementation of the legacy checkbox-selection Orders grid, functionally equivalent
  to `Grid/CheckboxSelection.aspx`, genuinely verified running in a browser in this
  environment via a documented local mock standing in for the real backend.

### Modified Capabilities
(none — legacy code untouched, and this doesn't change requirements of the first
capability's `orders-grid-api` spec, it's a sibling capability sharing the same API
project for convenience)

## Impact

- **New files, backend**: `modern/OrdersApi/Controllers/CheckboxSelectionController.cs`,
  `modern/OrdersApi/Data/CheckboxSelectionOrdersRepository.cs`, `Models` reused from the
  first capability where the shape matches.
- **New files, frontend**: `modern/orders-grid-web/src/components/CheckboxSelectionGrid.tsx`,
  a matching typed API client.
- **New files, local verification only**: a `json-server` mock dataset (not part of the
  production build) so the UI can be exercised in a real browser without the .NET SDK.
- **Dependencies**: `json-server` (dev-only, local verification) added via `npm install
  --save-dev`; no production dependency changes.
- **No impact to legacy app or to the first capability's shipped code.**

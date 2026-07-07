## 1. Backend: extend the existing ASP.NET Core Web API

- [x] 1.1 Added `Data/BasicSelectionOrdersRepository.cs`, porting `BindDataSource()`'s
      exact loop/values from `Grid/BasicSelection.aspx.cs` (48 rows: 8 iterations × 6
      rows). Authored, not compiled — see task 5.1.
- [x] 1.2 Added `Controllers/BasicSelectionController.cs` exposing
      `GET /api/basic-selection-orders`.
- [x] 1.3 Reused the existing `Models/Order.cs` — genuinely reused this time (project
      already existed from capability 2), not recreated.

## 2. Local mock API (verification-only, not shipped)

- [x] 2.1 Generated the exact 48 rows and added them to `mock/db.json` under a
      `basic-selection-orders` key.
- [x] 2.2 **ADAPTED**: originally planned as a separate `mock/basic-selection-db.json`
      file on its own port. Since both grids now render in the same `App.tsx` page
      simultaneously, they need to fetch from the same running mock server at the same
      time — `json-server` supports multiple top-level keys as separate resource
      endpoints from ONE instance, so merged both capabilities' data into the single
      existing `mock/db.json` (`checkbox-selection-orders` + `basic-selection-orders`
      keys) instead of running two servers on two ports. Verified both endpoints serve
      correctly from one `json-server mock/db.json --port 3001` instance.
- [x] 2.3 `json-server` already installed from capability 2 — confirmed no reinstall
      needed.

## 3. Frontend: React + TypeScript

- [x] 3.1 Added `src/api/basicSelectionClient.ts` — typed fetch, configurable resource
      path (same pattern as `checkboxSelectionClient.ts`).
- [x] 3.2 Added `src/components/BasicSelectionGrid.tsx` — six data columns, no checkbox
      column, click-anywhere-on-row toggle (verified: `firstRowHasCheckbox: false`),
      independent multi-row selection, paging, loading/error states.
- [x] 3.3 Wired `BasicSelectionGrid` into `App.tsx` alongside `CheckboxSelectionGrid` —
      both sections visible with clear headings, confirmed via accessibility snapshot
      (both "Checkbox Selection Grid" and "Basic Selection Grid" headings present).
- [x] 3.4 Verified the app builds — RAN FOR REAL: `tsc -b && vite build` succeeded,
      21 modules transformed (up from 19 with one grid), dist output produced.

## 4. Live browser verification (the actual point of this change)

- [x] 4.1 Started one combined `json-server mock/db.json --port 3001` (after killing a
      stale process from an earlier session that was holding the port with old data —
      found via `netstat -ano`, killed via `taskkill`). Confirmed via curl: 40 checkbox
      rows + 48 basic-selection rows, both correct.
- [x] 4.2 `.env.local` updated with `VITE_BASIC_SELECTION_ORDERS_PATH=basic-selection-orders`
      alongside the existing checkbox path var, both pointing at the same mock base URL.
- [x] 4.3 Opened in a real browser preview and verified, for real, via DOM inspection
      (screenshot tool itself timed out on this longer two-grid page — confirmed via
      console logs this was a tool/rendering-size issue, not an app error; accessibility
      snapshot + direct DOM queries used instead, equally valid evidence):
      - First row confirmed to have **no checkbox** (`firstRowHasCheckbox: false`).
      - Clicked rows 0 and 2 (orders 10001, 10003) — both became `selected: true`,
        others `false` — independent multi-selection confirmed.
      - Clicked row 0 again — became `selected: false`, row 2 remained `selected: true`
        — toggle-off confirmed, doesn't affect other selected rows.
      - Paged to page 2 — confirmed different rows (10011-10020).
      - Paged back to page 1 — order 10003 **still `selected: true`**, all others
        correctly `false` — cross-page persistence confirmed.
      - Console logs checked (`level: error`): **"No console logs."** — zero errors
        across the whole session, both grids.
- [x] 4.4 Evidence captured (DOM state snapshots above, embedded in
      `EXAMPLE_WALKTHROUGH.md` Part 12b) in place of a screenshot, since the full-page
      screenshot tool timed out on this taller two-grid page.

## 5. Real-backend verification (deferred, same as capabilities 1 and 2)

- [ ] 5.1 (requires local .NET 8 SDK — not available in this sandbox) `dotnet build` /
      `dotnet run`, confirm `GET /api/basic-selection-orders` returns the expected 48
      records.
- [ ] 5.2 Re-point the frontend at the real API, re-verify browser behavior is unchanged.

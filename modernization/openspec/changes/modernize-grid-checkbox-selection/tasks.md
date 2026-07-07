## 1. Backend: extend the existing ASP.NET Core Web API

- [x] 1.1 Add `Data/CheckboxSelectionOrdersRepository.cs`, porting `BindDataSource()`'s
      exact loop/values from `Grid/CheckboxSelection.aspx.cs` (40 rows, not 48).
- [x] 1.2 Add `Controllers/CheckboxSelectionController.cs` exposing
      `GET /api/checkbox-selection-orders`.
- [x] 1.3 Add `Models/Order.cs` — this is a fresh workspace (no prior capability built
      here), so "reuse" meant create it now, shaped identically to what capability 1 used
      in the earlier throwaway clone. Authored, not compiled — see task 5.1.

## 2. Local mock API (verification-only, not shipped)

- [x] 2.1 Add `mock/db.json` seeded with the exact same 40 rows as task 1.1's repository
      (generated from the same literal values, not re-derived).
- [x] 2.2 **DEVIATED FROM PLAN**: `mock/routes.json` remapping is not supported by the
      installed `json-server` (1.0.0-beta.15 — the classic `--routes` custom-routing flag
      from v0.x is gone; confirmed via `npx json-server --help`, and confirmed nested JSON
      does NOT create nested routes either, tested directly). Adapted instead: the mock
      exposes a flat `/checkbox-selection-orders` resource, and the frontend client takes
      the resource path as a configurable value (`VITE_CHECKBOX_ORDERS_PATH`), defaulting
      to the real API's `api/checkbox-selection-orders` and overridden to
      `checkbox-selection-orders` for local mock verification. No routes file needed.
- [x] 2.3 Installed `json-server` as a dev dependency for real
      (`npm install --save-dev json-server` — 43 packages added, 0 vulnerabilities).

## 3. Frontend: React + TypeScript

- [x] 3.1 Add `src/api/checkboxSelectionClient.ts` — typed fetch wrapper, with the
      configurable resource path from task 2.2's deviation.
- [x] 3.2 Add `src/components/CheckboxSelectionGrid.tsx` — checkbox column + six data
      columns, paging (10/page), independent per-row checkbox state (persists across
      pages via a `Set<number>` keyed by orderId), loading/error states.
- [x] 3.3 **ADAPTED**: wired `CheckboxSelectionGrid` as the sole component in `App.tsx` —
      there is no capability-1 `OrdersGrid` in this fresh workspace to place it alongside
      (that was built in an earlier, separate throwaway clone). This is the first and only
      capability built in this persistent workspace so far.
- [x] 3.4 Verified the app builds — RAN FOR REAL: `tsc -b && vite build` succeeded,
      19 modules transformed, dist output produced.

## 4. Live browser verification (the actual point of this change)

- [x] 4.1 Started `json-server mock/db.json --port 3001` for real — confirmed via direct
      curl: 40 rows returned, values match `BindDataSource()` exactly.
- [x] 4.2 Started the Vite dev server via a real preview tool (`.claude/launch.json` +
      `preview_start`), `.env.local` pointing `VITE_API_BASE_URL=http://localhost:3001`
      and `VITE_CHECKBOX_ORDERS_PATH=checkbox-selection-orders` at the mock.
- [x] 4.3 Opened in an actual rendered browser preview and verified, for real:
      - Grid renders with real data (10001/VINET/Reims, matching the legacy page exactly).
      - Checked orders 10001 and 10003 via their checkboxes.
      - Navigated to page 2 — confirmed different rows (10011-10019), independently
        unchecked.
      - Navigated back to page 1 — confirmed 10001 and 10003 **still checked**
        (`{order10001_checked: true, order10003_checked: true}`, read directly from the
        DOM), proving cross-page selection persistence per the spec.
      - Console logs checked (`preview_console_logs`, level=error): zero errors.
- [x] 4.4 Screenshot captured (embedded in `EXAMPLE_WALKTHROUGH.md`).

## 5. Real-backend verification (deferred, same as capability 1)

- [ ] 5.1 (requires local .NET 8 SDK — not available in this sandbox) `dotnet build` /
      `dotnet run` in `modern/OrdersApi`, confirm `GET /api/checkbox-selection-orders`
      returns the expected 40 records.
- [ ] 5.2 Re-point `VITE_API_BASE_URL` at the real running API instead of the mock,
      re-verify browser behavior is unchanged.

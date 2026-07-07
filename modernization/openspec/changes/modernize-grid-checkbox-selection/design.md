## Context

Same environment constraints as the first capability: this authoring sandbox has Node.js
+ npm (verified) but no .NET SDK (`dotnet` not on PATH — verified again for this change).
The legacy page (`Grid/CheckboxSelection.aspx.cs`, class `Grid.DefaultPaging`) generates
its 40-row Orders dataset in-process — no database — so, like the first capability, a
byte-identical port doesn't require standing up a database.

This change's explicit goal (unlike the first) is that a human can actually exercise the
modernized UI in a browser during this authoring session, not just read verified build
logs. That requires something that actually serves HTTP responses the frontend can fetch
— which the unrunnable ASP.NET Core backend can't provide here.

## Goals / Non-Goals

**Goals:**
- Byte-identical data to `BindDataSource()` (40 rows, not the first capability's 48 —
  different loop bounds).
- Checkbox-column multi-select + paging, matching the legacy `ej:Grid`'s
  `<ej:Column Type="checkbox">` + `AllowPaging="True"`.
- **A real, running, clickable browser demo** in this authoring session — the actual new
  requirement this change exists to satisfy, verified via a live preview, not just a build
  log.

**Non-Goals:**
- Running the real ASP.NET Core API in this session (blocked by missing .NET SDK — same
  as the first capability; still authored to the same standard, still needs `dotnet build`
  run locally before being considered production-verified).
- A production-grade mock/contract-testing setup — the `json-server` mock introduced here
  is explicitly local-verification-only, not part of the shipped build.

## Decisions

- **Add this capability's endpoint to the existing `modern/OrdersApi` project, not a new
  API project.** Alternative considered: a separate `CheckboxSelectionApi` project, one per
  capability (as the roadmap's suggested-scaffold-names imply). Rejected for this specific
  pair of capabilities — they're both "Orders grid variants" sharing the same data shape;
  splitting them into separate deployable APIs this early would be premature
  fragmentation. (The roadmap's one-project-per-capability suggestion is a reasonable
  *default*, not a rule — this is a case where two capabilities are close enough to share.)
- **A local `json-server` instance, seeded with the exact `BindDataSource()` values, stands
  in for the real API during browser verification in this environment.** Alternative
  considered: mock the fetch call inside the React component itself (e.g. hardcoded data
  returned from `ordersClient.ts` when an env flag is set). Rejected — that would leave
  fake-data logic inside production frontend code. A separate `json-server` process
  external to both frontend and backend code is a standard, well-understood pattern
  (contract-first frontend development against a fake backend) and requires zero backend
  or frontend code changes to remove once the real API is available — just point
  `VITE_API_BASE_URL` back at it.
- **`json-server` over hand-writing a tiny Express mock.** Alternative considered: a
  5-line Express server. Rejected — `json-server` needs zero code (one JSON data file +
  one routes file), which matters directly for the "only use SDD/openspec, no ad hoc
  coding" constraint this change was built under: the mock is *configuration*, not
  authored application logic.
- **Route remapping (`/api/checkbox-selection-orders` → json-server's default
  `/checkbox-selection-orders`) via a `routes.json`,** so the frontend's API client can use
  the exact same path shape it will use against the real ASP.NET Core API later — no
  frontend code needs to change when swapping the mock for the real backend.

## Risks / Trade-offs

- **[Risk]** A `json-server` mock returning correct-looking JSON doesn't prove the real
  ASP.NET Core controller/repository compiles or behaves identically →
  **[Mitigation]** `CheckboxSelectionOrdersRepository.cs` is still authored line-for-line
  from the legacy `BindDataSource()`, to the same standard as the first capability; the
  mock's `db.json` is generated from the *same* literal values, not independently
  invented, so at minimum the data contract is provably identical even though the C#
  itself isn't compiled here.
- **[Risk]** Two capabilities sharing one API project (see Decisions) could grow into an
  unintentionally monolithic API if every future capability gets added the same way →
  **[Mitigation]** Explicitly scoped to *this pair* in this decision; the roadmap's
  per-capability project default still applies to capability 3 onward unless a similarly
  explicit case is made.

## Migration Plan

No deployment/rollback concerns — additive, parallel to the untouched legacy page, same
as capability 1. Verification split, same honesty discipline as before:

- **Frontend + mock API integration**: fully verified in this environment — `npm run
  build` (compile check) and an actual running `npm run dev` + `json-server` pair, checked
  live via browser preview.
- **Real ASP.NET Core backend**: hand-authored only. Before this is production-ready,
  `dotnet build`/`dotnet run` locally with the .NET 8 SDK, confirm
  `GET /api/checkbox-selection-orders` returns the expected 40 rows, then re-point
  `VITE_API_BASE_URL` at it instead of the local mock and re-verify the browser behavior
  is unchanged.

## Open Questions

- At what point does sharing `OrdersApi` across capabilities stop making sense and warrant
  a split? Not a blocker here — revisit once a 3rd Orders-shaped capability is proposed.

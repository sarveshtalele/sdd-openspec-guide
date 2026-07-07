# Modernization Roadmap — aspnet-ej1-demos

Generated from the aspx-analyzer index. Target stack: **ASP.NET Core Web API + React/TypeScript (Vite)**.
Build order is simplest/lowest-risk capability first — direct-SQL pages weigh
heaviest in the ranking since data-access rewrite is the dominant migration cost,
not the UI port itself.

---

## 1. Target Stack Setup

```
modern/
├── <Capability>Api/            ASP.NET Core Web API for this capability
│   ├── <Capability>Api.csproj
│   ├── Program.cs              minimal hosting + CORS policy for the frontend dev server
│   ├── Models/                 DTOs matching the legacy code-behind's data classes
│   ├── Data/                   repository/service porting the legacy data-access logic
│   └── Controllers/            one controller per legacy page being replaced
└── <capability>-web/           React + TypeScript frontend (Vite)
    ├── src/
    │   ├── api/                 typed fetch client(s) against the API above
    │   └── components/          one component per legacy page/control being replaced
    └── package.json
```

```bash
# Backend — one Web API project per capability keeps each migration slice
# independently buildable/deployable; consolidate later if the target
# architecture calls for a single shared API.
dotnet new webapi -n <Capability>Api -o modern/<Capability>Api

# Frontend
npm create vite@latest <capability>-web -- --template react-ts
cd modern/<capability>-web && npm install

# Verify the frontend at least (Node-only, always runnable):
npm run build
```

**Notes:**
- This exact stack was used and verified in this skill's own worked example (EXAMPLE_WALKTHROUGH.md, parent repo) — a real legacy grid page ported to a real, built ASP.NET Core Web API + React/TS app.
- CORS: the Web API must explicitly allow the Vite dev server origin (default http://localhost:5173) — see Program.cs pattern in EXAMPLE_WALKTHROUGH.md.
- No .NET SDK available to verify the backend compiles in a given environment? Say so explicitly rather than claiming it builds — the same discipline this skill's own walkthrough followed.

---

## 2. Build Order — Capabilities, Simplest First

| # | Capability | Pages | Direct SQL | AJAX | Unknown Auth | Score | Suggested first page |
|---|------------|-------|------------|------|---------------|-------|----------------------|
| 1 | Contact | 2 | 0 | 0 | 2 | 4 | `Slider/ButtonSupport.aspx` |
| 2 | Products | 1 | 1 | 0 | 1 | 5 | `XlsIO/StockPortFolio.aspx` |
| 3 | Configuration | 3 | 0 | 0 | 3 | 6 | `Gantt/TimeOption.aspx` |
| 4 | Orders | 3 | 1 | 0 | 3 | 9 | `Pdf/Invoice.aspx` |
| 5 | Search | 5 | 0 | 0 | 5 | 10 | `Schedule/AppointmentSearch.aspx` |
| 6 | Content | 5 | 0 | 1 | 5 | 11 | `Accordion/AjaxContent.aspx` |
| 7 | Users | 7 | 0 | 0 | 7 | 14 | `CircularGauge/UserInteraction.aspx` |
| 8 | Administration | 16 | 0 | 8 | 16 | 40 | `Dashboard/AirlineReservation.aspx` |
| 9 | Home | 70 | 1 | 1 | 0 | 74 | `Default.aspx` |
| 10 | Reports | 206 | 0 | 1 | 199 | 406 | `BulletGraph/API.aspx` |
| 11 | General | 829 | 3 | 53 | 828 | 1719 | `Accordion/API.aspx` |

### Per-capability detail

#### 1. Contact  (score: 4)

No direct-SQL or AJAX pages — good candidate to prove the migration pattern on before tackling harder capabilities.
- Start with: `Slider/ButtonSupport.aspx` (ButtonSupport page)
- Suggested scaffold names: `ContactApi` / `contact-web`

#### 2. Products  (score: 5)

**1 page(s) use direct SQL** in code-behind — plan a parametrized-query/repository migration as part of this capability's design, not a like-for-like port.
- Start with: `XlsIO/StockPortFolio.aspx` (Data entry / form — StockPortFolio)
- Suggested scaffold names: `ProductsApi` / `products-web`

#### 3. Configuration  (score: 6)

No direct-SQL or AJAX pages — good candidate to prove the migration pattern on before tackling harder capabilities.
- Start with: `Gantt/TimeOption.aspx` (TimeOption page)
- Suggested scaffold names: `ConfigurationApi` / `configuration-web`

#### 4. Orders  (score: 9)

**1 page(s) use direct SQL** in code-behind — plan a parametrized-query/repository migration as part of this capability's design, not a like-for-like port.
- Start with: `Pdf/Invoice.aspx` (Data entry / form — Invoice)
- Suggested scaffold names: `OrdersApi` / `orders-web`

#### 5. Search  (score: 10)

No direct-SQL or AJAX pages — good candidate to prove the migration pattern on before tackling harder capabilities.
- Start with: `Schedule/AppointmentSearch.aspx` (Search interface for AppointmentSearch)
- Suggested scaffold names: `SearchApi` / `search-web`

#### 6. Content  (score: 11)

- Start with: `Accordion/AjaxContent.aspx` (AjaxContent page)
- Suggested scaffold names: `ContentApi` / `content-web`

#### 7. Users  (score: 14)

No direct-SQL or AJAX pages — good candidate to prove the migration pattern on before tackling harder capabilities.
- Start with: `CircularGauge/UserInteraction.aspx` (UserInteraction page)
- Suggested scaffold names: `UsersApi` / `users-web`

#### 8. Administration  (score: 40)

- Start with: `Dashboard/AirlineReservation.aspx` (AirlineReservation page)
- Suggested scaffold names: `AdministrationApi` / `administration-web`

#### 9. Home  (score: 74)

**1 page(s) use direct SQL** in code-behind — plan a parametrized-query/repository migration as part of this capability's design, not a like-for-like port.
- Start with: `Default.aspx` (Application home page / dashboard)
- Suggested scaffold names: `HomeApi` / `home-web`

#### 10. Reports  (score: 406)

- Start with: `BulletGraph/API.aspx` (API page)
- Suggested scaffold names: `ReportsApi` / `reports-web`

#### 11. General  (score: 1719)

**3 page(s) use direct SQL** in code-behind — plan a parametrized-query/repository migration as part of this capability's design, not a like-for-like port.
- Start with: `Accordion/API.aspx` (API page)
- Suggested scaffold names: `GeneralApi` / `general-web`

---

## Using this with OpenSpec

Feed each row into its own change, in the order above:
```bash
openspec new change modernize-<capability-slug> --description "..." --goal "..."
openspec instructions proposal --change modernize-<capability-slug>
# ... proposal -> design -> specs -> tasks, same loop as EXAMPLE_WALKTHROUGH.md
```
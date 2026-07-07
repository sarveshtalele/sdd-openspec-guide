## ADDED Requirements

### Requirement: API returns the legacy dataset shape
The system SHALL expose `GET /api/checkbox-selection-orders` returning a JSON array of 40
orders, each with `orderId` (number), `customerId` (string), `employeeId` (number),
`freight` (number), `orderDate` (ISO 8601 date string), and `shipCity` (string) — matching
the fields produced by the legacy `Grid/CheckboxSelection.aspx.cs` `BindDataSource()`
method.

#### Scenario: Fetching orders returns the full dataset
- **WHEN** a client sends `GET /api/checkbox-selection-orders`
- **THEN** the API (or, during local verification without the .NET SDK, the equivalent
  local mock — see design.md) SHALL respond with HTTP 200 and a JSON array of 40 order
  records matching `BindDataSource()`'s values

### Requirement: Frontend grid displays a checkbox selection column
The system SHALL render a `CheckboxSelectionGrid` component with a checkbox column as the
first column, followed by the same six data columns as the API/legacy grid — matching
`Grid/CheckboxSelection.aspx`'s `<ej:Column Type="checkbox">` plus its data columns.

#### Scenario: Grid renders fetched orders with a checkbox per row
- **WHEN** the `CheckboxSelectionGrid` component mounts and the data request succeeds
- **THEN** the component SHALL render one row per order, each with a checkbox in the first
  column and the six data columns populated

#### Scenario: Grid handles a failed data request
- **WHEN** the data request fails or is unreachable
- **THEN** the component SHALL display an error state instead of an empty or broken table

### Requirement: Checkbox selection supports multi-row selection
The system SHALL allow selecting multiple rows independently via their checkboxes —
checking one row's box SHALL NOT affect any other row's checked state, matching the
legacy grid's checkbox-column selection model (distinct from the first capability's
click-anywhere-on-row toggle selection).

#### Scenario: Selecting multiple rows via checkboxes
- **WHEN** a visitor checks the checkboxes for two different rows
- **THEN** both rows SHALL show as checked/selected, independently of each other

#### Scenario: Unchecking a selected row
- **WHEN** a visitor unchecks an already-checked row's checkbox
- **THEN** that row SHALL become unselected while other checked rows remain checked

### Requirement: Frontend grid supports paging
The system SHALL paginate the rendered orders client-side, matching the legacy grid's
`AllowPaging="True"` behavior.

#### Scenario: Navigating to the next page preserves selection
- **WHEN** a visitor has checked a row, then navigates to the next page and back
- **THEN** the previously checked row SHALL still show as checked on return to its page

### Requirement: This capability is genuinely verifiable in a browser without a live .NET backend
The system SHALL be independently verifiable end-to-end (fetch, render, select, page) in a
browser using a local mock API that serves byte-identical data to the real ASP.NET Core
API, so a developer without a local .NET SDK can still confirm the frontend's behavior is
correct.

#### Scenario: Browser verification against the local mock
- **WHEN** the frontend dev server is pointed at the local mock API (per design.md) and
  opened in a browser
- **THEN** a developer SHALL be able to see the populated grid, check/uncheck rows, and
  page through results, with no console errors

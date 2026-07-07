## ADDED Requirements

### Requirement: API returns the legacy dataset shape
The system SHALL expose `GET /api/basic-selection-orders` returning a JSON array of 48
orders, each with `orderId`, `customerId`, `employeeId`, `freight`, `orderDate`, and
`shipCity` — matching `Grid/BasicSelection.aspx.cs`'s `BindDataSource()`.

#### Scenario: Fetching orders returns the full dataset
- **WHEN** a client sends `GET /api/basic-selection-orders`
- **THEN** the API (or the local mock during browser verification without a .NET SDK —
  see design.md) SHALL respond with HTTP 200 and 48 order records matching
  `BindDataSource()`'s values

### Requirement: Frontend grid displays the six data columns, no checkbox column
The system SHALL render a `BasicSelectionGrid` component with exactly the same six data
columns as the API, with no checkbox or other selection-affordance column — matching
`Grid/BasicSelection.aspx`'s column definitions (no `Type="checkbox"` column present).

#### Scenario: Grid renders fetched orders
- **WHEN** the component mounts and the data request succeeds
- **THEN** it SHALL render one row per order, all six columns populated, with no
  checkbox column

#### Scenario: Grid handles a failed data request
- **WHEN** the data request fails
- **THEN** the component SHALL display an error state

### Requirement: Clicking anywhere on a row toggles its selection
The system SHALL select a row when clicked anywhere in the row (not a specific
sub-control), and deselect it if clicked again while already selected — matching the
legacy grid's `AllowSelection="True"` + `SelectionSettings EnableToggle="true"` with no
checkbox column.

#### Scenario: Clicking an unselected row selects it
- **WHEN** a visitor clicks anywhere on a row that is not currently selected
- **THEN** that row SHALL become selected (visually distinguished)

#### Scenario: Clicking an already-selected row deselects it
- **WHEN** a visitor clicks anywhere on a row that is currently selected
- **THEN** that row SHALL become deselected

#### Scenario: Multiple rows can be selected independently
- **WHEN** a visitor clicks two different unselected rows in sequence
- **THEN** both rows SHALL be selected simultaneously

### Requirement: Frontend grid supports paging
The system SHALL paginate the rendered orders client-side, matching the legacy grid's
`AllowPaging="True"`.

#### Scenario: Navigating to the next page preserves selection
- **WHEN** a visitor has selected a row, navigates to another page, then back
- **THEN** the previously selected row SHALL still show as selected

### Requirement: This capability is genuinely verifiable in a browser without a live .NET backend
The system SHALL be independently verifiable end-to-end in a browser using the same local
mock API pattern as the first capability.

#### Scenario: Browser verification against the local mock
- **WHEN** the frontend dev server is pointed at a local mock API seeded with the
  `BindDataSource()` values and opened in a browser
- **THEN** a developer SHALL be able to see the populated grid, click rows to toggle
  selection, and page through results, with no console errors

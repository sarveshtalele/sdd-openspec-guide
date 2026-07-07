# Home — Modernization Proposal

## Why

`Home` is a legacy capability comprising 70 ASP.NET Web Forms page(s):

- `Default.aspx` — Application home page / dashboard (auth: anonymous)
- `Accordion\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `AutoComplete\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `Barcode\DefaultFunctionalities.aspx` — Data entry / form — DefaultFunctionalities (auth: anonymous)
- `Buttons\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `Captcha\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `CircularGauge\Default.aspx` — Application home page / dashboard (auth: anonymous)
- `ColorPicker\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `ComboBox\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `DatePicker\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `DateRangePicker\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `DateTimePicker\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `Dialog\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `DigitalGauge\Default.aspx` — Application home page / dashboard (auth: anonymous)
- `DocIO\DefaultFunctionalities.aspx` — Data entry / form — DefaultFunctionalities (auth: anonymous)
- `DropDownList\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `FileExplorer\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `Gantt\Default.aspx` — Application home page / dashboard (auth: anonymous)
- `Gantt\DefaultContextMenu.aspx` — DefaultContextMenu page (auth: anonymous)
- `Grid\DefaultFiltering.aspx` — DefaultFiltering page (auth: anonymous)
- `Grid\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `Grid\DefaultPaging.aspx` — DefaultPaging page (auth: anonymous)
- `Grid\DefaultServerEvents.aspx` — DefaultServerEvents page (auth: anonymous)
- `KanbanBoard\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `LinearGauge\Default.aspx` — Application home page / dashboard (auth: anonymous)
- `ListBox\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `ListView\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `Menu\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `NavigationDrawer\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `Pager\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `PdfViewer\Default.aspx` — Application home page / dashboard (auth: anonymous)
- `PivotClient\OlapDefault.aspx` — OlapDefault page (auth: anonymous)
- `PivotClient\RelationalDefault.aspx` — RelationalDefault page (auth: anonymous)
- `PivotGauge\OlapDefault.aspx` — OlapDefault page (auth: anonymous)
- `PivotGauge\RelationalDefault.aspx` — RelationalDefault page (auth: anonymous)
- `PivotGrid\OlapDefault.aspx` — OlapDefault page (auth: anonymous)
- `PivotGrid\RelationalDefault.aspx` — RelationalDefault page (auth: anonymous)
- `PivotTreeMap\Default.aspx` — Application home page / dashboard (auth: anonymous)
- `Presentation\DefaultFunctionality.aspx` — DefaultFunctionality page (auth: anonymous)
- `ProgressBar\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `RadialMenu\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `RadialSlider\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `RangeNavigator\Default.aspx` — Application home page / dashboard (auth: anonymous)
- `Rating\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `Ribbon\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `RichTextEditor\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `Rotator\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `Schedule\Default.aspx` — Application home page / dashboard (auth: anonymous)
- `Schedule\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `Schedule\HorizontalDefault.aspx` — HorizontalDefault page (auth: anonymous)
- `Schedule\RecurrenceEditorDefault.aspx` — Edit / data entry form — RecurrenceEditorDefault (auth: anonymous)
- `ScrollBar\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `Signature\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `Slider\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `Sparkline\Default.aspx` — Application home page / dashboard (auth: anonymous)
- `SpellCheck\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `Splitter\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `Spreadsheet\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `Tab\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `TagCloud\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `Textboxes\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `TileView\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `TimePicker\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `Toolbar\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `Tooltip\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `TreeGrid\TreeGridDefault.aspx` — TreeGridDefault page (auth: anonymous)
- `TreeView\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `UploadBox\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `WaitingPopup\DefaultFunctionalities.aspx` — DefaultFunctionalities page (auth: anonymous)
- `XlsIO\DefaultFunctionalities.aspx` — Data entry / form — DefaultFunctionalities (auth: anonymous)

**Data-access risk:** 1 page(s) in this capability use direct SQL in code-behind: Schedule\DefaultFunctionalities.aspx. Plan a parametrized-query or repository-layer migration for these before cutover.

## What Changes

<!-- TODO: describe the target modern implementation for this capability -->

## Impact

- Affected legacy pages: 70
- Pages with unresolved/unknown auth: 0
- Pages with direct SQL usage: 1
<!-- TODO: list affected APIs/services/dependencies in the modernized system -->

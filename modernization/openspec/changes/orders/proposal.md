# Orders — Modernization Proposal

## Why

`Orders` is a legacy capability comprising 3 ASP.NET Web Forms page(s):

- `DocIO\SalesInvoice.aspx` — Data entry / form — SalesInvoice (auth: unknown)
- `Pdf\Invoice.aspx` — Data entry / form — Invoice (auth: unknown)
- `XlsIO\SalesInvoice.aspx` — Data entry / form — SalesInvoice (auth: unknown)

**Data-access risk:** 1 page(s) in this capability use direct SQL in code-behind: XlsIO\SalesInvoice.aspx. Plan a parametrized-query or repository-layer migration for these before cutover.

## What Changes

<!-- TODO: describe the target modern implementation for this capability -->

## Impact

- Affected legacy pages: 3
- Pages with unresolved/unknown auth: 3
- Pages with direct SQL usage: 1
<!-- TODO: list affected APIs/services/dependencies in the modernized system -->

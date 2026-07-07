# Products — Modernization Proposal

## Why

`Products` is a legacy capability comprising 1 ASP.NET Web Forms page(s):

- `XlsIO\StockPortFolio.aspx` — Data entry / form — StockPortFolio (auth: unknown)

**Data-access risk:** 1 page(s) in this capability use direct SQL in code-behind: XlsIO\StockPortFolio.aspx. Plan a parametrized-query or repository-layer migration for these before cutover.

## What Changes

<!-- TODO: describe the target modern implementation for this capability -->

## Impact

- Affected legacy pages: 1
- Pages with unresolved/unknown auth: 1
- Pages with direct SQL usage: 1
<!-- TODO: list affected APIs/services/dependencies in the modernized system -->

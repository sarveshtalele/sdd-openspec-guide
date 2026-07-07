# aspnet-ej1-demos — ASP.NET Web Forms Application Analysis

> Generated: 2026-07-07T13:33:35.043122Z

---

## Executive Summary

This is an **ASP.NET Web Forms** application with **1147 pages**, **4 user controls**, and **2 master pages** across **11 functional areas**.

**Databases:** ApplicationServices, SQLConnectionString, SelfReferenceConnectionString, Linq_To_SQLConnectionString, ScheduleConnectionString, DiagramDataConnectionString, Adventure Works, Adventure Works DW1, ScheduleDataEntities, AspNetSqlMembershipProvider, AspNetSqlProfileProvider, AspNetSqlRoleProvider

---

## Codebase Metrics

| Metric | Count |
|--------|-------|
| ASPX Pages | 1147 |
| User Controls (.ascx) | 4 |
| Master Pages | 2 |
| Functional Areas | 11 |
| Pages with Code-Behind | 1146 |
| Pages using Master Page | 1120 |
| Pages with AJAX (UpdatePanel) | 64 |
| Pages with Direct SQL | 6 |
| Pages with Validators | 9 |
| Named Routes (RouteConfig) | 0 |

---

## Access Control Breakdown

| Requirement | Pages |
|-------------|-------|
| `unknown` | 1069 |
| `anonymous` | 78 |

---

## Master Pages

### `Samplebrowser.Master`
- **Purpose:** Layout master template
- **Used by:** 1119 pages
- **Content Placeholders:** `HeadSection`, `ScriptSection`, `StyleSection`, `SampleHeading`, `ActionDescriptionSection`, `ControlsSection`, `PropertySection`, `EventSection`
- **ScriptManager (AJAX):** Yes

### `Layout.Master`
- **Purpose:** Layout master template
- **Used by:** 1 pages
- **Content Placeholders:** `HeadContent`, `LayoutSection`
- **Navigation Controls:** asp:Menu

---

## Functional Areas Overview

### Administration (16 pages)
- **AirlineReservation** — AirlineReservation page  *(auth: `unknown`)*
- **AppointmentPlanner** — Data entry / form — AppointmentPlanner  *(auth: `unknown`)*
- **AuditShowcase** — Data entry / form — AuditShowcase  *(auth: `unknown`)*
- **CallCenterDashboard** — CallCenterDashboard page  *(auth: `unknown`)*
- **DiagramBuilder** — Data entry / form — DiagramBuilder  *(auth: `unknown`)*
- **ExpenseAnalysis** — Data entry / form — ExpenseAnalysis  *(auth: `unknown`)*
- _10 more pages…_

### Configuration (3 pages)
- **CategorizeOption** — CategorizeOption page  *(auth: `unknown`)*
- **TabWizard** — Data entry / form — TabWizard  *(auth: `unknown`)*
- **TimeOption** — TimeOption page  *(auth: `unknown`)*

### Contact (2 pages)
- **ButtonSupport** — ButtonSupport page  *(auth: `unknown`)*
- **EncryptionSupport** — Data entry / form — EncryptionSupport  *(auth: `unknown`)*

### Content (5 pages)
- **AjaxContent** — AjaxContent page  *(auth: `unknown`)*
- **AjaxContent** — AjaxContent page  *(auth: `unknown`)*
- **AjaxContent** — AjaxContent page  *(auth: `unknown`)*
- **AjaxContent** — AjaxContent page  *(auth: `unknown`)*
- **ImagewithContent** — ImagewithContent page  *(auth: `unknown`)*

### General (829 pages)
- **API** — Data entry / form — API  *(auth: `unknown`)*
- **API** — API page  *(auth: `unknown`)*
- **API** — Data entry / form — API  *(auth: `unknown`)*
- **API** — API page  *(auth: `unknown`)*
- **API** — Data entry / form — API  *(auth: `unknown`)*
- **API** — Data entry / form — API  *(auth: `unknown`)*
- _823 more pages…_

### Home (70 pages)
- **Default** — Application home page / dashboard  *(auth: `anonymous`)*
- **Default** — Application home page / dashboard  *(auth: `anonymous`)*
- **Default** — Application home page / dashboard  *(auth: `anonymous`)*
- **Default** — Application home page / dashboard  *(auth: `anonymous`)*
- **Default** — Application home page / dashboard  *(auth: `anonymous`)*
- **Default** — Application home page / dashboard  *(auth: `anonymous`)*
- _64 more pages…_

### Orders (3 pages)
- **Invoice** — Data entry / form — Invoice  *(auth: `unknown`)*
- **SalesInvoice** — Data entry / form — SalesInvoice  *(auth: `unknown`)*
- **SalesInvoice** — Data entry / form — SalesInvoice  *(auth: `unknown`)*

### Products (1 page)
- **StockPortFolio** — Data entry / form — StockPortFolio  *(auth: `unknown`)*

### Reports (206 pages)
- **3DChart** — 3DChart page  *(auth: `unknown`)*
- **API** — API page  *(auth: `unknown`)*
- **ATR** — ATR page  *(auth: `unknown`)*
- **AccessDataBinding** — AccessDataBinding page  *(auth: `unknown`)*
- **AccumulationDistribution** — AccumulationDistribution page  *(auth: `unknown`)*
- **AdaptiveSpreadsheet** — AdaptiveSpreadsheet page  *(auth: `unknown`)*
- _200 more pages…_

### Search (5 pages)
- **AppointmentSearch** — Search interface for AppointmentSearch  *(auth: `unknown`)*
- **FindAndExtract** — Data entry / form — FindAndExtract  *(auth: `unknown`)*
- **FindAndReplace** — Data entry / form — FindAndReplace  *(auth: `unknown`)*
- **QueryCellInfo** — QueryCellInfo page  *(auth: `unknown`)*
- **SortFilter** — SortFilter page  *(auth: `unknown`)*

### Users (7 pages)
- **DocumentSettings** — Data entry / form — DocumentSettings  *(auth: `unknown`)*
- **PageSettings** — Data entry / form — PageSettings  *(auth: `unknown`)*
- **PrintSettings** — Data entry / form — PrintSettings  *(auth: `unknown`)*
- **UserHandles** — Data entry / form — UserHandles  *(auth: `unknown`)*
- **UserInteraction** — UserInteraction page  *(auth: `unknown`)*
- **UserInteraction** — UserInteraction page  *(auth: `unknown`)*
- _1 more pages…_

---

## Most-Used User Controls

| Control | Purpose | Used By |
|---------|---------|---------|
| `ShowCaseTab.ascx` | ShowCaseTab reusable UI component | 1 pages |
| `LayoutHeader.ascx` | Page header / top navigation component | 0 pages |
| `LeftColumn.ascx` | LeftColumn reusable UI component | 0 pages |
| `Sourcecodetab.ascx` | Sourcecodetab reusable UI component | 0 pages |
import { CheckboxSelectionGrid } from "./components/CheckboxSelectionGrid";
import { BasicSelectionGrid } from "./components/BasicSelectionGrid";
import "./App.css";

function App() {
  return (
    <main>
      <section>
        <h1>Checkbox Selection Grid (modernized from Grid/CheckboxSelection.aspx)</h1>
        <p>
          Legacy page: <code>Grid/CheckboxSelection.aspx</code> — checkbox-column
          multi-row selection + paging on an Orders list. This modernized version
          fetches from the ASP.NET Core Web API in production, or a local mock
          (see openspec/changes/modernize-grid-checkbox-selection/design.md) for
          browser verification without a .NET SDK.
        </p>
        <CheckboxSelectionGrid />
      </section>

      <hr />

      <section>
        <h1>Basic Selection Grid (modernized from Grid/BasicSelection.aspx)</h1>
        <p>
          Legacy page: <code>Grid/BasicSelection.aspx</code> — click-anywhere-on-row
          toggle multi-selection + paging on a (differently seeded) Orders list. No
          checkbox column — clicking the row itself toggles selection. See
          openspec/changes/modernize-grid-basic-selection/design.md for the local-mock
          verification pattern (same approach as the checkbox capability above).
        </p>
        <BasicSelectionGrid />
      </section>
    </main>
  );
}

export default App;

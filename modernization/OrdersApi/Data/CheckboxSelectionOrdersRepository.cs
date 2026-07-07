using OrdersApi.Models;

namespace OrdersApi.Data;

// Ported line-for-line from BindDataSource() in Grid/CheckboxSelection.aspx.cs
// (WebSampleBrowser.Grid.DefaultPaging) — same loop bounds (8 iterations x 5
// rows = 40 rows), same literal values. Do not "clean up" the repeated
// values without also updating the openspec change this came from
// (openspec/changes/modernize-grid-checkbox-selection, or openspec/specs/
// checkbox-selection-grid-api after archive).
public static class CheckboxSelectionOrdersRepository
{
    public static List<Order> GetAll()
    {
        var orders = new List<Order>();
        var orderId = 10000;
        var empId = 0;

        for (var i = 1; i < 9; i++)
        {
            orders.Add(new Order(orderId + 1, "VINET", empId + 1, 32.38, new DateTime(2014, 12, 25), "Reims"));
            orders.Add(new Order(orderId + 2, "TOMSP", empId + 2, 11.61, new DateTime(2014, 12, 21), "Munster"));
            orders.Add(new Order(orderId + 3, "ANATER", empId + 3, 45.34, new DateTime(2014, 10, 18), "Berlin"));
            orders.Add(new Order(orderId + 4, "ALFKI", empId + 4, 37.28, new DateTime(2014, 11, 23), "Mexico"));
            orders.Add(new Order(orderId + 5, "FRGYE", empId + 5, 67.00, new DateTime(2014, 05, 05), "Colchester"));
            orderId += 5;
            empId += 5;
        }

        return orders;
    }
}

using OrdersApi.Models;

namespace OrdersApi.Data;

// Ported line-for-line from BindDataSource() in Grid/BasicSelection.aspx.cs
// (WebSampleBrowser.Grid.BasicSelection) — 8 iterations x 6 rows = 48 rows,
// same literal values. See openspec/changes/modernize-grid-basic-selection
// (or openspec/specs/basic-selection-grid-api after archive).
public static class BasicSelectionOrdersRepository
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
            orders.Add(new Order(orderId + 6, "JGERT", empId + 6, 23.32, new DateTime(2014, 10, 18), "Newyork"));
            orderId += 6;
            empId += 6;
        }

        return orders;
    }
}

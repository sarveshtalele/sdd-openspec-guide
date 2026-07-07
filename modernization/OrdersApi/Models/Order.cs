namespace OrdersApi.Models;

// Shared shape across every Orders-family capability in this API — first
// used by the checkbox-selection-grid-api capability (openspec/changes/
// modernize-grid-checkbox-selection). Mirrors the legacy Orders classes in
// Grid/*.aspx.cs field-for-field.
public class Order
{
    public int OrderId { get; set; }
    public string CustomerId { get; set; } = string.Empty;
    public int EmployeeId { get; set; }
    public double Freight { get; set; }
    public DateTime OrderDate { get; set; }
    public string ShipCity { get; set; } = string.Empty;

    public Order() { }

    public Order(int orderId, string customerId, int employeeId, double freight, DateTime orderDate, string shipCity)
    {
        OrderId = orderId;
        CustomerId = customerId;
        EmployeeId = employeeId;
        Freight = freight;
        OrderDate = orderDate;
        ShipCity = shipCity;
    }
}

// Matches OrdersApi.Models.Order (modern/OrdersApi/Models/Order.cs), which
// mirrors the legacy Grid.DefaultPaging.Orders class in
// Grid/CheckboxSelection.aspx.cs field-for-field.
export interface Order {
  orderId: number;
  customerId: string;
  employeeId: number;
  freight: number;
  orderDate: string; // ISO 8601 date string
  shipCity: string;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:5000";

// The real ASP.NET Core API serves this at api/checkbox-selection-orders.
// The local json-server mock used for browser verification in this sandbox
// (no .NET SDK available — see design.md) can't remap paths in the installed
// json-server 1.0.0-beta version (no --routes support), so its flat resource
// key is exposed at plain /checkbox-selection-orders instead. This override
// lets local verification point at the mock without changing the real path.
const RESOURCE_PATH =
  import.meta.env.VITE_CHECKBOX_ORDERS_PATH ?? "api/checkbox-selection-orders";

export async function fetchCheckboxSelectionOrders(): Promise<Order[]> {
  const response = await fetch(`${API_BASE_URL}/${RESOURCE_PATH}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch orders: ${response.status} ${response.statusText}`);
  }
  return (await response.json()) as Order[];
}

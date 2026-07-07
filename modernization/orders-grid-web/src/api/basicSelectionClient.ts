// Matches OrdersApi.Models.Order, mirroring the legacy
// Grid.BasicSelection.Orders class in Grid/BasicSelection.aspx.cs field-for-field.
export interface Order {
  orderId: number;
  customerId: string;
  employeeId: number;
  freight: number;
  orderDate: string;
  shipCity: string;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:5000";

// Same configurable-resource-path pattern as checkboxSelectionClient.ts — the
// installed json-server (1.0.0-beta.15) can't remap paths, so local mock
// verification points this at a flat resource name instead of api/....
const RESOURCE_PATH =
  import.meta.env.VITE_BASIC_SELECTION_ORDERS_PATH ?? "api/basic-selection-orders";

export async function fetchBasicSelectionOrders(): Promise<Order[]> {
  const response = await fetch(`${API_BASE_URL}/${RESOURCE_PATH}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch orders: ${response.status} ${response.statusText}`);
  }
  return (await response.json()) as Order[];
}

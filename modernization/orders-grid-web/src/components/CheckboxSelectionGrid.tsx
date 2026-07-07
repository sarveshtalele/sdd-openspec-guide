import { useEffect, useMemo, useState } from "react";
import { fetchCheckboxSelectionOrders, type Order } from "../api/checkboxSelectionClient";

const PAGE_SIZE = 10;

export function CheckboxSelectionGrid() {
  const [orders, setOrders] = useState<Order[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [checkedIds, setCheckedIds] = useState<Set<number>>(new Set());

  useEffect(() => {
    let cancelled = false;
    fetchCheckboxSelectionOrders()
      .then((data) => {
        if (!cancelled) setOrders(data);
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const totalPages = orders ? Math.max(1, Math.ceil(orders.length / PAGE_SIZE)) : 1;

  const visibleOrders = useMemo(() => {
    if (!orders) return [];
    const start = (page - 1) * PAGE_SIZE;
    return orders.slice(start, start + PAGE_SIZE);
  }, [orders, page]);

  // Checked state is keyed by orderId in one Set shared across pages, so
  // navigating to another page and back preserves it (spec requirement).
  function toggleChecked(orderId: number) {
    setCheckedIds((prev) => {
      const next = new Set(prev);
      if (next.has(orderId)) {
        next.delete(orderId);
      } else {
        next.add(orderId);
      }
      return next;
    });
  }

  if (error) {
    return <div role="alert">Could not load orders: {error}</div>;
  }

  if (!orders) {
    return <div>Loading orders…</div>;
  }

  return (
    <div className="checkbox-selection-grid">
      <table>
        <thead>
          <tr>
            <th aria-label="Select"></th>
            <th>Order ID</th>
            <th>Customer ID</th>
            <th>Employee ID</th>
            <th>Freight</th>
            <th>Order Date</th>
            <th>Ship City</th>
          </tr>
        </thead>
        <tbody>
          {visibleOrders.map((order) => (
            <tr key={order.orderId} className={checkedIds.has(order.orderId) ? "checked" : undefined}>
              <td>
                <input
                  type="checkbox"
                  checked={checkedIds.has(order.orderId)}
                  onChange={() => toggleChecked(order.orderId)}
                  aria-label={`Select order ${order.orderId}`}
                />
              </td>
              <td>{order.orderId}</td>
              <td>{order.customerId}</td>
              <td>{order.employeeId}</td>
              <td>{order.freight.toFixed(2)}</td>
              <td>{new Date(order.orderDate).toLocaleDateString()}</td>
              <td>{order.shipCity}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="pager">
        <button type="button" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
          Previous
        </button>
        <span>
          Page {page} of {totalPages} — {checkedIds.size} selected
        </span>
        <button
          type="button"
          disabled={page >= totalPages}
          onClick={() => setPage((p) => p + 1)}
        >
          Next
        </button>
      </div>
    </div>
  );
}

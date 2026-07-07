import { useEffect, useMemo, useState } from "react";
import { fetchBasicSelectionOrders, type Order } from "../api/basicSelectionClient";

const PAGE_SIZE = 10;

export function BasicSelectionGrid() {
  const [orders, setOrders] = useState<Order[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  // Selection is keyed by orderId in one Set shared across pages (not
  // per-page state), so it survives paging away and back — same pattern as
  // CheckboxSelectionGrid, applied here to click-toggle instead of checkbox.
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());

  useEffect(() => {
    let cancelled = false;
    fetchBasicSelectionOrders()
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

  // Clicking anywhere on the row toggles it — no checkbox control at all,
  // matching the legacy ej:Grid's AllowSelection + EnableToggle behavior
  // (no Type="checkbox" column in its markup).
  function toggleRow(orderId: number) {
    setSelectedIds((prev) => {
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
    <div className="basic-selection-grid">
      <table>
        <thead>
          <tr>
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
            <tr
              key={order.orderId}
              onClick={() => toggleRow(order.orderId)}
              aria-selected={selectedIds.has(order.orderId)}
              className={selectedIds.has(order.orderId) ? "selected" : undefined}
            >
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
          Page {page} of {totalPages} — {selectedIds.size} selected
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

// Stores orders in localStorage. Only this browser can see them, but tabs of
// the same browser stay in sync, which is enough to build and demo the app.
import { today } from "./util.js";

const KEY = "skipTheLine.orders";
const listeners = new Set();

function readAll() {
  try {
    return JSON.parse(localStorage.getItem(KEY)) || [];
  } catch {
    return [];
  }
}

function writeAll(orders) {
  localStorage.setItem(KEY, JSON.stringify(orders));
  notify();
}

function todaysOrders() {
  return readAll().filter((o) => o.day === today());
}

function notify() {
  const orders = todaysOrders();
  listeners.forEach((cb) => cb(orders));
}

// Another tab changed localStorage -> refresh this tab too.
window.addEventListener("storage", (e) => {
  if (e.key === KEY) notify();
});

export function subscribeOrders(callback) {
  listeners.add(callback);
  callback(todaysOrders());
  return () => listeners.delete(callback);
}

export async function placeOrder(order) {
  const all = readAll();
  const day = today();
  const lastTicket = all
    .filter((o) => o.day === day && o.vendorId === order.vendorId)
    .reduce((max, o) => Math.max(max, o.ticket), 0);
  const saved = {
    ...order,
    id: crypto.randomUUID(),
    day,
    ticket: lastTicket + 1,
    status: "waiting",
    createdAt: Date.now(),
  };
  all.push(saved);
  writeAll(all);
  return saved;
}

export async function setStatus(orderId, status) {
  const all = readAll();
  const order = all.find((o) => o.id === orderId);
  if (order) {
    order.status = status;
    writeAll(all);
  }
}

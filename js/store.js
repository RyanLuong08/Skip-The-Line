// The rest of the app only talks to this file. It forwards every call to either
// the local store or the Firebase store, so switching backends is one setting.
//
// Order object:
// {
//   id, day: "2026-11-19", hallId, vendorId, vendorName,
//   items: [{ id, name, price, qty }], total,
//   pickup: "ASAP" | "12:10", ticket: 12,
//   status: "waiting" | "cooking" | "ready" | "done" | "cancelled",
//   createdAt: 1763520000000 (milliseconds)
// }
import { BACKEND } from "./config.js";

const backend =
  BACKEND === "firebase"
    ? await import("./store-firebase.js")
    : await import("./store-local.js");

// Calls callback(orders) now and every time today's orders change.
// Returns a function that stops listening.
export const subscribeOrders = backend.subscribeOrders;

// Saves a new order, gives it the next ticket number for that vendor today,
// and returns the saved order.
export const placeOrder = backend.placeOrder;

// Changes an order's status, e.g. "waiting" -> "cooking".
export const setStatus = backend.setStatus;

export const backendName = BACKEND;

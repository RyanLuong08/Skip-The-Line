import { PEAK_HOURS, SLOT_COUNT, SLOT_STEP_MIN } from "./config.js";

export const ACTIVE = ["waiting", "cooking"];

// "2026-11-19" in the user's local time zone.
export function today(date = new Date()) {
  const pad = (n) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

export async function loadMenu() {
  const res = await fetch("data/menu.json");
  if (!res.ok) throw new Error("Could not load data/menu.json");
  return res.json();
}

// Orders still being made at one vendor.
export function queueFor(orders, vendorId) {
  return orders.filter((o) => o.vendorId === vendorId && ACTIVE.includes(o.status));
}

// Rough wait: orders ahead x average minutes per order.
export function estimateWaitMin(orders, vendor) {
  return queueFor(orders, vendor.id).length * vendor.avgPrepMin;
}

// Number of active orders created before this one at the same vendor.
export function ordersAhead(orders, order) {
  return queueFor(orders, order.vendorId).filter((o) => o.createdAt < order.createdAt).length;
}

export function waitLevel(minutes) {
  if (minutes <= 5) return "low";
  if (minutes <= 15) return "mid";
  return "high";
}

function toMinutes(hhmm) {
  const [h, m] = hhmm.split(":").map(Number);
  return h * 60 + m;
}

function hhmm(totalMin) {
  const h = Math.floor(totalMin / 60) % 24;
  const m = totalMin % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

export function isPeak(date = new Date()) {
  const now = date.getHours() * 60 + date.getMinutes();
  return PEAK_HOURS.some((p) => now >= toMinutes(p.start) && now < toMinutes(p.end));
}

// ["ASAP", "12:10", "12:20", ...] starting at the next round slot.
export function pickupSlots(date = new Date()) {
  const now = date.getHours() * 60 + date.getMinutes();
  const first = Math.ceil((now + SLOT_STEP_MIN) / SLOT_STEP_MIN) * SLOT_STEP_MIN;
  const slots = ["ASAP"];
  for (let i = 0; i < SLOT_COUNT; i++) slots.push(hhmm(first + i * SLOT_STEP_MIN));
  return slots;
}

export function money(n) {
  return n == null ? "Ask at counter" : `NT$${n}`;
}

// Always use this when putting data into innerHTML.
export function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

export const STATUS_LABEL = {
  waiting: "In queue",
  cooking: "Cooking",
  ready: "Ready for pickup",
  done: "Picked up",
  cancelled: "Cancelled",
};

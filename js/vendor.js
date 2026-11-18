// Vendor page: see incoming orders and move them New -> Cooking -> Ready -> Picked up.
import { subscribeOrders, setStatus } from "./store.js";
import { loadMenu, money, esc } from "./util.js";

const $ = (id) => document.getElementById(id);
const NEXT = { waiting: "cooking", cooking: "ready", ready: "done" };
const BUTTON = { waiting: "Start cooking", cooking: "Mark ready", ready: "Picked up" };

let orders = [];
const menu = await loadMenu();
const vendors = menu.halls.flatMap((h) => h.vendors.map((v) => ({ ...v, hall: h.name })));

// Remember the chosen vendor in the address bar, e.g. vendor.html?v=fengyun-love-curry
const params = new URLSearchParams(location.search);
let vendorId = params.get("v") || vendors[0]?.id;

$("vendorSelect").innerHTML = vendors
  .map((v) => `<option value="${v.id}" ${v.id === vendorId ? "selected" : ""}>${esc(v.hall)} · ${esc(v.name)}</option>`)
  .join("");

function card(o) {
  const items = o.items.map((i) => `<li>${i.qty} × ${esc(i.name)}</li>`).join("");
  const time = new Date(o.createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  return `<div class="order">
      <div class="order-head"><span class="num">#${o.ticket}</span>
        <span class="muted">ordered ${time} · pickup ${esc(o.pickup)}</span></div>
      <ul>${items}</ul>
      <div class="order-foot"><span>${money(o.total)}</span>
        <button class="primary" data-id="${o.id}" data-next="${NEXT[o.status]}">${BUTTON[o.status]}</button>
        ${o.status === "waiting" ? `<button class="link" data-id="${o.id}" data-next="cancelled">Cancel</button>` : ""}
      </div>
    </div>`;
}

function render() {
  const mine = orders.filter((o) => o.vendorId === vendorId).sort((a, b) => a.ticket - b.ticket);
  for (const [status, col, count] of [
    ["waiting", "colWaiting", "countWaiting"],
    ["cooking", "colCooking", "countCooking"],
    ["ready", "colReady", "countReady"],
  ]) {
    const list = mine.filter((o) => o.status === status);
    $(col).innerHTML = list.map(card).join("") || `<p class="muted">Nothing here.</p>`;
    $(count).textContent = list.length;
  }
  const ready = mine.filter((o) => o.status === "ready");
  $("nowServing").textContent = ready.length ? ready.map((o) => "#" + o.ticket).join(", ") : "–";
}

$("vendorSelect").addEventListener("change", (e) => {
  vendorId = e.target.value;
  history.replaceState(null, "", `?v=${vendorId}`);
  render();
});

document.querySelector(".board").addEventListener("click", (e) => {
  const btn = e.target.closest("[data-next]");
  if (btn) setStatus(btn.dataset.id, btn.dataset.next);
});

subscribeOrders((list) => {
  orders = list;
  render();
});

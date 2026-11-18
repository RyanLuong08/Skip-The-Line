// Student page: browse vendors, see live wait times, order ahead, track tickets.
import { subscribeOrders, placeOrder } from "./store.js";
import {
  loadMenu, estimateWaitMin, queueFor, ordersAhead, waitLevel, isPeak,
  pickupSlots, money, esc, STATUS_LABEL,
} from "./util.js";

const MY_TICKETS_KEY = "skipTheLine.myTickets";
const $ = (id) => document.getElementById(id);

const state = {
  menu: null,
  orders: [],
  hallId: "fengyun",
  vendor: null,
  category: "all",
  search: "",
  cart: [], // [{ id, name, price, qty }]
  myTickets: JSON.parse(localStorage.getItem(MY_TICKETS_KEY) || "[]"),
};

const currentHall = () => state.menu.halls.find((h) => h.id === state.hallId);

// ---------- Rendering ----------

function renderHalls() {
  $("halls").innerHTML = state.menu.halls
    .map((h) => `<button data-hall="${h.id}" class="${h.id === state.hallId ? "active" : ""}">
        ${esc(h.name)} <small>${esc(h.nameZh)}</small></button>`)
    .join("");
}

function renderVendors() {
  const hall = currentHall();
  $("hallNote").textContent = hall.vendors.length ? `${hall.vendors.length} at ${hall.name}` : "";
  if (!hall.vendors.length) {
    $("vendors").innerHTML = `<p class="muted">${esc(hall.name)} menu data is still being collected.</p>`;
    return;
  }
  $("vendors").innerHTML = hall.vendors
    .map((v) => {
      const wait = estimateWaitMin(state.orders, v);
      const queue = queueFor(state.orders, v.id).length;
      return `<button class="vendor" data-vendor="${v.id}">
          <strong>${esc(v.name)}</strong>
          <span class="muted">${esc(v.nameZh)} · ${esc(v.cuisine)} · ${v.items.length} dishes</span>
          <span class="wait ${waitLevel(wait)}">~${wait} min · ${queue} in queue</span>
        </button>`;
    })
    .join("");
}

function renderMenu() {
  const v = state.vendor;
  $("vendorTitle").textContent = `${v.name} ${v.nameZh}`;
  const wait = estimateWaitMin(state.orders, v);
  $("vendorWait").innerHTML = `Current wait: <span class="wait ${waitLevel(wait)}">~${wait} min</span>`;

  const cats = ["all", ...new Set(v.items.map((i) => i.category))];
  $("categories").innerHTML = cats
    .map((c) => `<button data-cat="${esc(c)}" class="${c === state.category ? "active" : ""}">${esc(c)}</button>`)
    .join("");

  const q = state.search.toLowerCase();
  const items = v.items.filter(
    (i) =>
      (state.category === "all" || i.category === state.category) &&
      (!q || i.name.toLowerCase().includes(q) || i.nameZh.includes(state.search))
  );
  $("items").innerHTML = items.length
    ? items
        .map((i) => `<li>
            <div><strong>${esc(i.name)}</strong> ${i.vegetarian ? '<span class="tag">veg</span>' : ""}
              <div class="muted">${esc(i.nameZh)}${i.calories ? ` · ${i.calories} kcal` : ""}</div></div>
            <div class="price">${money(i.price)}</div>
            <button data-add="${i.id}" aria-label="Add ${esc(i.name)}">+</button>
          </li>`)
        .join("")
    : `<li class="muted">No dishes match.</li>`;
}

function renderCart() {
  $("cart").innerHTML = state.cart.length
    ? state.cart
        .map((c) => `<li>
            <span>${c.qty} × ${esc(c.name)}</span>
            <span>${money(c.price == null ? null : c.price * c.qty)}</span>
            <button data-remove="${c.id}" aria-label="Remove">−</button>
          </li>`)
        .join("")
    : `<li class="muted">Pick a vendor and add dishes.</li>`;
  const total = state.cart.reduce((sum, c) => sum + (c.price ?? 0) * c.qty, 0);
  const unknown = state.cart.some((c) => c.price == null);
  $("total").textContent = `NT$${total}${unknown ? " + items priced at counter" : ""}`;
  $("placeOrder").disabled = state.cart.length === 0;
}

function renderPickup() {
  const chosen = $("pickup").value;
  $("pickup").innerHTML = pickupSlots().map((s) => `<option ${s === chosen ? "selected" : ""}>${s}</option>`).join("");
}

function renderTickets() {
  const mine = state.orders
    .filter((o) => state.myTickets.includes(o.id))
    .sort((a, b) => b.createdAt - a.createdAt);
  if (!mine.length) {
    $("tickets").innerHTML = `<p class="muted">No orders yet today.</p>`;
    return;
  }
  $("tickets").innerHTML = mine
    .map((o) => {
      const ahead = ordersAhead(state.orders, o);
      const detail =
        o.status === "waiting" ? `${ahead} order${ahead === 1 ? "" : "s"} ahead of you`
        : o.status === "ready" ? "Show this number at the counter"
        : "";
      return `<div class="ticket ${o.status}">
          <div class="num">#${o.ticket}</div>
          <div><strong>${esc(o.vendorName)}</strong>
            <div>${STATUS_LABEL[o.status]} · pickup ${esc(o.pickup)}</div>
            <div class="muted">${detail}</div></div>
        </div>`;
    })
    .join("");
}

function render() {
  renderHalls();
  $("peak").hidden = !isPeak();
  $("vendorView").hidden = !!state.vendor;
  $("menuView").hidden = !state.vendor;
  if (state.vendor) renderMenu();
  else renderVendors();
  renderCart();
  renderTickets();
}

// ---------- Actions ----------

function openVendor(vendorId) {
  const vendor = currentHall().vendors.find((v) => v.id === vendorId);
  if (state.cart.length && state.vendor?.id !== vendorId) {
    if (!confirm("One order is for one vendor. Clear your current order?")) return;
    state.cart = [];
  }
  state.vendor = vendor;
  state.category = "all";
  state.search = "";
  $("search").value = "";
  render();
}

function addItem(itemId) {
  const item = state.vendor.items.find((i) => i.id === itemId);
  const line = state.cart.find((c) => c.id === itemId);
  if (line) line.qty++;
  else state.cart.push({ id: item.id, name: item.name, price: item.price, qty: 1 });
  renderCart();
}

function removeItem(itemId) {
  const line = state.cart.find((c) => c.id === itemId);
  line.qty--;
  if (line.qty === 0) state.cart = state.cart.filter((c) => c !== line);
  renderCart();
}

async function submitOrder() {
  $("placeOrder").disabled = true;
  try {
    const order = await placeOrder({
      hallId: state.hallId,
      vendorId: state.vendor.id,
      vendorName: state.vendor.name,
      items: state.cart,
      total: state.cart.reduce((sum, c) => sum + (c.price ?? 0) * c.qty, 0),
      pickup: $("pickup").value,
    });
    state.myTickets.push(order.id);
    localStorage.setItem(MY_TICKETS_KEY, JSON.stringify(state.myTickets));
    state.cart = [];
    render();
  } catch (err) {
    alert("Order failed: " + err.message);
    renderCart();
  }
}

// ---------- Events ----------

$("halls").addEventListener("click", (e) => {
  const btn = e.target.closest("[data-hall]");
  if (!btn) return;
  state.hallId = btn.dataset.hall;
  state.vendor = null;
  render();
});
$("vendors").addEventListener("click", (e) => {
  const btn = e.target.closest("[data-vendor]");
  if (btn) openVendor(btn.dataset.vendor);
});
$("back").addEventListener("click", () => {
  state.vendor = null;
  render();
});
$("categories").addEventListener("click", (e) => {
  const btn = e.target.closest("[data-cat]");
  if (!btn) return;
  state.category = btn.dataset.cat;
  renderMenu();
});
$("search").addEventListener("input", (e) => {
  state.search = e.target.value.trim();
  renderMenu();
});
$("items").addEventListener("click", (e) => {
  const btn = e.target.closest("[data-add]");
  if (btn) addItem(btn.dataset.add);
});
$("cart").addEventListener("click", (e) => {
  const btn = e.target.closest("[data-remove]");
  if (btn) removeItem(btn.dataset.remove);
});
$("placeOrder").addEventListener("click", submitOrder);

// ---------- Start ----------

state.menu = await loadMenu();
renderPickup();
setInterval(renderPickup, 60_000);
subscribeOrders((orders) => {
  state.orders = orders;
  render();
});

// Stores orders in Cloud Firestore so every device sees the same queue.
// Used when BACKEND = "firebase" in config.js (Step 8 of the guide).
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import {
  getFirestore, collection, doc, query, where, onSnapshot,
  runTransaction, updateDoc,
} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js";
import { firebaseConfig } from "./config.js";
import { today } from "./util.js";

const db = getFirestore(initializeApp(firebaseConfig));
const ordersCol = collection(db, "orders");

export function subscribeOrders(callback) {
  const q = query(ordersCol, where("day", "==", today()));
  return onSnapshot(
    q,
    (snap) => callback(snap.docs.map((d) => ({ id: d.id, ...d.data() }))),
    (err) => {
      console.error(err);
      alert("Could not load orders from Firebase: " + err.message);
    }
  );
}

export async function placeOrder(order) {
  const day = today();
  // One counter document per vendor per day, e.g. counters/fengyun-love-curry_2026-11-19.
  // The transaction makes sure two students never get the same ticket number.
  const counterRef = doc(db, "counters", `${order.vendorId}_${day}`);
  const orderRef = doc(ordersCol);
  return runTransaction(db, async (tx) => {
    const counter = await tx.get(counterRef);
    const ticket = (counter.exists() ? counter.data().last : 0) + 1;
    const saved = { ...order, day, ticket, status: "waiting", createdAt: Date.now() };
    tx.set(counterRef, { last: ticket });
    tx.set(orderRef, saved);
    return { id: orderRef.id, ...saved };
  });
}

export async function setStatus(orderId, status) {
  await updateDoc(doc(db, "orders", orderId), { status });
}

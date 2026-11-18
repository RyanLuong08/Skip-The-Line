// ===== Project settings =====

// Where orders are stored:
//   "local"    -> in this browser only (good for coding and demos; open the
//                 student page and vendor page as two tabs of the SAME browser)
//   "firebase" -> in the cloud, shared by every phone and computer (Step 8 of the guide)
export const BACKEND = "local";

// Paste your Firebase web app config here in Step 8 (Firebase console >
// Project settings > Your apps > SDK setup and configuration > Config).
export const firebaseConfig = {
  apiKey: "PASTE_HERE",
  authDomain: "PASTE_HERE",
  projectId: "PASTE_HERE",
  storageBucket: "PASTE_HERE",
  messagingSenderId: "PASTE_HERE",
  appId: "PASTE_HERE",
};

// Pickup time slots offered to students (minutes between slots, how many to show).
export const SLOT_STEP_MIN = 10;
export const SLOT_COUNT = 9;

// Peak hours, used to warn students (24h clock).
export const PEAK_HOURS = [
  { start: "11:50", end: "12:40" },
  { start: "17:20", end: "18:30" },
];

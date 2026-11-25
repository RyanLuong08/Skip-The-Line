// 中文 / English for every page (owner: A).
//
// In HTML:  <h2 data-i18n="my_tickets">My tickets</h2>  (the English stays as a fallback)
//           <input data-i18n-placeholder="search_all">
// In JS:    t("ahead", { n: 3 })  ->  "3 orders ahead of you" / "前面還有 3 單"
//           pick(dish)             ->  dish.name_zh in 中文 mode (if there is one), else dish.name
//
// The language follows the phone (a Chinese phone opens in 中文) until someone presses the
// 中文 / EN button in the top bar; that choice is remembered in this browser.
// To add a sentence: add the same key to BOTH lists below.

const I18N = {
  en: {
    // top bar
    nav_order: "Order", nav_vendor: "Vendor", nav_stats: "Stats", nav_board: "Board", nav_qr: "QR",
    log_out: "Log out", lang_button: "中文",
    // student page
    peak: "It's peak hour. Order ahead and pick a pickup time to skip the queue.",
    vendors: "Vendors", vendors_n: "{n} vendors",
    wait_hint: "Wait times count only orders placed in this app, not the line at the counter.",
    search_all: "Search every dish, e.g. beef noodles 牛肉麵",
    search_menu: "Search this menu",
    f_veg: "Vegetarian", f_cheap: "Under NT${n}",
    results_n: "{n} dishes found", results_more: "Showing the first {n}. Type more to narrow it down.",
    no_results: "No dishes match.", searching_all: "Results from every dining hall",
    order_again: "Order again", order_again_btn: "Order again",
    order_again_gone: "Some dishes from that order aren't available today, so they were left out.",
    order_again_none: "None of those dishes are available today.",
    hall_empty: "This dining hall's menu is still being collected.",
    back: "← All vendors",
    dishes_n: "{n} dishes", dish_1: "1 dish",
    wait_some: "~{min} min · {n} app orders ahead", wait_one: "~{min} min · 1 app order ahead",
    wait_none: "No app orders waiting",
    closed_until: "Closed · opens at {time}", closed_today: "Closed for today",
    paused: "Not taking app orders right now. Order at the counter.",
    hours: "Hours {hours}",
    veg: "veg", sold_out: "Sold out", add: "Add {name}", ask_counter: "Ask at counter",
    all: "all",
    your_order: "Your order", empty_cart: "Pick a vendor and add dishes.", remove_one: "Remove one",
    total: "Total:", plus_counter: " + dishes priced at the counter",
    pickup_time: "Pickup time", no_pickup: "Closed: no pickup times left today",
    payment: "Payment", pay_transfer: "Bank transfer", pay_counter: "Pay at pickup",
    under: "(under NT${n})", transfer_to: "Transfer {amount} to:", last5: "Last 5 digits of the account you pay from",
    transfer_wait: "The vendor starts cooking once they see your transfer.",
    must_transfer: "Orders of NT${n} or more must be paid by transfer.",
    no_bank: "This vendor doesn't take transfers yet.",
    unpriced_counter: "Some dishes have no price yet, so they can only be paid at pickup.",
    remove_some: "Remove some dishes to place this order.",
    noshow_blocked: "You didn't pick up {n} orders, so pay at pickup is off for you. Please pay by transfer.",
    noshow_warn: "You didn't pick up {n} of your orders. After {limit}, you'll have to pay by transfer.",
    place_order: "Place order",
    ordered: "Ordered! Your ticket is #{ticket}.", ordered_counter: "Pay NT${total} at the counter when you pick it up.",
    ordered_transfer: "The vendor will start once they see your transfer.",
    one_vendor: "One order is for one vendor. Clear your current order?",
    view_order: "View order ↑", items_n: "{n} items", item_1: "1 item",
    my_tickets: "My tickets", no_tickets: "No orders yet today.",
    st_waiting: "In queue", st_cooking: "Cooking", st_ready: "Ready for pickup", st_done: "Picked up",
    st_cancelled: "Cancelled", st_no_show: "Not picked up",
    pickup_at: "pickup {time}", wait_transfer: "Waiting for the vendor to see your transfer",
    ahead_some: "{n} orders ahead of you", ahead_one: "1 order ahead of you", ahead_none: "You're next",
    show_number: "Show this number at the counter",
    paid: "Paid ✓", pay_transfer_line: "Transfer {amount} · from account …{ref}", pay_counter_line: "Pay {amount} at pickup",
    plus_counter_short: " + counter-priced dishes",
    cancel_order: "Cancel order", cancel_q: "Cancel ticket #{ticket} at {vendor}?",
    cancel_refund: " If you already sent the money, ask the vendor to send it back.",
    notify: "🔔 Notify me when my food is ready",
    notify_on: "🔔 Your phone will buzz when your food is ready, even with this page closed.",
    notify_https: "Notifications need the https:// link of this site. This page still vibrates when your food is ready, as long as it stays open.",
    notify_iphone: "For notifications on iPhone: tap Share → Add to Home Screen, then open Skip the Line from your home screen.",
    notify_none: "This browser can't show notifications. Keep this page open: it vibrates when your food is ready.",
    notify_blocked: "Notifications are blocked. Allow them in your browser's site settings.",
    notify_failed: "Couldn't turn on notifications: {error}",
    ready_title: "✅ {tickets} READY",
    close: "Close",
    // categories
    cat_rice: "rice", cat_noodle: "noodles", cat_drinks: "drinks", cat_bread: "bread", cat_snack: "snacks",
    cat_wrap: "wraps", cat_dumpling: "dumplings", cat_soup: "soup", cat_other: "other",
    // vendor dashboard
    vendor_label: "Vendor", now_serving: "Now serving", sound_on: "🔔 Sound on", sound_off: "🔕 Sound off",
    col_new: "New", col_cooking: "Cooking", col_ready: "Ready", nothing: "Nothing here.",
    start_cooking: "Start cooking", mark_ready: "Mark ready", picked_up: "Picked up", cancel: "Cancel",
    no_show: "No-show", no_show_in: "No-show possible in {n} min",
    no_show_q: "Ticket #{ticket} never came to pick up? This counts against the student.",
    cancel_vendor_q: "Cancel ticket #{ticket}?", refund_warning: " They already paid, so remember to refund them.",
    ordered_at: "ordered {time} · pickup {pickup}", confirm_paid: "Confirm paid", confirm_first: "Confirm the transfer first",
    collect: "Collect {amount} at pickup", transfer_from: "Transfer {amount} · from account …{ref} · ",
    paid_amount: "Paid ✓ {amount}", new_order_title: "({n}) New order · ",
    pause: "⏸ Pause app orders", resume: "▶ Take app orders again", paused_banner: "App orders are paused for today. Students are told to order at the counter.",
    menu_panel: "Menu: mark dishes sold out", sold_out_today: "Sold out today", available: "Available",
    // login
    login_title: "Vendor login", login_hint: "This page is for the stalls. Students order on the order page.",
    pin: "PIN", open_dashboard: "Open dashboard",
    // board
    board_ready: "Ready: come and get it", board_cooking: "Cooking", board_waiting: "{n} waiting",
    board_empty: "No orders yet.", board_hint: "Order ahead at {address}",
    // qr
    qr_title: "Scan to order", qr_local: "Opened on this laptop, so this is its Wi-Fi address. Phones must be on the same Wi-Fi.",
    qr_http: "This is an http:// link: ordering works, but \"Notify me\" needs the https:// ngrok link.",
    qr_missing: "QR codes need the qrcode package: python -m pip install -r requirements.txt",
  },
  zh: {
    nav_order: "點餐", nav_vendor: "店家", nav_stats: "統計", nav_board: "叫號", nav_qr: "QR",
    log_out: "登出", lang_button: "EN",
    peak: "現在是尖峰時段。提前點餐、選取餐時間，就不用排隊。",
    vendors: "店家", vendors_n: "{n} 家",
    wait_hint: "等候時間只計算本 App 的訂單，不含櫃台前排隊的人。",
    search_all: "搜尋所有餐點，例如 牛肉麵 beef noodles",
    search_menu: "搜尋這家的餐點",
    f_veg: "素食", f_cheap: "NT${n} 以下",
    results_n: "找到 {n} 道餐點", results_more: "只顯示前 {n} 道，請再多打幾個字。",
    no_results: "沒有符合的餐點。", searching_all: "所有餐廳的搜尋結果",
    order_again: "再點一次", order_again_btn: "再點一次",
    order_again_gone: "上次有些餐點今天沒有供應，已略過。",
    order_again_none: "上次的餐點今天都沒有供應。",
    hall_empty: "這個餐廳的菜單還在整理中。",
    back: "← 所有店家",
    dishes_n: "{n} 道餐點", dish_1: "1 道餐點",
    wait_some: "約 {min} 分鐘 · 前面 {n} 單", wait_one: "約 {min} 分鐘 · 前面 1 單",
    wait_none: "目前沒有 App 訂單",
    closed_until: "休息中 · {time} 開門", closed_today: "今日已打烊",
    paused: "目前暫停 App 點餐，請到櫃台點餐。",
    hours: "營業時間 {hours}",
    veg: "素", sold_out: "售完", add: "加入 {name}", ask_counter: "請洽櫃台",
    all: "全部",
    your_order: "我的訂單", empty_cart: "請選擇店家並加入餐點。", remove_one: "減少一份",
    total: "總計：", plus_counter: " + 櫃台計價的餐點",
    pickup_time: "取餐時間", no_pickup: "今日已無可取餐時間",
    payment: "付款方式", pay_transfer: "轉帳", pay_counter: "取餐付款",
    under: "（NT${n} 以下）", transfer_to: "請轉帳 {amount} 至：", last5: "轉出帳號後五碼",
    transfer_wait: "店家確認收到轉帳後就會開始製作。",
    must_transfer: "NT${n} 以上的訂單請用轉帳付款。",
    no_bank: "這家店還不能轉帳。",
    unpriced_counter: "有些餐點還沒有價格，只能取餐時付款。",
    remove_some: "請移除部分餐點後再送出。",
    noshow_blocked: "你已有 {n} 次未取餐，取餐付款已停用，請用轉帳付款。",
    noshow_warn: "你已有 {n} 次未取餐。達到 {limit} 次後只能轉帳付款。",
    place_order: "送出訂單",
    ordered: "點餐成功！你的號碼是 #{ticket}。", ordered_counter: "取餐時請在櫃台付 NT${total}。",
    ordered_transfer: "店家確認收到轉帳後就會開始製作。",
    one_vendor: "一張訂單只能點一家店。要清空目前的訂單嗎？",
    view_order: "查看訂單 ↑", items_n: "{n} 份", item_1: "1 份",
    my_tickets: "我的號碼", no_tickets: "今天還沒有訂單。",
    st_waiting: "排隊中", st_cooking: "製作中", st_ready: "可以取餐了", st_done: "已取餐",
    st_cancelled: "已取消", st_no_show: "未取餐",
    pickup_at: "取餐 {time}", wait_transfer: "等店家確認轉帳",
    ahead_some: "前面還有 {n} 單", ahead_one: "前面還有 1 單", ahead_none: "下一個就是你",
    show_number: "請在櫃台出示這個號碼",
    paid: "已付款 ✓", pay_transfer_line: "轉帳 {amount} · 帳號後五碼 {ref}", pay_counter_line: "取餐時付 {amount}",
    plus_counter_short: " + 櫃台計價餐點",
    cancel_order: "取消訂單", cancel_q: "要取消 {vendor} 的 #{ticket} 嗎？",
    cancel_refund: " 如果已經轉帳，請向店家要求退款。",
    notify: "🔔 餐點完成時通知我",
    notify_on: "🔔 餐點完成時手機會震動通知，關掉這個頁面也可以。",
    notify_https: "通知需要用本網站的 https:// 連結。只要頁面開著，餐點完成時仍會震動。",
    notify_iphone: "iPhone 要收通知：點「分享」→「加入主畫面」，再從主畫面打開 Skip the Line。",
    notify_none: "這個瀏覽器不能顯示通知。請保持頁面開啟，餐點完成時會震動。",
    notify_blocked: "通知已被封鎖，請到瀏覽器的網站設定中允許。",
    notify_failed: "無法開啟通知：{error}",
    ready_title: "✅ {tickets} 可取餐",
    close: "關閉",
    cat_rice: "飯", cat_noodle: "麵", cat_drinks: "飲料", cat_bread: "麵包", cat_snack: "小吃",
    cat_wrap: "捲餅", cat_dumpling: "餃子", cat_soup: "湯", cat_other: "其他",
    vendor_label: "店家", now_serving: "請取餐", sound_on: "🔔 提示音開", sound_off: "🔕 提示音關",
    col_new: "新訂單", col_cooking: "製作中", col_ready: "可取餐", nothing: "目前沒有。",
    start_cooking: "開始製作", mark_ready: "完成", picked_up: "已取餐", cancel: "取消",
    no_show: "未取餐", no_show_in: "{n} 分鐘後可標記未取餐",
    no_show_q: "#{ticket} 一直沒來取餐嗎？這會記錄在該學生的紀錄上。",
    cancel_vendor_q: "要取消 #{ticket} 嗎？", refund_warning: " 對方已付款，記得退款。",
    ordered_at: "{time} 點餐 · 取餐 {pickup}", confirm_paid: "確認已收款", confirm_first: "請先確認收到轉帳",
    collect: "取餐時收 {amount}", transfer_from: "轉帳 {amount} · 帳號後五碼 {ref} · ",
    paid_amount: "已付款 ✓ {amount}", new_order_title: "({n}) 新訂單 · ",
    pause: "⏸ 暫停 App 點餐", resume: "▶ 恢復 App 點餐", paused_banner: "今天已暫停 App 點餐，學生會看到「請到櫃台點餐」。",
    menu_panel: "菜單：標記售完", sold_out_today: "今日售完", available: "供應中",
    login_title: "店家登入", login_hint: "此頁面供店家使用。學生請到點餐頁面。",
    pin: "密碼", open_dashboard: "進入後台",
    board_ready: "請取餐", board_cooking: "製作中", board_waiting: "{n} 單排隊中",
    board_empty: "目前沒有訂單。", board_hint: "提前點餐：{address}",
    qr_title: "掃描 QR Code 點餐", qr_local: "這是在筆電上開啟的，所以顯示筆電的 Wi-Fi 位址。手機需連同一個 Wi-Fi。",
    qr_http: "這是 http:// 連結：可以點餐，但「通知我」需要 https:// 的 ngrok 連結。",
    qr_missing: "QR Code 需要 qrcode 套件：python -m pip install -r requirements.txt",
  },
};

const LANG = (() => {
  let saved = null;
  try { saved = localStorage.getItem("lang"); } catch (e) { /* private mode: no storage */ }
  if (saved === "en" || saved === "zh") return saved;
  return (navigator.language || "").toLowerCase().startsWith("zh") ? "zh" : "en";
})();

function t(key, vars = {}) {
  const text = I18N[LANG][key] ?? I18N.en[key] ?? key;
  return text.replace(/\{(\w+)\}/g, (_, name) => (name in vars ? vars[name] : `{${name}}`));
}

// The name to show first, and the other language's name to show under it (may be "").
function pick(thing) {
  return LANG === "zh" && thing.name_zh ? thing.name_zh : thing.name;
}
function otherName(thing) {
  const second = LANG === "zh" ? thing.name : thing.name_zh;
  return second && second !== pick(thing) ? second : "";
}

function category(c) {
  return I18N[LANG][`cat_${c}`] ? t(`cat_${c}`) : c;
}

function applyI18n(root = document) {
  document.documentElement.lang = LANG === "zh" ? "zh-Hant" : "en";
  for (const node of root.querySelectorAll("[data-i18n]")) node.textContent = t(node.dataset.i18n);
  for (const node of root.querySelectorAll("[data-i18n-placeholder]")) node.placeholder = t(node.dataset.i18nPlaceholder);
  for (const node of root.querySelectorAll("[data-i18n-label]")) node.setAttribute("aria-label", t(node.dataset.i18nLabel));
  const button = document.getElementById("langToggle");
  if (button) {
    button.textContent = t("lang_button");
    button.onclick = () => {
      try { localStorage.setItem("lang", LANG === "zh" ? "en" : "zh"); } catch (e) { /* ignore */ }
      location.reload();
    };
  }
}

document.addEventListener("DOMContentLoaded", () => applyI18n());

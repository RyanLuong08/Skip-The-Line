"""Payment rules: how a student pays for an order (owner: A).

Plain Python with no Flask and no database, so it is easy to test.

After choosing dishes the student picks one of two ways to pay:
- "transfer": bank transfer (轉帳) before pickup. The student types the last 5 digits of the
  account they paid from (後五碼), so the vendor can find the payment in their bank app and
  press "Confirm paid". The vendor can't start cooking a transfer order until it is paid.
- "counter": pay at the counter when picking up. Only for orders under NT$200, so a student
  who never turns up doesn't leave the vendor with a big unpaid order.
"""

TRANSFER = "transfer"
COUNTER = "counter"
METHODS = (TRANSFER, COUNTER)

COUNTER_LIMIT = 200       # pay at the counter only if the total is UNDER this (NT$199 ok, NT$200 not)
TRANSFER_REF_DIGITS = 5   # last 5 digits of the student's bank account

# Where students send transfers. The real numbers do NOT go in this file (the repo is public):
# put them in instance/bank_accounts.json, which git ignores. app.py reads it at startup:
#   {
#     "default": {"bank": "822 中國信託 CTBC", "account": "123456789012", "holder": "Your Name"},
#     "vendors": {"fengyun-love-curry": {"bank": "...", "account": "...", "holder": "..."}}
#   }
# A vendor that isn't under "vendors" uses "default". No file (or no "default") = transfer is
# switched off for those vendors. Never use a made-up account number: someone might really pay it.
DEFAULT_ACCOUNT = None
BANK_ACCOUNTS = {}
ACCOUNT_FIELDS = ("bank", "account", "holder")


def parse_bank_accounts(data):
    """Check the contents of bank_accounts.json (already turned into Python by json.load).
    Returns (default_account_or_None, {vendor_slug: account}). Raises ValueError if it's wrong."""
    if not isinstance(data, dict):
        raise ValueError("bank_accounts.json must be one { ... } object")

    def account(value, where):
        if not isinstance(value, dict) or any(not str(value.get(f, "")).strip() for f in ACCOUNT_FIELDS):
            raise ValueError(f"{where} needs bank, account and holder")
        return {f: str(value[f]).strip() for f in ACCOUNT_FIELDS}

    default = account(data["default"], '"default"') if data.get("default") is not None else None
    vendors = data.get("vendors") or {}
    if not isinstance(vendors, dict):
        raise ValueError('"vendors" must be { "vendor-slug": {...}, ... }')
    return default, {slug: account(value, f'"vendors" -> "{slug}"') for slug, value in vendors.items()}


def use_bank_accounts(default, vendors):
    """Switch on transfers with these accounts (app.py calls this at startup)."""
    global DEFAULT_ACCOUNT, BANK_ACCOUNTS
    DEFAULT_ACCOUNT, BANK_ACCOUNTS = default, dict(vendors)


def bank_account(vendor_slug):
    """The account to transfer to for this vendor, or None if it doesn't take transfers yet."""
    return BANK_ACCOUNTS.get(vendor_slug, DEFAULT_ACCOUNT)


def counter_allowed(total):
    """True if an order of this total may be paid at the counter."""
    return total < COUNTER_LIMIT


def parse_transfer_ref(value):
    """The last 5 digits of the student's account, as text like "01234" (a leading 0 is kept)."""
    text = value.strip() if isinstance(value, str) else ""
    if len(text) != TRANSFER_REF_DIGITS or not text.isdigit() or not text.isascii():
        raise ValueError(f"Type the last {TRANSFER_REF_DIGITS} digits of the account you paid from.")
    return text


def check_payment(method, total, unpriced, has_account, transfer_ref=None):
    """Check the payment choice for an order. Returns the transfer ref ("" for counter).

    total: NT$ of the dishes that have a price. unpriced: True if some dishes have no price yet.
    has_account: True if the vendor has a bank account set up. Raises ValueError if not allowed.
    """
    if method not in METHODS:
        raise ValueError("Choose how to pay: bank transfer or pay at pickup.")
    if method == COUNTER:
        if not counter_allowed(total):
            raise ValueError(f"Pay at pickup is only for orders under NT${COUNTER_LIMIT}. "
                             "Please pay by bank transfer.")
        return ""
    if not has_account:
        raise ValueError("This vendor doesn't take bank transfers yet.")
    if unpriced:
        raise ValueError("Some dishes have no price yet, so the transfer amount isn't known. "
                         "Remove them or pay at pickup.")
    return parse_transfer_ref(transfer_ref)


def can_start_cooking(method, paid):
    """A transfer order is only cooked once the vendor has confirmed the money arrived."""
    return method != TRANSFER or paid

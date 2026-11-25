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

# Where students send transfers. Key: vendor slug, e.g. "fengyun-love-curry".
# A vendor that isn't listed uses DEFAULT_ACCOUNT. Leave DEFAULT_ACCOUNT as None until you have a
# real account: then transfer is switched off (never put a made-up account number here, someone
# might really send money to it). For the class demo you can use one teammate's account, e.g.
#   DEFAULT_ACCOUNT = {"bank": "822 中國信託 CTBC", "account": "123456789012", "holder": "陶海峰"}
DEFAULT_ACCOUNT = None
BANK_ACCOUNTS = {}


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

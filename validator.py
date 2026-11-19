"""
validator.py  -  STEP 2: Check the extracted data.

Every invoice ends up with one of three results:
    VALID       -> everything is present and correct
    INCOMPLETE  -> some required field is missing
    INCORRECT   -> all fields are there, but something is wrong
                   (maths mistake, bad date, duplicate number, ...)
"""

import re
from datetime import datetime, date

# ---------------------------------------------------------------
# Settings you can change easily
# ---------------------------------------------------------------
INVOICE_NUMBER_PATTERN = r"^INV-\d+$"                                  # e.g. INV-1001
GSTIN_PATTERN = r"^\d{2}[A-Z]{5}\d{4}[A-Z][A-Z\d]Z[A-Z\d]$"           # Indian GST number
TOLERANCE = 0.01                                                       # allowed rounding difference (1 paisa)
DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]                    # accepted date styles

# Fields that MUST be present, with a friendly name for the report
REQUIRED_FIELDS = {
    "invoice_number": "Invoice number",
    "invoice_date": "Invoice date",
    "vendor_name": "Vendor name",
    "vendor_address": "Vendor address",
    "subtotal": "Subtotal",
    "tax_amount": "Tax amount",
    "total": "Total amount",
}


def same_amount(a, b):
    """True if two money values are equal (allowing tiny rounding difference)."""
    return abs(a - b) <= TOLERANCE


def parse_date(text):
    """Try each known date format. Return a date, or None if it is not a real date."""
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def validate_invoice(inv, seen_numbers):
    """
    Check one invoice (a dictionary from extractor.py).
    `seen_numbers` is a set of invoice numbers already processed (to catch duplicates).
    Returns a dictionary: {"status": ..., "missing": [...], "errors": [...]}
    """
    missing = []   # fields that are not in the PDF
    errors = []    # things that are wrong

    # ---- Check 1: required fields present? ----
    for key, name in REQUIRED_FIELDS.items():
        if inv[key] is None:
            missing.append(name)
    if len(inv["items"]) == 0:
        missing.append("Line items")

    # ---- Check 2: invoice number format + duplicate ----
    number = inv["invoice_number"]
    if number:
        if not re.match(INVOICE_NUMBER_PATTERN, number):
            errors.append(f"Invoice number '{number}' has a wrong format")
        if number in seen_numbers:
            errors.append(f"Duplicate invoice number '{number}'")
        seen_numbers.add(number)

    # ---- Check 3: date is real and not in the future ----
    if inv["invoice_date"]:
        invoice_date = parse_date(inv["invoice_date"])
        if invoice_date is None:
            errors.append(f"Invoice date '{inv['invoice_date']}' is not a valid date")
        elif invoice_date > date.today():
            errors.append(f"Invoice date {invoice_date} is in the future")

    # ---- Check 4: GSTIN format (only if the vendor gave one) ----
    if inv["vendor_gstin"] and not re.match(GSTIN_PATTERN, inv["vendor_gstin"]):
        errors.append(f"Vendor GSTIN '{inv['vendor_gstin']}' is not valid")

    # ---- Check 5: each line item:  quantity x price = amount ----
    for number_in_list, item in enumerate(inv["items"], start=1):
        if item["quantity"] <= 0 or item["unit_price"] <= 0:
            errors.append(f"Item {number_in_list} ({item['description']}): quantity/price must be positive")
        expected = item["quantity"] * item["unit_price"]
        if not same_amount(expected, item["amount"]):
            errors.append(
                f"Item {number_in_list} ({item['description']}): "
                f"{item['quantity']} x {item['unit_price']:.2f} = {expected:.2f}, "
                f"but invoice shows {item['amount']:.2f}"
            )

    # ---- Check 6: sum of items = subtotal ----
    if inv["items"] and inv["subtotal"] is not None:
        items_sum = sum(item["amount"] for item in inv["items"])
        if not same_amount(items_sum, inv["subtotal"]):
            errors.append(f"Items add up to {items_sum:.2f}, but subtotal shows {inv['subtotal']:.2f}")

    # ---- Check 7: tax = subtotal x tax rate ----
    if inv["subtotal"] is not None and inv["tax_rate"] is not None and inv["tax_amount"] is not None:
        expected_tax = inv["subtotal"] * inv["tax_rate"] / 100
        if not same_amount(expected_tax, inv["tax_amount"]):
            errors.append(
                f"Tax at {inv['tax_rate']:g}% should be {expected_tax:.2f}, "
                f"but invoice shows {inv['tax_amount']:.2f}"
            )

    # ---- Check 8: subtotal + tax = total ----
    if None not in (inv["subtotal"], inv["tax_amount"], inv["total"]):
        expected_total = inv["subtotal"] + inv["tax_amount"]
        if not same_amount(expected_total, inv["total"]):
            errors.append(
                f"Subtotal + tax = {expected_total:.2f}, but total shows {inv['total']:.2f}"
            )

    # ---- Decide the final status ----
    if missing:
        status = "INCOMPLETE"
    elif errors:
        status = "INCORRECT"
    else:
        status = "VALID"

    return {"status": status, "missing": missing, "errors": errors}

"""
extractor.py  -  STEP 1: Read a PDF and pull out the invoice data.

How it works (simple idea):
  1. pdfplumber turns the PDF into plain text.
  2. "Regular expressions" (regex) search that text for patterns like
     "Invoice No: INV-1001" and grab the value.
"""

import re
import pdfplumber


# ---------------------------------------------------------------
# Small helper functions
# ---------------------------------------------------------------
def read_pdf_text(pdf_path):
    """Open a PDF and return all its text as one string."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += (page.extract_text() or "") + "\n"
    return text


def find(pattern, text):
    """Search for a pattern. Return the captured value, or None if not found."""
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None


def to_number(value):
    """Turn '1,250.50' into 1250.5. Return None if there is no value."""
    if value is None:
        return None
    return float(value.replace(",", ""))


# ---------------------------------------------------------------
# Line items (description, quantity, price, amount)
# ---------------------------------------------------------------
# A line item looks like:   Laptop   2   45000.00   90000.00
ITEM_LINE = re.compile(
    r"^(.+?)\s+(\d+)\s+(?:Rs\.?\s*)?([\d,]+\.\d{2})\s+(?:Rs\.?\s*)?([\d,]+\.\d{2})$"
)


def extract_items(text):
    """Go through the text line by line and collect every item row."""
    items = []
    for line in text.splitlines():
        match = ITEM_LINE.match(line.strip())
        if match:
            items.append({
                "description": match.group(1),
                "quantity": int(match.group(2)),
                "unit_price": to_number(match.group(3)),
                "amount": to_number(match.group(4)),
            })
    return items


# ---------------------------------------------------------------
# Main function: PDF  ->  dictionary of invoice data
# ---------------------------------------------------------------
def extract_invoice(pdf_path):
    """Read one PDF and return a dictionary with all the invoice fields.
    A field that cannot be found is set to None (the validator will notice)."""
    text = read_pdf_text(pdf_path)

    money = r"(?:Rs\.?\s*)?([\d,]+\.\d{2})"   # matches 'Rs. 1,250.50' or '1250.50'

    invoice = {
        "file_name": pdf_path.split("/")[-1],
        "invoice_number": find(r"Invoice\s*(?:No|Number|#)\.?\s*[:\-]?\s*([A-Z0-9\-/]+)", text),
        "invoice_date": find(r"Invoice\s*Date\s*[:\-]?\s*(\d{4}-\d{2}-\d{2}|\d{2}[/-]\d{2}[/-]\d{4})", text),
        "vendor_name": find(r"^Vendor\s*[:\-]\s*(.+)$", text),
        "vendor_address": find(r"^Address\s*[:\-]\s*(.+)$", text),
        "vendor_gstin": find(r"GSTIN\s*[:\-]\s*(\S+)", text),
        "items": extract_items(text),
        "subtotal": to_number(find(r"^Subtotal\s*[:\-]?\s*" + money, text)),
        "tax_rate": to_number(find(r"^Tax\s*\((\d+(?:\.\d+)?)%\)", text)),
        "tax_amount": to_number(find(r"^Tax\s*(?:\([^)]*\))?\s*[:\-]?\s*" + money, text)),
        "total": to_number(find(r"^Total\s*(?:Amount)?\s*[:\-]?\s*" + money, text)),
    }
    return invoice


# Quick test: python extractor.py invoices/invoice_01.pdf
if __name__ == "__main__":
    import sys
    from pprint import pprint
    pprint(extract_invoice(sys.argv[1]))

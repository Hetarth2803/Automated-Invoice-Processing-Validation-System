"""
make_sample_invoices.py  -  Creates test PDF invoices in the 'invoices' folder.

Some are correct, some are deliberately wrong, so you can see the
validator catching problems. You only need to run this once.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


# ---------------------------------------------------------------
# Build the invoice DATA (correct by default)
# ---------------------------------------------------------------
def build_invoice(number, date, vendor, items, tax_rate=18, gstin="24ABCDE1234F1Z5"):
    """items = list of (description, quantity, unit_price)"""
    lines = [{"desc": d, "qty": q, "price": p, "amount": q * p} for d, q, p in items]
    subtotal = sum(line["amount"] for line in lines)
    tax = round(subtotal * tax_rate / 100, 2)
    return {
        "number": number, "date": date, "vendor": vendor,
        "address": "12 Ring Road, Surat, Gujarat 395002", "gstin": gstin,
        "lines": lines, "subtotal": subtotal, "tax_rate": tax_rate,
        "tax": tax, "total": round(subtotal + tax, 2),
    }


# ---------------------------------------------------------------
# Draw the data onto a PDF page
# ---------------------------------------------------------------
def draw_pdf(inv, path):
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4
    y = height - 60

    def line(text, size=11, font="Helvetica", gap=18):
        nonlocal y
        c.setFont(font, size)
        c.drawString(50, y, text)
        y -= gap

    line("INVOICE", 20, "Helvetica-Bold", 35)
    if inv["number"]:
        line(f"Invoice No: {inv['number']}")
    if inv["date"]:
        line(f"Invoice Date: {inv['date']}")
    if inv["vendor"]:
        line(f"Vendor: {inv['vendor']}")
    line(f"Address: {inv['address']}")
    if inv["gstin"]:
        line(f"GSTIN: {inv['gstin']}")
    line("Bill To: Sample Customer Pvt Ltd", gap=35)

    # Table header
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Description")
    c.drawRightString(320, y, "Qty")
    c.drawRightString(420, y, "Unit Price")
    c.drawRightString(520, y, "Amount")
    y -= 8
    c.line(50, y, 520, y)
    y -= 18

    # Table rows
    c.setFont("Helvetica", 11)
    for item in inv["lines"]:
        c.drawString(50, y, item["desc"])
        c.drawRightString(320, y, str(item["qty"]))
        c.drawRightString(420, y, f"{item['price']:.2f}")
        c.drawRightString(520, y, f"{item['amount']:.2f}")
        y -= 18

    y -= 10
    c.line(50, y + 12, 520, y + 12)

    # Totals (right side)
    def total_line(label, value, bold=False):
        nonlocal y
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 11)
        c.drawString(330, y, f"{label}: Rs. {value:.2f}")
        y -= 18

    if inv["lines"]:
        total_line("Subtotal", inv["subtotal"])
        total_line(f"Tax ({inv['tax_rate']}%)", inv["tax"])
        total_line("Total", inv["total"], bold=True)

    c.save()


# ---------------------------------------------------------------
# Create the 8 test invoices
# ---------------------------------------------------------------
def main():
    os.makedirs("invoices", exist_ok=True)

    # 1 & 2: correct invoices
    inv1 = build_invoice("INV-1001", "2026-10-05", "ABC Traders Pvt Ltd",
                         [("Laptop", 2, 45000.00), ("Wireless Mouse", 5, 750.00)])
    inv2 = build_invoice("INV-1002", "2026-11-02", "Sharma Stationery",
                         [("A4 Paper Ream", 20, 280.00), ("Ball Pens (box)", 10, 120.00),
                          ("Stapler", 4, 95.50)], gstin="27PQRST5678G1Z9")

    # 3: line item maths is wrong (3 x 1500 should be 4500, shows 4800)
    inv3 = build_invoice("INV-1003", "2026-10-20", "Patel Electronics",
                         [("LED Monitor", 3, 1500.00), ("HDMI Cable", 10, 200.00)])
    inv3["lines"][0]["amount"] = 4800.00

    # 4: tax is wrong (18% stated, but only 5% was charged)
    inv4 = build_invoice("INV-1004", "2026-09-15", "Mehta Furniture",
                         [("Office Chair", 6, 3200.00)])
    inv4["tax"] = round(inv4["subtotal"] * 5 / 100, 2)
    inv4["total"] = round(inv4["subtotal"] + inv4["tax"], 2)

    # 5: INCOMPLETE - vendor name and invoice date are missing
    inv5 = build_invoice("INV-1005", None, None, [("Printer Toner", 4, 2100.00)])

    # 6: DUPLICATE - same invoice number as invoice 1
    inv6 = build_invoice("INV-1001", "2026-10-06", "ABC Traders Pvt Ltd",
                         [("Laptop", 2, 45000.00), ("Wireless Mouse", 5, 750.00)])

    # 7: future date + invalid GSTIN
    inv7 = build_invoice("INV-1007", "2027-03-01", "Zenith Supplies",
                         [("Router", 3, 2500.00)], gstin="INVALID123")

    # 8: grand total is wrong (500 extra)
    inv8 = build_invoice("INV-1008", "2026-11-10", "Kiran Hardware",
                         [("Drill Machine", 2, 4200.00), ("Drill Bits Set", 3, 650.00)])
    inv8["total"] = inv8["total"] + 500

    names = ["01_valid", "02_valid", "03_wrong_line_amount", "04_wrong_tax",
             "05_missing_fields", "06_duplicate", "07_bad_date_gstin", "08_wrong_total"]
    for name, inv in zip(names, [inv1, inv2, inv3, inv4, inv5, inv6, inv7, inv8]):
        draw_pdf(inv, f"invoices/invoice_{name}.pdf")

    print("Created 8 sample invoices in the 'invoices' folder.")


if __name__ == "__main__":
    main()

"""
main.py  -  The program you run.

    python main.py                 -> processes all PDFs in the 'invoices' folder
    python main.py my_folder       -> processes all PDFs in 'my_folder'

What it does:
    for each PDF  ->  extract data (extractor.py)
                  ->  validate data (validator.py)
                  ->  print a result and save reports in the 'output' folder
"""

import csv
import os
import sys

from extractor import extract_invoice
from validator import validate_invoice


def save_summary_csv(results, path):
    """One row per invoice: key fields + status + problems found."""
    columns = ["file_name", "invoice_number", "invoice_date", "vendor_name",
               "vendor_gstin", "subtotal", "tax_amount", "total", "status", "problems"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for inv, check in results:
            row = {col: inv.get(col) for col in columns if col not in ("status", "problems")}
            row["status"] = check["status"]
            problems = ["Missing: " + m for m in check["missing"]] + check["errors"]
            row["problems"] = " | ".join(problems)
            writer.writerow(row)


def save_items_csv(results, path):
    """One row per line item (description, quantity, price, amount)."""
    columns = ["file_name", "invoice_number", "description", "quantity", "unit_price", "amount"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for inv, _ in results:
            for item in inv["items"]:
                writer.writerow({
                    "file_name": inv["file_name"],
                    "invoice_number": inv["invoice_number"],
                    **item,
                })


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else "invoices"
    if not os.path.isdir(folder):
        print(f"Folder '{folder}' not found.")
        return

    pdf_files = sorted(f for f in os.listdir(folder) if f.lower().endswith(".pdf"))
    if not pdf_files:
        print(f"No PDF files found in '{folder}'. Run 'python make_sample_invoices.py' first.")
        return

    results = []            # list of (invoice_data, validation_result)
    seen_numbers = set()    # used to catch duplicate invoice numbers

    print(f"\nProcessing {len(pdf_files)} invoice(s) from '{folder}'...\n")

    for file_name in pdf_files:
        path = os.path.join(folder, file_name)
        try:
            invoice = extract_invoice(path)                  # STEP 1: extract
            check = validate_invoice(invoice, seen_numbers)  # STEP 2: validate
        except Exception as error:                           # e.g. corrupted PDF
            print(f"{file_name}: could not be read ({error})")
            continue
        results.append((invoice, check))

        # STEP 3: show the result on screen
        print(f"{file_name}  [{invoice['invoice_number'] or 'no number'}]  ->  {check['status']}")
        for m in check["missing"]:
            print(f"      - Missing: {m}")
        for e in check["errors"]:
            print(f"      - {e}")

    # STEP 4: save reports
    os.makedirs("output", exist_ok=True)
    save_summary_csv(results, "output/invoice_summary.csv")
    save_items_csv(results, "output/invoice_items.csv")

    # Final count
    count = {"VALID": 0, "INCOMPLETE": 0, "INCORRECT": 0}
    for _, check in results:
        count[check["status"]] += 1
    print("\n" + "=" * 50)
    print(f"Total: {len(results)} | Valid: {count['VALID']} | "
          f"Incomplete: {count['INCOMPLETE']} | Incorrect: {count['INCORRECT']}")
    print("Reports saved in the 'output' folder.")


if __name__ == "__main__":
    main()

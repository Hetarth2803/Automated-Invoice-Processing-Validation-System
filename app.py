"""
app.py  -  The WEBSITE version of the project (built with Streamlit).

Run it with:     streamlit run app.py

It reuses the same two files as before:
    extractor.py  -> reads the PDF
    validator.py  -> checks the data
Streamlit only adds the web page (upload button, tables, download buttons).
"""

import os
import tempfile

import pandas as pd
import streamlit as st

from extractor import extract_invoice
from validator import validate_invoice

# ---------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------
st.set_page_config(page_title="Invoice Processor", page_icon="🧾", layout="wide")
st.title("🧾 Automated Invoice Processing & Validation")
st.write("Upload PDF invoices. The app extracts the data and checks it for mistakes.")

# ---------------------------------------------------------------
# Sidebar: choose where the PDFs come from
# ---------------------------------------------------------------
st.sidebar.header("Input")
use_samples = st.sidebar.checkbox("Use sample invoices (demo)")
uploaded_files = st.file_uploader("Upload invoice PDFs", type="pdf", accept_multiple_files=True)


def collect_pdfs():
    """Return a list of (file_name, path_on_disk) for every PDF to process."""
    pdfs = []
    if use_samples:
        # If the sample PDFs are missing (e.g. not uploaded to GitHub), create them now
        has_pdfs = os.path.isdir("invoices") and any(f.lower().endswith(".pdf") for f in os.listdir("invoices"))
        if not has_pdfs:
            import make_sample_invoices
            make_sample_invoices.main()
        for name in sorted(os.listdir("invoices")):
            if name.lower().endswith(".pdf"):
                pdfs.append((name, os.path.join("invoices", name)))
    for file in uploaded_files:
        # An uploaded file lives in memory, so save it to a temporary file first
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        temp.write(file.getbuffer())
        temp.close()
        pdfs.append((file.name, temp.name))
    return pdfs


pdfs = collect_pdfs()

if not pdfs:
    st.info("Upload one or more PDF invoices, or tick 'Use sample invoices' in the sidebar.")
    st.stop()

# ---------------------------------------------------------------
# Process every PDF (same logic as main.py)
# ---------------------------------------------------------------
results = []
seen_numbers = set()

for file_name, path in pdfs:
    try:
        invoice = extract_invoice(path)
        invoice["file_name"] = file_name          # show the real name, not the temp name
        check = validate_invoice(invoice, seen_numbers)
        results.append((invoice, check))
    except Exception as error:
        st.error(f"{file_name}: could not be read ({error})")

# ---------------------------------------------------------------
# Show the totals
# ---------------------------------------------------------------
count = {"VALID": 0, "INCOMPLETE": 0, "INCORRECT": 0}
for _, check in results:
    count[check["status"]] += 1

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total invoices", len(results))
c2.metric("✅ Valid", count["VALID"])
c3.metric("⚠️ Incomplete", count["INCOMPLETE"])
c4.metric("❌ Incorrect", count["INCORRECT"])

# ---------------------------------------------------------------
# Summary table (one row per invoice)
# ---------------------------------------------------------------
summary_rows = []
item_rows = []
for inv, check in results:
    problems = ["Missing: " + m for m in check["missing"]] + check["errors"]
    summary_rows.append({
        "File": inv["file_name"],
        "Invoice No": inv["invoice_number"],
        "Date": inv["invoice_date"],
        "Vendor": inv["vendor_name"],
        "GSTIN": inv["vendor_gstin"],
        "Subtotal": inv["subtotal"],
        "Tax": inv["tax_amount"],
        "Total": inv["total"],
        "Status": check["status"],
        "Problems": " | ".join(problems),
    })
    for item in inv["items"]:
        item_rows.append({"File": inv["file_name"], "Invoice No": inv["invoice_number"], **item})

summary_df = pd.DataFrame(summary_rows)
items_df = pd.DataFrame(item_rows)

st.subheader("Summary")
st.dataframe(summary_df, width="stretch", hide_index=True)

# ---------------------------------------------------------------
# Details for each invoice (click to expand)
# ---------------------------------------------------------------
st.subheader("Invoice details")
icons = {"VALID": "✅", "INCOMPLETE": "⚠️", "INCORRECT": "❌"}

for inv, check in results:
    title = f"{icons[check['status']]} {inv['file_name']}  -  {inv['invoice_number'] or 'no number'}  -  {check['status']}"
    with st.expander(title):
        left, right = st.columns(2)
        left.write(f"**Vendor:** {inv['vendor_name']}")
        left.write(f"**Address:** {inv['vendor_address']}")
        left.write(f"**GSTIN:** {inv['vendor_gstin']}")
        right.write(f"**Invoice date:** {inv['invoice_date']}")
        right.write(f"**Subtotal:** {inv['subtotal']}")
        right.write(f"**Tax ({inv['tax_rate']}%):** {inv['tax_amount']}")
        right.write(f"**Total:** {inv['total']}")

        if inv["items"]:
            st.table(pd.DataFrame(inv["items"]))

        for m in check["missing"]:
            st.warning(f"Missing: {m}")
        for e in check["errors"]:
            st.error(e)
        if check["status"] == "VALID":
            st.success("All checks passed.")

# ---------------------------------------------------------------
# Download buttons
# ---------------------------------------------------------------
st.subheader("Download reports")
d1, d2 = st.columns(2)
d1.download_button("⬇️ Summary CSV", summary_df.to_csv(index=False), "invoice_summary.csv", "text/csv")
if not items_df.empty:
    d2.download_button("⬇️ Line items CSV", items_df.to_csv(index=False), "invoice_items.csv", "text/csv")

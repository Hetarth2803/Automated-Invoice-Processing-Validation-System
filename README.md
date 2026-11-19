# Automated Invoice Processing & Validation System

Reads PDF invoices, extracts the important data, checks it for mistakes,
and saves a report.

## How to run

```bash
pip install -r requirements.txt     # 1. install libraries (once)
python make_sample_invoices.py      # 2. create 8 test PDFs (once)
python main.py                      # 3. process all PDFs in 'invoices' folder
```

To process your own PDFs: put them in a folder and run `python main.py your_folder`.

## Run as a website (Streamlit)

```bash
pip install -r requirements.txt
streamlit run app.py
```

Your browser opens at http://localhost:8501 - upload PDFs (or tick "Use sample invoices").

### Put it online for free (Streamlit Community Cloud)
1. Create a GitHub repository and upload this whole folder (keep the `invoices` folder with the sample PDFs).
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **Create app**, choose your repository, set the main file to `app.py`, click **Deploy**.
4. In a few minutes you get a public link to share.

## Project structure

| File | What it does |
|------|--------------|
| `app.py` | The website version (Streamlit) - upload page, tables, download buttons |
| `main.py` | The program you run. Loops over PDFs, prints results, saves CSV reports |
| `extractor.py` | STEP 1 - reads PDF text and finds invoice number, date, vendor, items, tax, total |
| `validator.py` | STEP 2 - checks the data and gives a status |
| `make_sample_invoices.py` | Creates test PDFs (some correct, some deliberately wrong) |
| `invoices/` | Input PDFs |
| `output/` | Reports: `invoice_summary.csv` and `invoice_items.csv` |

## Flow

    PDF  ->  extract_invoice()  ->  validate_invoice()  ->  console + CSV report

## Validation checks

1. Required fields present (number, date, vendor name/address, items, subtotal, tax, total)
2. Invoice number format, and no duplicates
3. Date is real and not in the future
4. GSTIN format (if given)
5. Each item: quantity x unit price = amount
6. Sum of items = subtotal
7. Tax = subtotal x tax rate
8. Subtotal + tax = total

## Statuses

- **VALID** - all checks passed
- **INCOMPLETE** - a required field is missing
- **INCORRECT** - fields exist but something is wrong

## Limitations

- Works on text-based PDFs (not scanned images; those need OCR).
- The regex patterns match the sample layout ("Invoice No:", "Vendor:", ...).
  For a different invoice layout, edit the patterns in `extractor.py`.

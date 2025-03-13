from flask import Flask, jsonify
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject
import os
import json

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "PDF Filler API is running"}), 200

@app.route("/fill-pdf", methods=["POST"])
def pdf_filler_tool():
    try:
        # --- Google Sheets Setup ---
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        service_account_info = json.loads(os.environ["GOOGLE_CREDENTIALS"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)
        client = gspread.authorize(creds)

        # Open the Google Sheet
        sheet = client.open("autofill").sheet1

        # Read data into a Pandas DataFrame
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        if df.empty:
            return jsonify({"error": "No data found in the Google Sheet."}), 400

        # --- Select the Most Recent Row ---
        row = df.iloc[-1]

        # --- Map Google Sheet Columns to PDF Fields ---
        fields = {
            "Physical Address":      row.get("Physical Address", ""),
            "Address":               row.get("Owner Address", ""),
            "Zip":                   row.get("Zip", ""),
            "Owner Name":            row.get("Owner Name", ""),
            "Owner Zip":             row.get("Owner Zip", ""),
            "Owner Phone":           row.get("Owner Phone", ""),
            "Owner Email":           row.get("Owner Email", ""),
            "Cost of Demolition":    str(row.get("Cost of Demolition", "")),
            "Floors":                str(row.get("Floors", "")),
            "Units":                 str(row.get("Units", "")),
            "Total SQ FT":           str(row.get("Total SQ FT", "")),
            "Sewer":                 row.get("Sewer", ""),
            "Septic":                row.get("Septic", ""),
            "Electrical":            row.get("Electrical", ""),
            "Plumbing":              row.get("Plumbing", ""),
            "Gas":                   row.get("Gas", ""),
            "Escambia County":       row.get("Escambia County", ""),
            "City of Pensacola":     row.get("City of Pensacola", ""),
            "City":                  row.get("City", ""),
            "Parcel I":              row.get("Parcel ID", ""),
            "Owner City":            row.get("Owner City", ""),
            "State":                 row.get("State", ""),
            "Owner State":           row.get("Owner State", ""),
            "Scope":                 row.get("Scope", ""),
        }

        # --- Fill the PDF Form ---
        pdf_template = "Demo_permit.pdf"  # Ensure this file exists in the project folder
        output_pdf = "filled_permit.pdf"   # Output file

        reader = PdfReader(pdf_template)
        writer = PdfWriter()

        # Copy all pages from the original PDF
        for page in reader.pages:
            writer.add_page(page)

        # Retrieve and assign AcroForm (if exists)
        acroform = reader.trailer["/Root"].get("/AcroForm")
        if acroform:
            writer._root_object[NameObject("/AcroForm")] = acroform

        # Update the fields on the first page
        writer.update_page_form_field_values(writer.pages[0], fields)

        # Write to a new PDF file
        with open(output_pdf, "wb") as output_file:
            writer.write(output_file)

        return jsonify({"message": f"✅ PDF has been filled and saved as: {output_pdf}"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
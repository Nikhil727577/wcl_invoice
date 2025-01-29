from PyPDF2 import PdfReader
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import uvicorn
import re

app = FastAPI()

def extract_text(file: UploadFile):
    """Extract text from the uploaded PDF file."""
    try:
        reader = PdfReader(file.file)
        text = "".join(page.extract_text() or "" for page in reader.pages)  # Handle empty pages safely
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error extracting text: {e}")

def extract_details_from_text(text):
    """
    Extract details such as Invoice Number, Invoice Date, and Total Amount from the text.
    """
    try:
        # Regular expression patterns for details
        invoice_no_pattern = r"Invoice No[:\-]?\s*(\S+)"
        invoice_date_pattern = r"Invoice Date[:\-]?\s*(\d{2}[/-]\d{2}[/-]\d{4})"
        total_amount_pattern = r"Total Amount.*?(\d[\d,]*\.\d{2})"

        # Extract details using regex
        invoice_no = re.search(invoice_no_pattern, text)
        invoice_date = re.search(invoice_date_pattern, text)
        total_amount = re.search(total_amount_pattern, text, re.DOTALL)

        # Extracted values (handle None if the pattern doesn't match)
        extracted_details = {
            "Invoice Number": invoice_no.group(1) if invoice_no else None,
            "Invoice Date": invoice_date.group(1) if invoice_date else None,
            "Total Amount": total_amount.group(1) if total_amount else None
        }

        return extracted_details
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error extracting details: {e}")

def is_valid_invoice(text):
    """
    Validate if the uploaded document contains essential invoice markers.
    """
    required_markers = ["Invoice No", "Invoice Date", "Total Amount"]
    return any(marker in text for marker in required_markers)

@app.post("/IRN_verification")
def process_document(invoice_number: str = Form(...), invoice_date: str = Form(...), total_amount: str = Form(...), file_path: UploadFile = File()):
    """
    Process the document: Extract invoice details and compare them with user inputs.
    """
    print(f"Processing file: {file_path.filename}")

    # Ensure a valid file is uploaded
    if not file_path.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a valid PDF file.")

    text = extract_text(file_path)

    # Check if the uploaded document contains essential invoice markers
    if not is_valid_invoice(text):
        raise HTTPException(status_code=400, detail="Please make sure you are uploading a valid Invoice")

    extracted_details = extract_details_from_text(text)

    # Check for missing values and mark them as "invalid"
    response = {
        "invoice_number": "valid" if invoice_number == extracted_details["Invoice Number"] else "invalid",
        "document_date": "valid" if invoice_date == extracted_details["Invoice Date"] else "invalid",
        "total_amount": "valid" if total_amount == extracted_details["Total Amount"] else "invalid"
    }

    return response

if __name__ == "__main__":
    uvicorn.run(app)

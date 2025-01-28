from PyPDF2 import PdfReader
from fastapi import FastAPI,UploadFile,File,Form,HTTPException
import uvicorn
import re

app=FastAPI()


def extract_text(file:UploadFile):
    try:
        reader=PdfReader(file.file)
        text = "".join(page.extract_text() for page in reader.pages)
        return text
    except Exception as e:
        return f"Error extracting text: {e}"

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
        print(extracted_details)
        
        return extracted_details
    except Exception as e:
        print(f"Error extracting details: {e}")
        return None



# def validate_document_format(text):
#     """
#     Validate the format of the document based on specific markers.
#     """
#     required_markers = ["Tax Invoice", "GSTIN", "Invoice No", "Invoice Date", "Place of Supply"]
#     return all(marker in text for marker in required_markers)

@app.post("/IRN_verification")
def process_document(invoice_number: str = Form(...), invoice_date: str = Form(...), total_amount: str = Form(...), file_path: UploadFile = File()):
    """
    Process the document: check digital signature and validate format.
    """
    print(f"Processing file: {file_path.filename}")
    text = extract_text(file_path)

    
        # Extract details from the document text
    extracted_details = extract_details_from_text(text)

    # Check if all required details are present
    if not extracted_details or not all(extracted_details.values()):
        raise HTTPException(status_code=400, detail="Please make sure you are uploading a valid Invoice")

    # Compare the extracted details with the provided details
    response = {
        "invoice_number": "valid" if invoice_number == extracted_details["Invoice Number"] else "invalid",
        "document_date": "valid" if invoice_date == extracted_details["Invoice Date"] else "invalid",
        "total_amount": "valid" if total_amount == extracted_details["Total Amount"] else "invalid"
    }

    return response
    # except Exception as e:
    #     # Handle any errors
    #     raise HTTPException(status_code=400, detail=f"An error occurred while processing the document: {e}")

if __name__ =="__main__":
    uvicorn.run(app)
import os
import re
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from models.schemas import TextInput
from services.ai_service import extract_json
from services.report import generate_report

router = APIRouter()





def clean_text(text: str) -> str:
    # 1. Convert all line breaks + tabs to space
    text = re.sub(r'[\n\r\t]+', ' ', text)

    # 2. Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)

    # 3. Remove weird control characters (important for PDF crashes)
    text = re.sub(r'[^\x20-\x7E\u00A0-\uFFFF]', '', text)

    # 4. Trim
    text = text.strip()
    print("Cleaned Text:", text)
    return text






@router.post("/generate-report")
def generate_report_api(data: TextInput):
    print("Received Text:", data.text)
    try:

        cleaned_text = clean_text(data)
        print("Cleaned Text:", cleaned_text)
        # Step 1: Extract structured data
        extracted_data = extract_json(cleaned_text)
        print("Extracted Data:", extracted_data)
            
        # Step 2: Generate PDF
        filepath = generate_report(extracted_data)

        # Step 3: Check file exists
        if not os.path.exists(filepath):
            raise HTTPException(status_code=500, detail="PDF not created")

        # Step 4: Return file
        return FileResponse(
            path=filepath,
            media_type="application/pdf",
            filename=os.path.basename(filepath)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
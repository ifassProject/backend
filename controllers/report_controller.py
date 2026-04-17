import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from models.schemas import TextInput
from services.ai_service import extract_json
from services.report import generate_report

router = APIRouter()

@router.post("/generate-report")
def generate_report_api(data: TextInput):
    try:
        # Step 1: Extract structured data
        extracted_data = extract_json(data)
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
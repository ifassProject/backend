from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import re

from models.schemas import TextInput
from services.ai_service import extract_json
from services.report import generate_report

router = APIRouter()


def clean_text(text: str) -> str:
    text = re.sub(r'[\n\r\t]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\x20-\x7E\u00A0-\uFFFF]', '', text)
    return text.strip()


@router.post("/generate-report")
def generate_report_api(data: TextInput):
    try:
        cleaned_text = clean_text(data.text)

        extracted_data = extract_json(cleaned_text)

        pdf_buffer = generate_report(extracted_data)

        pdf_buffer.seek(0)
        print(f"Generated PDF size: {pdf_buffer.getbuffer().nbytes} bytes")
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=report.pdf"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
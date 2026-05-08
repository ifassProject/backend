import json
import os
import re
from copy import deepcopy
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set")

# Initialize OpenAI client
client = OpenAI(api_key=API_KEY)

SOAP_TEMPLATE = {
    "client_info": {
        "name_last": None,
        "name_first": None,
        "date": "",
        "date_of_birth": None
    },
    "subjective": {
        "chief_complaint": "",
        "health_history_updates": "",
        "current_symptoms": "",
        "accidents_injuries": "",
        "work_sport_activity": "",
        "medical_conditions": "",
        "allergies": ""
    },
    "objective": {
        "bp_pr_before": None,
        "bp_pr_after": None,
        "observations": "",
        "vitals": {
            "temperature": None,
            "texture": "",
            "tone_ht": "",
            "tenderness": "",
            "referral_pain": "",
            "rom_mrt_tests": ""
        }
    },
    "assessment": {
        "findings_summary": "",
        "client_response": "",
        "client_progress": ""
    },
    "plan": {
        "duration_minutes": 60,
        "parts_of_body": "",
        "modality": "",
        "focus_on": "",
        "avoid_areas": "",
        "detail_tx": "",
        "future_tx_plan": "",
        "home_care_recommendations": "",
        "scheduling": "",
        "referral": ""
    }
}


def _extract_json_text(raw_text: str) -> str:
    """
    Extract valid JSON object from model response
    """

    text = (raw_text or "").strip()

    # Remove markdown code blocks
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)

    # Find JSON object
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model output")

    return text[start:end + 1]


def _merge_template(template, data):
    """
    Keep only template keys and coerce basic types
    """

    if isinstance(template, dict):

        data = data if isinstance(data, dict) else {}

        out = {}

        for k, v in template.items():
            out[k] = _merge_template(v, data.get(k))

        return out

    if isinstance(template, int):

        try:
            return int(data) if data is not None else template

        except (TypeError, ValueError):
            return template

    if template is None:
        return data if data is not None else None

    return str(data).strip() if data is not None else template


def extract_json(text: str):

    prompt = f"""
You are a SOAP medical report extractor.

Return ONLY valid JSON.
No explanation.
No markdown.

Use this exact schema and fill missing values with null or "".

Schema:
{json.dumps(SOAP_TEMPLATE, ensure_ascii=False, indent=2)}

TEXT:
{text}
""".strip()

    try:

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You extract SOAP medical reports into structured JSON. "
                        "Always return valid JSON only."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        raw = response.choices[0].message.content

        parsed = json.loads(_extract_json_text(raw))

        cleaned = _merge_template(
            deepcopy(SOAP_TEMPLATE),
            parsed
        )

        return cleaned

    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON returned by OpenAI: {e}")

    except Exception as e:
        raise RuntimeError(f"Failed to generate valid SOAP JSON: {e}")


# Test
if __name__ == "__main__":

    sample_text = """
    Client John Doe complains of neck pain and headaches.

    Temperature normal.

    Tenderness around upper trapezius.

    Recommended massage therapy and stretching.

    Follow-up next week.
    """

    result = extract_json(sample_text)

    print(json.dumps(result, indent=2, ensure_ascii=False))
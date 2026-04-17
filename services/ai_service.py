# ...existing code...
import json
import os
import re
from copy import deepcopy
from dotenv import load_dotenv

import google.generativeai as genai
from google.api_core.exceptions import NotFound

# IMPORTANT: move key to environment variable
load_dotenv()
# Windows PowerShell: setx GEMINI_API_KEY "your_key"
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set")

genai.configure(api_key=API_KEY)

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
    text = (raw_text or "").strip()

    # Remove markdown fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)

    # Keep only first JSON object
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model output")
    return text[start:end + 1]


def _merge_template(template, data):
    """Keep only template keys and coerce basic types."""
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

    # string default
    return str(data).strip() if data is not None else template


def _candidate_models():
    # Try common names first, then fallback to list_models()
    base = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-2.0-flash",
        "models/gemini-1.5-flash",
        "models/gemini-1.5-pro",
        "models/gemini-2.0-flash",
    ]
    seen = set(base)

    try:
        for m in genai.list_models():
            methods = getattr(m, "supported_generation_methods", []) or []
            if "generateContent" in methods:
                if m.name not in seen:
                    base.append(m.name)
                    seen.add(m.name)
    except Exception:
        pass

    return base


def extract_json(text: str):
    prompt = f"""
You are a SOAP medical report extractor.
Return ONLY valid JSON (no explanation, no markdown).
Use this exact schema and fill missing values with null or "".

Schema:
{json.dumps(SOAP_TEMPLATE, ensure_ascii=False, indent=2)}

TEXT:
{text}
""".strip()

    last_err = None
    for model_name in _candidate_models():
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            raw = getattr(response, "text", "") or ""
            parsed = json.loads(_extract_json_text(raw))
            return _merge_template(deepcopy(SOAP_TEMPLATE), parsed)
        except NotFound as e:
            last_err = e
            continue
        except json.JSONDecodeError as e:
            last_err = e
            continue
        except Exception as e:
            last_err = e
            continue

    raise RuntimeError(f"Failed to generate valid SOAP JSON. Last error: {last_err}")

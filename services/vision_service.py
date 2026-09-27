import json
import time
from pathlib import Path

from google import genai
from PIL import Image

from utils.config import GEMINI_API_KEY


def _retry_gemini_call(callable_obj, retries=3):
    last_error = None
    for attempt in range(retries):
        try:
            return callable_obj()
        except Exception as exc:
            last_error = exc
            message = str(exc).lower()
            if "503" not in message and "unavailable" not in message and "429" not in message and "resource_exhausted" not in message:
                raise
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
    raise last_error


def validate_image(file_path):
    try:
        image = Image.open(file_path)
        image.verify()
        image = Image.open(file_path)
        width, height = image.size
        if width <= 0 or height <= 0:
            raise ValueError("Image dimensions are invalid.")
        if image.size[0] * image.size[1] > 100000000:
            raise ValueError("Image is too large. Please upload a smaller image.")
        return {"valid": True, "width": width, "height": height}
    except Exception as exc:
        raise ValueError(f"Invalid image file: {exc}") from exc


def _safe_json_extract(text):
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


def build_inspection_prompt(product_name="", category=""):
    return f"""
    You are an AI-assisted visual product quality inspector.
    Perform visual inspection only. Do not claim to detect hidden defects or defects that are not visible.
    Inspect the product in the image for visible quality issues.
    Product name: {product_name or 'Unknown'}
    Category: {category or 'Unknown'}

    Detect visible defects including scratches, cracks, dents, missing components, broken parts, discoloration, deformation, surface damage, manufacturing defects, and any other visible abnormalities.

    Return valid JSON only with this structure:
    {{
      "product_detected": true,
      "result": "PASS" or "FAIL" or "INVALID",
      "confidence": 0.0 to 1.0,
      "defects": [
        {{"type": "string", "description": "string", "severity": "Low|Medium|High"}}
      ],
      "severity": "None|Low|Medium|High|Unknown",
      "summary": "string",
      "recommendation": "string"
    }}

    Rules:
    - If the image does not appear to contain a valid product, return {{"product_detected": false, "result": "INVALID", "confidence": 0, "defects": [], "severity": "Unknown", "summary": "The uploaded image does not appear to contain a valid product.", "recommendation": "Upload a clear product image."}}
    - For a valid product with no visible defects, result should be "PASS", confidence between 0.80 and 0.99, defects as [], severity "None".
    - For a real visible defect, result should be "FAIL", confidence between 0.80 and 0.99, defects list with details.
    - Keep the summary concise but clear.
    - Do not use markdown or any extra text outside the JSON object.
    """


def analyze_product_image(image_path, product_name="", category=""):
    if not GEMINI_API_KEY:
        raise ValueError("Gemini API key is not configured. Please add GEMINI_API_KEY in your .env file.")

    try:
        validate_image(image_path)
    except ValueError:
        raise

    client = genai.Client(api_key=GEMINI_API_KEY)

    image = Path(image_path)
    prompt = build_inspection_prompt(product_name, category)

    try:
        image_bytes = image.read_bytes()
        response = _retry_gemini_call(
            lambda: client.models.generate_content(
                model="gemini-3.8-flash",
                contents=[
                    prompt,
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_bytes,
                        }
                    },
                ],
            )
        )
        output = response.text
        parsed = _safe_json_extract(output)

        if not isinstance(parsed, dict):
            raise ValueError("AI response was not a valid JSON object.")

        if "product_detected" not in parsed:
            parsed["product_detected"] = True
        if "result" not in parsed:
            parsed["result"] = "FAIL"
        if "confidence" not in parsed:
            parsed["confidence"] = 0.0
        if "defects" not in parsed or not isinstance(parsed["defects"], list):
            parsed["defects"] = []
        if "severity" not in parsed:
            parsed["severity"] = "None"
        if "summary" not in parsed:
            parsed["summary"] = "Inspection completed."
        if "recommendation" not in parsed:
            parsed["recommendation"] = "Please review manually before approval."

        parsed["confidence"] = max(0.0, min(float(parsed["confidence"]), 1.0))
        if parsed["result"] == "INVALID":
            parsed["product_detected"] = False
            parsed["defects"] = []
            parsed["severity"] = "Unknown"
            parsed["confidence"] = 0
        return parsed
    except Exception as exc:
        raise ValueError(f"AI inspection failed: {exc}") from exc


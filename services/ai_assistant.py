import time

from google import genai

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


def build_quality_assistant_reply(prompt, inspection=None):
    if not GEMINI_API_KEY:
        return "Gemini API is not configured. Add your API key in the .env file to enable the AI Quality Assistant."

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        context = ""
        if inspection:
            context = f"""
            Current inspection context:
            - Product: {inspection.get('product_name', 'Unknown')}
            - Result: {inspection.get('result', 'Unknown')}
            - Confidence: {inspection.get('confidence', 0)}
            - Severity: {inspection.get('severity', 'Unknown')}
            - Defects: {inspection.get('defects', [])}
            - Summary: {inspection.get('summary', '')}
            - Recommendation: {inspection.get('recommendation', '')}
            """

        response = _retry_gemini_call(
            lambda: client.models.generate_content(
                model="gemini-3.8-flash",
                contents=f"""
                You are an AI quality assistant for a product inspection platform.
                Provide helpful, practical guidance for quality control and inspection questions.
                Clearly distinguish general guidance from professional inspection requirements. Never act like a human quality engineer and never claim hidden defects.
                Keep your answer concise but useful.
                {context}
                User question: {prompt}
                """,
            )
        )
        return response.text.strip()
    except Exception as exc:
        return f"I could not answer that question right now. Please try again in a moment. Error: {exc}"

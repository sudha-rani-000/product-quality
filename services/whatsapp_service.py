import json
import os
from urllib.parse import quote

import requests

from utils.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER, WHATSAPP_API_TOKEN, WHATSAPP_API_VERSION, WHATSAPP_PHONE_NUMBER_ID, whatsapp_is_configured


def _build_whatsapp_url():
    if WHATSAPP_API_TOKEN and WHATSAPP_PHONE_NUMBER_ID:
        return f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_WHATSAPP_NUMBER:
        return f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    return None


def send_whatsapp_message(phone_number, message, development_mode=False, development_otp=None):
    if not whatsapp_is_configured():
        if development_mode:
            return {"status": "development", "message": f"WhatsApp integration is not configured. Development OTP: {development_otp}"}
        return {"status": "skipped", "message": "WhatsApp integration is not configured."}

    if WHATSAPP_API_TOKEN and WHATSAPP_PHONE_NUMBER_ID:
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {
                "body": message,
            },
        }
        headers = {
            "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
            "Content-Type": "application/json",
        }
        response = requests.post(_build_whatsapp_url(), headers=headers, json=payload, timeout=20)
        if response.status_code >= 400:
            return {"status": "error", "message": response.text}
        return {"status": "sent", "message": response.json()}

    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_WHATSAPP_NUMBER:
        form_data = {
            "From": f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
            "To": f"whatsapp:{phone_number}",
            "Body": message,
        }
        response = requests.post(
            _build_whatsapp_url(),
            auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            data=form_data,
            timeout=20,
        )
        if response.status_code >= 400:
            return {"status": "error", "message": response.text}
        return {"status": "sent", "message": response.json()}

    return {"status": "skipped", "message": "WhatsApp integration is not configured."}

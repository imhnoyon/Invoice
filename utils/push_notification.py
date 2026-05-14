# services/onesignal.py
import requests
from django.conf import settings

HEADERS = {
    "Content-Type": "application/json; charset=utf-8",
    "Authorization": f"Basic {settings.ONESIGNAL_API_KEY}",
}

def send_push_notification(message: str, onesignal_id: str):
    payload = {
        "app_id": settings.ONESIGNAL_APP_ID,
        "include_player_ids": [onesignal_id],
        "contents": {"en": message},
    }

    url = f"{settings.ONESIGNAL_API_URL}/notifications"

    response = requests.post(url, json=payload, headers=HEADERS, timeout=5)

    # OneSignal can return 200/201 on success.
    if response.status_code not in (200, 201):
        raise Exception(f"OneSignal Error: {response.text}")

    try:
        return response.json()
    except ValueError:
        return {"status": response.status_code, "text": response.text}
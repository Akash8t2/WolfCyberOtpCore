#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NumberPanel OTP Bot
Mode: LAST 3 OTP ONLY
Stable + Heroku Safe
"""

import time
import json
import re
import requests
from datetime import datetime

# ================= CONFIG =================
BASE_URL = "http://51.89.99.105/NumberPanel"
API_PATH = "/client/res/data_smscdr.php"

# ⚠️ SECURITY NOTE:
# Ye values Heroku Config Vars me rakhna BEST hai
PHPSESSID = "ct38cra540a4hil76g82dirrft"
BOT_TOKEN = "7448362382:AAGzYcF4XH5cAOIOsrvJ6E9MXqjnmOdKs2o"

CHAT_ID = "-1003405109562"
CHECK_INTERVAL = 10
STATE_FILE = "state.json"

# ================= HEADERS =================
HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": f"{BASE_URL}/client/SMSDashboard",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

# ================= SESSION =================
session = requests.Session()
session.cookies.set(
    name="PHPSESSID",
    value=PHPSESSID,
    domain="51.89.99.105",
    path="/"
)

# ================= HELPERS =================
def load_state():
    try:
        return json.load(open(STATE_FILE))
    except Exception:
        return {"sent": []}

def save_state(state):
    json.dump(state, open(STATE_FILE, "w"))

def extract_otp(text):
    """
    OTP formats supported:
    123456
    589-837
    589 837
    """
    if not text:
        return None
    m = re.search(r"\b(\d{3,4}[-\s]?\d{3,4})\b", text)
    return m.group(1) if m else None

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": msg,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        },
        timeout=10
    )
    print("📤 Telegram:", r.status_code)

# ================= START =================
print("🚀 NumberPanel OTP Bot Started")
print("⚡ Mode: LAST 3 OTP ONLY")
print("📢 Group:", CHAT_ID)

state = load_state()
sent = state.get("sent", [])

while True:
    try:
        params = {
            "fdate1": "2025-01-01 00:00:00",
            "fdate2": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "iDisplayStart": 0,
            "iDisplayLength": 3,   # 🔥 LAST 3 OTP ONLY
            "sEcho": 1,
            "_": int(time.time() * 1000),
        }

        r = session.get(
            BASE_URL + API_PATH,
            headers=HEADERS,
            params=params,
            timeout=15
        )

        # ---------- SAFETY CHECKS ----------
        if not r.text or not r.text.strip():
            print("⚠️ Empty response from server")
            time.sleep(CHECK_INTERVAL)
            continue

        if "login" in r.text.lower():
            print("🔐 SESSION EXPIRED — UPDATE PHPSESSID")
            time.sleep(60)
            continue

        if "text/html" in (r.headers.get("Content-Type") or ""):
            print("⚠️ HTML response received (ignored)")
            time.sleep(CHECK_INTERVAL)
            continue

        try:
            data = r.json()
        except Exception:
            print("⚠️ JSON parse failed")
            print("RAW:", r.text[:200])
            time.sleep(CHECK_INTERVAL)
            continue

        rows = data.get("aaData", [])
        if not rows:
            time.sleep(CHECK_INTERVAL)
            continue

        # Oldest → Newest order
        rows.reverse()

        for row in rows:
            ts, pool, number, service, message = row[:5]
            key = f"{number}_{ts}"

            if key in sent:
                continue

            otp = extract_otp(message)
            print("🧾 SMS:", message)

            if otp:
                msg = (
                    f"🔐 *NEW OTP RECEIVED*\n"
                    f"━━━━━━━━━━━━━━\n"
                    f"🕒 `{ts}`\n"
                    f"📞 `{number}`\n"
                    f"📲 `{service}`\n"
                    f"🔢 *OTP:* `{otp}`\n"
                )
                send_telegram(msg)

            sent.append(key)

        # memory limit
        sent = sent[-10:]
        save_state({"sent": sent})

    except Exception as e:
        print("💥 UNEXPECTED ERROR:", e)

    time.sleep(CHECK_INTERVAL)

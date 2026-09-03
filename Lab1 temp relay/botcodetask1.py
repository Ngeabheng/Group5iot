# ==============================
# LAB 1: Temperature Sensor with Relay Control
# ESP32 + DHT22 + Telegram Bot
# ==============================
import time
import network
import urequests
import dht
from machine import Pin

# ---------- USER CONFIG ----------
WIFI_SSID = "Robotic WIFI"
WIFI_PASSWORD = "rbtWIFI@2025"
BOT_TOKEN = "8968694049:AAGn5cIzMF-EH8ngKmNaHyU-a46SznCzqn4"
CHAT_ID = "1119054297"

DHT_PIN = 33        # D4 per wiring diagram
RELAY_PIN = 15      # D2 per wiring diagram
TEMP_THRESHOLD = 25.0
SAMPLE_INTERVAL = 5  # seconds
# ---------------------------------

# ---------- HARDWARE SETUP ----------
sensor = dht.DHT11(Pin(DHT_PIN))
relay = Pin(RELAY_PIN, Pin.OUT)
relay.off()
# -----------------------------------

# ---------- WIFI ----------
def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        timeout = 20
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
    if wlan.isconnected():
        print("WiFi connected:", wlan.ifconfig())
        return True
    else:
        print("WiFi failed")
        return False

wifi_connect()
# -----------------------------------

# ---------- TELEGRAM ----------
def send_message(text):
    try:
        url = "https://api.telegram.org/bot{}/sendMessage".format(BOT_TOKEN)
        payload = {"chat_id": CHAT_ID, "text": text}
        r = urequests.post(url, json=payload)
        print("Telegram status:", r.status_code)
        r.close()
    except Exception as e:
        print("Telegram error:", e)

def get_updates(offset):
    try:
        url = "https://api.telegram.org/bot{}/getUpdates?offset={}".format(BOT_TOKEN, offset)
        r = urequests.get(url)
        data = r.json()
        r.close()
        return data
    except Exception as e:
        print("GetUpdates error:", e)
        return {"result": []}
# -----------------------------------

# ---------- STATE ----------
last_update_id = 0
auto_off_notified = False   # tracks one-time auto-off message
# -----------------------------------

# ---------- COMMAND HANDLER (Task 3) ----------
def handle_commands(temp, hum):
    global last_update_id
    updates = get_updates(last_update_id + 1)
    for item in updates["result"]:
        last_update_id = item["update_id"]

        # Guard against non-text updates (e.g. edited messages, stickers)
        message = item.get("message", {})
        text = message.get("text", "")

        if text == "/status":
            state = "ON" if relay.value() else "OFF"
            msg = "Temp: {:.2f}°C\nHum: {:.2f}%\nRelay: {}".format(temp, hum, state)
            send_message(msg)
        elif text == "/on":
            relay.on()
            send_message("Relay turned ON")
        elif text == "/off":
            relay.off()
            send_message("Relay turned OFF")
# -----------------------------------

# ---------- MAIN LOOP ----------
print("System started")
while True:
    try:
        # Reconnect WiFi if dropped
        if not network.WLAN(network.STA_IF).isconnected():
            wifi_connect()

        # ---- Task 1: Read sensor every 5s, print with 2 decimals ----
        sensor.measure()
        temperature = sensor.temperature()
        humidity = sensor.humidity()

        # Sanity check - reject garbage reads (DHT22 range: -40 to 80°C, 0-100% RH)
        if temperature < -40 or temperature > 80 or humidity < 0 or humidity > 100:
            print("Invalid reading, skipping:", temperature, humidity)
            time.sleep(SAMPLE_INTERVAL)
            continue

        print("Temp: {:.2f}C | Hum: {:.2f}%".format(temperature, humidity))

        # ---- Task 3: handle bot commands (run before alert logic so /on registers same loop) ----
        handle_commands(temperature, humidity)

        # ---- Task 4: alert / auto-off state machine ----
        if temperature < TEMP_THRESHOLD:
            # Below threshold: no messages at all, UNLESS this is the moment relay
            # needs to auto-turn-off (one-time notice)
            if relay.value():
                relay.off()
                if not auto_off_notified:
                    send_message("Temperature normal ({:.2f}°C). Relay auto-OFF.".format(temperature))
                    auto_off_notified = True
            else:
                # Relay already off and cool -> reset flag so next hot cycle
                # gets its own fresh one-time auto-off notice later
                auto_off_notified = False
        else:
            # T >= threshold
            if not relay.value():
                # Relay OFF -> keep alerting every loop until /on is received
                send_message("ALERT: Temperature {:.2f}°C - relay is OFF".format(temperature))
            # If relay is ON (user sent /on), no alert - stays silent per spec

    except OSError as e:
        print("Sensor error:", e)
    except Exception as e:
        print("Unexpected error:", e)

    time.sleep(SAMPLE_INTERVAL)
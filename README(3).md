# Lab 3 – IoT Smart Gate Control with Blynk, IR Sensor, Servo Motor, and TM1637

## Overview

This lab implements an ESP32-based smart gate system in MicroPython, built around the Blynk cloud platform. An IR obstacle sensor detects approaching objects, an SG90 servo physically drives the gate, and a TM1637 4-digit display shows detection activity locally. The Blynk app mirrors sensor status, exposes a manual slider for the servo, and lets the operator flip between automatic and manual control.

The project ties together sensing, actuation, cloud dashboards, and a local display into a single event-driven control loop.

## Learning Outcomes (CLO Alignment)

- Read an IR sensor and reflect its detection status on Blynk.
- Drive a servo motor from a Blynk slider.
- Trigger automatic gate opening/closing from IR detection events.
- Track detection counts and mirror the value on both TM1637 and Blynk.
- Support both automatic and manual operating modes.
- Document the wiring, dashboard layout, and system behavior.

## Equipment

- ESP32 development board (MicroPython firmware flashed)
- IR obstacle detection sensor
- SG90 servo motor
- TM1637 4-digit 7-segment display
- Breadboard and jumper wires
- USB cable and laptop with Thonny
- Wi-Fi access and a Blynk account (mobile app, iOS/Android)

## Wiring

![Component Setup](./screenshot/component.png)

### Pin Connections

| Component     | ESP32 Pin | Description                        |
| -------------- | --------- | ------------------------------------ |
| IR Sensor VCC | 5V        | Power supply for IR sensor         |
| IR Sensor GND | GND       | Ground                             |
| IR Sensor OUT | GPIO12    | Digital output (LOW when detected) |
| Servo Signal  | GPIO13    | PWM control signal (yellow wire)   |
| Servo VCC     | 5V        | Power supply for servo (red wire)  |
| Servo GND     | GND       | Ground (brown wire)                |
| TM1637 VCC    | 5V        | Power supply for display           |
| TM1637 GND    | GND       | Ground                             |
| TM1637 CLK    | GPIO17    | Clock signal                       |
| TM1637 DIO    | GPIO16    | Data I/O signal                    |

## Configuration

Settings needed to run every task in this lab:

```python
# Blynk Configuration
BLYNK_TOKEN = "YOUR_BLYNK_AUTH_TOKEN"
BLYNK_API = "http://blynk.cloud/external/api"

# Wi-Fi Configuration
WIFI_SSID = "YOUR_SSID"
WIFI_PASS = "YOUR_PASSWORD"

# Pin Configuration
IR_PIN = 12
SERVO_PIN = 13
TM_CLK = 17
TM_DIO = 16

# Servo Configuration
SERVO_CLOSED = 0    # Closed position (degrees)
SERVO_OPEN = 90     # Open position (degrees)
AUTO_DELAY = 1      # Time to hold the gate open (seconds)
```

## Setup Instructions

### 1. Blynk Setup

1. Install the Blynk app (App Store or Google Play) and sign in or create an account.
2. Create a new project:
   - Project name: "Smart Gate Control"
   - Device: ESP32
   - Connection type: Wi-Fi
3. Copy the **Auth Token** emailed to you.
4. Add these widgets to the dashboard:
   - **Label** (V0) – IR sensor status ("Detected" / "Not Detected")
   - **Slider** (V1) – Manual servo control (0–180°)
   - **Value Display** (V2) – Detection counter
   - **Switch** (V3) – Automatic / Manual mode toggle

### 2. ESP32 Setup

1. Flash MicroPython onto the ESP32 (if not already done).
2. Wire the components per the diagram above.
3. Grab the display driver: `tm1637.py` ([GitHub](https://github.com/mcauser/micropython-tm1637)).
4. Fill in your credentials in `Lab3_Main.py`:
   ```python
   BLYNK_TOKEN = "YourAuthTokenFromEmail"
   WIFI_SSID = "YOUR_WIFI_SSID"
   WIFI_PASS = "YOUR_WIFI_PASSWORD"
   ```
5. Upload `Lab3_Main.py` and `tm1637.py` to the ESP32 via Thonny.
6. Reset the board (or run the script) and watch the serial monitor for the connection status.
7. Open Blynk and confirm the device comes online.

## Usage

### Blynk Dashboard

**Monitoring**
- **IR Status (V0)** – flips between "Detected" and "Not Detected" in real time.
- **Detection Counter (V2)** – running total of detection events, mirrored from the TM1637.

**Controls**
- **Servo Slider (V1)** – 0°–180°, only takes effect while manual mode is active.
- **Mode Switch (V3)** – OFF = automatic (IR drives the gate), ON = manual (slider drives the gate, IR ignored).

### Local Display (TM1637)

- Shows the running detection count, zero-padded (e.g. `0042`).
- Brightness is adjustable in code (0–7).

### System Behavior

**Automatic mode (default)**
1. IR sensor is polled continuously.
2. On a new detection:
   - Servo swings to `SERVO_OPEN` (90°).
   - Counter increments; TM1637 and Blynk (V2) both update.
   - IR status label (V0) shows "Detected".
3. After `AUTO_DELAY` seconds, the servo returns to `SERVO_CLOSED` (0°).
4. System is ready for the next detection.

**Manual mode**
1. Operator flips the mode switch (V3) on.
2. IR readings are ignored — no counting, no auto-open.
3. Servo position tracks the slider (V1) directly.
4. TM1637 holds its last counted value.

## Virtual Pin Map

| Virtual Pin | Type   | Direction | Description                                    |
| ----------- | ------ | --------- | ------------------------------------------------ |
| V0          | String | ESP → App | IR status ("Detected" / "Not Detected")         |
| V1          | Slider | App → ESP | Manual servo angle (0–180)                      |
| V2          | Value  | ESP → App | Detection counter                               |
| V3          | Switch | App → ESP | Mode select (0 = automatic, 1 = manual)         |

## Tasks and Checkpoints

### Task 1 — IR Sensor Monitoring (15 pts)

**Objective:** Read the IR sensor's digital output and reflect its status on Blynk, updating only when the state changes.

```python
from machine import Pin
import urequests as requests

ir = Pin(12, Pin.IN)

def send_ir_status(status):
    url = f"{BLYNK_API}/update?token={BLYNK_TOKEN}&V0={status}"
    try:
        r = requests.get(url)
        r.close()
    except:
        print("HTTP Error (IR)")
```

```python
# In main loop
current = ir.value()
if current == 0:
    send_ir_status("Detected")
else:
    send_ir_status("Not%20Detected")
```

**Evidence:** Screenshot of the IR status showing on Blynk.

![Task 1 - IR Sensor Status](./screenshot/task1.jpg)

---

### Task 2 — Blynk-Controlled Servo (15 pts)

**Objective:** Add a 0–180° Blynk slider that drives the servo, with the selected angle shown in the app.

```python
from machine import Pin, PWM
import urequests as requests

servo = PWM(Pin(13), freq=50)

def set_angle(angle):
    duty = int((angle / 180) * 102 + 26)
    servo.duty(duty)

def read_slider_v1():
    url = f"{BLYNK_API}/get?token={BLYNK_TOKEN}&v1"
    try:
        r = requests.get(url)
        value = int(str(r.text).strip('[]"'))
        r.close()
        return value
    except Exception as e:
        print("Failed to read slider:", e)
        return None
```

```python
# In main loop
angle = read_slider_v1()
if angle is not None and angle != last_angle:
    angle = max(0, min(180, angle))
    set_angle(angle)
    last_angle = angle
```

**Evidence:** Short video of the slider driving the servo.

[Task 2 - Servo Control Video](https://youtu.be/JnMRalt_NaY)

---

### Task 3 — Automatic IR Gate Operation (15 pts)

**Objective:** Open the gate automatically on a new IR detection, hold briefly, then close — firing once per new detection rather than repeatedly while the object stays in range.

```python
def auto_open_servo():
    print("Auto opening servo")
    set_angle(SERVO_OPEN)
    time.sleep(AUTO_DELAY)
    print("Closing servo")
    set_angle(SERVO_CLOSED)
```

```python
# In main loop
if not manual_override:
    current = ir.value()
    if current != prev_state:
        if current == 0:
            print("Detected")
            send_ir_status("Detected")

            # Increment counter
            ir_counter += 1
            display_counter(ir_counter)
            send_counter_v2(ir_counter)

            # Automatic servo
            auto_open_servo()
        else:
            send_ir_status("Not%20Detected")
        prev_state = current
```

The `current != prev_state` check is what keeps the gate from re-triggering while the same object is still sitting in the detection zone.

**Evidence:** Short video of the automatic open/close cycle.

[Task 3 - Automatic Gate Video](https://youtube.com/shorts/UL46Ju1LQi8)

---

### Task 4 — TM1637 Detection Counter (15 pts)

**Objective:** Count each new detection event and keep the TM1637 and Blynk's numeric widget in sync.

```python
import tm1637
from machine import Pin
import urequests as requests

tm = tm1637.TM1637(Pin(17), Pin(16))
tm.set_brightness(7)  # 0-7

def display_counter(value):
    try:
        tm.show_number(value)
    except Exception as e:
        print("TM1637 display error:", e)

def send_counter_v2(counter):
    url = f"{BLYNK_API}/update?token={BLYNK_TOKEN}&V2={counter}"
    try:
        r = requests.get(url)
        r.close()
    except:
        print("HTTP Error (Counter)")
```

```python
ir_counter = 0

# In IR detection handler
if current == 0:
    ir_counter += 1
    print("IR Count:", ir_counter)
    display_counter(ir_counter)
    send_counter_v2(ir_counter)
```

**Evidence:** Short video showing matching TM1637/Blynk counts.

[Task 4 - TM1637 Display](https://youtube.com/shorts/E_47fxhAMRg)

---

### Task 5 — Complete Smart Gate Integration (20 pts)

**Objective:** Merge Tasks 1–4 into a single program and dashboard, add a Blynk switch (V3) to pick Automatic vs. Manual mode, and keep IR status and the detection counter visible on Blynk at all times.

- **OFF (Automatic):** the IR sensor drives the gate, per Task 3.
- **ON (Manual):** IR input is ignored; the servo follows the Blynk slider (V1) instead, per Task 2.

```python
def read_manual_override_v3():
    """Read Blynk switch for manual override (0 = automatic, 1 = manual)"""
    url = f"{BLYNK_API}/get?token={BLYNK_TOKEN}&v3"
    try:
        r = requests.get(url)
        val = int(str(r.text).strip('[]"'))
        r.close()
        return val == 1  # True if manual override active
    except Exception as e:
        print("Failed to read manual override:", e)
        return False
```

```python
# In main loop
manual_override = read_manual_override_v3()

if not manual_override:
    # Automatic mode - IR sensor controls the servo
    current = ir.value()
    if current != prev_state:
        if current == 0:
            auto_open_servo()
        prev_state = current
else:
    # Manual override active - IR ignored, slider controls the servo
    prev_state = -1
    print("Manual override active - IR ignored")
```

Because the IR handler, servo control, counter, and TM1637 update all live in the same loop, this task is really the previous four running together behind a single mode switch — nothing new to build beyond the `manual_override` gate shown above.

**Evidence:** Video showing the system working in both modes.

[Task 5 - Manual Override Demo](https://youtube.com/shorts/_8cbKmmfn3Y?feature=share)

---

### Task 6 — Documentation and Demonstration (20 pts)

Submit a private GitHub repository containing:

- `Lab3_Main.py` and any required helper files (e.g. `tm1637.py`)
- A wiring diagram or clear wiring photo
- Wi-Fi and Blynk setup instructions, including the virtual pin mapping
- Usage instructions for each Blynk widget
- Screenshots of the completed Blynk dashboard
- A demonstration video

**Demo Video:** [YouTube Link](https://youtube.com/shorts/9V-JWfi_ZXU)

## Technical Features

### Key Implementation Highlights

1. **HTTP API Integration** — Blynk's HTTP API via `urequests`; polling-based reads of virtual pins, RESTful updates for status/counter.
2. **State Management** — `manual_override` for mode switching, `prev_state` for IR edge detection, `ir_counter` as a persistent count, `last_angle` to avoid redundant servo writes.
3. **PWM Servo Control** — 50 Hz signal, duty-cycle mapping across 0–180°, automatic open/close with a configurable delay.
4. **TM1637 Driver** — brightness control plus direct `show_number()` updates.
5. **Blynk Integration** — HTTP GET for reading slider/switch state, HTTP GET for pushing status/counter updates, full virtual pin mapping, mobile dashboard.
6. **Error Handling** — Wi-Fi connection timeout logic, try/except around every HTTP call, graceful degradation on API failure.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Blynk Cloud Server                     │
│                    (blynk.cloud/external/api)               │
└─────────────────────────────────────────────────────────────┘
                            ▲ │
                            │ │ HTTP API (urequests)
                            │ ▼
┌─────────────────────────────────────────────────────────────┐
│                         ESP32                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              MicroPython Runtime                     │   │
│  │  ┌────────────┐  ┌──────────┐  ┌─────────────┐       │   │
│  │  │ urequests  │  │ TM1637   │  │ Servo PWM   │       │   │
│  │  │ (HTTP API) │  │ Driver   │  │ Control     │       │   │
│  │  └────────────┘  └──────────┘  └─────────────┘       │   │
│  │  ┌──────────────────────────────────────────────┐    │   │
│  │  │         Main Control Logic                   │    │   │
│  │  │  - Auto/Manual Mode Polling                  │    │   │
│  │  │  - IR Detection Handler                      │    │   │
│  │  │  - Counter Management                        │    │   │
│  │  │  - HTTP API Read/Write Functions             │    │   │
│  │  └──────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
    ┌────────┐    ┌─────────┐    ┌────────┐    ┌─────────┐
    │   IR   │    │  Servo  │    │ TM1637 │    │  Blynk  │
    │ Sensor │    │  Motor  │    │Display │    │   App   │
    └────────┘    └─────────┘    └────────┘    └─────────┘
```

**Main components of `Lab3_Main.py`:**

- Wi-Fi connection setup
- Blynk HTTP API integration via `urequests`
- IR sensor read function
- PWM-based servo control
- TM1637 display update function
- Virtual pin read/write helpers
- Automatic gate control logic
- Manual override handling
- Main event loop

## Troubleshooting

1. **ESP32 won't connect to Blynk**
   - Confirm the auth token (check your email).
   - Double-check Wi-Fi credentials and confirm the ESP32 associated (serial monitor).
   - Confirm `blynk.cloud` is reachable from your network.

2. **Servo not moving**
   - Servos need 5V, not 3.3V — check the power rail.
   - Confirm the signal wire is on **GPIO13**.
   - Test with the manual slider first to isolate wiring vs. logic issues.
   - Verify the duty-cycle range (roughly 26–128 for SG90).

3. **IR sensor not detecting**
   - Adjust the sensitivity potentiometer on the module.
   - Confirm the onboard LED lights when an object is near.
   - Confirm the output is wired to **GPIO12**.
   - Probe with a multimeter — output should go LOW on detection.

4. **TM1637 not displaying numbers**
   - Confirm CLK is on **GPIO17** and DIO is on **GPIO16**.
   - Check the module's power requirement (3.3V or 5V, depending on the board).
   - Run a minimal display test to isolate driver issues.
   - Adjust brightness in code if the digits look faint.

5. **Counter not incrementing**
   - Make sure automatic mode is active (switch OFF on Blynk).
   - Confirm the IR sensor itself is working.
   - Add print statements inside the detection handler.
   - Verify `ir_counter` is actually being updated in that branch.

6. **Blynk widgets not updating**
   - Confirm the main loop is actually running and not stuck.
   - Double-check virtual pin numbers match the widget configuration.
   - Confirm the device shows "online" in the Blynk app.
   - Add a small delay (50–100ms) between API calls to avoid throttling.

## Submission and Academic Integrity

The demonstration video must show:

- Live IR sensor status displayed on Blynk
- Servo angle controlled using the Blynk slider
- Automatic gate opening and closing when an object is detected
- Matching detection counts on TM1637 and Blynk
- Automatic/Manual mode switching and manual override

All submitted work must be original. Do not share or copy another student's complete source code, and do not publish Wi-Fi passwords or Blynk authentication tokens in the repository.

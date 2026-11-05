import network, time, struct
from machine import Pin, ADC, I2C
from umqtt.simple import MQTTClient
import ujson

SSID = "Robotic WIFI"
PASSWORD = "rbtWIFI@2025"

BROKER = "broker.hivemq.com"
PORT = 1883
CLIENT_ID = b"esp32_lab4_gas"
TOPIC = b"/aupp/esp32/lab4/gas"
KEEPALIVE = 30

# --- MQ-5 ---
gas_adc = ADC(Pin(33))
gas_adc.atten(ADC.ATTN_11DB)
gas_adc.width(ADC.WIDTH_12BIT)
WINDOW = 5
samples = []

# --- I2C bus (shared) ---
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
MLX_ADDR = 0x5A
RTC_ADDR = 0x68
FEVER_THRESHOLD = 32.5
SEA_LEVEL_HPA = 1013.25

# ---------- MQ-5 ----------
def moving_average(value):
    samples.append(value)
    if len(samples) > WINDOW:
        samples.pop(0)
    return sum(samples) / len(samples)

def classify_gas(avg):
    if avg < 2100:
        return "SAFE"
    elif avg < 2600:
        return "WARNING"
    else:
        return "DANGER"

# ---------- MLX90614 ----------
def read_body_temp():
    data = i2c.readfrom_mem(MLX_ADDR, 0x07, 3)
    raw = data[0] | (data[1] << 8)
    return raw * 0.02 - 273.15

def fever_check(temp):
    return 1 if temp >= FEVER_THRESHOLD else 0

# ---------- BMP280 ----------
class BMP280:
    def __init__(self, i2c, addr):
        self.i2c = i2c
        self.addr = addr
        cal = i2c.readfrom_mem(addr, 0x88, 24)
        (self.T1, self.T2, self.T3,
         self.P1, self.P2, self.P3, self.P4, self.P5,
         self.P6, self.P7, self.P8, self.P9) = struct.unpack('<HhhHhhhhhhhh', cal)
        i2c.writeto_mem(addr, 0xF4, b'\x27')   # temp x1, press x1, normal mode
        time.sleep_ms(100)

    def read(self):
        d = self.i2c.readfrom_mem(self.addr, 0xF7, 6)
        adc_p = (d[0] << 12) | (d[1] << 4) | (d[2] >> 4)
        adc_t = (d[3] << 12) | (d[4] << 4) | (d[5] >> 4)

        v1 = (adc_t / 16384.0 - self.T1 / 1024.0) * self.T2
        v2 = ((adc_t / 131072.0 - self.T1 / 8192.0) ** 2) * self.T3
        t_fine = v1 + v2
        temp = t_fine / 5120.0

        v1 = t_fine / 2.0 - 64000.0
        v2 = v1 * v1 * self.P6 / 32768.0
        v2 = v2 + v1 * self.P5 * 2.0
        v2 = v2 / 4.0 + self.P4 * 65536.0
        v1 = (self.P3 * v1 * v1 / 524288.0 + self.P2 * v1) / 524288.0
        v1 = (1.0 + v1 / 32768.0) * self.P1
        p = 1048576.0 - adc_p
        p = (p - v2 / 4096.0) * 6250.0 / v1
        v1 = self.P9 * p * p / 2147483648.0
        v2 = p * self.P8 / 32768.0
        p = p + (v1 + v2 + self.P7) / 16.0

        pressure = p / 100.0                                   # hPa
        altitude = 44330.0 * (1.0 - (pressure / SEA_LEVEL_HPA) ** (1 / 5.255))
        return temp, pressure, altitude

# ---------- DS3231 ----------
def bcd2dec(b):
    return (b >> 4) * 10 + (b & 0x0F)

def dec2bcd(v):
    return ((v // 10) << 4) | (v % 10)

def set_rtc(year, month, day, weekday, hour, minute, second):
    i2c.writeto_mem(RTC_ADDR, 0x00, bytes([
        dec2bcd(second), dec2bcd(minute), dec2bcd(hour),
        dec2bcd(weekday), dec2bcd(day), dec2bcd(month), dec2bcd(year - 2000)]))

def read_timestamp():
    d = i2c.readfrom_mem(RTC_ADDR, 0x00, 7)
    sec = bcd2dec(d[0] & 0x7F)
    mn = bcd2dec(d[1])
    hr = bcd2dec(d[2] & 0x3F)
    day = bcd2dec(d[4])
    mon = bcd2dec(d[5] & 0x1F)
    yr = 2000 + bcd2dec(d[6])
    return "%04d-%02d-%02d %02d:%02d:%02d" % (yr, mon, day, hr, mn, sec)

# ---------- Network ----------
def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(SSID, PASSWORD)
        t0 = time.ticks_ms()
        while not wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), t0) > 20000:
                raise RuntimeError("Wi-Fi connect timeout")
            time.sleep(0.3)
    print("WiFi OK:", wlan.ifconfig())
    return wlan

def make_client():
    return MQTTClient(client_id=CLIENT_ID, server=BROKER, port=PORT, keepalive=KEEPALIVE)

def connect_mqtt(c):
    time.sleep(0.5)
    c.connect()
    print("MQTT connected")

def main():
    found = i2c.scan()
    print("I2C devices:", [hex(a) for a in found])

    # Run ONCE to set the clock (use current date/time, weekday Mon=1..Sun=7), then delete/comment:
    # set_rtc(2026, 11, 5, 4, 16, 30, 0)

    bmp_addr = 0x76 if 0x76 in found else 0x77
    bmp = BMP280(i2c, bmp_addr)

    wifi_connect()
    client = make_client()
    while True:
        try:
            connect_mqtt(client)
            while True:
                raw = gas_adc.read()
                avg = moving_average(raw)
                risk = classify_gas(avg)

                body_temp = round(read_body_temp(), 2)
                fever = fever_check(body_temp)

                room_temp, pressure, altitude = bmp.read()
                ts = read_timestamp()

                print("Raw:", raw, "| Avg:", round(avg, 1), "| Risk:", risk,
                      "| Temp:", body_temp, "| Fever:", fever,
                      "| P:", round(pressure, 2), "| Alt:", round(altitude, 1), "|", ts)

                payload = ujson.dumps({
                    "gas_avg": round(avg, 1),
                    "risk_level": risk,
                    "body_temp": body_temp,
                    "fever_flag": fever,
                    "pressure": round(pressure, 2),
                    "altitude": round(altitude, 1),
                    "timestamp": ts
                })
                client.publish(TOPIC, payload)
                print("Sent:", payload)
                time.sleep(1)
        except OSError as e:
            print("MQTT error:", e)
            try:
                client.close()
            except:
                pass
            print("Retrying MQTT in 3s...")
            time.sleep(3)

main()
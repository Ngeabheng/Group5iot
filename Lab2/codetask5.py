import network
import socket
import time
import dht

from machine import Pin, SoftI2C, time_pulse_us, PWM
from machine_i2c_lcd import I2cLcd


# ==========================================
# WIFI SETUP
# ==========================================

ssid = "Robotic WIFI"
password = "rbtWIFI@2025"


# ==========================================
# SENSOR PIN SETUP
# ==========================================

# DHT11
dht_sensor = dht.DHT11(Pin(33))

# HC-SR04
trig = Pin(27, Pin.OUT)
echo = Pin(26, Pin.IN)


# ==========================================
# SERVO SETUP
# ==========================================

servo = PWM(Pin(13), freq=50)

servo_angle = 90


# ==========================================
# LCD SETUP
# ==========================================

I2C_ADDR = 0x27

i2c = SoftI2C(
    sda=Pin(21),
    scl=Pin(22),
    freq=400000
)

lcd = I2cLcd(
    i2c,
    I2C_ADDR,
    2,
    16
)

lcd.clear()

lcd.putstr("IoT LAB")
lcd.move_to(0, 1)
lcd.putstr("Task 2")

time.sleep(2)

lcd.clear()


# ==========================================
# TASK 2: SHOW STATES
# ==========================================

show_distance = False
show_temperature = False


# ==========================================
# READ DHT11
# ==========================================

def read_dht11():

    try:

        dht_sensor.measure()

        temperature = dht_sensor.temperature()
        humidity = dht_sensor.humidity()

        return temperature, humidity

    except Exception as error:

        print("DHT11 error:", error)

        return None, None


# ==========================================
# READ ULTRASONIC DISTANCE
# ==========================================

def read_distance():

    try:

        # Trigger OFF
        trig.value(0)
        time.sleep_us(2)

        # Trigger ON
        trig.value(1)
        time.sleep_us(10)

        # Trigger OFF
        trig.value(0)

        # Measure ECHO pulse
        duration = time_pulse_us(
            echo,
            1,
            30000
        )

        if duration < 0:

            return None

        # Convert to centimetres
        distance = (
            duration * 0.0343
        ) / 2

        return distance

    except Exception as error:

        print(
            "Ultrasonic error:",
            error
        )

        return None


# ==========================================
# TASK 2: CLEAR LCD ROW
# ==========================================

def clear_lcd_row(row):

    lcd.move_to(0, row)

    lcd.putstr(
        "                "
    )


# ==========================================
# TASK 2: DISPLAY DISTANCE
# ==========================================

def display_distance(distance):

    lcd.move_to(0, 0)

    if distance is None:

        lcd.putstr(
            "Distance Error"
        )

    else:

        lcd.putstr(
            "Dist: {:.1f} cm".format(
                distance
            )
        )


# ==========================================
# TASK 2: DISPLAY TEMPERATURE
# ==========================================

def display_temperature(temperature):

    lcd.move_to(0, 1)

    if temperature is None:

        lcd.putstr(
            "Temp Error"
        )

    else:

        lcd.putstr(
            "Temp: {} C".format(
                temperature
            )
        )


# ==========================================
# TASK 3: MOVE SERVO
# ==========================================

def move_servo(angle):

    # Keep angle between 0 and 180
    if angle < 0:

        angle = 0

    if angle > 180:

        angle = 180

    # Servo PWM duty range
    duty_min = 40
    duty_max = 115

    # Convert angle to PWM duty
    duty = int(
        duty_min
        + (angle / 180)
        * (duty_max - duty_min)
    )

    # Send duty to servo
    servo.duty(duty)

    print(
        "Servo angle:",
        angle
    )

    print(
        "PWM duty:",
        duty
    )


# ==========================================
# INITIAL SERVO POSITION
# ==========================================

move_servo(servo_angle)


# ==========================================
# TASK 4: URL DECODE
# ==========================================

def url_decode(text):

    result = bytearray()

    index = 0

    while index < len(text):

        if text[index] == "+":

            # Convert + to space
            result.append(32)

            index += 1

        elif text[index] == "%":

            try:

                hex_value = text[
                    index + 1:index + 3
                ]

                result.append(
                    int(hex_value, 16)
                )

                index += 3

            except:

                index += 1

        else:

            result.extend(
                text[index].encode()
            )

            index += 1

    try:

        return result.decode(
            "utf-8"
        )

    except:

        return str(result)


# ==========================================
# TASK 4: DISPLAY MESSAGE
# ==========================================

def display_message(message):

    lcd.clear()

    if len(message) < 16:

        lcd.putstr(message)

    else:

        lcd.scroll_text(message)


# ==========================================
# CREATE FINAL WEBPAGE
# ==========================================

def create_webpage(
    temperature,
    humidity,
    distance,
    show_distance,
    show_temperature,
    angle
):

    # --------------------------------------
    # Temperature
    # --------------------------------------

    if temperature is None:

        temperature_text = "Sensor error"

    else:

        temperature_text = (
            str(temperature)
            + " &deg;C"
        )


    # --------------------------------------
    # Humidity
    # --------------------------------------

    if humidity is None:

        humidity_text = "Sensor error"

    else:

        humidity_text = (
            str(humidity)
            + " %"
        )


    # --------------------------------------
    # Distance
    # --------------------------------------

    if distance is None:

        distance_text = "Out of range"

    else:

        distance_text = (
            "{:.1f} cm".format(
                distance
            )
        )


    # --------------------------------------
    # Distance Button
    # --------------------------------------

    if show_distance:

        distance_button_text = (
            "Hide Distance"
        )

        distance_button_class = (
            "hide-button"
        )

    else:

        distance_button_text = (
            "Show Distance"
        )

        distance_button_class = (
            "show-button"
        )


    # --------------------------------------
    # Temperature Button
    # --------------------------------------

    if show_temperature:

        temperature_button_text = (
            "Hide Temperature"
        )

        temperature_button_class = (
            "hide-button"
        )

    else:

        temperature_button_text = (
            "Show Temperature"
        )

        temperature_button_class = (
            "show-button"
        )


    # ======================================
    # HTML
    # ======================================

    html = """

<!DOCTYPE html>

<html>

<head>

    <title>
        ESP32 IoT Dashboard
    </title>

    <meta
        name="viewport"
        content="width=device-width,
                 initial-scale=1"
    >


    <style>

        body {

            font-family: Arial;

            text-align: center;

            background-color: #f2f2f2;

            margin: 0;

            padding: 20px;
        }


        h1 {

            color: #333;
        }


        .card {

            background-color: white;

            width: 80%;

            max-width: 500px;

            margin: 20px auto;

            padding: 20px;

            border-radius: 10px;

            box-shadow:
                0 2px 8px
                rgba(0, 0, 0, 0.2);
        }


        .value {

            color: #2196F3;

            font-size: 24px;

            font-weight: bold;
        }


        button {

            border: none;

            color: white;

            padding: 12px 20px;

            margin: 5px;

            border-radius: 8px;

            font-size: 16px;

            cursor: pointer;
        }


        .show-button {

            background-color: #4CAF50;
        }


        .hide-button {

            background-color: #f44336;
        }


        input[type="range"] {

            width: 280px;

            margin-top: 20px;
        }


        .angle {

            color: #007bff;

            font-size: 32px;

            font-weight: bold;
        }


        input[type="text"] {

            width: 80%;

            max-width: 260px;

            padding: 12px;

            font-size: 16px;

            border: 1px solid #cccccc;

            border-radius: 6px;

            margin-bottom: 15px;
        }


        .send-button {

            background-color: #0066cc;
        }


        #status {

            color: #28a745;

            margin-top: 15px;

            font-weight: bold;
        }

    </style>


    <script>

        function sendMessage() {

            var message =
                document.getElementById(
                    "message"
                ).value;


            if (message == "") {

                document.getElementById(
                    "status"
                ).innerHTML =
                    "Please enter a message.";

                return;
            }


            fetch(
                "/message?text=" +
                encodeURIComponent(message)
            );


            document.getElementById(
                "status"
            ).innerHTML =
                "Message sent to LCD";
        }

    </script>

</head>


<body>


    <h1>
        ESP32 IoT Dashboard
    </h1>


    <!-- SENSOR VALUES -->

    <div class="card">

        <h2>
            Temperature
        </h2>

        <p class="value">
            TEMPERATURE_VALUE
        </p>


        <h2>
            Humidity
        </h2>

        <p class="value">
            HUMIDITY_VALUE
        </p>


        <h2>
            Distance
        </h2>

        <p class="value">
            DISTANCE_VALUE
        </p>

    </div>


    <!-- LCD SENSOR CONTROL -->

    <div class="card">

        <h2>
            LCD Sensor Control
        </h2>


        <a href="/?distance=toggle">

            <button
                class="DISTANCE_BUTTON_CLASS"
            >
                DISTANCE_BUTTON_TEXT
            </button>

        </a>


        <a href="/?temperature=toggle">

            <button
                class="TEMPERATURE_BUTTON_CLASS"
            >
                TEMPERATURE_BUTTON_TEXT
            </button>

        </a>

    </div>


    <!-- SERVO CONTROL -->

    <div class="card">

        <h2>
            Servo Control
        </h2>


        <p
            class="angle"
            id="angle-value"
        >
            SERVO_ANGLE
        </p>


        <input
            type="range"
            min="0"
            max="180"
            value="SERVO_ANGLE"

            oninput="
                document.getElementById(
                    'angle-value'
                ).innerHTML = this.value
            "

            onchange="
                fetch(
                    '/servo?angle='
                    + this.value
                )
            "
        >


        <p>
            Move the slider to
            control the servo.
        </p>

    </div>


    <!-- CUSTOM LCD TEXT -->

    <div class="card">

        <h2>
            Send Text to LCD
        </h2>


        <input
            type="text"
            id="message"
            placeholder="Enter your message"
        >


        <br>


        <button
            class="send-button"
            onclick="sendMessage()"
        >
            Send
        </button>


        <p id="status"></p>

    </div>


</body>

</html>

"""


    # ======================================
    # REPLACE VALUES
    # ======================================

    html = html.replace(
        "TEMPERATURE_VALUE",
        temperature_text
    )


    html = html.replace(
        "HUMIDITY_VALUE",
        humidity_text
    )


    html = html.replace(
        "DISTANCE_VALUE",
        distance_text
    )


    html = html.replace(
        "DISTANCE_BUTTON_TEXT",
        distance_button_text
    )


    html = html.replace(
        "DISTANCE_BUTTON_CLASS",
        distance_button_class
    )


    html = html.replace(
        "TEMPERATURE_BUTTON_TEXT",
        temperature_button_text
    )


    html = html.replace(
        "TEMPERATURE_BUTTON_CLASS",
        temperature_button_class
    )


    html = html.replace(
        "SERVO_ANGLE",
        str(angle)
    )


    return html


# ==========================================
# CONNECT TO WIFI
# ==========================================

wifi = network.WLAN(
    network.STA_IF
)

wifi.active(True)


if not wifi.isconnected():

    print(
        "Connecting to Wi-Fi..."
    )

    wifi.connect(
        ssid,
        password
    )


    while not wifi.isconnected():

        print(
            ".",
            end=""
        )

        time.sleep(1)


ip = wifi.ifconfig()[0]


print()

print(
    "Wi-Fi connected!"
)

print(
    "ESP32 IP address:",
    ip
)

print(
    "Open this address:"
)

print(
    "http://" + ip
)


# ==========================================
# START WEB SERVER
# ==========================================

address = socket.getaddrinfo(
    "0.0.0.0",
    80
)[0][-1]


server = socket.socket()


server.setsockopt(
    socket.SOL_SOCKET,
    socket.SO_REUSEADDR,
    1
)


server.bind(address)

server.listen(1)


print(
    "Web server is running..."
)


# ==========================================
# MAIN PROGRAM
# ==========================================

while True:

    client = None

    try:

        client, client_address = (
            server.accept()
        )


        print(
            "Browser connected:",
            client_address
        )


        # ----------------------------------
        # RECEIVE REQUEST
        # ----------------------------------

        request = client.recv(
            1024
        )

        request = request.decode()


        request_line = request.split(
            "\r\n"
        )[0]


        print(
            "Request:",
            request_line
        )


        # ==================================
        # READ SENSORS
        # ==================================

        temperature, humidity = (
            read_dht11()
        )

        distance = read_distance()


        print(
            "Temperature:",
            temperature
        )

        print(
            "Humidity:",
            humidity
        )

        print(
            "Distance:",
            distance
        )


        # ==================================
        # TASK 4: CUSTOM MESSAGE
        # ==================================

        if (
            "GET /message?text="
            in request_line
        ):

            start = (
                request_line.find(
                    "/message?text="
                )
                + len(
                    "/message?text="
                )
            )


            end = request_line.find(
                " ",
                start
            )


            encoded_message = (
                request_line[
                    start:end
                ]
            )


            message = url_decode(
                encoded_message
            )


            print(
                "Message:",
                message
            )


            # Respond BEFORE scrolling

            client.send(
                "HTTP/1.1 204 No Content\r\n"
            )

            client.send(
                "Connection: close\r\n"
            )

            client.send(
                "\r\n"
            )


            client.close()

            client = None


            # Display or scroll

            display_message(
                message
            )


        # ==================================
        # TASK 3: SERVO
        # ==================================

        elif (
            "GET /servo?angle="
            in request_line
        ):

            try:

                start = (
                    request_line.find(
                        "/servo?angle="
                    )
                    + len(
                        "/servo?angle="
                    )
                )


                end = request_line.find(
                    " ",
                    start
                )


                angle_text = (
                    request_line[
                        start:end
                    ]
                )


                servo_angle = int(
                    angle_text
                )


                move_servo(
                    servo_angle
                )


                client.send(
                    "HTTP/1.1 204 No Content\r\n"
                )

                client.send(
                    "Connection: close\r\n"
                )

                client.send(
                    "\r\n"
                )


            except Exception as error:

                print(
                    "Servo control error:",
                    error
                )


        # ==================================
        # TASK 2: DISTANCE BUTTON
        # ==================================

        elif (
            "/?distance=toggle"
            in request_line
        ):

            show_distance = (
                not show_distance
            )


            if show_distance:

                display_distance(
                    distance
                )

                print(
                    "Distance shown on LCD"
                )

            else:

                clear_lcd_row(0)

                print(
                    "Distance hidden"
                )


        # ==================================
        # TASK 2: TEMPERATURE BUTTON
        # ==================================

        elif (
            "/?temperature=toggle"
            in request_line
        ):

            show_temperature = (
                not show_temperature
            )


            if show_temperature:

                display_temperature(
                    temperature
                )

                print(
                    "Temperature shown on LCD"
                )

            else:

                clear_lcd_row(1)

                print(
                    "Temperature hidden"
                )


        # ==================================
        # UPDATE SHOWN SENSOR VALUES
        # ==================================

        if show_distance:

            display_distance(
                distance
            )


        if show_temperature:

            display_temperature(
                temperature
            )


        # ==================================
        # SEND MAIN WEBPAGE
        # ==================================

        if client is not None:

            webpage = create_webpage(
                temperature,
                humidity,
                distance,
                show_distance,
                show_temperature,
                servo_angle
            )


            client.send(
                "HTTP/1.1 200 OK\r\n"
            )

            client.send(
                "Content-Type: text/html\r\n"
            )

            client.send(
                "Connection: close\r\n"
            )

            client.send(
                "\r\n"
            )

            client.sendall(
                webpage
            )


    except Exception as error:

        print(
            "Server error:",
            error
        )


    finally:

        if client is not None:

            client.close()
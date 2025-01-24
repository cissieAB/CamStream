from flask import Flask, Response, render_template
from turbo_flask import Turbo

import threading
import time
import io
import cv2
from picamera2 import Picamera2

from pi_therm_cam import pithermalcam

# For the sensors
from mpu6050 import mpu6050
import bme280   #RPi.bme280
import smbus
import smbus2

app = Flask(__name__)
turbo = Turbo(app)

# Global variables for HD and Thermal camera frames
hd_output_frame = None
thermal_output_frame = None
hd_lock = threading.Lock()
thermal_lock = threading.Lock()

# Define the desired crop dimensions for HD camera
#CROP_LEFT = 294
#CROP_RIGHT = 176
CROP_TOP = 198
CROP_BOTTOM = 152
CROP_LEFT = 176
CROP_RIGHT = 294

mpu6050 = mpu6050(0x68, bus=5)

def celsius_to_fahrenheit(celsius):
    return (celsius * 9/5) + 32

@app.context_processor
def capture_mpu6050():
    #global mpu6050

    try:
        # Read the accelerometer values
        accelerometer_data = mpu6050.get_accel_data()

        # Read the gyroscope values
        gyroscope_data = mpu6050.get_gyro_data()

        # Read temp
        temperature = mpu6050.get_temp()

        return {'accelerometer': str(accelerometer_data),
                'gyroscope': str(gyroscope_data),
                }
    except KeyboardInterrupt:
        print('Program stopped')
    except Exception as e:
        print('An unexpected error occurred:', str(e))

@app.context_processor
def capture_bme280():
    global address, bus, calibration_params

    # BME280 sensor address (default address)
    address = 0x76

    # Initialize I2C bus
    bus = smbus2.SMBus(6)

    # Load calibration parameters
    calibration_params = bme280.load_calibration_params(bus, address)

    try:
        # Read sensor data
        data = bme280.sample(bus, address, calibration_params)

        # Extract temperature, pressure, and humidity
        temperature_celsius = data.temperature
        pressure = data.pressure
        humidity = data.humidity

        # Convert temperature to Fahrenheit
        temperature_fahrenheit = celsius_to_fahrenheit(temperature_celsius)

        return {'temp': str(round(temperature_fahrenheit,2)),
                'pressure': str(round(pressure,2)),
                'humidity': str(round(humidity,2))
                }
    except KeyboardInterrupt:
        print('Program stopped')
    except Exception as e:
        print('An unexpected error occurred:', str(e))

# HD Camera Thread and Functionality
def capture_hd_frames():
    global hd_output_frame, hd_lock
    picam2_hd = Picamera2()
    config_hd = picam2_hd.create_preview_configuration(main={"size": (1270, 950)})  # Set capture size to 1270x950
    picam2_hd.configure(config_hd)
    picam2_hd.start()

    while True:
        image_hd = picam2_hd.capture_array()

        # Crop the image
        cropped_hd_image = image_hd[CROP_TOP:-CROP_BOTTOM, CROP_LEFT:-CROP_RIGHT]

        # Convert to RGB for compatibility with OpenCV
        cropped_hd_image = cv2.cvtColor(cropped_hd_image, cv2.COLOR_BGR2RGB)

        with hd_lock:
            hd_output_frame = cropped_hd_image.copy()

# Thermal Camera Thread and Functionality
def pull_images():
    global thermal_output_frame, thermal_lock
    thermcam = pithermalcam(output_folder='/home/pi/pithermalcam/saved_snapshots/')
    time.sleep(0.01)

    while True:
        current_frame = thermcam.update_image_frame()
        if current_frame is not None:
            with thermal_lock:
                thermal_output_frame = current_frame.copy()

# Flask Routes
@app.route("/")
def index():
    return render_template("index.html")

def generate():
    global hd_output_frame, thermal_output_frame, hd_lock, thermal_lock
    while True:
        with hd_lock:
            hd_frame = hd_output_frame.copy() if hd_output_frame is not None else None
        with thermal_lock:
            thermal_frame = thermal_output_frame.copy() if thermal_output_frame is not None else None

        if hd_frame is None or thermal_frame is None:
            continue

        hd_frame = cv2.resize(hd_frame, (640, 480))
        thermal_frame = cv2.resize(thermal_frame, (640, 480))

        # Combine frames horizontally
        combined_frame = cv2.hconcat([hd_frame, thermal_frame])

        # Encode combined frame
        (flag, encoded_image) = cv2.imencode(".jpg", combined_frame)
        if not flag:
            continue

        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encoded_image) + b'\r\n')
        time.sleep(0.01)

@app.route("/video_feed")
def video_feed():
    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.before_first_request
def before_first_request():
    threading.Thread(target=update_sensors).start()

def update_sensors():
    with app.app_context():
        while True:
            time.sleep(5)
            turbo.push(turbo.replace(render_template('sensors.html'), 'sensors'))

if __name__ == '__main__':
    # Start HD camera thread
    hd_thread = threading.Thread(target=capture_hd_frames)
    hd_thread.daemon = True
    hd_thread.start()

    # Start Thermal camera thread
    thermal_thread = threading.Thread(target=pull_images)
    thermal_thread.daemon = True
    thermal_thread.start()

    #Start sensors thread
    bme280_thread = threading.Thread(target=capture_bme280)
    bme280_thread.daemon = True
    bme280_thread.start()
    mpu6050_thread = threading.Thread(target=capture_mpu6050)
    mpu6050_thread.daemon = True
    mpu6050_thread.start()

    # Run Flask app
    app.run(host='0.0.0.0', port=8000, debug=True, threaded=True, use_reloader=False)

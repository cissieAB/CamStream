"The receiver side backend APIs."

import time
import json
import cv2
import numpy as np
import requests


from flask import Flask, render_template, Response

app = Flask(__name__)

# TODO: Set your RTSP stream URL (from an IP camera, another device, etc.)
# RTSP_URL = "rtsp://your_rtsp_stream_here"

# TODO: URL of the Raspberry Pi's processed thermal image (assuming it's served via HTTP)
THERMAL_IMAGE_URL = "http://127.0.0.1:8083/raw_frame"  # the emulator address for now

# Open RTSP stream
# cap = cv2.VideoCapture(RTSP_URL)


def get_thermal_uint8_array(raw_data, min_val, max_val):
    """Trasfer the numpy thermal data to an unit8 image array."""
    if max_val <= min_val:
        raise ValueError("max_val should be greater than min_val")
        exit(1)

    clipped_data = np.clip(raw_data, min_val, max_val)
    scaled_data = np.uint8((clipped_data - min_val) / (max_val - min_val) * 255).reshape(24, 32)
    flipped_data = cv2.flip(scaled_data, 1)    # Flip on the low resolution data
    return flipped_data


def fetch_thermal_frame():
    """Continuously listen to the SSE stream and yield thermal frames."""
    try:
        with requests.get(THERMAL_IMAGE_URL, stream=True, timeout=1) as response:
            print("Connected to thermal SSE stream.")

            for line in response.iter_lines():
                if line:
                    line = line.decode("utf-8").strip()

                    # Only process lines starting with "data: "
                    if line.startswith("data: "):
                        json_text = line[6:].strip()  # Remove "data: " prefix
                        try:
                            data = json.loads(json_text)  # Parse JSON
                            temperature_data = np.array(data["temperature_data"])
                            # print(temperature_data)
                            timestamp = data["timestamp"]

                            print(f"Received thermal frame at {timestamp}, shape: {temperature_data.shape}")
                            yield temperature_data  # Yield the NumPy array
                        except json.JSONDecodeError as e:
                            print("Error parsing JSON:", e, "| Raw data:", json_text)

    except requests.exceptions.RequestException as e:
        print("Error connecting to SSE stream:", e)


def process_thermal_frame(f, width=640, height=480):
    "Rescale and colormap the uint8 thermal image array."

    # TODO: width & height checkup. Match the 4:3 ratio.

    # Update the interpolation here
    resized_frame = cv2.resize(f, (width, height), interpolation=cv2.INTER_CUBIC)
    # Update the colormap here
    image = cv2.applyColorMap(resized_frame, cv2.COLORMAP_JET)
    print("get processed thermal image")
    return image


def generate_frames():

    while True:
        # Place holder for the combined frame
        combined_frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)

        # TODO: Placeholder for the RSTP HD camera feed.

        # Get the thermal image from Raspberry Pi
        thermal_frame = np.array(list(fetch_thermal_frame()))
        if thermal_frame is not None:
            # Resize the thermal image to match the video stream size
            thermal_img = process_thermal_frame(
                get_thermal_uint8_array(thermal_frame, min_val=10, max_val=65))

            # # Apply overlay (blend two images with some transparency)
            # alpha = 0.4  # Transparency factor for thermal overlay
            # frame = cv2.addWeighted(frame, 1 - alpha, thermal_img, alpha, 0)
            combined_frame = thermal_img

        # Encode the final frame to JPEG
        _, buffer = cv2.imencode('.jpg', combined_frame)
        yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

        time.sleep(1)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return render_template('index.html')

# @app.route('/start', methods=['POST'])
# def start_processing():
#     return jsonify({"message": "Processing started"}), 200

# @app.route('/stop', methods=['POST'])
# def stop_processing():
#     return jsonify({"message": "Processing stopped"}), 200

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)

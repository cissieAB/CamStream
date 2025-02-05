"The receiver side backend APIs."

import time
import io
import threading

import cv2
import numpy as np

import socketio

from flask import Flask, render_template, Response, send_file

app = Flask(__name__)
sio = socketio.Client()

# TODO: Set your RTSP stream URL (from an IP camera, another device, etc.)
# RTSP_URL = "rtsp://your_rtsp_stream_here"
# Open RTSP stream
# cap = cv2.VideoCapture(RTSP_URL)

# TODO: URL of the Raspberry Pi's thermal frame.
#       Now it's the emulator address.
SIO_THERMAL_FRAME_URL = "http://127.0.0.1:8083"  # the emulator address for now

# Need to match the real Socket name.
SIO_API_NAME = "request_thermal"

latest_thermal_raw = np.zeros((24, 32), dtype=np.float32)

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# SocketIO endpoints
#
@sio.on("connect")
def on_connect():
    """Handle WebSocket connection."""
    print(f"*socketio: Connected to {SIO_THERMAL_FRAME_URL}\n")
    sio.emit(SIO_API_NAME)  # If required to trigger thermal frame sending

@sio.on("disconnect")
def on_disconnect():
    """Handle WebSocket disconnection."""
    print("*socketio: Disconnected from thermal data server.")

@sio.on("thermal_data")
def receive_thermal(data):
    """Receive raw thermal data from WebSocket."""
    global latest_thermal_raw

    if not isinstance(data, dict) or "data" not in data:
        print("**socketio: Error: Unexpected thermal data format")
        return

    try:
        raw_bytes = data["data"]
        timestamp = data["timestamp"]   # TODO: deal with timestamp

        if isinstance(raw_bytes, str):
            raw_bytes = raw_bytes.encode("latin1")  # Convert string to bytes

        buf = io.BytesIO(raw_bytes)
        thermal_array = np.load(buf)

        latest_thermal_raw = thermal_array.reshape((24, 32))
        # print(f"Received thermal data at {timestamp}:", latest_thermal_raw[:10])

    except Exception as e:
        print(f"**Error processing thermal data: {e}")


def connect_ws():
    """Connect to the WebSocket server."""
    while True:
        try:
            sio.connect(SIO_THERMAL_FRAME_URL, transports=['websocket'])
            print("SocketIO connection established.")
            break
        except Exception as e:
            print(f"WebSocket connection failed, retrying in 5 seconds: {e}")
            time.sleep(5)


# Run WebSocket connection in the background
threading.Thread(target=connect_ws, daemon=True).start()

# SocketIO endpoints
# -------------------------------------------------------------


def get_thermal_uint8(raw_data, min_val, max_val, target_shape=(24, 32)):
    """Scale the 2D np.float32 raw thermal array to an unit8 flip it."""
    if max_val <= min_val:
        raise ValueError("max_val should be greater than min_val")

    # Reshape if data is 1D
    if raw_data.ndim == 1:
        expected_size = target_shape[0] * target_shape[1]
        if raw_data.size != expected_size:
            raise ValueError(f"Expected {expected_size} elements but got {raw_data.size}")
        raw_data = raw_data.reshape(target_shape)

    clipped_data = np.clip(raw_data, min_val, max_val)
    scaled_data = np.uint8((clipped_data - min_val) / (max_val - min_val) * 255)
    flipped_data = cv2.flip(scaled_data, 1)    # Flip on the low resolution data
    return flipped_data


def process_thermal_frame(f, width=640, height=480):
    """Upscale the unit8 thermal frame to the desired size and apply a colormap."""

    # TODO: width & height checkup. Match the 4:3 ratio.

    # Update the interpolation here
    resized_frame = cv2.resize(f, (width, height), interpolation=cv2.INTER_CUBIC)
    # Update the colormap here
    image = cv2.applyColorMap(resized_frame, cv2.COLORMAP_JET)
    print(f"[{time.time()}] Get processed thermal image")
    return image


def generate_frames():
    """Generate frames to include both thermal and HD feed."""
    while True:
        # Place holder for the combined frame
        combined_frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)

        # TODO: Placeholder for the RSTP HD camera feed.

        # Get the raw thermal data from Raspberry Pi or the emulator.
        raw_thermal_min = np.min(latest_thermal_raw)
        raw_thermal_max = np.max(latest_thermal_raw)
        if raw_thermal_min == 0 and raw_thermal_max == 0:
            print("No valid thermal data received yet.")
            time.sleep(1)
            continue

        # TODO: explore caching machenism here so we dot need to process every raw thermal
        #       frame. Also if we do not receive any frame, we can use the cached one.
        thermal_img = process_thermal_frame(
            get_thermal_uint8(latest_thermal_raw, min_val=10, max_val=65))

        # # Apply overlay (blend two images with some transparency)
        # alpha = 0.4  # Transparency factor for thermal overlay
        # frame = cv2.addWeighted(frame, 1 - alpha, thermal_img, alpha, 0)
        combined_frame = thermal_img

        # Encode the final frame to JPEG
        _, buffer = cv2.imencode('.jpg', combined_frame)
        yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')


@app.route('/video_feed')
def video_feed():
    """Serve the GUI "video_field" endpoint."""
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/display_image')
def display_image():
    """Serve the demo image."""
    return send_file("./images/demo.jpeg", mimetype='image/jpeg')

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)



from flask import Flask, render_template, Response
from flask_socketio import SocketIO, emit
import threading
import cv2
import numpy as np
from picamera2 import Picamera2
from pithermalcam import pithermalcam

app = Flask(__name__)
socketio = SocketIO(app)

# Global variables for HD and Thermal camera frames
hd_output_frame = None
thermal_output_frame = None
hd_lock = threading.Lock()
thermal_lock = threading.Lock()

# HD Camera Thread
def capture_hd_frames():
    global hd_output_frame, hd_lock
    picam2_hd = Picamera2()
    config_hd = picam2_hd.create_preview_configuration(main={"size": (640, 480)})
    picam2_hd.configure(config_hd)
    picam2_hd.start()

    while True:
        image_hd = picam2_hd.capture_array()
        with hd_lock:
            hd_output_frame = cv2.cvtColor(image_hd, cv2.COLOR_BGR2RGB)

# Thermal Camera Thread
def capture_thermal_frames():
    global thermal_output_frame, thermal_lock
    thermcam = pithermalcam(output_folder='/home/pi/pithermalcam/saved_snapshots/')
    while True:
        frame = thermcam.update_image_frame()
        if frame is not None:
            with thermal_lock:
                thermal_output_frame = frame.copy()

# Flask Routes
@app.route("/")
def index():
    return render_template("index.html")

@socketio.on('message')
def handle_message(message):
    emit('message', message, broadcast=True)

def generate_hd():
    global hd_output_frame, hd_lock
    while True:
        with hd_lock:
            frame = hd_output_frame.copy() if hd_output_frame is not None else None
        if frame is None:
            continue
        (flag, encoded_image) = cv2.imencode(".jpg", frame)
        if flag:
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encoded_image) + b'\r\n')

def generate_thermal():
    global thermal_output_frame, thermal_lock
    while True:
        with thermal_lock:
            frame = thermal_output_frame.copy() if thermal_output_frame is not None else None
        if frame is None:
            continue
        (flag, encoded_image) = cv2.imencode(".jpg", frame)
        if flag:
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encoded_image) + b'\r\n')

@app.route("/video_feed_hd")
def video_feed_hd():
    return Response(generate_hd(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/video_feed_thermal")
def video_feed_thermal():
    return Response(generate_thermal(), mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__ == '__main__':
    hd_thread = threading.Thread(target=capture_hd_frames)
    hd_thread.daemon = True
    hd_thread.start()

    thermal_thread = threading.Thread(target=capture_thermal_frames)
    thermal_thread.daemon = True
    thermal_thread.start()

    socketio.run(app, host='0.0.0.0', port=8010, debug=True, use_reloader=False)

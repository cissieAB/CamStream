"""
An emulator to send 32x24 raw temperature arrays (in Celcius).
Expose at localhost:5001/raw_frame using Flask SocketIO to achieve high speed.
"""

import io
import time

from flask import Flask
from flask_socketio import SocketIO
import numpy as np


THERMAL_FRAME_SHAPE = (768, )   # Tuple. width 32 x height 24
SLEEP_INTERVAL = 1    # in seconds. FPS = 1/SLEEP_INTERVAL

EMU_TEMP_MEAN = 25.0
EMU_TEMP_STD = 2.0

SIO_API_NAME = "request_thermal"
SIO_NAMESPACE = "/thermal"

app = Flask(__name__)
 # Enable WebSocket. NOTE: logger can be removed later.
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)


def generate_fake_thermal_data(temp_mean=EMU_TEMP_MEAN, temp_std=EMU_TEMP_STD):
    """Generates a 32x24 matrix of simulated temperature data (in Celsius)."""
    emu_thermal_data = np.around(
        np.random.normal(loc=temp_mean, scale=temp_std, size=THERMAL_FRAME_SHAPE),
        decimals=1
    )
    return emu_thermal_data


@socketio.on(SIO_API_NAME)
def send_emu_thermal():
    """"Generate thermal frames with the desired FPS."""

    while True:
        # Simulate a 32x32 thermal camera frame with values between 20-40°C.
        thermal_data = generate_fake_thermal_data()
        timestamp = time.time()

        # Serialize data
        buf = io.BytesIO()
        np.save(buf, thermal_data)
        buf.seek(0)

        # Send data as binary over WebSocket.
        socketio.emit("thermal_data",
                      {"timestamp": timestamp, "data": buf.getvalue()})
        time.sleep(SLEEP_INTERVAL)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8083)

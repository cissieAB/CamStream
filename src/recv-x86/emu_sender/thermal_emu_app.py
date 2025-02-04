"""
An emulator to send 32x24 raw temperature frames (in Celcius) at 4 FPS (frame per second).
Expose at localhost:5001/raw_frame using SSE (portal keeps openning).
"""

import time
import json

from flask import Flask, Response
import numpy as np


THERMAL_FRAME_SHAPE = 768   # width 32 x height 24
SLEEP_INTERVAL = 2    # in seconds. FPS = 1/SLEEP_INTERVAL

app = Flask(__name__)

def generate_fake_thermal_data(temp_mean=25, temp_std=2):
    """Generates a 32x24 matrix of simulated temperature data (in Celsius)."""
    emu_thermal_data = np.around(
        np.random.normal(loc=temp_mean, scale=temp_std, size=THERMAL_FRAME_SHAPE),
        decimals=1
    )
    return emu_thermal_data

def generate_thermal_stream():
    """"Generate thermal frames 4 times per second (SSE streaming)."""
    # Sample response
    # data: {"timestamp": 1738700660.5725446, "temperature_data": [23.  26.4 21.  ...]}

    while True:
        # Simulate a 32x32 thermal camera frame with values between 20-40°C
        temperature_data = generate_fake_thermal_data()
        timestamp = time.time()

        # SSE format: Prefix with "data: " and separate messages with `\n\n`
        event_data = f"data: {json.dumps({'timestamp': timestamp, 'temperature_data': temperature_data.tolist()})}\n\n"

        yield event_data
        time.sleep(SLEEP_INTERVAL)


@app.route('/raw_frame')
def raw_frame():
    """Streams raw temperature data at 4 FPS using Server-Sent Events (SSE)."""
    return Response(generate_thermal_stream(), content_type='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8083, threaded=True)

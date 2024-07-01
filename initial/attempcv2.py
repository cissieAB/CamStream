
# Cv2?

import cv2
from picamera2 import Picamera2, Preview
from pithermalcam import MLX90640
import matplotlib
import time
import numpy as np
import threading
#import adafruit_mlx90640

def capture_picam(stop_event, frame_queue):
    picam = Picamera2()
    picam.start_preview()
    time.sleep(2) #camera warm-up

    #picam settings resolution, fps, array, etc
    config = picam.create_preview_configuration()
    picam.configure(config)
    picam.start()

def capture_thermal(stop_event, frame_queue):
    thermal = MLX90640()
    while not stop_event.is_set():
        frame = thermal.get_frame()
        if frame is not None:
            frame = np.array(frame, dtype=np.float32)
            frame = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX)
            frame = np.uint8(frame)
            frame = cv2.applyColorMap(frame, cv2.COLORMAP_JET)
            frame_queue['thermal'] = frame 

ptc = MLX90640()



#while True:
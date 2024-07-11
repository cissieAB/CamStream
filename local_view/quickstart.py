
from picamera2 import Picamera2, Preview
import time
from pprint import *
from pynput import keyboard

picam2 = Picamera2()
camera_running = False
config = picam2.create_preview_configuration()
picam2.confingure(config)
#hi

from picamera2 import Picamera2
from libcamera import controls 

picam2 = Picamera2()

config = picam2.create_video_configuration({"size":(2028,1520)})
picam2.start(show_video=True)
picam2.set_controls({"AfMode":controls.AfModeEnum.Auto})
# pg 23

job = picam2.autofocus_cycle(wait=False)

# Now do other things
# when you want to be sure autofocus cycle is done:
success = picam2.autofocus_cycle()


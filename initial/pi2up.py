


from picamera2 import Picamera2 #Preview?
import time

def picam_video_init():
    """Capture image from picamera2"""
    picam2 = Picamera2()
    config = picam2.create_video_configuration(main={"format": "RGB888", "size": (800, 600)})
    picam2.configure(config)
    picam2.start()
    return picam2

def picam_still_init():
    """Capture image from picamera2"""
    picam2 = Picamera2()
    config = picam2.create_still_configuration(main={"format": "RGB888", "size": (800, 600)})
    picam2.configure(config)
    picam2.start()
    return picam2
   

picam2 = Picamera2()
config = picam2.create_video_configuration()
preview_config = picam2.create_preview_configuration(queue=False)
picam2.configure(config)
#picam2.start()


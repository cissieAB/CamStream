


from picamera2 import Picamera2 #Preview?
import time

picam2 = Picamera2()
config = picam2.create_video_configuration()
preview_config = picam2.creat_preview_configuration(queue=False)
picam2.configure(config)
#picam2.start()


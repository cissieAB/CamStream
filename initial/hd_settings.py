
from picamera2 import Picamera2, Preview
import time
from pprint import *
from pynput import keyboard

picam2 = Picamera2()
camera_running = False
config = picam2.create_video_configuration()
print("Press 's' to show preview")
print("Press 'x' to print sensor details")
print("Press 'q' to quit")

def on_press(key):
    global camera_running
    try: 
        if key.char == 'x':
            if camera_running == False:
                print("Camera not on, press s to start")
        
            else:
                pprint(picam2.sensor_modes)



        if key.char == 's':
            if camera_running == False:
                picam2.configure (config)
                picam2.start()
                picam2.start_preview (Preview. QTGL)
                camera_running = True
            else:
                print ("Camera already running")
                
        if key.char == 'q':
            print (" Exiting ... ")
            picam2.stop_preview ()
            picam2.stop ()
            return False

    except AttributeError:
        pass

    except KeyboardInterrupt:
        picam2.stop_preview()
        picam2.stop()

with keyboard.Listener(on_press=on_press) as listener:
    listener.join()
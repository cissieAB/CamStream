
from picamera2 import Picamera2, Preview
import time
from pprint import *
import keyboard
#from hd_settings import config


global camera_running
global picam2
global preview_on
global configured
global i
i=0

picam2 = Picamera2()
camera_running = False
preview_on = False
configured = False
config = picam2.create_preview_configuration()


# config = picam2.create_preview_configuration()
# main: Any = {},
# lores: Any | None = None,
# raw: Any = {},
# transform: Any = libcamera.Transform(),
# colour_space: Any = libcamera.ColorSpace.Sycc(),
# buffer_count: int = 4,
# controls: Any = {},
# display: str = "main",
# encode: str = "main",
# queue: bool = True,
# sensor: Any = {},
# use_case: str = "preview"
# {'use_case': 'preview', 
# 'transform': <libcamera.Transform 'identity'>, 
# 'colour_space': <libcamera.ColorSpace 'sYCC'>, 
# 'buffer_count': 4, 
# 'queue': True, 
# 'main': {'format': 'XBGR8888', 'size': (640, 480)}, 
# 'lores': None, 
# 'raw': {'format': 'SRGGB12_CSI2P', 'size': (640, 480)}, 

# 'controls': {'NoiseReductionMode': <NoiseReductionModeEnum.Minimal: 3>, 
# 			'FrameDurationLimits': (100, 83333)}, 'sensor': {}, 
# 		'display': 'main', 'encode': 'main'}



def toggle_cam():
	global i, camera_running, picam2, preview_on
	try:
		if i == 0:
			hd_cam_on()
			i = 1

		elif i == 1:
			hd_cam_off()
			i = 0

		else:
			print(f"i Error")
			return

	except RuntimeError as e:
		camera_running == True
		print(f"Error: {e}")
		if preview_on == True:
			picam2.stop_preview()
		picam2.stop()

def hd_cam_off():
	global i, camera_running, picam2, preview_on
	if preview_on == True:
		picam2.stop_preview()
		preview_on = False
		camera_running = True


def hd_cam_on():
	global i, camera_running, picam2, configured, preview_on
	if configured == False:
		picam2.configure(config)
		configured = True
		time.sleep(1)

	if preview_on == False:
			picam2.start_preview(Preview.QTGL)
			preview_on = True

	if camera_running == False:
		picam2.start()
		camera_running = True
	i = 1


	

def hd_settings():
	global camera_running
	global picam2
	global preview_on
	global configured
	config = picam2.create_preview_configuration()
	
	try: 
		if configured:
			print(config['main'])
		else:
			print("Configuring...")
			picam2.configure(config)
			configuration = True
			time.sleep(1)
			print(config['main'])

		command = input("Press 'm' to view possible modes or hit 'b' to go back").strip().lower()
		if command == 'm':
			if camera_running or preview_on:
				if preview_on:
					picam2.stop_preview()
					preview_on = False
				elif camera_running:
					picam2.stop()
					camera_running = False
				time.sleep(1)
				pprint(picam2.sensor_modes)	
				
			else:
				time.sleep(1)
				pprint(picam2.sensor_modes)

		if command == 'b' or 'esc':
			return
		
		else:
			print("Wrong input, try 'm' to view possible modes or 'b' to go back")

	except RuntimeError as e:
		camera_running == True
		print(f"Error: {e}")
		if preview_on == True:
			picam2.stop_preview()
		picam2.stop()


def exit():
	global i, camera_running, picam2, preview_on
	print(" Exiting")
	if preview_on == True:
		picam2.stop_preview()
	picam2.stop()
	picam2.close()
	
	

def main():
	global camera_running
	global picam2
	global preview_on
	global configured

	while True:
		command = input("Enter 'c' to toggle camera, 's' for settings, 'q' to quit: ").strip().lower()
		if command == 'c':
			toggle_cam()
		
		elif command == 's':
			hd_settings()
			
		elif command == 'q' or KeyboardInterrupt: 
			exit()
			break

		else:
			print("Wrong input, try 'c' to toggle, 's' see setting, or 'q' to quit").strip().lower()




if __name__ == "__main__":
	main()
	

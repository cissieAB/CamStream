
from picamera2 import Picamera2, Preview
import time
from pprint import *
import keyboard
import os
import io
import cv2
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
capture_config = picam2.create_still_configuration()
# File to store the current image number
image_number_file = 'image_number.txt'

# Directory to save images
save_directory = '/home/pi/test/CamStream/chessboard/hd_images'
if not os.path.exists(save_directory):
    os.makedirs(save_directory)


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

# Function to read the current image number from a file
def read_image_number(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return int(f.read().strip())
    else:
        return 0

# Function to write the current image number to a file
def write_image_number(file_path, number):
    with open(file_path, 'w') as f:
        f.write(str(number))

def capture_image():
	global current_image_number

	# Create an in-memory byte stream
	data = io.BytesIO()

	# Capture an image and write it to the byte stream in JPEG format
	picam2.capture_file(data, format='jpeg')

	# Move the cursor of the byte stream to the beginning
	data.seek(0)

	# Read the image data from the byte stream
	image_data = np.frombuffer(data.read(), dtype=np.uint8)

	# Decode the image data to a NumPy array
	image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)

	# Increment the image number
	current_image_number += 1

	# Generate filename
	filename = os.path.join(save_directory, f'chessboard{current_image_number}.png')

	# Save the image
	cv2.imwrite(filename, image)
	print(f'Saved {filename}')

	# Update the image number file
	write_image_number(image_number_file, current_image_number)

	# Capture an image
	
def exit():
	global i, camera_running, picam2, preview_on
	print(" Exiting")
	if preview_on == True:
		picam2.stop_preview()
	picam2.stop()
	picam2.close()

	# picam2=Picamera2()picam2.start(show_preview=True)picam2.set_controls({"AfMode":controls.AfModeEnum.Continuous})

def main():
	global camera_running
	global picam2
	global preview_on
	global configured
	
	while True:
		command = input("Enter 'c' to toggle camera, 's' for settings, 'q' to quit: ").strip().lower()
		if command == 'c':
			command = input("Enter 'p' to capture picture or 'b' to go back: ").strip().lower()
			toggle_cam()
						
			if command == 'p':
				
				picam2.stop_preview()
				# Configure the camera for still image capture
				picam2.configure(picam2.create_still_configuration())
				picam2.start()
				time.sleep(1)
				capture_image()
				time.sleep(1)
				toggle_cam()


			if command == 'b' or 'esc':
				return

		
		elif command == 's':
			hd_settings()
			
		elif command == 'q' or KeyboardInterrupt: 
			exit()
			break

		else:
			print("Wrong input, try 'c' to toggle, 's' see setting, or 'q' to quit").strip().lower()




if __name__ == "__main__":
	main()
	

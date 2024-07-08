
#import 
import time, board, busio, traceback
from picamera2 import Picamera2
import numpy as np
import adafruit_mlx90640
import datetime as dt
import cv2
import logging
import cmapy
from scipy import ndimage
from libcamera import Transform
import matplotlib
import threading
import matplotlib.pyplot



# Set up logging
logging.basicConfig(filename='pithermcam.log', filemode='a',
                    format='%(asctime)s %(levelname)-8s [%(filename)s:%(name)s:%(lineno)d] %(message)s',
                    level=logging.WARNING, datefmt='%d-%b-%y %H:%M:%S')
logger = logging.getLogger(__name__)

class pithermalcam:
    # Color maps and interpolation methods
    _colormap_list = ['jet', 'bwr', 'seismic', 'coolwarm', 'PiYG_r', 'tab10', 'tab20', 'gnuplot2', 'brg']
    _interpolation_list = [cv2.INTER_NEAREST, cv2.INTER_LINEAR, cv2.INTER_AREA, cv2.INTER_CUBIC, cv2.INTER_LANCZOS4, 5, 6]
    _interpolation_list_name = ['Nearest', 'Inter Linear', 'Inter Area', 'Inter Cubic', 'Inter Lanczos4', 'Pure Scipy', 'Scipy/CV2 Mixed']
    
    def init_thermalcam(self, use_f: bool = True, filter_image: bool = False, image_width: int = 1200, 
                 image_height: int = 900, output_folder: str = '/home/pi/pithermalcam/saved_snapshots/'):
        self.use_f = use_f
        self.filter_image = filter_image
        self.image_width = image_width
        self.image_height = image_height
        self.output_folder = output_folder

        self._colormap_index = 0
        self._interpolation_index = 3
        self._setup_therm_cam()
        self._t0 = time.time()
        self.update_image_frame()

    def __del__(self):
        logger.debug("ThermalCam Object deleted.")

    def _setup_thermalcam(self):
        """Initialize the thermal camera"""
        self.i2c = busio.I2C(board.SCL, board.SDA, frequency=800000)
        self.mlx = adafruit_mlx90640.MLX90640(self.i2c)
        self.mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_8_HZ
        time.sleep(0.1)

    def _c_to_f(self, temp: float):
        """ Convert temperature from C to F """
        return (9.0 / 5.0) * temp + 32.0

    def get_mean_temp(self):
        """
        Get mean temp of entire field of view. Return both temp C and temp F.
        """
        frame = np.zeros((24 * 32,))
        while True:
            try:
                self.mlx.getFrame(frame)
                break
            except ValueError:
                continue

        temp_c = np.mean(frame)
        temp_f = self._c_to_f(temp_c)
        return temp_c, temp_f

    def pull_raw_thermal_image(self):
        """Get one pull of the raw image data, converting temp units if necessary"""
        self._raw_image = np.zeros((24 * 32,))
        try:
            self.mlx.getFrame(self._raw_image)
            self._temp_min = np.min(self._raw_image)
            self._temp_max = np.max(self._raw_image)
            self._raw_image = self._temps_to_rescaled_uints(self._raw_image, self._temp_min, self._temp_max)
            self._current_frame_processed = False
        except ValueError:
            print("Math error; continuing...")
            self._raw_image = np.zeros((24 * 32,))
            logger.info(traceback.format_exc())
        except OSError:
            print("IO Error; continuing...")
            self._raw_image = np.zeros((24 * 32,))
            logger.info(traceback.format_exc())

    def _temps_to_rescaled_uints(self, raw_image, temp_min, temp_max,  scale_min=20, scale_max=60):
        
        #Convert temperature values to scaled unsigned integers
        scale_range = (scale_max - scale_min)
        normalized = (raw_image - temp_min) / (temp_max - temp_min)

        #scale normalized to target temp range
        scaled = scale_min + normalized * scale_range
        
        rescaled = 255*(scaled - scale_min)/(scale_range)

        return np.clip(rescaled, 0, 255).astype(np.uint8)

    def process_thermal_image(self):
        """Process the raw temp data to a colored image. Filter if necessary"""
        if self._interpolation_index == 5:
            self._image = ndimage.zoom(self._raw_image, 25)
            self._image = cv2.applyColorMap(self._image, cmapy.cmap(self._colormap_list[self._colormap_index]))
        elif self._interpolation_index == 6:
            self._image = ndimage.zoom(self._raw_image, 10)
            self._image = cv2.applyColorMap(self._image, cmapy.cmap(self._colormap_list[self._colormap_index]))
            self._image = cv2.resize(self._image, (800, 600), interpolation=cv2.INTER_CUBIC)
        else:
            self._image = cv2.applyColorMap(self._raw_image, cmapy.cmap(self._colormap_list[self._colormap_index]))
            self._image = cv2.resize(self._image, (800, 600), interpolation=self._interpolation_list[self._interpolation_index])
            self._image = cv2.flip(self._image, 1)
        if self.filter_image:
            self._image = cv2.bilateralFilter(self._image, 15, 80, 80)

    def _add_image_text(self):
        """Set image text content"""
        if self.use_f:
            temp_min = self._c_to_f(self._temp_min)
            temp_max = self._c_to_f(self._temp_max)
            text = f'Tmin={temp_min:+.1f}F - Tmax={temp_max:+.1f}F - FPS={1/(time.time() - self._t0):.1f} - Interpolation: {self._interpolation_list_name[self._interpolation_index]} - Colormap: {self._colormap_list[self._colormap_index]} - Filtered: {self.filter_image}'
        else:
            text = f'Tmin={self._temp_min:+.1f}C - Tmax={self._temp_max:+.1f}C - FPS={1/(time.time() - self._t0):.1f} - Interpolation: {self._interpolation_list_name[self._interpolation_index]} - Colormap: {self._colormap_list[self._colormap_index]} - Filtered: {self.filter_image}'
        cv2.putText(self._image, text, (30, 18), cv2.FONT_HERSHEY_SIMPLEX, .4, (255, 255, 255), 1)
        self._t0 = time.time()

        if self._file_saved_notification_start is not None and (time.monotonic() - self._file_saved_notification_start) < 1:
            cv2.putText(self._image, 'Snapshot Saved!', (300, 300), cv2.FONT_HERSHEY_SIMPLEX, .8, (255, 255, 255), 2)

    def add_customized_text(self, text):
        """Add custom text to the center of the image, used mostly to notify user that server is off."""
        cv2.putText(self._image, text, (300, 300), cv2.FONT_HERSHEY_SIMPLEX, .8, (255, 255, 255), 2)
        time.sleep(0.1)

        
def video_init(picam2):
        """Capture image from picamera2"""
        config = picam2.create_video_configuration(main={"format": "RGB888", "size": (800, 600)})
        picam2.configure(config)
        picam2.start()
        return picam2


#def still_init(picam2, bitrate=None, repeat=True, iperiod=None, framerate=None, enable_sps_framerate=False,
                 qp=None, profile=None):
        """Capture image from picamera2"""
        
        config = picam2.create_still_configuration(main={"format": "RGB888", "size": (800, 600)})
        picam2.configure(config)
        picam2.start()
        return picam2


def fps_test(picam2):
    md = picam2.capture_metadata()
    t0 = time.clock_gettime(time.CLOCK_REALTIME)
    md = picam2.capture_metadata()
    t1 = time.clock_gettime(time.CLOCK_REALTIME)
    print("Frame took", t1 - t0, "seconds")
    if t1 - t0 < 4:
        print("ERROR: frame arrived too quickly", t1 - t0, "seconds")

    picam2.stop()
    t2 = time.clock_gettime(time.CLOCK_REALTIME)
    print("Stopping took", t2 - t1, "seconds")
    if t2 - t1 > 0.5:
        print("ERROR: stop took too long", t2 - t1, "seconds")
   

def blend_images(picam2_image, thermal_image):
    """Blend two images"""
    picam2_image = cv2.cvtColor(picam2_image, cv2.COLOR_RGB2BGR)

    if thermal_image.shape != picam2_image.shape:
        thermal_image = cv2.resize(thermal_image, (800, 600))
        picam2_image = cv2.resize(picam2_image, (800, 600))
    
    # Use cv2.addWeighted to blend the images
    alpha = 0.5  # weight for the first image
    beta = 1.0 - alpha  # weight for the second image
    blended_image = cv2.addWeighted(thermal_image, alpha, picam2_image, beta, 0)

    return blended_image
    
if __name__ == "__main__":
    thermal_output_folder = '/home/pi/PiThermalCam/saved_snapshots/'
    thermcam = pithermalcam(thermal_output_folder=output_folder)
    thermcam.init_thermalcam()
    thermcam.pull_raw_thermal_image() # Execute
    thermcam.process_thermal_image()
    thermal_image = thermcam._image

    picam2 = Picamera2()
    

    # thermal_image = thermcam.process_thermal_image()
    cv2.imshow('Blended image', blended_image(picam2_image, thermal_image))

import time, board, busio, traceback
from picamera2 import Picamera2
import numpy as np
import adafruit_mlx90640
import datetime as dt
import cv2
import logging
import cmapy
from scipy import ndimage



# Set up logging
logging.basicConfig(filename='pithermcam.log',filemode='a',
                    format='%(asctime)s %(levelname)-8s [%(filename)s:%(name)s:%(lineno)d] %(message)s',
                    level=logging.WARNING,datefmt='%d-%b-%y %H:%M:%S')
logger = logging.getLogger(__name__)


class pithermalcam:
    # See https://gitlab.com/cvejarano-oss/cmapy/-/blob/master/docs/colorize_all_examples.md to for options that can be put in this list
    _colormap_list=['jet','bwr','seismic','coolwarm','PiYG_r','tab10','tab20','gnuplot2','brg']
    _interpolation_list =[cv2.INTER_NEAREST,cv2.INTER_LINEAR,cv2.INTER_AREA,cv2.INTER_CUBIC,cv2.INTER_LANCZOS4,5,6]
    _interpolation_list_name = ['Nearest','Inter Linear','Inter Area','Inter Cubic','Inter Lanczos4','Pure Scipy', 'Scipy/CV2 Mixed']
    _current_frame_processed=False  # Tracks if the current processed image matches the current raw image
    i2c=None
    mlx=None
    _temp_min=None
    _temp_max=None
    _raw_image=None
    _image=None
    _file_saved_notification_start=None
    _displaying_onscreen=False
    _exit_requested=False

    def __init__(self,use_f:bool = True, filter_image:bool = False, image_width:int=1200, 
                image_height:int=900, output_folder:str = '/home/pi/pithermalcam/saved_snapshots/'):
        self.use_f=use_f
        self.filter_image=filter_image
        self.image_width=image_width
        self.image_height=image_height
        self.output_folder=output_folder

        self._colormap_index = 0
        self._interpolation_index = 3
        self._setup_therm_cam()
        self._t0 = time.time()
        self.update_image_frame()

    def __del__(self):
        logger.debug("ThermalCam Object deleted.")

    def _setup_therm_cam(self):
        """Initialize the thermal camera"""
        # Setup camera
        self.i2c = busio.I2C(board.SCL, board.SDA, frequency=800000)  # setup I2C
        self.mlx = adafruit_mlx90640.MLX90640(self.i2c)  # begin MLX90640 with I2C comm
        self.mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_8_HZ  # set refresh rate
        time.sleep(0.1)

    def _c_to_f(self,temp:float):
        """ Convert temperature from C to F """
        return ((9.0/5.0)*temp+32.0)

    def get_mean_temp(self):
        """
        Get mean temp of entire field of view. Return both temp C and temp F.
        """
        frame = np.zeros((24*32,))  # setup array for storing all 768 temperatures
        while True:
            try:
                self.mlx.getFrame(frame)  # read MLX temperatures into frame var
                break
            except ValueError:
                continue  # if error, just read again

        temp_c = np.mean(frame)
        temp_f=self._c_to_f(temp_c)
        return temp_c, temp_f

    def _pull_raw_image(self):
        """Get one pull of the raw image data, converting temp units if necessary"""
        # Get image
        self._raw_image = np.zeros((24*32,))
        try:
            self.mlx.getFrame(self._raw_image)  # read mlx90640
            self._temp_min = np.min(self._raw_image)
            self._temp_max = np.max(self._raw_image)
            self._raw_image=self._temps_to_rescaled_uints(self._raw_image,self._temp_min,self._temp_max)
            self._current_frame_processed=False  # Note that the newly updated raw frame has not been processed
        except ValueError:
            print("Math error; continuing...")
            self._raw_image = np.zeros((24*32,))  # If something went wrong, make sure the raw image has numbers
            logger.info(traceback.format_exc())
        except OSError:
            print("IO Error; continuing...")
            self._raw_image = np.zeros((24*32,))  # If something went wrong, make sure the raw image has numbers
            logger.info(traceback.format_exc())

def _process_raw_image(self):
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
            temp_min=self._c_to_f(self._temp_min)
            temp_max=self._c_to_f(self._temp_max)
            text = f'Tmin={temp_min:+.1f}F - Tmax={temp_max:+.1f}F - FPS={1/(time.time() - self._t0):.1f} - Interpolation: {self._interpolation_list_name[self._interpolation_index]} - Colormap: {self._colormap_list[self._colormap_index]} - Filtered: {self.filter_image}'
        else:
            text = f'Tmin={self._temp_min:+.1f}C - Tmax={self._temp_max:+.1f}C - FPS={1/(time.time() - self._t0):.1f} - Interpolation: {self._interpolation_list_name[self._interpolation_index]} - Colormap: {self._colormap_list[self._colormap_index]} - Filtered: {self.filter_image}'
        cv2.putText(self._image, text, (30, 18), cv2.FONT_HERSHEY_SIMPLEX, .4, (255, 255, 255), 1)
        self._t0 = time.time()  # Update time to this pull

        # For a brief period after saving, display saved notification
        if self._file_saved_notification_start is not None and (time.monotonic()-self._file_saved_notification_start)<1:
            cv2.putText(self._image, 'Snapshot Saved!', (300,300),cv2.FONT_HERSHEY_SIMPLEX, .8, (255, 255, 255), 2)

    def add_customized_text(self,text):
        """Add custom text to the center of the image, used mostly to notify user that server is off."""
        cv2.putText(self._image, text, (300,300),cv2.FONT_HERSHEY_SIMPLEX, .8, (255, 255, 255), 2)
        time.sleep(0.1)

    def picam_init():
     # Capture image from picamera2
     picam2 = Picamera2()
     config = picam2.create_video_configuration(main={"format": "RGB888", "size": (800, 600)})
     picam2.configure(config)
     picam2.start()
     picamera2_image = picam2.capture_array()
     picam2.stop()
    
    def blend_images()
 
     # Ensure the captured image is in BGR format (OpenCV format)
     picamera2_image = cv2.cvtColor(picamera2_image, cv2.COLOR_RGB2BGR)
    
     # Ensure both images are of the same size (800x600)
     if self._image.shape != picamera2_image.shape:
         self._image = cv2.resize(self._image, (800, 600))
         picamera2_image = cv2.resize(picamera2_image, (800, 600))
    
     # Use cv2.addWeighted to blend the images
     alpha = 0.5  # weight for the first image
     beta = 1.0 - alpha  # weight for the second image
     blended_image = cv2.addWeighted(self._image, alpha, picamera2_image, beta, 0)
    
     # Save or display the blended image
     #cv2.imwrite('blended_image.png', blended_image)
     #cv2.imshow('Blended Image', blended_image)
     #cv2.waitKey(0)
     #cv2.destroyAllWindows()
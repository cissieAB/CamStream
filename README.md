# DACERI

## Python Env Setup
On Raspberry PI, after cloning this repo, setup a Python virtual environment at the root.

```bash
$ python -m venv .venv # setup a Python virtual environment whose name is ".venv". Use `ls -a` to find the .venv repo
$ source .venv/bin/activate  # activate the virtual environment

## Virtual environment .venv
 (.venv)$ pip install -r requirements.txt # install the packages

## Clone the repository
  git clone --recurse-submodules https://github.com/cissieAB/CamStream.git
```


## Theraml Camera and IMX477 (HD Camera) Setup

### Thermal camera
Once you have all the Python dependency ready, follow the below steps to set up the thermal camera.
1. Update the system config file at `/boot/firmware/config.txt`.

    ```bash
    $ sudo nano /boot/firmware/config.txt

    ## Find the line with dtparam_arm = on and update it to:
    dtparam_arm = on, arm_baudrate = 400000
    ```
    Confirm the camera is connected with command `sudo i2cdetect -y 1`. You should see a matrix with number "33" as [this picture](https://images.squarespace-cdn.com/content/v1/59b037304c0dbfb092fbe894/1591722759211-V68N42XVLZG96DG448BA/i2c_detect_mlx90640.png?format=2500w) shows.

 2. Make sure the basic Python package `adafruit_mlx90640` is working with [detect_thermalcam.py](./scripts/detect_thermalcam.py).
    ```bash
    (.venv)$ python scripts/detect_thermalcam.py
    ```
    You should be able to see the raw temperature array printed out on the screen.

3. Tricks to make the submodule [PiThermalCam](https://github.com/tomshaffner/PiThermalCam) working.

    A. Find the Python dependency files at `<.venv path>/lib/python3.11/site-packages/`.
      - Update `cmapy.py`:
        - Replace `matplotlib.cm.get_cmap()` with `matplotlib.pyplot.get_cmap()`;
        - At the top of the file, add `import matplotlib.pyplot`.
      - [Optional] Update `adafruit_mlx90640.py`:
        - Line 160: Replace `if cnt > 4` to `if cnt > 400`.

    B. Run the camera test to check if there is any error.

    ```bash
    (.venv)$ python PiThermalCam/examples/cam_test.py
    ```
### IMX477 HD Camera

Follow the [guide](./doc/IMX477_configuration.md) to update the system configuration file and test with `libcamera`.

As the system config file `/boot/firmware/config.txt` is updated twice, we save [a backup copy](./scripts/config_bk.txt) in this repo.


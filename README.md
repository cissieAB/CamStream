# DACERI

## Env Setup
On Raspberry PI, after cloning this repo, setup a Python virtual environment at the root.
```
## Bash 
$ python3 -m venv --system-site-packages .venv # setup a Python virtual environment whose name is ".venv". Use `ls -a` to find the .venv repo
$ source .venv/bin/activate  # activate the virtual environment

## Virtual environment .venv
 (.venv)$ pip install pithermalcam  # install the package (optional)

## Clone the repository 
  git clone --recurse-submodules https://github.com/cissieAB/CamStream.git
```

## HD Camera Setup

```
## Bash
$ sudo nano /boot/firmware/config.txt

## Find line with dtparam_arm = on and change to: 
dtparam_arm = on, arm_baudrate = 400000

## Confirm the camera is connected with command
$ sudo i2cdetect -y 1 
```
## Notes
- The trick to make [PiThermalCam](https://github.com/tomshaffner/PiThermalCam) running if you want to use the pip module 

  After `pip install pithermacam`, find the `cmapy.py` file and update it as following:
  1. Replace `matplotlib.cm.get_cmap()` with `matplotlib.pyplot.get_cmap()`
  2. At the top of the file, add `import matplotlib.pyplot`

  After that, run the camera test to check if there is any error.
  ```
  (.venv)$ python3 PiThermalCam/examples/cam_test.py 
  ```
  

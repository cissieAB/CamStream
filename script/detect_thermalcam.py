'''
Use this file to detect whether the thermal camera is working after 
`sudo i2cdetect -y 1` is successful.

If executed successfully, it will output the 24x32 temp frame and mean temp.
'''

import time
import board
import busio
import numpy as np
import adafruit_mlx90640

i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)
mlx = adafruit_mlx90640.MLX90640(i2c)
mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ

print("Support IC rates:")
print(dir(adafruit_mlx90640.RefreshRate))

frame = np.zeros((24 * 32, ))
while True:
    try:
        mlx.getFrame(frame)
        break  # Loop until get one frame
    except ValueError:
        continue

print(frame)
print(f"Average MLX90640 temp (C): {np.mean(frame)}")

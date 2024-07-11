
import cv2

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
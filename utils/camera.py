import os
import cv2
import numpy as np
from picamera2 import Picamera2
from libcamera import Transform
from time import sleep
import time

OUT_PATH = "output"

MIN_AREA = 500
UPPER_RATIO = 1.2
LOWER_RATIO = 0.8
ARC_SCALE = 0.02

class CameraHandler():
  """
  Class to handle loading and preprocessing images for inference. 
  """

  def __init__(self):
    # Set camera configuration.
    self.picam2 = Picamera2()
    self.picam2.preview_configuration.main.size = (320,240)
    self.picam2.preview_configuration.main.format = "RGB888"
    self.picam2.preview_configuration.align()
    self.picam2.preview_configuration.transform = Transform(vflip=True, hflip=True) 
    self.picam2.configure("preview")
    self.picam2.start()

    self.latest_img = None
    self.poster_cordinates = None
    self.count = 0

    # Create the output directory, if it does not exist.
    os.makedirs(OUT_PATH, exist_ok=True)

    sleep(0.5)

  def get_processed_image(self, count=0, save=False, debug=False):
    """
    Run the full preprocessing step on the latest frame.

    Arguments:
      count: Number to write images with, defaults to 0.
      save: Whether to write images, defaults to false.
      debug: Whether to print debug output, defaults to false.
    """
    self.capture(count, save)
    self.detect_poster(save)
    return self.crop_and_resize(count, save, debug)

  def capture(self, count=None, save=False):
    """
    Store the latest frame.

    Arguments:
      count: Number to write images with, defaults to 0.
      save: Whether to write images, defaults to false.
    """
    raw_cap = self.picam2.capture_array("main")
    self.latest_img = raw_cap
    if save:
        if count is None:
            count = self.count
            self.count += 1
        cv2.imwrite(os.path.join(OUT_PATH, f"01_raw_frame_{self.count}.jpg"), self.latest_img)
          
  def detect_poster(self, save=False):
    """
    Use thresholding, polygon approximation, and geometric tolerancing to process the latest frame.

    Arguments:
      save: Whether to write images, defaults to false.
    """
    # Copy latest frame.
    img = self.latest_img.copy()
    
    # Convert image to grayscale.
    gray = cv2.cvtColor(img.copy(), cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(gray,3)
    if save:
      cv2.imwrite(os.path.join("output", f"02_gray_frame_{self.count}_gray.jpg"), gray)
    
    # Adaptive threshold image.
    adaptive_thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 3)
    if save:
      cv2.imwrite(os.path.join("output", f"03_thresholded_frame_{self.count}.jpg"), adaptive_thresh)
    
    # Find contours of image.
    contours, hierarchies = cv2.findContours(adaptive_thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    
    # Find the square that bounds the poster.
    poster_area = float('inf')
    for cnt in contours:
      # Calculate the area of the contour.
      area = cv2.contourArea(cnt) 
      # Get the polygon approximation of the contour.
      approx = cv2.approxPolyDP(cnt, ARC_SCALE*cv2.arcLength(cnt, True), True)
      # Consider the contour as a candidate if it has 4 edges and area above MIN_AREA.
      if len(approx) == 4 and area > MIN_AREA:
        # Approximate contour with a rectangle.
        x, y, w, h = cv2.boundingRect(cnt) 
        # Calculate the ratio between width and height.
        ratio = float(w)/h 
        # If the ratio is within a margin, we consider it as a squre poster.
        if ratio >= LOWER_RATIO and ratio <= UPPER_RATIO and (area < poster_area):
              poster_area = area
              # Transform the square to a 2d matrix.
              approx = approx.reshape(-1,2) 
              # Update poster coordinates.
              self.poster_cordinates = approx
    
    # Make sure a poster has been found.
    if self.poster_cordinates is not None:
      print("Poster found!")
      # Use the coordinates to draw the estimated outline back on the frame.
      x1, y1 = self.poster_cordinates[0]
      cv2.putText(img, 'estimated_poster_outline', (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
      img = cv2.drawContours(img, [self.poster_cordinates], -1, (0,255,255), 3)
    if save:
      cv2.imwrite(os.path.join("output", f"04_labeled_frame_{self.count}.jpg"), img)

  def crop_and_resize(self, count=0, save=False, debug=False):
    """
    Flatten, crop, and re threshold the latest frame.

    Arguments:
      count: Number to write images with, defaults to 0.
      save: Whether to write images, defaults to false.
      debug: Whether to print debug output, defaults to false.
    """
    #Adapted from https://stackoverflow.com/questions/71337994/opencv-get-correct-corners-for-perspective-correction-using-python
    img = self.latest_img.copy()
        
    # Get the width and height of the image.
    hh, ww = img.shape[:2]

    out = None
    try:
      # Convert the order of the poster coordinates to a specific sequence.
      cordinates = self.order_points(self.poster_cordinates)

      # Convert the corners from ints to floats.
      inpts = np.float32(cordinates)

      # Create an ideal square to map the sticky note to (28 pixels x 28 pixels).
      num = 28
      outpts = np.float32([[num, num], [0, num], [0, 0], [num, 0]])

      # Perform perspective correction from the real corners to the ideal corners.
      M = None
      warpimg = None
      M = cv2.getPerspectiveTransform(inpts, outpts)
      gray = cv2.cvtColor(img.copy(), cv2.COLOR_BGR2GRAY)
      blur = cv2.medianBlur(gray,3)
      adaptive_thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 3)
      warpimg = cv2.warpPerspective(adaptive_thresh, M, (ww,hh))
      if save:
        cv2.imwrite(os.path.join(OUT_PATH, f"05_flattened_frame_{self.count}.jpg"), warpimg)

      # Crop the image to 28 x 28 like in the MNIST dataset.
      crop = warpimg[0:num, 0:num]
      if save:
        cv2.imwrite(os.path.join(OUT_PATH, f"06_cropped_frame_{self.count}.jpg"), crop)

      # Perform color correction (invert in grayscale and threshold it).
      crop_f = np.float32(crop)
      out = 255.0 - 255.0*(crop_f - np.min(crop_f))/np.max(crop_f - np.min(crop_f))
      out = np.int32(out)
      # Make it a binary image.
      out[out > 0] = 255
      if save:
        cv2.imwrite(os.path.join(OUT_PATH, f"07_inverted_frame_{self.count}.jpg"), out)

      # Black out the four edge pixels.
      out = self.paint_border_black(out)
      if save:
          cv2.imwrite(os.path.join(OUT_PATH, f"08_bordered_frame_{self.count}.jpg"), out)

    except Exception as e:
        # Something went wrong in the pipeline (like it could not find a sticky note).
        if debug == True:
            print(e)
        return None
  
    self.poster_cordinates = None
    return out.reshape(-1)

  def order_points(self, pts):
    """
    Put points in clockwise order starting with the upperleft most point.

    Arguments:
      pts: List of (x, y) points.

    Returns:
      The list of (x, y) points reordered.
    """
    # Initialzie a list of coordinates that will be ordered
    # such that the first entry in the list is the top-left,
    # the second entry is the top-right, the third is the
    # bottom-right, and the fourth is the bottom-left.
    rect = np.zeros((4, 2), dtype = "float32")

    # The top-left point will have the smallest sum, whereas
    # the bottom-right point will have the largest sum.
    s = pts.sum(axis = 1)
    rect[2] = pts[np.argmin(s)]
    rect[0] = pts[np.argmax(s)]

    # Now, compute the difference between the points, the
    # top-right point will have the smallest difference,
    # whereas the bottom-left will have the largest difference.
    diff = np.diff(pts, axis = 1)
    rect[3] = pts[np.argmin(diff)]
    rect[1] = pts[np.argmax(diff)]

    # Return the ordered coordinates.
    return rect
  
  def paint_border_black(self, img):
    """
    Set 4 pixels in from the border of a 28x28 binary image to black.

    Arguments:
      img: 28x28 image.

    Returns:
      The image with borders set to black.
    """
    rows = [0,1,2,3,24,25,26,27]
    cols = [0,1,2,3,24,25,26,27]
    for row in rows:
      for j in range(28):
        img[row][j] = 0
        
    for i in range(4,24):
      for col in cols:
        img[i][col] = 0
    
    return img

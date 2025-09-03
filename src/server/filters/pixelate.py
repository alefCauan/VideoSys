# filters/pixelate.py
import cv2

def apply(frame, size=(64, 64)):
    h, w = frame.shape[:2]
    small = cv2.resize(frame, size, interpolation=cv2.INTER_LINEAR)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)

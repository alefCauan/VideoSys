# filters/edges.py
import cv2

def apply(frame):
    edges = cv2.Canny(frame, 100, 200)
    return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

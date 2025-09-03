# storage/paths.py
import os

MEDIA_ROOT = "../media"
INCOMING = os.path.join(MEDIA_ROOT, "incoming")
VIDEOS = os.path.join(MEDIA_ROOT, "videos")

os.makedirs(INCOMING, exist_ok=True)
os.makedirs(VIDEOS, exist_ok=True)

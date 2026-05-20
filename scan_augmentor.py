import logging
import random
import numpy as np
from pathlib import Path

log = logging.getLogger("pipeline.augmentor")

try:
    from PIL import Image, ImageFilter, ImageEnhance, ImageDraw
except ImportError:
    raise ImportError("pip install Pillow")

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


def apply_rotation(img, max_degrees=2.5):
    return img.rotate(random.uniform(-max_degrees, max_degrees), expand=True, fillcolor=(255,255,255))

def apply_gaussian_blur(img, radius_range=(0.3, 1.2)):
    return img.filter(ImageFilter.GaussianBlur(radius=random.uniform(*radius_range)))

def apply_brightness_contrast(img):
    img = ImageEnhance.Brightness(img).enhance(random.uniform(0.82, 1.05))
    return ImageEnhance.Contrast(img).enhance(random.uniform(0.80, 1.10))

def apply_salt_pepper_noise(img, density=None):
    if not CV2_AVAILABLE:
        return img
    density = density or random.uniform(0.001, 0.008)
    arr = np.array(img)
    n = arr.shape[0] * arr.shape[1]
    coords = [np.random.randint(0, i, int(n * density)) for i in arr.shape[:2]]
    arr[coords[0], coords[1]] = 255
    coords = [np.random.randint(0, i, int(n * density * 0.5)) for i in arr.shape[:2]]
    arr[coords[0], coords[1]] = 0
    return Image.fromarray(arr)

def apply_paper_texture(img, intensity=None):
    intensity = intensity or random.uniform(0.02, 0.07)
    arr = np.array(img).astype(np.float32)
    arr = np.clip(arr + np.random.normal(0, intensity * 255, arr.shape), 0, 255).astype(np.uint8)
    return Image.fromarray(arr)

def apply_shadow_overlay(img):
    arr = np.array(img).astype(np.float32)
    h, w = arr.shape[:2]
    side = random.choice(["left", "right", "top", "bottom"])
    strength = random.uniform(0.15, 0.35)
    fade = random.randint(int(w * 0.08), int(w * 0.25))
    gradient = np.ones(w if side in ("left", "right") else h, dtype=np.float32)
    for i in range(fade):
        gradient[i if side in ("left", "top") else -(i+1)] = 1.0 - (strength * (1 - i / fade))
    gradient = gradient[np.newaxis, :, np.newaxis] if side in ("left", "right") else gradient[:, np.newaxis, np.newaxis]
    return Image.fromarray(np.clip(arr * gradient, 0, 255).astype(np.uint8))

def apply_jpeg_compression(img, quality_range=(55, 85)):
    import io
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=random.randint(*quality_range))
    buf.seek(0)
    return Image.open(buf).copy()

def apply_perspective_warp(img, max_shift=0.012):
    if not CV2_AVAILABLE:
        return img
    arr = np.array(img)
    h, w = arr.shape[:2]
    s = lambda: random.uniform(-max_shift, max_shift)
    src = np.float32([[0,0],[w,0],[w,h],[0,h]])
    dst = np.float32([[w*s(),h*s()],[w+w*s(),h*s()],[w+w*s(),h+h*s()],[w*s(),h+h*s()]])
    M = cv2.getPerspectiveTransform(src, dst)
    return Image.fromarray(cv2.warpPerspective(arr, M, (w, h), borderValue=(255,255,255)))

def apply_coffee_stain(img):
    draw = ImageDraw.Draw(img, "RGBA")
    w, h = img.size
    cx, cy = random.randint(int(w*0.1), int(w*0.9)), random.randint(int(h*0.1), int(h*0.9))
    r = random.randint(20, 60)
    color = (random.randint(160,200), random.randint(120,160), random.randint(80,120), random.randint(15,40))
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=color)
    return img.convert("RGB")

def apply_dot_matrix_lines(img):
    arr = np.array(img).astype(np.float32)
    spacing, fade = random.randint(24, 40), random.uniform(0.94, 0.97)
    for y in range(0, arr.shape[0], spacing):
        arr[y] = arr[y] * fade
    return Image.fromarray(arr.astype(np.uint8))


SCAN_PROFILES = {
    "mobile_camera":  [apply_rotation, apply_perspective_warp, apply_shadow_overlay, apply_brightness_contrast, apply_gaussian_blur, apply_jpeg_compression],
    "photocopy":      [apply_brightness_contrast, apply_paper_texture, apply_salt_pepper_noise, apply_gaussian_blur, apply_jpeg_compression],
    "clean_laser":    [apply_brightness_contrast, apply_salt_pepper_noise],
    "thermal_faded":  [apply_brightness_contrast, apply_paper_texture, apply_gaussian_blur],
    "dot_matrix":     [apply_dot_matrix_lines, apply_brightness_contrast, apply_salt_pepper_noise],
    "hand_annotated": [apply_rotation, apply_brightness_contrast, apply_paper_texture, apply_coffee_stain, apply_jpeg_compression],
}

SCAN_PROFILE_WEIGHTS = {
    "mobile_camera": 30, "photocopy": 25, "clean_laser": 20,
    "thermal_faded": 10, "dot_matrix": 10, "hand_annotated": 5,
}


def augment_image(img, profile=None):
    if profile is None:
        profile = random.choices(list(SCAN_PROFILE_WEIGHTS.keys()), weights=list(SCAN_PROFILE_WEIGHTS.values()), k=1)[0]
    log.debug(f"Augmenting with profile={profile} steps={[fn.__name__ for fn in SCAN_PROFILES[profile]]}")
    for fn in SCAN_PROFILES[profile]:
        try:
            img = fn(img)
            log.debug(f"  Applied: {fn.__name__}")
        except Exception as e:
            log.warning(f"  Skipped {fn.__name__}: {e}")
    return img

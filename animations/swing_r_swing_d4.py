import cv2
import numpy as np
import math

def ease_in_out(t):
    return t * t * (3 - 2 * t)

def add_white_border(image, border_width=10):
    return cv2.copyMakeBorder(
        image, border_width, border_width, border_width, border_width,
        cv2.BORDER_CONSTANT, value=(255, 255, 255)
    )

def safe_paste(bg, img, x, y):
    h, w = img.shape[:2]
    bg_h, bg_w = bg.shape[:2]
    y1, y2 = max(0, y), min(bg_h, y + h)
    x1, x2 = max(0, x), min(bg_w, x + w)
    img_y1, img_y2 = max(0, -y), h - max(0, (y + h) - bg_h)
    img_x1, img_x2 = max(0, -x), w - max(0, (x + w) - bg_w)
    if y1 < y2 and x1 < x2:
        bg[y1:y2, x1:x2] = img[img_y1:img_y2, img_x1:img_x2]

def create_gradient_background(height, width, top_color, bottom_color):
    gradient = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        alpha = y / height
        color = (1 - alpha) * np.array(top_color) + alpha * np.array(bottom_color)
        gradient[y, :] = color
    return gradient

def resize_fullscreen_cover(image, target_h=1920, target_w=1080):
    """Resize image to fully cover the canvas (1080x1920)."""
    h, w = image.shape[:2]
    scale = max(target_w / w, target_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    resized = cv2.resize(image, (new_w, new_h))

    # Crop center
    x1 = (new_w - target_w) // 2
    y1 = (new_h - target_h) // 2
    return resized[y1:y1 + target_h, x1:x1 + target_w]

def animate_swing_r_swing_d4(user_image, out_path, fps=30):
    """
    0–4s: Fullscreen Swing (image covers 1080x1920)
    4–7s: Slide-In from Right + Swing Down
    7–10s: Diagonal Swing
    """
    bg_h, bg_w = 1920, 1080
    top_color = (128, 0, 255)
    bottom_color = (203, 192, 255)
    bg_img = create_gradient_background(bg_h, bg_w, top_color, bottom_color)

    # prepare both versions (fullscreen + normal)
    fullscreen_img = resize_fullscreen_cover(user_image, bg_h, bg_w)
    bordered_img = add_white_border(resize_fullscreen_cover(user_image, bg_h, bg_w), 10)

    img_h, img_w = bordered_img.shape[:2]
    center_x = bg_w // 2 - img_w // 2
    center_y = bg_h // 2 - img_h // 2

    total_dur = 10
    total_frames = int(total_dur * fps)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps, (bg_w, bg_h))

    for f in range(total_frames):
        t = f / fps
        frame = bg_img.copy()

        # === 0–4s → Fullscreen image swing ===
        if t <= 4:
            phase = t / 4
            angle = math.sin(phase * math.pi * 2) * 5
            sway_x = int(math.sin(phase * math.pi * 2) * 20)
            sway_y = int(math.sin(phase * math.pi * 2) * 10)
            M = cv2.getRotationMatrix2D((bg_w // 2, bg_h // 2), angle, 1.0)
            rotated = cv2.warpAffine(fullscreen_img, M, (bg_w, bg_h), borderValue=(255, 255, 255))
            safe_paste(frame, rotated, sway_x, sway_y)

        # === 4–7s → Slide-In from Right + Swing Down ===
        elif t <= 5:
            phase = (t - 4) / 2
            slide_in = int((1 - ease_in_out(phase)) * (bg_w // 2 + img_w))
            sway_y = int(math.sin(phase * math.pi * 2) * 50)
            angle = math.sin(phase * math.pi * 2) * 6
            M = cv2.getRotationMatrix2D((img_w // 2, img_h // 2), angle, 1.0)
            rotated = cv2.warpAffine(bordered_img, M, (img_w, img_h), borderValue=(255, 255, 255))
            safe_paste(frame, rotated, center_x + slide_in, center_y + sway_y)

        # === 7–10s → Diagonal Swing ===
        else:
            phase = (t - 7) / 3
            sway_x = int(math.sin(phase * math.pi * 2) * 40)
            sway_y = int(math.sin(phase * math.pi * 2) * 40)
            angle = math.sin(phase * math.pi * 2) * 10
            M = cv2.getRotationMatrix2D((img_w // 2, img_h // 2), angle, 1.0)
            rotated = cv2.warpAffine(bordered_img, M, (img_w, img_h), borderValue=(255, 255, 255))
            safe_paste(frame, rotated, center_x + sway_x, center_y + sway_y)

        writer.write(frame)

    writer.release()
    print(f"[INFO] ✅ Fullscreen Swing → Slide-In → Diagonal animation done → {out_path}")
    return total_dur, total_frames

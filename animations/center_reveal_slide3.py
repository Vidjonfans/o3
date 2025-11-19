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

def animate_center_reveal_slide3(user_image, out_path, fps=30):
    """
    Full canvas → reveal (1.3 s) → zoom (1.3–3 s)
    → slide-in from left (3–5 s) → animated hold (5–7 s)
    Gradient background (Purple → Pink)
    """
    # 🎨 Gradient Background
    bg_h, bg_w = 1920, 1080
    top_color = (128, 0, 255)
    bottom_color = (203, 192, 255)
    bg_img = create_gradient_background(bg_h, bg_w, top_color, bottom_color)

    # 🖼️ Prepare user image
    user_img = cv2.resize(user_image, (bg_w, bg_h))
    bordered_img = add_white_border(user_img, 0)
    img_h, img_w = bordered_img.shape[:2]
    center_x = bg_w // 2 - img_w // 2
    center_y = bg_h // 2 - img_h // 2

    # Timing
    reveal_dur, zoom_dur, slide_dur, hold_dur = 1.3, 1.7, 2.0, 4.0
    total_dur = reveal_dur + zoom_dur + slide_dur + hold_dur
    total_frames = int(total_dur * fps)

    # 🎥 Writer
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps, (bg_w, bg_h))

    for f in range(total_frames):
        t = f / fps
        frame = bg_img.copy()

        # --- 0–1.3 s: Reveal ---
        if t <= reveal_dur:
            progress = ease_in_out(t / reveal_dur)
            mask = np.zeros_like(bordered_img, dtype=np.uint8)
            hw, hh = int((img_w // 2) * progress), int((img_h // 2) * progress)
            x1, x2 = img_w // 2 - hw, img_w // 2 + hw
            y1, y2 = img_h // 2 - hh, img_h // 2 + hh
            if x2 > x1 and y2 > y1:
                mask[y1:y2, x1:x2] = bordered_img[y1:y2, x1:x2]
            safe_paste(frame, mask, center_x, center_y)

        # --- 1.3–3 s: Zoom out ---
        elif t <= reveal_dur + zoom_dur:
            progress = ease_in_out((t - reveal_dur) / zoom_dur)
            scale = 1.0 + progress * 0.4
            new_w, new_h = int(img_w * scale), int(img_h * scale)
            zoomed = cv2.resize(bordered_img, (new_w, new_h))
            cx, cy = bg_w // 2 - new_w // 2, bg_h // 2 - new_h // 2
            safe_paste(frame, zoomed, cx, cy)

        # --- 3–5 s: Slide in from left ---
        elif t <= reveal_dur + zoom_dur + slide_dur:
            progress = ease_in_out((t - (reveal_dur + zoom_dur)) / slide_dur)
            slide_offset = int((1 - progress) * bg_w)
            cx, cy = -slide_offset, center_y
            safe_paste(frame, bordered_img, cx, cy)

        # --- 5–7 s: Animated Hold (subtle movement) ---
        else:
            hold_time = t - (reveal_dur + zoom_dur + slide_dur)
            loop_p = math.sin(hold_time * math.pi * 1.2) * 0.02  # gentle oscillation ±2 %
            scale = 1.2 + loop_p
            sway = int(math.sin(hold_time * math.pi * 0.8) * 15)  # ±15 px sway
            new_w, new_h = int(img_w * scale), int(img_h * scale)
            moving = cv2.resize(bordered_img, (new_w, new_h))
            cx = bg_w // 2 - new_w // 2 + sway
            cy = bg_h // 2 - new_h // 2
            safe_paste(frame, moving, cx, cy)

        writer.write(frame)

    writer.release()
    print(f"[INFO] ✅ Reveal + Zoom + Slide + Animated-Hold video created → {out_path}")

    # Return for API
    try:
        from .utils import get_video_duration
        duration = get_video_duration(out_path)
    except Exception:
        duration = total_dur
    return duration, total_frames

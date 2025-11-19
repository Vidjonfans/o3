import cv2
import numpy as np
import requests
import math
from .utils import get_video_duration

# ✅ Background image (fixed)
BACKGROUND_URL = "https://res.cloudinary.com/dvsubaggj/image/upload/v1761447077/Screenshot_2025-10-19_155811_rkg3nz.png"


def load_image_from_url(url):
    """Download image from URL and return OpenCV image."""
    try:
        resp = requests.get(url, timeout=10)
        arr = np.asarray(bytearray(resp.content), dtype=np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception as e:
        print(f"[ERROR] Could not load image: {e}")
        return None


def add_white_border(image, border_width=10):
    """Add white border around image."""
    return cv2.copyMakeBorder(
        image,
        border_width,
        border_width,
        border_width,
        border_width,
        cv2.BORDER_CONSTANT,
        value=(255, 255, 255),
    )


def ease_in_out(t):
    """Smooth ease-in-out interpolation (0→1)."""
    return t * t * (3 - 2 * t)


def animate_collage_tapestry(user_image, out_path, fps=24):
    """
    Create a 10-sec travel tapestry:
      - 0–4s: collage animation
      - 4–4.9s: fade & blur out
      - 4.9s–6.4s: center image spins once (1 rotation)
      - 6.4s–7.9s: pause (no movement)
      - 7.9s–8.9s: slide-right + fade out
    """
    bg_img = load_image_from_url(BACKGROUND_URL)
    if bg_img is None:
        raise ValueError("Failed to load background image.")

    bg_h, bg_w = bg_img.shape[:2]
    total_duration = 10
    frames = int(fps * total_duration)

    slide_duration = 0.9
    slide_frames = int(fps * slide_duration)
    text_fade_duration = 1.0
    text_fade_frames = int(fps * text_fade_duration)
    blur_fade_duration = 0.9
    blur_fade_frames = int(fps * blur_fade_duration)
    blur_start_frame = int(fps * 4)

    # ✅ Collage image (small)
    img_w, img_h = int(bg_w * 0.40), int(bg_h * 0.30)
    small_img = cv2.resize(user_image, (img_w, img_h))
    bordered_img = add_white_border(small_img, 8)
    bordered_h, bordered_w = bordered_img.shape[:2]

    # ✅ Center image (large)
    center_w, center_h = int(bg_w * 0.58), int(bg_h * 0.68)
    center_img = cv2.resize(user_image, (center_w, center_h))
    center_bordered = add_white_border(center_img, 10)
    center_h, center_w = center_bordered.shape[:2]

    # Collage positions
    positions = [
        (int(bg_w * 0.08), int(bg_h * 0.30)),  # top-left
        (int(bg_w * 0.38), int(bg_h * 0.10)),  # top-right
        (int(bg_w * 0.20), int(bg_h * 0.70)),  # bottom-left
        (int(bg_w * 0.38), int(bg_h * 0.50)),  # bottom-right
    ]

    # Writer
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps, (bg_w, bg_h))

    # === Animation ===
    for f in range(frames):
        t = f / fps
        frame = bg_img.copy()

        # === 0–4s: Collage animation ===
        if f < blur_start_frame:
            for i, (base_x, base_y) in enumerate(positions):
                offset_x = int(3 * math.sin(t * 1.5 + i * 0.5))
                offset_y = int(2 * math.cos(t * 1.2 + i * 0.7))
                img_x = base_x + offset_x
                img_y = base_y + offset_y

                if f < slide_frames:
                    progress = ease_in_out(f / slide_frames)
                    if i == 0:
                        img_y += int((1 - progress) * bg_h * 0.25)
                    elif i == 2:
                        img_y -= int((1 - progress) * bg_h * 0.25)
                    elif i in [1, 3]:
                        img_x += int((1 - progress) * bg_w * 0.4)

                y2 = min(img_y + bordered_h, bg_h)
                x2 = min(img_x + bordered_w, bg_w)
                if img_x >= 0 and img_y >= 0 and y2 > img_y and x2 > img_x:
                    overlay = frame[img_y:y2, img_x:x2]
                    blended = cv2.addWeighted(
                        overlay, 0.15, bordered_img[: y2 - img_y, : x2 - img_x], 0.85, 0
                    )
                    frame[img_y:y2, img_x:x2] = blended

            # Text Fade-In
            if f >= slide_frames:
                text_progress = min((f - slide_frames) / text_fade_frames, 1.0)
                alpha = ease_in_out(text_progress)
                color = (int(30 + 200 * alpha), int(30 + 200 * alpha), int(30 + 200 * alpha))

                cv2.putText(frame, "Happy", (int(bg_w * 0.07), int(bg_h * 0.12)),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.1, color, 3, cv2.LINE_AA)
                cv2.putText(frame, "Diwali", (int(bg_w * 0.07), int(bg_h * 0.22)),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 3, cv2.LINE_AA)

                para_lines = [
                    "Every travel collage ",
                    "tells a story,",
                    "a mosaic of adventure, ",
                    "discovery,",
                    "and memories ",
                    "etched in time.",
                ]
                start_y = int(bg_h * 0.80)
                for j, line in enumerate(para_lines):
                    text_size = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                    text_x = bg_w - text_size[0] - int(bg_w * 0.05)
                    text_y = start_y + j * 25
                    cv2.putText(frame, line, (text_x, text_y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

        # === 4–4.9s: Blur & fade ===
        elif blur_start_frame <= f < blur_start_frame + blur_fade_frames:
            fade_progress = (f - blur_start_frame) / blur_fade_frames
            blur_amount = int(1 + fade_progress * 15)
            blurred = cv2.GaussianBlur(frame, (0, 0), blur_amount)
            alpha = 1 - ease_in_out(fade_progress)
            frame = (blurred * alpha).astype(np.uint8)

        # === After 4.9s: Spin → Pause → Slide Right ===
        else:
            frame = bg_img.copy()
            elapsed = (f - (blur_start_frame + blur_fade_frames)) / fps

            spin_duration = 1.5
            pause_duration = 1.5
            slide_duration = 1.0

            # Stage 1: Spin once (360°)
            if elapsed < spin_duration:
                progress = ease_in_out(elapsed / spin_duration)
                angle = progress * 360
                M = cv2.getRotationMatrix2D((center_w // 2, center_h // 2), -angle, 1.0)
                rotated = cv2.warpAffine(
                    center_bordered, M, (center_w, center_h),
                    flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT
                )

                cx = bg_w // 2 - center_w // 2
                cy = bg_h // 2 - center_h // 2
                roi = frame[cy:cy + center_h, cx:cx + center_w]
                frame[cy:cy + center_h, cx:cx + center_w] = cv2.addWeighted(roi, 0, rotated, 1, 0)

            # Stage 2: Pause (no movement)
            elif elapsed < spin_duration + pause_duration:
                cx = bg_w // 2 - center_w // 2
                cy = bg_h // 2 - center_h // 2
                roi = frame[cy:cy + center_h, cx:cx + center_w]
                frame[cy:cy + center_h, cx:cx + center_w] = cv2.addWeighted(roi, 0, center_bordered, 1, 0)

            # Stage 3: Slide-right + fade-out
            elif elapsed < spin_duration + pause_duration + slide_duration:
                slide_elapsed = elapsed - (spin_duration + pause_duration)
                progress = ease_in_out(slide_elapsed / slide_duration)
                slide_offset = int(progress * bg_w * 0.5)
                alpha = 1 - progress

                cx = bg_w // 2 - center_w // 2 + slide_offset
                cy = bg_h // 2 - center_h // 2

                y1, y2 = cy, min(cy + center_h, bg_h)
                x1, x2 = cx, min(cx + center_w, bg_w)
                if 0 <= x1 < bg_w and 0 <= y1 < bg_h:
                    overlay = frame[y1:y2, x1:x2]
                    blended = cv2.addWeighted(
                        overlay, 1 - alpha, center_bordered[: y2 - y1, : x2 - x1], alpha, 0
                    )
                    frame[y1:y2, x1:x2] = blended

        writer.write(frame)

    writer.release()
    print(f"[INFO] Final video created successfully → {out_path}")
    return get_video_duration(out_path), frames

import cv2
import numpy as np
import math
import random
from .utils import get_video_duration


def ease_in_out(t):
    """Smooth cubic easing for smooth animation start/end"""
    return t * t * t * (t * (6 * t - 15) + 10)


def generate_particle(canvas_w, canvas_h):
    """एक नई चमकती हुई कण (particle) स्थिति उत्पन्न करें।"""
    return [
        random.randint(0, canvas_w),  # x
        random.randint(0, canvas_h),  # y
        random.randint(1, 3),         # radius
        random.uniform(0.5, 2.0),     # dy (speed)
        255.0,                        # opacity
        random.randint(20, 50)        # lifetime
    ]


def animate_zoomin_zoomout_fadein2(user_image, out_path, fps=24):
    """
    Final clean version:
    - Starts after 2 sec delay
    - Zoom + slide (pan) effect for 5 sec
    - Then roll (180° rotation) and zoom-out for 3 sec
    - Natural fade-in/out + sparkle particles
    """

    oh, ow = user_image.shape[:2]
    canvas_w, canvas_h = int(ow * 1.6), int(oh * 1.6)

    wait_before_start = 2.0
    zoom_slide_duration = 5.0
    roll_out_duration = 3.0
    total_duration = wait_before_start + zoom_slide_duration + roll_out_duration
    total_frames = int(fps * total_duration)

    writer = cv2.VideoWriter(
        out_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (canvas_w, canvas_h)
    )

    # Scale & motion parameters
    scale_to_fill = max(canvas_w / ow, canvas_h / oh)
    zoom_start = scale_to_fill * 1.15
    zoom_end = scale_to_fill * 1.0

    slide_start_x, slide_end_x = -80, 80
    slide_start_y, slide_end_y = 40, -40

    # Particle system
    MAX_PARTICLES = 120
    SPAWN_RATE = 5
    particles = [generate_particle(canvas_w, canvas_h) for _ in range(MAX_PARTICLES // 3)]

    for f in range(total_frames):
        frame = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)

        time_sec = f / fps

        # Before 2 sec → keep blank (no image yet)
        if time_sec < wait_before_start:
            alpha = time_sec / wait_before_start
            overlay = np.zeros_like(frame)
            frame = cv2.addWeighted(frame, alpha, overlay, 1 - alpha, 0)
            writer.write(frame)
            continue

        # After 2 sec → start main animation
        t_main = (time_sec - wait_before_start) / (zoom_slide_duration + roll_out_duration)
        t_main = min(max(t_main, 0.0), 1.0)
        ease = ease_in_out(t_main)

        # PHASE 1: 0–5 sec (zoom + slide)
        if time_sec < wait_before_start + zoom_slide_duration:
            progress = (time_sec - wait_before_start) / zoom_slide_duration
            ease_zoom = ease_in_out(progress)
            scale = zoom_start + (zoom_end - zoom_start) * ease_zoom
            dx = int(slide_start_x + (slide_end_x - slide_start_x) * ease_zoom)
            dy = int(slide_start_y + (slide_end_y - slide_start_y) * ease_zoom)
            rotated = user_image.copy()

        # PHASE 2: roll + zoom-out
        else:
            progress = (time_sec - (wait_before_start + zoom_slide_duration)) / roll_out_duration
            ease_roll = ease_in_out(progress)
            angle = 180 * ease_roll
            scale = zoom_end * (1.0 - ease_roll * 0.9)
            dx = int(slide_end_x * (1 - ease_roll))
            dy = int(slide_end_y * (1 - ease_roll))

            M = cv2.getRotationMatrix2D((ow // 2, oh // 2), angle, 1.0)
            rotated = cv2.warpAffine(user_image, M, (ow, oh), borderValue=(255, 255, 255))

        # Resize + paste
        sw, sh = int(ow * scale), int(oh * scale)
        resized = cv2.resize(rotated, (sw, sh))
        x = (canvas_w - sw) // 2 + dx
        y = (canvas_h - sh) // 2 + dy

        # Paste image
        x1, y1 = max(x, 0), max(y, 0)
        x2, y2 = min(x + sw, canvas_w), min(y + sh, canvas_h)
        frame[y1:y2, x1:x2] = resized[
            (y1 - y):(y2 - y),
            (x1 - x):(x2 - x)
        ]

        # Particles
        new_particles = []
        for p in particles:
            x_p, y_p, radius, dy_p, opacity, life = p
            y_p += dy_p
            opacity -= (255 / life) * (fps / 24)
            if opacity > 0 and y_p < canvas_h + 5:
                new_particles.append([x_p, y_p, radius, dy_p, opacity, life])
                color = (200, 255, 255)
                cv2.circle(frame, (int(x_p), int(y_p)), radius, color, -1)
        particles = new_particles

        if len(particles) < MAX_PARTICLES:
            for _ in range(SPAWN_RATE):
                particles.append(generate_particle(canvas_w, canvas_h))

        # Fade in/out
        fade_frames = int(fps * 0.5)
        alpha_factor = 1.0
        if f < fade_frames:
            alpha_factor = f / fade_frames
        elif f > total_frames - fade_frames:
            alpha_factor = (total_frames - f) / fade_frames
        if alpha_factor < 1.0:
            overlay = np.zeros_like(frame)
            frame = cv2.addWeighted(frame, alpha_factor, overlay, 1 - alpha_factor, 0)

        writer.write(frame)

    writer.release()
    print(f"[INFO] Video created successfully → {out_path}")
    return get_video_duration(out_path), total_frames

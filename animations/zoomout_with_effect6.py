import cv2
import numpy as np
from moviepy import vfx
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip

# ==========================================================
# 🧩 Utility Functions
# ==========================================================
def add_white_border(image, border_width=10):
    return cv2.copyMakeBorder(
        image, border_width, border_width, border_width, border_width,
        cv2.BORDER_CONSTANT, value=(255, 255, 255)
    )

def create_gradient_background(height, width, top_color, bottom_color):
    gradient = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        alpha = y / height
        color = (1 - alpha) * np.array(top_color) + alpha * np.array(bottom_color)
        gradient[y, :] = color
    return gradient

# ==========================================================
# 🎞️ Animation Effects
# ==========================================================
def apply_zoom(frame, factor):
    h, w = frame.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, 0, factor)
    return cv2.warpAffine(frame, M, (w, h))

def apply_slide_out(frame, shift):
    """Slide image out of the frame (right side)."""
    h, w = frame.shape[:2]
    M = np.float32([[1, 0, shift], [0, 1, 0]])
    return cv2.warpAffine(frame, M, (w, h))

def apply_slide_left(frame, shift):
    """Slide image out of the frame (left side)."""
    h, w = frame.shape[:2]
    M = np.float32([[1, 0, -shift], [0, 1, 0]])
    return cv2.warpAffine(frame, M, (w, h))

def apply_blur_fade(frame, blur_strength, alpha):
    """Apply blur + fade (disappear effect)."""
    blurred = cv2.GaussianBlur(frame, (blur_strength, blur_strength), 0)
    black = np.zeros_like(frame)
    return cv2.addWeighted(blurred, alpha, black, 1 - alpha, 0)

# ==========================================================
# 🎨 Main Animation Function
# ==========================================================
def animate_zoomout_with_effect6(user_image, out_path="animated_output.mp4", fps=30, duration=5):
    bg_h, bg_w = 1920, 1080
    top_color = (128, 0, 255)
    bottom_color = (203, 192, 255)
    bg_img = create_gradient_background(bg_h, bg_w, top_color, bottom_color)

    user_img = cv2.resize(user_image, (bg_w, bg_h))
    bordered = add_white_border(user_img, 0)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps, (bg_w, bg_h))

    total_frames = int(duration * fps)
    frames = []

    # Timing divisions
    zoom_in_frames = int(3 * fps)
    slide_out_frames = int(0.3 * fps)
    zoom_out_frames = int(3 * fps)
    slide_left_frames = int(0.5 * fps)
    blur_fade_frames = int(1.0 * fps)
    total_needed = zoom_in_frames + slide_out_frames + zoom_out_frames + slide_left_frames + blur_fade_frames

    if total_needed > total_frames:
        total_frames = total_needed

    for i in range(total_frames):
        frame = bg_img.copy()
        blended = cv2.addWeighted(frame, 0.3, bordered, 0.7, 0)

        # 1️⃣ Zoom-in
        if i < zoom_in_frames:
            factor = 1.0 + (i / zoom_in_frames) * 0.3
            animated = apply_zoom(blended, factor)

        # 2️⃣ Slide-out (right)
        elif i < zoom_in_frames + slide_out_frames:
            progress = (i - zoom_in_frames) / slide_out_frames
            shift = int(progress * bg_w * 1.2)
            animated = apply_slide_out(blended, shift)

        # 3️⃣ Zoom-out (slow)
        elif i < zoom_in_frames + slide_out_frames + zoom_out_frames:
            progress = (i - (zoom_in_frames + slide_out_frames)) / zoom_out_frames
            factor = 1.3 - progress * 0.3
            animated = apply_zoom(blended, factor)

        # 4️⃣ Slide-out (left)
        elif i < zoom_in_frames + slide_out_frames + zoom_out_frames + slide_left_frames:
            progress = (i - (zoom_in_frames + slide_out_frames + zoom_out_frames)) / slide_left_frames
            shift = int(progress * bg_w * 1.2)
            animated = apply_slide_left(blended, shift)

        # 5️⃣ Blur + Fade-out (Disappear)
        # 5️⃣ Blur + Fade-out (Disappear)
        elif i < zoom_in_frames + slide_out_frames + zoom_out_frames + slide_left_frames + blur_fade_frames:
            progress = (i - (zoom_in_frames + slide_out_frames + zoom_out_frames + slide_left_frames)) / blur_fade_frames
            factor = 1.0 + progress * 0.2  # slight zoom while disappearing
            blur_strength = max(3, int(3 + progress * 25))
            if blur_strength % 2 == 0:  # make sure kernel size is odd
                blur_strength += 1
            alpha = 1.0 - progress  # fade to black
            zoomed = apply_zoom(blended, factor)
            animated = apply_blur_fade(zoomed, blur_strength, alpha)


        else:
            animated = blended

        writer.write(animated)
        frames.append(animated[:, :, ::-1])  # BGR → RGB

    writer.release()

    # 🎬 MoviePy cinematic output
    moviepy_out = out_path.replace(".mp4", "_moviepy.mp4")
    try:
        clip = ImageSequenceClip(frames, fps=fps).fx(vfx.fadein, 1).fx(vfx.fadeout, 1)
        clip.write_videofile(moviepy_out, codec="libx264")
        print(f"[INFO] 🎞 MoviePy cinematic video created → {moviepy_out}")
    except Exception as e:
        print(f"[⚠️] MoviePy cinematic render skipped due to error: {e}")

    print(f"[INFO] ✅ Dual animation videos created:\n  - {out_path}\n  - {moviepy_out}")
    return out_path, moviepy_out


# ==========================================================
# 🚀 Example Usage
# ==========================================================
if __name__ == "__main__":
    img = cv2.imread("human.jpg")
    animate_zoomout_with_effect6(img, "animated_output.mp4", fps=30, duration=10)

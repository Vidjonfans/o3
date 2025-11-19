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

def apply_blur_fade(frame, blur_strength, alpha):
    """Apply blur + fade effect."""
    if blur_strength % 2 == 0:
        blur_strength += 1
    blurred = cv2.GaussianBlur(frame, (blur_strength, blur_strength), 0)
    black = np.zeros_like(frame)
    return cv2.addWeighted(blurred, alpha, black, 1 - alpha, 0)

# ==========================================================
# 🎨 Main Animation Function
# ==========================================================
def animate_ultra_zoom_blur7(user_image, out_path="animated_output.mp4", fps=30):
    bg_h, bg_w = 1920, 1080
    top_color = (128, 0, 255)
    bottom_color = (203, 192, 255)
    bg_img = create_gradient_background(bg_h, bg_w, top_color, bottom_color)

    user_img = cv2.resize(user_image, (bg_w, bg_h))
    bordered = add_white_border(user_img, 0)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps, (bg_w, bg_h))

    # Frame timing (based on your sequence)
    zoom_in_frames = int(3.0 * fps)
    blur_zoom_frames = int(0.8 * fps)

    # Sequence pattern: 4 zooms, 3 blurs
    sequence = [
        "zoom", "blur",
        "zoom", "blur",
        "zoom", "blur",
        "zoom"
    ]

    frames = []

    for step in sequence:
        if step == "zoom":
            for i in range(zoom_in_frames):
                progress = i / zoom_in_frames
                factor = 1.0 + progress * 0.3
                frame = bg_img.copy()
                blended = cv2.addWeighted(frame, 0.3, bordered, 0.7, 0)
                animated = apply_zoom(blended, factor)
                writer.write(animated)
                frames.append(animated[:, :, ::-1])

        elif step == "blur":
            for i in range(blur_zoom_frames):
                progress = i / blur_zoom_frames
                factor = 1.3 + progress * 1.5  # ultra zoom
                blur_strength = max(3, int(5 + progress * 25))
                if blur_strength % 2 == 0:
                    blur_strength += 1
                alpha = 1.0 - (progress * 0.8)
                frame = bg_img.copy()
                blended = cv2.addWeighted(frame, 0.3, bordered, 0.7, 0)
                zoomed = apply_zoom(blended, factor)
                animated = apply_blur_fade(zoomed, blur_strength, alpha)
                writer.write(animated)
                frames.append(animated[:, :, ::-1])

    writer.release()

    # 🎬 MoviePy Cinematic Output
    moviepy_out = out_path.replace(".mp4", "_moviepy.mp4")
    try:
        clip = ImageSequenceClip(frames, fps=fps).fx(vfx.fadein, 0.8).fx(vfx.fadeout, 1.0)
        clip.write_videofile(moviepy_out, codec="libx264")
        print(f"[INFO] 🎞 MoviePy cinematic video created → {moviepy_out}")
    except Exception as e:
        print(f"[⚠️] MoviePy cinematic render skipped due to error: {e}")

    print(f"[INFO] ✅ Final animation video created:\n  - {out_path}\n  - {moviepy_out}")
    return out_path, moviepy_out


# ==========================================================
# 🚀 Example Usage
# ==========================================================
if __name__ == "__main__":
    img = cv2.imread("human.jpg")
    animate_ultra_zoom_blur_sequence(img, "animated_output.mp4", fps=30)

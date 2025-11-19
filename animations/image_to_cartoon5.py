import cv2
import numpy as np

def add_white_border(image, border_width=10):
    return cv2.copyMakeBorder(
        image, border_width, border_width, border_width, border_width,
        cv2.BORDER_CONSTANT, value=(255, 255, 255)
    )

def create_gradient_background(height, width, top_color, bottom_color):
    """Create a vertical gradient background."""
    gradient = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        alpha = y / height
        color = (1 - alpha) * np.array(top_color) + alpha * np.array(bottom_color)
        gradient[y, :] = color
    return gradient

def cartoonize_image(img):
    """Advanced cartoon effect with edge enhancement and color quantization."""
    # Resize for better consistency
    img = cv2.resize(img, (1080, 1920))

    # Step 1: Edge detection
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 7)
    edges = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        9, 10
    )

    # Step 2: Color quantization (reduces number of shades)
    data = np.float32(img).reshape((-1, 3))
    K = 8  # number of color clusters
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, label, center = cv2.kmeans(data, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    center = np.uint8(center)
    quantized = center[label.flatten()].reshape(img.shape)

    # Step 3: Bilateral filtering for smooth cartoon look
    smooth = cv2.bilateralFilter(quantized, d=9, sigmaColor=200, sigmaSpace=200)

    # Step 4: Combine edges with smoothed image
    cartoon = cv2.bitwise_and(smooth, smooth, mask=edges)

    return cartoon

def animate_image_to_cartoon5(user_image, out_path, fps=30, duration=4):
    """
    Create a 4-sec video of a full-canvas cartoon image (1080x1920),
    with a soft gradient background.
    """
    bg_h, bg_w = 1920, 1080
    top_color = (128, 0, 255)
    bottom_color = (203, 192, 255)
    bg_img = create_gradient_background(bg_h, bg_w, top_color, bottom_color)

    # Resize image to canvas size
    user_img = cv2.resize(user_image, (bg_w, bg_h))

    # Convert to advanced cartoon
    cartoon_img = cartoonize_image(user_img)
    bordered = add_white_border(cartoon_img, 0)

    # Video writer setup
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps, (bg_w, bg_h))

    total_frames = int(duration * fps)

    for _ in range(total_frames):
        frame = bg_img.copy()
        blended = cv2.addWeighted(frame, 0.3, bordered, 0.7, 0)
        writer.write(blended)

    writer.release()
    print(f"[INFO] ✅ Cartoon full-screen video created → {out_path}")
    return duration, total_frames

# 🧪 Example usage
if __name__ == "__main__":
    img = cv2.imread("human.jpg")  # Replace with your image path
    animate_image_to_cartoon5(img, "cartoon_output.mp4", fps=30, duration=4)

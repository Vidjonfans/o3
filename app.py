import cv2
import numpy as np
import aiohttp
import os
import uuid
import asyncio
import requests  # 🔹 Added for Cloudinary upload
from fastapi import FastAPI, Query, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys, os
sys.path.append(os.path.join(os.getcwd(), "venv", "Lib", "site-packages"))
print("✅ Custom site-packages path added:", os.path.join(os.getcwd(), "venv", "Lib", "site-packages"))

# ✅ Import animations + utils
from animations.vertical_reveal import animate_collage_tapestry
from animations.zoomout_zoomin2 import animate_zoomin_zoomout_fadein2
from animations.center_reveal_slide3 import animate_center_reveal_slide3
from animations.swing_r_swing_d4 import animate_swing_r_swing_d4
from animations.image_to_cartoon5 import animate_image_to_cartoon5
from animations.zoomout_with_effect6 import animate_zoomout_with_effect6
from animations.ultra_zoom_blur7 import animate_ultra_zoom_blur7





from animations.utils import fix_mp4, add_audio_to_video


# ✅ FastAPI app
app = FastAPI(
    title="🎬 Image Animation API with Audio",
    description="Generate animated videos from images using cinematic effects and custom audio.",
    version="2.3.0"
)

# ✅ Enable CORS for all origins (Flutter Web fix)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Output folder setup
OUTDIR = "outputs"
os.makedirs(OUTDIR, exist_ok=True)
app.mount("/outputs", StaticFiles(directory=OUTDIR), name="outputs")


# ---- Health check ----
@app.head("/")
async def head_check():
    return Response(status_code=200)


# ---- Root endpoint ----
@app.get("/")
async def home():
    return {
        "message": "🎥 Animation API is running!",
        "available_animations": [
            "reveal_vertical_zoomout",
            "zoomin_zoomout_fadein2",
            "center_reveal_slide3",
            "swing_r_swing_d4",
            "image_to_cartoon5",
            "zoomout_with_effect6",
            "ultra_zoom_blur7"
        ],
        "example_request": "/process?image_url=https://yourimage.jpg&animation=zoomin_zoomout_fadein2&audio_url=https://youraudio.aac"
    }


# ---- Helper: Download image ----
async def fetch_image(url: str):
    """Download image from public URL."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as resp:
                if resp.status != 200:
                    print(f"[ERROR] Invalid image URL: {url}")
                    return None
                data = await resp.read()
                nparr = np.frombuffer(data, np.uint8)
                return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except Exception as e:
        print(f"[ERROR] fetch_image failed: {e}")
        return None


# ---- Helper: Upload video to Cloudinary ----
def upload_to_cloudinary(local_path: str):
    """Upload the video to Cloudinary and return its secure URL."""
    cloud_name = "dvsubaggj"
    upload_preset = "flutter_unsigned_upload"
    url = f"https://api.cloudinary.com/v1_1/{cloud_name}/video/upload"

    try:
        with open(local_path, "rb") as file_data:
            res = requests.post(
                url,
                files={"file": file_data},
                data={"upload_preset": upload_preset},
                timeout=120
            )
        result = res.json()
        if res.status_code == 200:
            secure_url = result["secure_url"]
            print(f"[✅] Cloudinary upload successful → {secure_url}")
            return secure_url
        else:
            print(f"[❌] Cloudinary upload failed → {result}")
            return None
    except Exception as e:
        print(f"[ERROR] Upload to Cloudinary failed: {e}")
        return None


# ---- Animation runner ----
def run_animation_sync(img, out_path, animation, audio_url=None):
    """Run selected animation and optionally add audio."""
    try:
        # ✅ Select animation
        if animation == "reveal_vertical_zoomout":
            duration, frames = animate_collage_tapestry(img, out_path)
        elif animation == "zoomin_zoomout_fadein2":
            duration, frames = animate_zoomin_zoomout_fadein2(img, out_path)
        elif animation == "center_reveal_slide3":
            duration, frames = animate_center_reveal_slide3(img, out_path)
        elif animation == "swing_r_swing_d4":
            duration, frames = animate_swing_r_swing_d4(img, out_path)
        elif animation == "image_to_cartoon5":
            duration, frames = animate_image_to_cartoon5(img, out_path)
        elif animation == "zoomout_with_effect6":
            duration, frames = animate_zoomout_with_effect6(img, out_path)
        elif animation == "ultra_zoom_blur7":
            duration, frames = animate_ultra_zoom_blur7(img, out_path)


        else:
            raise ValueError(f"Invalid animation type: {animation}")

        # ✅ Re-encode for browser
        fix_mp4(out_path)

        # ✅ Add custom audio (if provided)
        if audio_url:
            out_with_audio = out_path.replace(".mp4", "_audio.mp4")
            added = add_audio_to_video(out_path, audio_url, out_with_audio)
            if added:
                os.replace(out_with_audio, out_path)
                print(f"[INFO] Audio added from {audio_url}")

        print(f"[INFO] Animation '{animation}' completed successfully → {out_path}")
        return duration, frames

    except Exception as e:
        print(f"[ERROR] Animation failed: {e}")
        raise


# ---- Main endpoint ----
@app.get("/process")
async def process(
    request: Request,
    image_url: str = Query(..., description="Public image URL"),
    animation: str = Query("reveal_vertical_zoomout", description="Animation type"),
    audio_url: str = Query(None, description="Optional audio URL (MP3, AAC, etc.)")
):
    """Download image → apply selected animation → attach audio (optional) → upload to Cloudinary."""
    img = await fetch_image(image_url)
    if img is None:
        return {"error": "❌ Image download failed or invalid URL"}

    out_path = os.path.join(OUTDIR, f"anim_{uuid.uuid4().hex}.mp4")

    # ✅ Run animation
    try:
        loop = asyncio.get_event_loop()
        duration, frames = await loop.run_in_executor(
            None, lambda: run_animation_sync(img, out_path, animation, audio_url)
        )
    except Exception as e:
        return {"error": f"❌ Animation processing failed: {str(e)}"}

    # ✅ Wait for output
    timeout = 30
    for _ in range(timeout):
        if os.path.exists(out_path) and os.path.getsize(out_path) > 5000:
            break
        await asyncio.sleep(1)

    if not os.path.exists(out_path):
        return {"error": "⚠️ Video generation failed or file missing."}

    # ✅ Upload to Cloudinary directly
    cloudinary_url = upload_to_cloudinary(out_path)

    if not cloudinary_url:
        return {"error": "❌ Failed to upload video to Cloudinary."}

    # ✅ Cleanup local file after upload
    try:
        os.remove(out_path)
        print(f"[INFO] Local file deleted after upload.")
    except Exception:
        pass

    # ✅ Response (Public Cloudinary URL)
    print(f"[SUCCESS] Final Cloudinary URL: {cloudinary_url}")

    return {
        "status": "✅ Success",
        "animation": animation,
        "audio_attached": bool(audio_url),
        "duration_seconds": duration,
        "frames_written": frames,
        "video_url": cloudinary_url,  # 🔹 Public Cloudinary URL
    }


# ---- Startup Event ----
@app.on_event("startup")
async def startup_event():
    print("🚀 Initializing Animation API...")
    await asyncio.sleep(3)
    print("✅ Ready to process requests.")


# ---- Run locally ----
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=10000, reload=False)

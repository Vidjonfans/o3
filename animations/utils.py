import cv2
import subprocess
import os
import tempfile
import requests

def get_video_duration(out_path):
    """Return duration (in seconds) of a video file."""
    cap = cv2.VideoCapture(out_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps_val = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    duration = total_frames / fps_val if fps_val > 0 else 0
    return duration


def fix_mp4(out_path):
    """
    ✅ Re-encode MP4 for browser compatibility (H.264 + AAC)
    Ensures Chrome/Edge/Firefox can play the file directly.
    """
    fixed_path = out_path.replace(".mp4", "_fixed.mp4")
    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", out_path,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",  # for web playback
            fixed_path
        ]

        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.replace(fixed_path, out_path)
        print(f"[INFO] MP4 fixed and replaced → {out_path}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] ffmpeg failed to re-encode video: {e}")
    except Exception as e:
        print(f"[ERROR] fix_mp4 unexpected error: {e}")


def add_audio_to_video(video_path, audio_url, output_path):
    """
    ✅ Add background audio from a URL (or local file) to the given video.
    Keeps the video duration same as the shorter of the two.
    """
    try:
        # Step 1: Download audio if it's a URL
        if audio_url.startswith("http"):
            r = requests.get(audio_url, timeout=20)
            if r.status_code != 200:
                print("[ERROR] Failed to download audio:", audio_url)
                return None
            temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".aac")
            temp_audio.write(r.content)
            temp_audio.close()
            audio_file = temp_audio.name
        else:
            audio_file = audio_url

        # Step 2: Merge video + audio with FFmpeg
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_file,
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            output_path
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Step 3: Validate output
        if os.path.exists(output_path) and os.path.getsize(output_path) > 5000:
            print(f"[INFO] Audio added successfully → {output_path}")
            return output_path
        else:
            print("[ERROR] FFmpeg failed to add audio properly.")
            return None

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] add_audio_to_video failed (ffmpeg): {e}")
        return None
    except Exception as e:
        print(f"[ERROR] add_audio_to_video unexpected error: {e}")
        return None

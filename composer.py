import os
import subprocess
import json


def get_video_duration(path):
    """Retourne la durée d'une vidéo en secondes."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 60.0


def compose(
    background_path="background.mp4",
    avatar_path="avatar_talking.mp4",
    output_path="final.mp4"
):
    print("🎬 Composition finale 9:16...")

    if not os.path.exists(background_path):
        print(f"❌ Fond introuvable : {background_path}")
        return None

    if not os.path.exists(avatar_path):
        print(f"❌ Avatar introuvable : {avatar_path}")
        return None

    # Durée de référence = durée de la voix (avatar)
    avatar_duration = get_video_duration(avatar_path)
    print(f"   Durée avatar : {avatar_duration:.1f}s")

    # Dimensions finales : 1080x1920 (9:16 TikTok)
    # Avatar : 480x480, centré en bas (position y = 1920 - 500 = 1420)
    avatar_w = 480
    avatar_h = 480
    avatar_x = (1080 - avatar_w) // 2   # centré horizontalement = 300
    avatar_y = 1920 - avatar_h - 80      # en bas avec marge = 1360

    # Filtre FFmpeg :
    # 1. Redimensionne le fond à 1080x1920
    # 2. Redimensionne l'avatar
    # 3. Overlay l'avatar en bas centré
    # 4. Coupe à la durée de l'avatar
    filter_complex = (
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        f"crop=1080:1920,setpts=PTS-STARTPTS[bg];"
        f"[1:v]scale={avatar_w}:{avatar_h}:force_original_aspect_ratio=decrease,"
        f"pad={avatar_w}:{avatar_h}:(ow-iw)/2:(oh-ih)/2:color=black@0,"
        f"setpts=PTS-STARTPTS[av];"
        f"[bg][av]overlay={avatar_x}:{avatar_y}:shortest=1[out]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", background_path,
        "-i", avatar_path,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-map", "1:a",           # audio de l'avatar (voix off)
        "-t", str(avatar_duration),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        output_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"✅ Vidéo finale : {output_path} ({size_mb:.1f} MB)")
            return output_path
        else:
            print(f"❌ Erreur FFmpeg :\n{result.stderr[-1000:]}")
            return None
    except subprocess.TimeoutExpired:
        print("❌ Timeout FFmpeg.")
        return None
    except Exception as e:
        print(f"❌ Erreur inattendue : {e}")
        return None


if __name__ == "__main__":
    compose()

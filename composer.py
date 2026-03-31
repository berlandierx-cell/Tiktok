import os
import subprocess
import json

INTRO_DURATION = 5
OUTRO_DURATION = 5

WIDTH = 1080
HEIGHT = 1920


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


# ─────────────────────────────────────────────
# INTRO
# ─────────────────────────────────────────────

def create_intro(metadata_path="video_metadata.json", output="intro.mp4"):
    with open(metadata_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    titre = data.get("titre", "TITRE")
    niveau = data.get("niveau", "débutant")

    # Image du niveau
    niveau_image = {
        "débutant": "assets/debutant.png",
        "intermédiaire": "assets/intermediaire.png",
        "confirmé": "assets/confirme.png"
    }.get(niveau, "assets/debutant.png")

    print(f"🎬 Création intro ({niveau})...")

    # Bandeau transparent premium (70%)
    # Montserrat → nécessite que la police soit installée sur la machine runner
    drawtext = (
        "drawbox=x=0:y=H-260:w=W:h=220:color=black@0.30:t=fill,"
        "drawbox=x=0:y=H-260:w=W:h=220:color=white@0.9:t=3,"
        f"drawtext=text='{titre}':fontcolor=white:fontsize=72:"
        "font='Montserrat':x=(w-text_w)/2:y=H-200"
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", niveau_image,
        "-vf", drawtext,
        "-t", str(INTRO_DURATION),
        "-preset", "fast",
        output
    ]

    subprocess.run(cmd, capture_output=True)
    print(f"✅ Intro générée : {output}")


# ─────────────────────────────────────────────
# OUTRO
# ─────────────────────────────────────────────

def create_outro(output="outro.mp4"):
    print("🎬 Création outro...")

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", "assets/disclaimers.png",
        "-vf", "fade=t=in:st=0:d=0.5,fade=t=out:st=4.5:d=0.5",
        "-t", str(OUTRO_DURATION),
        "-preset", "fast",
        output
    ]

    subprocess.run(cmd, capture_output=True)
    print(f"✅ Outro générée : {output}")


# ─────────────────────────────────────────────
# FOND + AVATAR
# ─────────────────────────────────────────────

def compose_main(background="background.mp4", avatar="avatar_talking.mp4", output="main.mp4"):
    print("🎞️ Composition fond + avatar...")

    if not os.path.exists(background):
        print(f"❌ Fond introuvable : {background}")
        return None

    if not os.path.exists(avatar):
        print(f"❌ Avatar introuvable : {avatar}")
        return None

    avatar_duration = get_video_duration(avatar)
    print(f"   Durée avatar : {avatar_duration:.1f}s")

    # Placement avatar
    avatar_w = 480
    avatar_h = 480
    avatar_x = (WIDTH - avatar_w) // 2
    avatar_y = HEIGHT - avatar_h - 80

    filter_complex = (
        f"[0:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={WIDTH}:{HEIGHT},setpts=PTS-STARTPTS[bg];"
        f"[1:v]scale={avatar_w}:{avatar_h}:force_original_aspect_ratio=decrease,"
        f"pad={avatar_w}:{avatar_h}:(ow-iw)/2:(oh-ih)/2:color=black@0,"
        f"setpts=PTS-STARTPTS[av];"
        f"[bg][av]overlay={avatar_x}:{avatar_y}:shortest=1[out]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", background,
        "-i", avatar,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-map", "1:a",
        "-t", str(avatar_duration),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        output
    ]

    subprocess.run(cmd, capture_output=True)
    print(f"✅ Fond + avatar : {output}")
    return output


# ─────────────────────────────────────────────
# CONCAT FINAL
# ─────────────────────────────────────────────

def concat_all(intro="intro.mp4", main="main.mp4", outro="outro.mp4", output="final.mp4"):
    print("🔗 Concat final...")

    with open("concat_list.txt", "w") as f:
        f.write(f"file '{intro}'\n")
        f.write(f"file '{main}'\n")
        f.write(f"file '{outro}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "concat_list.txt",
        "-c", "copy",
        output
    ]

    subprocess.run(cmd, capture_output=True)
    print(f"🎉 Vidéo finale prête : {output}")


# ─────────────────────────────────────────────
# PIPELINE COMPLET
# ─────────────────────────────────────────────

def compose():
    create_intro()
    create_outro()
    compose_main()
    concat_all()


if __name__ == "__main__":
    compose()
import os
import subprocess
import json

WIDTH  = 1080
HEIGHT = 1920

INTRO_DURATION = 5
OUTRO_DURATION = 3


def get_duration(path):
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


def check_file(path, label):
    if not os.path.exists(path):
        print(f"❌ Fichier manquant [{label}] : {path}")
        return False
    size = os.path.getsize(path)
    print(f"   ✓ {label} : {path} ({size // 1024} KB)")
    return True


# ─────────────────────────────────────────────
# INTRO (5 secondes, image + titre, sans son)
# ─────────────────────────────────────────────

def create_intro(metadata_path="video_metadata.json", output="intro.mp4"):
    with open(metadata_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    titre  = data.get("titre", "TRADING").replace("'", "\\'")
    niveau = data.get("niveau", "débutant")

    niveau_image_map = {
        "débutant":      "assets/Debutant.png",
        "intermédiaire": "assets/Intermediare.png",
        "confirmé":      "assets/confirme.png"
    }

    niveau_image = niveau_image_map.get(niveau, "assets/Debutant.png")

    print(f"🎬 Création intro ({niveau})...")

    vf = (
        "scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        "drawbox=x=0:y=H-280:w=W:h=240:color=black@0.55:t=fill,"
        f"drawtext=text='{titre}':fontcolor=white:fontsize=60:"
        "x=(w-text_w)/2:y=H-220:shadowcolor=black:shadowx=2:shadowy=2"
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", niveau_image,
        "-vf", vf,
        "-t", str(INTRO_DURATION),
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        output
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Erreur intro FFmpeg :\n{result.stderr[-500:]}")
    else:
        print(f"✅ Intro générée : {output}")


# ─────────────────────────────────────────────
# OUTRO
# ─────────────────────────────────────────────

def create_outro(output="outro.mp4"):
    print("🎬 Création outro...")
    disclaimer = "assets/disclaimers.png"

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", disclaimer,
        "-vf", (
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,"
            f"fade=t=in:st=0:d=0.5,fade=t=out:st={OUTRO_DURATION - 0.5}:d=0.5"
        ),
        "-t", str(OUTRO_DURATION),
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        output
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Erreur outro :\n{result.stderr[-300:]}")
    else:
        print(f"✅ Outro générée : {output}")


# ─────────────────────────────────────────────
# AVATAR ROND + CONTOUR BLANC 3px
# ─────────────────────────────────────────────

def compose_main(background="background.mp4", avatar="avatar_talking.mp4",
                 metadata_path="video_metadata.json", output="main.mp4"):

    print("🎞️ Composition fond + avatar rond...")

    if not check_file(background, "background"):
        return None
    if not check_file(avatar, "avatar"):
        return None

    avatar_duration = get_duration(avatar)
    bg_duration     = get_duration(background)
    print(f"   Durée avatar : {avatar_duration:.1f}s | Fond : {bg_duration:.1f}s")

    av_w = 460
    av_h = 460

    av_x = WIDTH - av_w - 60
    av_y = HEIGHT - av_h - 100

    # Masque circulaire + contour blanc 3px
    filter_complex = (
        # Fond
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,setpts=PTS-STARTPTS[bg];"

        # Avatar → RGBA
        f"[1:v]scale={av_w}:{av_h},format=rgba[av0];"

        # Masque cercle
        f"[av0]geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':"
        f"a='if((X-{av_w/2})^2+(Y-{av_h/2})^2<{(av_w/2-3)**2},255,0)'[av_masked];"

        # Contour blanc (3px)
        f"[av0]geq=r='255':g='255':b='255':"
        f"a='if((X-{av_w/2})^2+(Y-{av_h/2})^2<{(av_w/2)**2},255,0)'[av_border];"

        # Fusion contour + avatar
        "[av_border][av_masked]overlay=(W-w)/2:(H-h)/2:format=auto[av_final];"

        # Overlay final
        f"[bg][av_final]overlay={av_x}:{av_y}:shortest=1[out]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", background,
        "-i", avatar,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-map", "1:a",
        "-t", str(avatar_duration),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        output
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        print(f"❌ Erreur composition :\n{result.stderr[-800:]}")
        return None

    print(f"✅ Composition : {output} ({os.path.getsize(output) // (1024*1024)} MB)")
    return output


# ─────────────────────────────────────────────
# CONCAT FINAL
# ─────────────────────────────────────────────

def concat_all(intro="intro.mp4", main="main.mp4", outro="outro.mp4",
               output="final_video.mp4"):
    print("🔗 Assemblage final...")

    parts = []
    for f, label in [(intro, "intro"), (main, "main"), (outro, "outro")]:
        if os.path.exists(f) and os.path.getsize(f) > 1000:
            parts.append(f)
            print(f"   ✓ {label} inclus")
        else:
            print(f"   ⚠️ {label} ignoré (manquant ou vide)")

    if not parts:
        print("❌ Aucune partie valide pour le concat")
        return None

    with open("concat_list.txt", "w") as f:
        for p in parts:
            f.write(f"file '{os.path.abspath(p)}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "concat_list.txt",
        "-c", "copy",
        output
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"❌ Erreur concat :\n{result.stderr[-500:]}")
        return None

    size_mb = os.path.getsize(output) / (1024 * 1024)
    print(f"🎉 Vidéo finale : {output} ({size_mb:.1f} MB)")
    return output


# ─────────────────────────────────────────────
# PIPELINE COMPLET
# ─────────────────────────────────────────────

def compose():
    create_intro()
    create_outro()
    main = compose_main()
    if main:
        concat_all()
    else:
        print("❌ Composition principale échouée, final_video.mp4 non créé")


if __name__ == "__main__":
    compose()
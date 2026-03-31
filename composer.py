import os
import subprocess
import json
import random

WIDTH  = 1080
HEIGHT = 1920

INTRO_DURATION = 3
OUTRO_DURATION = 3

# Zones où l’avatar peut apparaître
ZONES = {
    "bottom_left":  (60,  HEIGHT - 620),
    "bottom_right": (WIDTH - 540, HEIGHT - 620),
    "bottom_center":(WIDTH // 2 - 240, HEIGHT - 620),
}

SEGMENT_DURATION = 2.0   # Avatar bouge toutes les X secondes


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
# INTRO
# ─────────────────────────────────────────────

def create_intro(metadata_path="video_metadata.json", output="intro.mp4"):
    with open(metadata_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    titre  = data.get("titre", "TRADING").replace("'", "\\'")
    niveau = data.get("niveau", "débutant")

    # Correction des noms (Linux = sensible à la casse)
    niveau_image_map = {
        "débutant":      "assets/debutant.png",
        "intermédiaire": "assets/intermediaire.png",
        "confirmé":      "assets/confirme.png"
    }
    niveau_image = niveau_image_map.get(niveau, "assets/debutant.png")

    print(f"🎬 Création intro ({niveau})...")

    vf = (
        f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"drawbox=x=0:y=H-280:w=W:h=240:color=black@0.55:t=fill,"
        f"drawtext=text='{titre}':fontcolor=white:fontsize=60:"
        f"x=(w-text_w)/2:y=H-220:shadowcolor=black:shadowx=2:shadowy=2"
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
        print(f"✅ Intro : {output}")


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
            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
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
        print(f"✅ Outro : {output}")


# ─────────────────────────────────────────────
# COMPOSITION PRINCIPALE
# ─────────────────────────────────────────────

def compose_main(background="background.mp4", avatar="avatar_talking.mp4",
                 metadata_path="video_metadata.json", output="main.mp4"):

    print("🎞️ Composition fond + avatar dynamique...")

    if not check_file(background, "background"):
        return None
    if not check_file(avatar, "avatar"):
        return None

    avatar_duration = get_duration(avatar)
    bg_duration     = get_duration(background)
    print(f"   Durée avatar : {avatar_duration:.1f}s | Fond : {bg_duration:.1f}s")

    # Taille avatar
    av_w = 460
    av_h = 460

    # Génération des segments dynamiques
    positions = list(ZONES.values())
    segments = []
    t = 0.0
    last_pos = None

    while t < avatar_duration:
        pos = random.choice(positions)
        while pos == last_pos:
            pos = random.choice(positions)

        segments.append((t, min(t + SEGMENT_DURATION, avatar_duration), pos))
        last_pos = pos
        t += SEGMENT_DURATION

    # Construction du filtre FFmpeg
    filter_complex = (
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        f"crop=1080:1920,setpts=PTS-STARTPTS[bg0];"
        f"[1:v]scale={av_w}:{av_h},colorkey=0x000000:0.25:0.08,setpts=PTS-STARTPTS[av];"
    )

    current = "bg0"
    for i, (start, end, (x, y)) in enumerate(segments):
        filter_complex += (
            f"[{current}][av]overlay={x}:{y}:enable='between(t,{start},{end})'[bg{i+1}];"
        )
        current = f"bg{i+1}"

    filter_complex += f"[{current}]copy[out]"

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
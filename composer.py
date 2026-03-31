import os
import subprocess
import json
import random

WIDTH = 1080
HEIGHT = 1920

INTRO_DURATION = 5
OUTRO_DURATION = 5

# Zones sûres (pondérées selon le fond)
ZONES = {
    "top_left":    (80, 200),
    "top_right":   (WIDTH - 560, 200),
    "bottom_left": (80, HEIGHT - 700),
    "bottom_right":(WIDTH - 560, HEIGHT - 700)
}

def get_video_duration(path):
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

    niveau_image = {
        "débutant": "assets/debutant.png",
        "intermédiaire": "assets/intermediaire.png",
        "confirmé": "assets/confirme.png"
    }.get(niveau, "assets/debutant.png")

    print(f"🎬 Création intro ({niveau})...")

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
# POSITIONS DYNAMIQUES
# ─────────────────────────────────────────────

def generate_avatar_positions(metadata_path="video_metadata.json"):
    with open(metadata_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    sous_titres = data.get("sous_titres", [])
    fond_type = data.get("fond_type", "chandeliers")

    # Pondération selon le fond
    if fond_type in ["indicateur_rsi", "indicateur_macd"]:
        weights = {
            "top_left": 3, "top_right": 3,
            "bottom_left": 1, "bottom_right": 1
        }
    elif fond_type == "texte_cles":
        weights = {
            "top_left": 2, "top_right": 2,
            "bottom_left": 2, "bottom_right": 2
        }
    else:
        weights = {
            "top_left": 2, "top_right": 2,
            "bottom_left": 2, "bottom_right": 2
        }

    positions = []
    last_zone = None

    for _ in sous_titres:
        zones = list(weights.keys())
        weights_list = list(weights.values())

        while True:
            zone = random.choices(zones, weights_list)[0]
            if zone != last_zone:
                break

        positions.append(zone)
        last_zone = zone

    return positions


# ─────────────────────────────────────────────
# SCRIPT FFmpeg DYNAMIQUE
# ─────────────────────────────────────────────

def generate_ffscript():
    script = r"""
# FFmpeg dynamic avatar script

[1:v]split=2[av0][av1];

# Remove black background
[av0]chromakey=0x000000:0.12:0.08,format=rgba[cut];

# Scale dynamically
[cut]scale='scale:scale'[scaled];

# Fade transition
[scaled]fade=t=in:st=0:d=0.25,fade=t=out:st=0.75:d=0.25[fade];

# Pop transition
[scaled]scale='scale*1.05:scale*1.05',fade=t=in:st=0:d=0.25[pop];

# Choose transition
[fade][pop]blend=all_expr='
    posfile="avatar_positions.txt";
    line=trunc(t/1);
    tr=readfile(posfile, line, 4);
    if(eq(tr,"fade"),A,B)
'[avatar];

# Overlay
[0:v][avatar]overlay=x='xpos':y='ypos':shortest=1[out]
"""
    with open("avatar_dynamic.ffscript", "w") as f:
        f.write(script)


# ─────────────────────────────────────────────
# MAIN COMPOSITION
# ─────────────────────────────────────────────

def compose_main(background="background.mp4", avatar="avatar_talking.mp4",
                 metadata_path="video_metadata.json", output="main.mp4"):

    print("🎞️ Composition fond + avatar dynamique...")

    avatar_duration = get_video_duration(avatar)

    positions = generate_avatar_positions(metadata_path)

    # Génération du fichier positions
    with open("avatar_positions.txt", "w") as f:
        for i, zone in enumerate(positions):
            x, y = ZONES[zone]
            size = random.choice([450, 480])
            transition = random.choice(["fade", "pop"])
            f.write(f"{i} {x} {y} {size} {transition}\n")

    # Génération du script FFmpeg
    generate_ffscript()

    cmd = [
        "ffmpeg", "-y",
        "-i", background,
        "-i", avatar,
        "-filter_complex_script", "avatar_dynamic.ffscript",
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
    print(f"✅ Fond + avatar dynamique : {output}")
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
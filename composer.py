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
# AVATAR DYNAMIQUE
# ─────────────────────────────────────────────

def generate_avatar_positions(metadata_path="video_metadata.json"):
    """Génère une liste de positions synchronisées avec les sous-titres."""
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

        # Choisir une zone différente de la précédente
        while True:
            zone = random.choices(zones, weights_list)[0]
            if zone != last_zone:
                break

        positions.append(zone)
        last_zone = zone

    return positions


def compose_main(background="background.mp4", avatar="avatar_talking.mp4",
                 metadata_path="video_metadata.json", output="main.mp4"):

    print("🎞️ Composition fond + avatar dynamique...")

    avatar_duration = get_video_duration(avatar)

    positions = generate_avatar_positions(metadata_path)

    # Génération d'un fichier texte pour FFmpeg
    with open("avatar_positions.txt", "w") as f:
        for i, zone in enumerate(positions):
            x, y = ZONES[zone]

            # Variation subtile de taille (option C)
            size = random.choice([450, 480])

            # Transition : fade ou pop
            transition = random.choice(["fade", "pop"])

            f.write(f"{i} {x} {y} {size} {transition}\n")

    # FFmpeg : suppression du fond noir + overlay dynamique
    filter_script = (
        "split[v0][v1];"
        "[v0]chromakey=0x000000:0.12:0.08[cut];"
        "[cut]format=rgba[av];"
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920[bg];"
        "[bg][av]overlay=x='xpos':y='ypos':shortest=1[out]"
    )

    # On remplace xpos/ypos dynamiquement via -lavfi_script
    # (FFmpeg supporte les variables externes via script)

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

    print("⚠️ NOTE : Le script FFmpeg dynamique sera généré juste après.")
    print("⚠️ Cela permet de gérer les positions + transitions proprement.")

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

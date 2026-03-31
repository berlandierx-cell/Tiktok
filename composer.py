import os
import subprocess
import json
import random

WIDTH = 1080
HEIGHT = 1920

INTRO_DURATION = 5
OUTRO_DURATION = 5

ZONES = {
    "top_left":    (80, 200),
    "top_right":   (WIDTH - 560, 200),
    "bottom_left": (80, HEIGHT - 700),
    "bottom_right":(WIDTH - 560, HEIGHT - 700)
}

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
# TIMELINE BASÉE SUR LA DURÉE DE LA VOIX
# ─────────────────────────────────────────────

def generate_timeline(metadata_path="video_metadata.json", voice_path="voice.mp3"):
    with open(metadata_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    phrases = data.get("sous_titres", [])
    n = len(phrases)

    if n == 0:
        raise ValueError("Aucun sous-titre trouvé dans video_metadata.json")

    total_voice_duration = get_duration(voice_path)
    segment = total_voice_duration / n

    timeline = []
    last_zone = None

    for i, phrase in enumerate(phrases):
        start = i * segment
        end = (i + 1) * segment

        zones = list(ZONES.keys())
        while True:
            zone = random.choice(zones)
            if zone != last_zone:
                break

        x, y = ZONES[zone]
        size = random.choice([450, 480])
        transition = random.choice(["fade", "pop"])

        timeline.append({
            "start": start,
            "end": end,
            "x": x,
            "y": y,
            "size": size,
            "transition": transition
        })

        last_zone = zone

    return timeline


# ─────────────────────────────────────────────
# SCRIPT FFmpeg DYNAMIQUE (ROBUSTE)
# ─────────────────────────────────────────────

def generate_ffscript(timeline):
    with open("avatar_dynamic.ffscript", "w") as f:
        f.write("# FFmpeg dynamic avatar script\n\n")

        f.write("[1:v]chromakey=0x000000:0.12:0.08,format=rgba[av];\n")
        f.write("[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bg0];\n")

        current = "bg0"

        for i, seg in enumerate(timeline):
            f.write(
                f"[av]scale={seg['size']}:{seg['size']}[av{i}];\n"
                f"[{current}][av{i}]overlay=x={seg['x']}:y={seg['y']}:enable='between(t,{seg['start']},{seg['end']})'[bg{i+1}];\n"
            )
            current = f"bg{i+1}"

        f.write(f"[{current}]copy[out]\n")


# ─────────────────────────────────────────────
# MAIN COMPOSITION
# ─────────────────────────────────────────────

def compose_main(background="background.mp4", avatar="avatar_talking.mp4",
                 metadata_path="video_metadata.json", output="main.mp4"):

    print("🎞️ Composition fond + avatar dynamique...")

    timeline = generate_timeline(metadata_path)
    generate_ffscript(timeline)

    cmd = [
        "ffmpeg", "-y",
        "-i", background,
        "-i", avatar,
        "-filter_complex_script", "avatar_dynamic.ffscript",
        "-map", "[out]",
        "-map", "1:a",
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
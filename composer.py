import os
import subprocess
import json

WIDTH  = 1080
HEIGHT = 1920

INTRO_DURATION = 5
OUTRO_DURATION = 3

AV_SIZE = 460

POP_POSITIONS = [
    (60,                   HEIGHT - AV_SIZE - 120),
    (WIDTH - AV_SIZE - 60, HEIGHT - AV_SIZE - 120),
    ((WIDTH - AV_SIZE)//2, HEIGHT - AV_SIZE - 120),
    (80,                   HEIGHT - AV_SIZE - 260),
    (WIDTH - AV_SIZE - 80, HEIGHT - AV_SIZE - 260),
]


def get_duration(path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
           "-of", "default=noprint_wrappers=1:nokey=1", path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 60.0


def check_file(path, label):
    if not os.path.exists(path):
        print(f"❌ Fichier manquant [{label}] : {path}")
        return False
    print(f"   ✓ {label} ({os.path.getsize(path) // 1024} KB)")
    return True


def create_circle_mask(size=460, border=6):
    try:
        from PIL import Image, ImageDraw
        # Masque alpha (disque blanc)
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse([border, border, size-border, size-border], fill=255)
        mask.save("circle_mask.png")
        # Contour blanc RGBA
        brd = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(brd)
        d.ellipse([0, 0, size, size], fill=(255, 255, 255, 255))
        d.ellipse([border, border, size-border, size-border], fill=(0, 0, 0, 0))
        brd.save("circle_border.png")
        print(f"   ✓ Masques circulaires générés")
        return True
    except ImportError:
        print("   ⚠️ PIL absent, fallback colorkey")
        return False


def create_intro(metadata_path="video_metadata.json", output="intro.mp4"):
    with open(metadata_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    titre  = data.get("titre", "TRADING").replace("'", "").replace(":", " -")
    niveau = data.get("niveau", "débutant")
    niveau_image_map = {
        "débutant":      "assets/Debutant.png",
        "intermédiaire": "assets/Intermediare.png",
        "confirmé":      "assets/confirme.png"
    }
    niveau_image = niveau_image_map.get(niveau, "assets/Debutant.png")
    print(f"🎬 Intro ({niveau})...")
    if not os.path.exists(niveau_image):
        cmd = ["ffmpeg", "-y", "-f", "lavfi",
               "-i", f"color=black:s=1080x1920:d={INTRO_DURATION}",
               "-vf", f"drawtext=text='{titre}':fontcolor=white:fontsize=55:x=(w-text_w)/2:y=(h-text_h)/2",
               "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p", output]
    else:
        vf = (f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
              f"drawbox=x=0:y=1640:w=1080:h=240:color=black@0.55:t=fill,"
              f"drawtext=text='{titre}':fontcolor=white:fontsize=55:"
              f"x=(w-text_w)/2:y=1700:shadowcolor=black:shadowx=2:shadowy=2")
        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", niveau_image,
               "-vf", vf, "-t", str(INTRO_DURATION),
               "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p", output]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Erreur intro :\n{result.stderr[-400:]}")
    else:
        print(f"✅ Intro : {output}")


def create_outro(output="outro.mp4"):
    print("🎬 Outro...")
    disclaimer = "assets/disclaimers.png"
    if os.path.exists(disclaimer):
        vf = (f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
              f"fade=t=in:st=0:d=0.5,fade=t=out:st={OUTRO_DURATION-0.5}:d=0.5")
        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", disclaimer,
               "-vf", vf, "-t", str(OUTRO_DURATION),
               "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p", output]
    else:
        cmd = ["ffmpeg", "-y", "-f", "lavfi",
               "-i", f"color=black:s=1080x1920:d={OUTRO_DURATION}",
               "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p", output]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Erreur outro :\n{result.stderr[-300:]}")
    else:
        print(f"✅ Outro : {output}")


def compose_main(background="background.mp4", avatar="avatar_talking.mp4",
                 metadata_path="video_metadata.json", output="main.mp4"):
    print("🎞️ Composition fond + avatar (pop dynamique)...")
    if not check_file(background, "background"): return None
    if not check_file(avatar, "avatar"):          return None

    avatar_duration = get_duration(avatar)
    print(f"   Durée avatar : {avatar_duration:.1f}s")

    has_mask = create_circle_mask(size=AV_SIZE, border=6)

    with open(metadata_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    sous_titres = data.get("sous_titres", [])
    n = max(len(sous_titres), 1)
    seg = avatar_duration / n

    # Séquence de positions alternées gauche/droite
    positions = []
    last_idx = -1
    for i in range(n):
        candidates = [j for j in range(len(POP_POSITIONS)) if j != last_idx]
        idx = candidates[i % len(candidates)]
        positions.append(POP_POSITIONS[idx])
        last_idx = idx

    filter_parts = []

    # --- Fond ---
    filter_parts.append(
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,setpts=PTS-STARTPTS[bg]"
    )

    if has_mask:
        # --- Avatar brut → RGBA ---
        filter_parts.append(
            f"[1:v]scale={AV_SIZE}:{AV_SIZE}:force_original_aspect_ratio=decrease,"
            f"pad={AV_SIZE}:{AV_SIZE}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"setpts=PTS-STARTPTS,format=rgba[av_raw]"
        )
        # --- Masque + border ---
        filter_parts.append(f"[2:v]scale={AV_SIZE}:{AV_SIZE},format=rgba[mask]")
        filter_parts.append(f"[3:v]scale={AV_SIZE}:{AV_SIZE},format=rgba[border]")
        # --- Appliquer masque circulaire ---
        filter_parts.append("[av_raw][mask]alphamerge[av_circle]")
        # --- Fusionner contour + avatar ---
        filter_parts.append("[border][av_circle]overlay=0:0:format=auto[av_base]")

        # --- Dupliquer av_base pour chaque segment ---
        # On split av_base en n copies
        split_outputs = "".join([f"[av{i}]" for i in range(n)])
        filter_parts.append(f"[av_base]split={n}{split_outputs}")

        # --- Overlays successifs, chacun consomme sa propre copie ---
        current = "bg"
        for i, (px, py) in enumerate(positions):
            t_start = i * seg
            t_end   = (i + 1) * seg
            enable  = f"between(t,{t_start:.3f},{t_end:.3f})"
            out_label = f"vout{i+1}"
            filter_parts.append(
                f"[{current}][av{i}]overlay={px}:{py}:"
                f"enable='{enable}':shortest=0[{out_label}]"
            )
            current = out_label

        filter_parts.append(f"[{current}]copy[out]")

        cmd = [
            "ffmpeg", "-y",
            "-i", background,
            "-i", avatar,
            "-i", "circle_mask.png",
            "-i", "circle_border.png",
            "-filter_complex", ";".join(filter_parts),
            "-map", "[out]", "-map", "1:a",
            "-t", str(avatar_duration),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k", "-pix_fmt", "yuv420p",
            output
        ]

    else:
        # --- Fallback colorkey ---
        filter_parts.append(
            f"[1:v]scale={AV_SIZE}:{AV_SIZE}:force_original_aspect_ratio=decrease,"
            f"pad={AV_SIZE}:{AV_SIZE}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"colorkey=0x000000:0.20:0.05,setpts=PTS-STARTPTS[av_base]"
        )
        split_outputs = "".join([f"[av{i}]" for i in range(n)])
        filter_parts.append(f"[av_base]split={n}{split_outputs}")

        current = "bg"
        for i, (px, py) in enumerate(positions):
            t_start = i * seg
            t_end   = (i + 1) * seg
            enable  = f"between(t,{t_start:.3f},{t_end:.3f})"
            out_label = f"vout{i+1}"
            filter_parts.append(
                f"[{current}][av{i}]overlay={px}:{py}:"
                f"enable='{enable}':shortest=0[{out_label}]"
            )
            current = out_label

        filter_parts.append(f"[{current}]copy[out]")

        cmd = [
            "ffmpeg", "-y",
            "-i", background,
            "-i", avatar,
            "-filter_complex", ";".join(filter_parts),
            "-map", "[out]", "-map", "1:a",
            "-t", str(avatar_duration),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k", "-pix_fmt", "yuv420p",
            output
        ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        print(f"❌ Erreur composition :\n{result.stderr[-1000:]}")
        return None

    size_mb = os.path.getsize(output) / (1024 * 1024)
    print(f"✅ Composition : {output} ({size_mb:.1f} MB)")
    return output


def concat_all(intro="intro.mp4", main="main.mp4", outro="outro.mp4",
               output="final_video.mp4"):
    print("🔗 Assemblage final...")
    parts = []
    for f, label in [(intro, "intro"), (main, "main"), (outro, "outro")]:
        if os.path.exists(f) and os.path.getsize(f) > 1000:
            parts.append(f)
            print(f"   ✓ {label}")
        else:
            print(f"   ⚠️ {label} ignoré")
    if not parts:
        print("❌ Rien à assembler")
        return None
    with open("concat_list.txt", "w") as f:
        for p in parts:
            f.write(f"file '{os.path.abspath(p)}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
           "-i", "concat_list.txt", "-c", "copy", output]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"❌ Erreur concat :\n{result.stderr[-400:]}")
        return None
    size_mb = os.path.getsize(output) / (1024 * 1024)
    print(f"🎉 Vidéo finale : {output} ({size_mb:.1f} MB)")
    return output


def compose():
    create_intro()
    create_outro()
    main = compose_main()
    if main:
        concat_all()
    else:
        print("❌ Pipeline interrompu")


if __name__ == "__main__":
    compose()

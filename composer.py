import os
import subprocess
import json
import math

WIDTH  = 1080
HEIGHT = 1920

INTRO_DURATION = 5
OUTRO_DURATION = 3

AV_SIZE = 420  # légèrement réduit pour mieux s'insérer

# Zone graphique background.py : header(10%) + graphique(48%) = 58% = 0→1113px
# Zone sous-titres background.py : 42% du bas = 1113→1920px  (807px de haut)
# → Avatar doit être SOUS y=1500 pour ne pas toucher les sous-titres
# → Sous-titres sont entre y≈1200 et y≈1750 sur l'image finale
# On place l'avatar encore plus bas : y_min = 1520

POP_POSITIONS = [
    # (x, y)  — avatar de 420px, zone safe : y entre 1500 et 1920-420=1500
    # On varie x gauche/droite, y légèrement pour du dynamisme
    (60,                   1500),   # gauche bas
    (WIDTH - AV_SIZE - 60, 1500),   # droite bas
    ((WIDTH - AV_SIZE)//2, 1490),   # centre bas
    (80,                   1470),   # gauche légèrement plus haut
    (WIDTH - AV_SIZE - 80, 1470),   # droite légèrement plus haut
]

SUBTITLES_PER_POP = 3


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


def create_circle_mask(size=420, border=6):
    try:
        from PIL import Image, ImageDraw
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse([border, border, size-border, size-border], fill=255)
        mask.save("circle_mask.png")
        brd = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(brd)
        d.ellipse([0, 0, size, size], fill=(255, 255, 255, 255))
        d.ellipse([border, border, size-border, size-border], fill=(0, 0, 0, 0))
        brd.save("circle_border.png")
        print(f"   ✓ Masques circulaires générés ({size}px)")
        return True
    except ImportError:
        print("   ⚠️ PIL absent, fallback colorkey")
        return False


def wrap_title(titre, max_chars=22):
    """Découpe le titre en 2 lignes max pour FFmpeg drawtext."""
    words = titre.split()
    line1, line2 = [], []
    current = []
    for w in words:
        if len(" ".join(current + [w])) <= max_chars:
            current.append(w)
        else:
            if not line1:
                line1 = current
                current = [w]
            else:
                line2 = current + [w]
                break
    if not line1:
        line1 = current
    elif not line2:
        line2 = current if current != line1 else []

    l1 = " ".join(line1)
    l2 = " ".join(line2) if line2 else ""
    return l1, l2


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

    line1, line2 = wrap_title(titre, max_chars=20)
    print(f"   Titre ligne 1 : '{line1}'")
    if line2:
        print(f"   Titre ligne 2 : '{line2}'")

    # Taille de fonte adaptée à la longueur
    fontsize = 75 if len(line1) <= 15 else 60

    if not os.path.exists(niveau_image):
        vf_parts = [
            f"color=black:s=1080x1920:d={INTRO_DURATION}",
            f"drawtext=text='{line1}':fontcolor=white:fontsize={fontsize}:"
            f"x=(w-text_w)/2:y=860:shadowcolor=black:shadowx=3:shadowy=3"
        ]
        if line2:
            vf_parts.append(
                f"drawtext=text='{line2}':fontcolor=white:fontsize={fontsize}:"
                f"x=(w-text_w)/2:y={860 + fontsize + 10}:shadowcolor=black:shadowx=3:shadowy=3"
            )
        cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", ",".join(vf_parts[:1]),
               "-vf", ",".join(vf_parts[1:]),
               "-t", str(INTRO_DURATION), "-r", "30",
               "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
               "-an", output]
    else:
        # Bande noire au centre + titre sur 1 ou 2 lignes + niveau en cyan
        y1 = 820
        y2 = y1 + fontsize + 15
        y_niveau = y2 + fontsize + 20 if line2 else y1 + fontsize + 20

        vf = (
            f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"drawbox=x=0:y=750:w=1080:h=400:color=black@0.65:t=fill,"
            f"drawtext=text='{line1}':"
            f"fontcolor=white:fontsize={fontsize}:"
            f"x=(w-text_w)/2:y={y1}:"
            f"shadowcolor=black:shadowx=4:shadowy=4"
        )
        if line2:
            vf += (
                f",drawtext=text='{line2}':"
                f"fontcolor=white:fontsize={fontsize}:"
                f"x=(w-text_w)/2:y={y2}:"
                f"shadowcolor=black:shadowx=4:shadowy=4"
            )
        vf += (
            f",drawtext=text='{niveau.upper()}':"
            f"fontcolor=#00e5ff:fontsize=46:"
            f"x=(w-text_w)/2:y={y_niveau}:"
            f"shadowcolor=black:shadowx=3:shadowy=3"
        )

        cmd = ["ffmpeg", "-y",
               "-loop", "1", "-i", niveau_image,
               "-vf", vf,
               "-t", str(INTRO_DURATION), "-r", "30",
               "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
               "-an", output]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Erreur intro :\n{result.stderr[-400:]}")
    else:
        print(f"✅ Intro : {output}")


def create_outro(output="outro.mp4"):
    print("🎬 Outro...")
    disclaimer = "assets/disclaimers.png"
    if os.path.exists(disclaimer):
        vf = (
            f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"fade=t=in:st=0:d=0.5,fade=t=out:st={OUTRO_DURATION-0.5}:d=0.5"
        )
        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", disclaimer,
               "-vf", vf, "-t", str(OUTRO_DURATION), "-r", "30",
               "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
               "-an", output]
    else:
        cmd = ["ffmpeg", "-y", "-f", "lavfi",
               "-i", f"color=black:s=1080x1920:d={OUTRO_DURATION}",
               "-r", "30", "-c:v", "libx264", "-preset", "fast",
               "-pix_fmt", "yuv420p", "-an", output]
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
    n_subtitles = max(len(sous_titres), 1)
    n_pops = max(math.ceil(n_subtitles / SUBTITLES_PER_POP), 1)
    seg = avatar_duration / n_pops

    print(f"   {n_subtitles} sous-titres → {n_pops} positions")

    positions = []
    last_idx = -1
    for i in range(n_pops):
        candidates = [j for j in range(len(POP_POSITIONS)) if j != last_idx]
        idx = candidates[i % len(candidates)]
        positions.append(POP_POSITIONS[idx])
        last_idx = idx

    filter_parts = []
    filter_parts.append(
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,setpts=PTS-STARTPTS[bg]"
    )

    if has_mask:
        filter_parts.append(
            f"[1:v]scale={AV_SIZE}:{AV_SIZE}:force_original_aspect_ratio=decrease,"
            f"pad={AV_SIZE}:{AV_SIZE}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"setpts=PTS-STARTPTS,format=rgba[av_raw]"
        )
        filter_parts.append(f"[2:v]scale={AV_SIZE}:{AV_SIZE},format=rgba[mask]")
        filter_parts.append(f"[3:v]scale={AV_SIZE}:{AV_SIZE},format=rgba[border]")
        filter_parts.append("[av_raw][mask]alphamerge[av_circle]")
        filter_parts.append("[border][av_circle]overlay=0:0:format=auto[av_base]")
        split_outputs = "".join([f"[av{i}]" for i in range(n_pops)])
        filter_parts.append(f"[av_base]split={n_pops}{split_outputs}")

        current = "bg"
        for i, (px, py) in enumerate(positions):
            t_start = i * seg
            t_end   = (i + 1) * seg
            out_label = f"vout{i+1}"
            filter_parts.append(
                f"[{current}][av{i}]overlay={px}:{py}:"
                f"enable='between(t,{t_start:.3f},{t_end:.3f})':shortest=0[{out_label}]"
            )
            current = out_label
        filter_parts.append(f"[{current}]copy[out]")

        cmd = [
            "ffmpeg", "-y",
            "-i", background, "-i", avatar,
            "-i", "circle_mask.png", "-i", "circle_border.png",
            "-filter_complex", ";".join(filter_parts),
            "-map", "[out]", "-map", "1:a",
            "-t", str(avatar_duration), "-r", "30",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k", "-pix_fmt", "yuv420p",
            output
        ]
    else:
        filter_parts.append(
            f"[1:v]scale={AV_SIZE}:{AV_SIZE}:force_original_aspect_ratio=decrease,"
            f"pad={AV_SIZE}:{AV_SIZE}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"colorkey=0x000000:0.20:0.05,setpts=PTS-STARTPTS[av_base]"
        )
        split_outputs = "".join([f"[av{i}]" for i in range(n_pops)])
        filter_parts.append(f"[av_base]split={n_pops}{split_outputs}")

        current = "bg"
        for i, (px, py) in enumerate(positions):
            t_start = i * seg
            t_end   = (i + 1) * seg
            out_label = f"vout{i+1}"
            filter_parts.append(
                f"[{current}][av{i}]overlay={px}:{py}:"
                f"enable='between(t,{t_start:.3f},{t_end:.3f})':shortest=0[{out_label}]"
            )
            current = out_label
        filter_parts.append(f"[{current}]copy[out]")

        cmd = [
            "ffmpeg", "-y",
            "-i", background, "-i", avatar,
            "-filter_complex", ";".join(filter_parts),
            "-map", "[out]", "-map", "1:a",
            "-t", str(avatar_duration), "-r", "30",
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
            parts.append((f, label))
            print(f"   ✓ {label}")
        else:
            print(f"   ⚠️ {label} ignoré")

    if not parts:
        print("❌ Rien à assembler")
        return None

    normalized = []
    for f, label in parts:
        out_norm = f"norm_{label}.mp4"
        dur = get_duration(f)
        if label == "main":
            cmd = [
                "ffmpeg", "-y", "-i", f,
                "-r", "30",
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
                "-pix_fmt", "yuv420p", out_norm
            ]
        else:
            cmd = [
                "ffmpeg", "-y", "-i", f,
                "-f", "lavfi", "-i", f"aevalsrc=0:c=stereo:s=44100:d={dur}",
                "-r", "30",
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
                "-pix_fmt", "yuv420p", "-shortest", out_norm
            ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            normalized.append(out_norm)
            print(f"   ✓ {label} normalisé")
        else:
            print(f"   ❌ Normalisation {label} échouée :\n{result.stderr[-200:]}")

    if not normalized:
        print("❌ Aucune partie normalisée")
        return None

    inputs = []
    filter_v = ""
    filter_a = ""
    for i, p in enumerate(normalized):
        inputs += ["-i", p]
        filter_v += f"[{i}:v]"
        filter_a += f"[{i}:a]"

    n = len(normalized)
    filter_complex = (
        f"{filter_v}concat=n={n}:v=1:a=0[vout];"
        f"{filter_a}concat=n={n}:v=0:a=1[aout]"
    )

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        output
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if result.returncode != 0:
        print(f"❌ Erreur concat :\n{result.stderr[-500:]}")
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

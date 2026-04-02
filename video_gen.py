import os
import json
import asyncio
import subprocess
import edge_tts

AVATAR_PATH = "assets/1774899221632.png"
ASSETS_DIR = "assets"
WAV2LIP_DIR = os.path.expanduser("~/Wav2Lip")

INTRO_DURATION = 5
OUTRO_DURATION = 5

NIVEAU_TO_IMAGE = {
    "débutant": "debutant.png",
    "intermédiaire": "intermediaire.png",
    "confirmé": "confirme.png"
}


async def generate_audio(text):
    print("🎙️ Création audio...")
    communicate = edge_tts.Communicate(text, "fr-FR-RemyNeural")
    await communicate.save("voice.mp3")
    print("✅ Audio prêt.")


def animate_character():
    print("🚀 Lancement Wav2Lip...")
    output_path = os.path.abspath("avatar_talking.mp4")

    cmd = [
        "python", "inference.py",
        "--checkpoint_path", "checkpoints/wav2lip.pth",
        "--face", os.path.abspath(AVATAR_PATH),
        "--audio", os.path.abspath("voice.mp3"),
        "--outfile", output_path,
        "--nosmooth"
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=WAV2LIP_DIR,
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            print("✅ Wav2Lip terminé.")
            return output_path
        else:
            print(f"❌ Erreur Wav2Lip :\n{result.stderr}")
            return None
    except Exception as e:
        print(f"❌ Erreur inattendue : {e}")
        return None


def create_intro(image_path, title):
    print("🎬 Création intro...")

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-vf", f"drawtext=text='{title}':fontcolor=white:fontsize=72:x=(w-text_w)/2:y=(h-text_h)/2",
        "-t", str(INTRO_DURATION),
        "intro.mp4"
    ]

    subprocess.run(cmd, capture_output=True)


def create_outro():
    print("🎬 Création outro...")

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", os.path.join(ASSETS_DIR, "disclaimers.png"),
        "-t", str(OUTRO_DURATION),
        "outro.mp4"
    ]

    subprocess.run(cmd, capture_output=True)


def assemble_video():
    print("🎞️ Assemblage final...")

    cmd = [
        "ffmpeg", "-y",
        "-i", "intro.mp4",
        "-i", "avatar_talking.mp4",
        "-i", "outro.mp4",
        "-filter_complex", "[0:v][1:v][2:v]concat=n=3:v=1:a=0",
        "final_video.mp4"
    ]

    subprocess.run(cmd, capture_output=True)
    print("✅ Vidéo finale prête : final_video.mp4")


async def main():
    if not os.path.exists("video_metadata.json"):
        print("❌ video_metadata.json introuvable.")
        return

    with open("video_metadata.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    titre = data.get("titre", "Titre manquant")
    niveau = data.get("niveau", "débutant")
    voix_off = data.get("voix_off", "")

    await generate_audio(voix_off)

    video = animate_character()
    if not video:
        print("❌ Impossible de générer l'avatar animé.")
        return

    intro_image = os.path.join(ASSETS_DIR, NIVEAU_TO_IMAGE[niveau])
    create_intro(intro_image, titre)
    create_outro()
    assemble_video()


if __name__ == "__main__":
    asyncio.run(main())

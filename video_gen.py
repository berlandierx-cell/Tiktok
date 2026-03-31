import os
import json
import asyncio
import subprocess
import edge_tts

AVATAR_PATH = "assets/1774899221632.png"
WAV2LIP_DIR = os.path.expanduser("~/Wav2Lip")


async def generate_audio(text):
    print("🎙️ Création audio...")
    communicate = edge_tts.Communicate(text, "fr-FR-HenriNeural")
    await communicate.save("voice.mp3")
    print("✅ Audio prêt.")


def animate_character():
    print("🚀 Lancement Wav2Lip en local...")
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
    except subprocess.TimeoutExpired:
        print("❌ Timeout Wav2Lip (5 min dépassées).")
        return None
    except Exception as e:
        print(f"❌ Erreur inattendue : {e}")
        return None


async def main():
    if not os.path.exists("video_metadata.json"):
        print("❌ Erreur : video_metadata.json introuvable.")
        return

    with open("video_metadata.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    voix_off = data.get("voix_off", "Le trading demande de la discipline.")

    await generate_audio(voix_off)

    video = animate_character()

    if video and os.path.exists(video):
        print("✨ Avatar animé : avatar_talking.mp4 créé !")
    else:
        print("⚠️ Échec de l'animation avatar.")


if __name__ == "__main__":
    asyncio.run(main())

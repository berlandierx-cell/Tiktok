import os
import json
import asyncio
import subprocess
import edge_tts

AVATAR_PATH = "assets/1774899221632.png"
WAV2LIP_DIR = os.path.expanduser("~/Wav2Lip")

async def generate_audio(text):
    print("🎙️ Création audio...")
    short_text = text.split('.')[0] + "."
    communicate = edge_tts.Communicate(short_text, "fr-FR-DeniseNeural")
    await communicate.save("voice.mp3")
    print("✅ Audio prêt.")

def animate_character():
    print("🚀 Lancement Wav2Lip en local...")
    output_path = "avatar_talking.mp4"

    cmd = [
        "python", "inference.py",
        "--checkpoint_path", "checkpoints/wav2lip.pth",
        "--face", os.path.abspath(AVATAR_PATH),
        "--audio", os.path.abspath("voice.mp3"),
        "--outfile", os.path.abspath(output_path),
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
        print("❌ Timeout : Wav2Lip a dépassé 5 minutes.")
        return None
    except Exception as e:
        print(f"❌ Erreur inattendue : {e}")
        return None

async def main():
    if not os.path.exists("video_metadata.json"):
        print("❌ Erreur : Pas de JSON trouvé.")
        return

    with open("video_metadata.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    await generate_audio(data.get("voix_off", "Succès."))

    video = animate_character()

    if video and os.path.exists(video):
        print("✨ VICTOIRE : avatar_talking.mp4 créé !")
    else:
        print("⚠️ Échec de la génération vidéo.")

if __name__ == "__main__":
    asyncio.run(main())

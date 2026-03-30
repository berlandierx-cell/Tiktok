import os
import json
import asyncio
import edge_tts
from gradio_client import Client

# CONFIGURATION
HF_SPACE_ID = "KwaiVGI/LivePortrait" # Remplace par TON ID de Space si tu l'as dupliqué
AVATAR_PATH = "assets/avatar.jpg"      # Ton image de trader (doit exister dans le dossier assets)

async def generate_audio(text):
    print(f"🎙️ Génération de la voix pour : {text[:50]}...")
    communicate = edge_tts.Communicate(text, "fr-FR-RemyNeural")
    await communicate.save("voice.mp3")
    print("✅ voice.mp3 créé.")

def animate_character():
    print(f"🚀 Connexion au Space Hugging Face : {HF_SPACE_ID}")
    try:
        client = Client(HF_SPACE_ID)
        # Note: Selon le Space, les noms des paramètres peuvent varier légèrement
        # Cette configuration correspond au standard LivePortrait
        result = client.predict(
            input_image_path=os.path.abspath(AVATAR_PATH),
            input_audio_path=os.path.abspath("voice.mp3"),
            api_name="/predict"
        )
        # Le résultat est souvent une liste ou un chemin vers un fichier temporaire
        video_output = result[0] if isinstance(result, list) else result
        print(f"✅ Animation terminée : {video_output}")
        return video_output
    except Exception as e:
        print(f"❌ Erreur Hugging Face : {e}")
        return None

async def main():
    if not os.path.exists("video_metadata.json"):
        print("❌ Fichier video_metadata.json introuvable !")
        return

    with open("video_metadata.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Créer l'audio
    await generate_audio(data["voix_off"])

    # 2. Créer l'animation
    video_tmp_path = animate_character()

    if video_tmp_path:
        # On renomme le résultat pour qu'il soit facile à trouver
        os.rename(video_tmp_path, "avatar_talking.mp4")
        print("✨ La vidéo finale de l'avatar est prête : avatar_talking.mp4")

if __name__ == "__main__":
    asyncio.run(main())

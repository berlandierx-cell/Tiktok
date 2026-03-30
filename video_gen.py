import os
import json
import asyncio
import edge_tts
import fal_client
import requests

# CONFIGURATION
# Tu devras ajouter FAL_KEY dans tes Secrets GitHub (comme pour Gemini)
os.environ["FAL_KEY"] = os.environ.get("FAL_KEY", "") 
AVATAR_PATH = "assets/1774899221632.png"

async def generate_audio(text):
    print(f"🎙️ Création de l'audio...")
    communicate = edge_tts.Communicate(text, "fr-FR-DeniseNeural")
    await communicate.save("voice.mp3")
    print("✅ Audio prêt.")

def animate_character():
    print(f"🚀 Animation haute vitesse sur Fal.ai...")
    try:
        # 1. Upload des fichiers sur leurs serveurs temporaires
        image_url = fal_client.upload_file(AVATAR_PATH)
        audio_url = fal_client.upload_file("voice.mp3")

        # 2. Lancement de l'animation LivePortrait
        # C'est le modèle le plus performant et stable en 2026
        result = fal_client.subscribe(
            "fal-ai/live-portrait/video-to-video", # Ou "fal-ai/live-portrait"
            arguments={
                "input_image_url": image_url,
                "input_audio_url": audio_url,
                "ref_video_url": "https://v.fal.media/live-portrait/ref.mp4", # Vidéo de référence standard
                "precision": "fast"
            },
            with_logs=True
        )
        
        video_url = result['video']['url']
        
        # 3. Téléchargement de la vidéo finale
        response = requests.get(video_url)
        with open("avatar_talking.mp4", "wb") as f:
            f.write(response.content)
            
        return "avatar_talking.mp4"
    except Exception as e:
        print(f"❌ Erreur Fal.ai : {e}")
        return None

async def main():
    if not os.path.exists("video_metadata.json"):
        return

    with open("video_metadata.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # Audio
    await generate_audio(data.get("voix_off", "Succès garanti."))

    # Vidéo
    video_file = animate_character()

    if video_file:
        print(f"✨ TERMINÉ : {video_file} créé en un temps record.")
    else:
        print("⚠️ L'animation a échoué.")

if __name__ == "__main__":
    asyncio.run(main())

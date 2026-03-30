import os
import json
import asyncio
import edge_tts
import shutil
import fal_client
import requests

# CONFIGURATION
os.environ["FAL_KEY"] = os.environ.get("FAL_KEY", "")

async def generate_audio(text):
    print(f"🎙️ Création de l'audio...")
    # On nettoie le texte pour éviter les bugs de synthèse
    clean_text = text.split('#')[0].strip()
    communicate = edge_tts.Communicate(clean_text, "fr-FR-DeniseNeural")
    await communicate.save("voice.mp3")
    print("✅ Audio prêt.")

def animate_character():
    print(f"🚀 Animation via Fal.ai (Mode Direct)...")
    try:
        # Si l'upload direct via fal_client échoue (403), on passe par une méthode plus brute
        # Mais d'abord, on tente la méthode standard avec une gestion d'erreur propre
        
        image_path = "assets/1774899221632.png"
        audio_path = "voice.mp3"

        if not os.path.exists(image_path):
            print(f"❌ Image introuvable : {image_path}")
            return None

        # Appel au modèle LivePortrait
        # On utilise 'fal-ai/live-portrait' qui est le plus stable
        handler = fal_client.submit(
            "fal-ai/live-portrait",
            arguments={
                "input_image_url": fal_client.upload_file(image_path),
                "input_audio_url": fal_client.upload_file(audio_path),
            }
        )
        
        result = handler.get()
        video_url = result['video']['url']
        
        print(f"📺 Vidéo générée, téléchargement...")
        response = requests.get(video_url)
        with open("avatar_talking.mp4", "wb") as f:
            f.write(response.content)
            
        return "avatar_talking.mp4"
    except Exception as e:
        print(f"❌ Erreur Fal.ai : {e}")
        if "403" in str(e):
            print("💡 CONSEIL : Vérifie sur ton dashboard Fal.ai que ton compte a bien quelques centimes de crédit ou que tu as validé ton identité.")
        return None

async def main():
    if not os.path.exists("video_metadata.json"):
        print("❌ Fichier JSON manquant.")
        return

    with open("video_metadata.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    script = data.get("voix_off", "Bonjour, voici un conseil trading.")
    
    await generate_audio(script)
    video_file = animate_character()

    if video_file:
        print(f"✨ SUCCÈS : {video_file} est prêt !")
    else:
        print("⚠️ L'animation a encore échoué.")

if __name__ == "__main__":
    asyncio.run(main())

import os
import json
import asyncio
import edge_tts
import shutil
from gradio_client import Client, handle_file

# CONFIGURATION
HF_SPACE_ID = "KwaiVGI/LivePortrait" 
AVATAR_PATH = "assets/1774899221632.png" 

async def generate_audio(text):
    # Nettoyage rapide du texte pour éviter les bugs de synthèse
    clean_text = text.replace('*', '').replace('#', '').strip()
    print(f"🎙️ Tentative de synthèse vocale pour : {clean_text[:100]}...")
    
    try:
        # On change pour Denise (souvent plus stable que Remy)
        communicate = edge_tts.Communicate(clean_text, "fr-FR-DeniseNeural")
        await communicate.save("voice.mp3")
        
        if os.path.exists("voice.mp3") and os.path.getsize("voice.mp3") > 0:
            print("✅ Fichier voice.mp3 généré avec succès.")
        else:
            raise Exception("Le fichier audio est vide.")
    except Exception as e:
        print(f"❌ Erreur Edge-TTS : {e}")
        raise

def animate_character():
    print(f"🚀 Connexion au moteur KwaiVGI/LivePortrait...")
    try:
        client = Client(HF_SPACE_ID)
        result = client.predict(
            input_image=handle_file(AVATAR_PATH),
            input_audio=handle_file("voice.mp3"),
            api_name="/predict"
        )
        return result[0] if isinstance(result, list) else result
    except Exception as e:
        print(f"❌ Erreur Animation : {e}")
        return None

async def main():
    if not os.path.exists("video_metadata.json"):
        print("❌ video_metadata.json manquant.")
        return

    with open("video_metadata.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # Récupération sécurisée du texte
    script_text = data.get("voix_off", data.get("script", ""))
    if not script_text:
        print("❌ Aucun texte trouvé dans video_metadata.json")
        return

    # 1. Générer l'audio
    await generate_audio(script_text)

    # 2. Lancer l'animation
    video_output = animate_character()

    if video_output:
        if os.path.exists("avatar_talking.mp4"):
            os.remove("avatar_talking.mp4")
        shutil.move(video_output, "avatar_talking.mp4")
        print("✨ TERMINÉ : avatar_talking.mp4 créé !")
    else:
        print("⚠️ L'animation a échoué.")

if __name__ == "__main__":
    asyncio.run(main())

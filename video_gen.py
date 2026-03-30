import os
import json
import asyncio
import edge_tts
from gradio_client import Client, handle_file

# CONFIGURATION DU MOTEUR OFFICIEL
HF_SPACE_ID = "KwaiVGI/LivePortrait" 
AVATAR_PATH = "assets/avatar.jpg"

async def generate_audio(text):
    print(f"🎙️ Création de la voix off...")
    # On utilise une voix masculine française naturelle
    communicate = edge_tts.Communicate(text, "fr-FR-RemyNeural")
    await communicate.save("voice.mp3")
    print("✅ Fichier voice.mp3 prêt.")

def animate_character():
    print(f"🚀 Connexion au moteur KwaiVGI/LivePortrait...")
    try:
        # On se connecte au Space officiel
        client = Client(HF_SPACE_ID)
        
        # Appel de l'API avec les fichiers locaux
        # handle_file permet d'uploader proprement vers Hugging Face
        result = client.predict(
            input_image=handle_file(AVATAR_PATH),
            input_audio=handle_file("voice.mp3"),
            api_name="/predict"
        )
        
        # Le résultat est le chemin vers la vidéo générée
        print(f"✅ Animation réussie !")
        return result
    except Exception as e:
        print(f"❌ Erreur lors de l'animation : {e}")
        return None

async def main():
    # Vérification des fichiers nécessaires
    if not os.path.exists("video_metadata.json"):
        print("❌ Erreur : video_metadata.json manquant. Lance d'abord brain.py")
        return
    
    if not os.path.exists(AVATAR_PATH):
        print(f"❌ Erreur : L'avatar est introuvable dans {AVATAR_PATH}")
        return

    # Lecture du script généré par Gemini
    with open("video_metadata.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Générer l'audio
    await generate_audio(data["voix_off"])

    # 2. Lancer l'animation (LipSync)
    video_output = animate_character()

    if video_output:
        # On récupère le fichier final
        os.rename(video_output, "avatar_talking.mp4")
        print("✨ TERMINÉ : avatar_talking.mp4 est prêt pour le montage.")
    else:
        print("⚠️ L'animation a échoué.")

if __name__ == "__main__":
    asyncio.run(main())

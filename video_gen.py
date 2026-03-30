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
    """Génère l'audio avec une voix stable"""
    clean_text = text.replace('*', '').replace('#', '').strip()
    print(f"🎙️ Synthèse vocale (Court) : {clean_text[:50]}...")
    try:
        communicate = edge_tts.Communicate(clean_text, "fr-FR-DeniseNeural")
        await communicate.save("voice.mp3")
        print("✅ voice.mp3 prêt.")
    except Exception as e:
        print(f"❌ Erreur Audio : {e}")
        raise

def animate_character():
    """Appel l'API avec les réglages optimisés pour le GPU gratuit"""
    print(f"🚀 Connexion au moteur {HF_SPACE_ID}...")
    try:
        client = Client(HF_SPACE_ID)
        
        # On utilise les paramètres param_0 à param_3 détectés dans tes logs
        result = client.predict(
            0.1,                    # param_0 : Intensité faible (Rapide)
            0.1,                    # param_1 : Intensité faible
            handle_file(AVATAR_PATH), # param_2 : Ton image
            True,                   # param_3 : LipSync activé
            api_name="/gpu_wrapped_execute_image"
        )
        
        # On extrait le chemin de la vidéo du résultat
        video_tmp = result[0] if isinstance(result, (list, tuple)) else result
        if isinstance(video_tmp, dict):
            video_tmp = video_tmp.get("video", video_tmp.get("path"))
            
        return video_tmp
    except Exception as e:
        print(f"❌ Erreur Animation (GPU Limit?) : {e}")
        return None

async def main():
    if not os.path.exists("video_metadata.json"):
        print("❌ Erreur : Lance brain.py d'abord.")
        return

    with open("video_metadata.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # Récupération du texte court
    text = data.get("voix_off", "")
    
    # 1. Audio
    await generate_audio(text)

    # 2. Animation
    video_output = animate_character()

    if video_output:
        final_name = "avatar_talking.mp4"
        if os.path.exists(final_name): os.remove(final_name)
        shutil.move(video_output, final_name)
        print(f"✨ SUCCÈS : {final_name} est créé !")
    else:
        print("⚠️ Échec de l'animation.")

if __name__ == "__main__":
    asyncio.run(main())

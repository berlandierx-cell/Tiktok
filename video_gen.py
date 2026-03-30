import os
import json
import asyncio
import edge_tts
import shutil
from gradio_client import Client, handle_file

HF_SPACE_ID = "KwaiVGI/LivePortrait"
AVATAR_PATH = "assets/1774899221632.png"

async def generate_audio(text):
    # Denise est rapide et claire
    communicate = edge_tts.Communicate(text, "fr-FR-DeniseNeural")
    await communicate.save("voice.mp3")
    print("✅ Audio prêt.")

def animate_character():
    print(f"🚀 Animation éclair sur Hugging Face...")
    try:
        client = Client(HF_SPACE_ID)
        
        # On met les intensités à 0 pour un calcul ultra-rapide par le GPU
        result = client.predict(
            0, 0,                   # Aucun mouvement inutile, focus LipSync
            handle_file(AVATAR_PATH), 
            True,                   # LipSync actif
            api_name="/gpu_wrapped_execute_image"
        )
        
        video_tmp = result[0] if isinstance(result, (list, tuple)) else result
        if isinstance(video_tmp, dict):
            video_tmp = video_tmp.get("video", video_tmp.get("path"))
        return video_tmp
    except Exception as e:
        print(f"❌ Erreur Serveur : {e}")
        return None

async def main():
    if not os.path.exists("video_metadata.json"): return
    with open("video_metadata.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # Audio (phrase très courte)
    await generate_audio(data.get("voix_off", "Trade le plan, pas l'émotion."))

    # Vidéo
    video_tmp = animate_character()

    if video_tmp:
        if os.path.exists("avatar_talking.mp4"): os.remove("avatar_talking.mp4")
        shutil.copy(video_tmp, "avatar_talking.mp4")
        print("✨ SUCCÈS : Vidéo générée !")
    else:
        print("⚠️ Le serveur Hugging Face est trop lent. Réessaie dans 5 minutes.")

if __name__ == "__main__":
    asyncio.run(main())

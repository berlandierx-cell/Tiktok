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
    print(f"🎙️ Voix off : {text[:50]}...")
    communicate = edge_tts.Communicate(text, "fr-FR-DeniseNeural")
    await communicate.save("voice.mp3")
    print("✅ Audio prêt.")

def animate_character():
    print(f"🚀 Animation sur Hugging Face ({HF_SPACE_ID})...")
    try:
        client = Client(HF_SPACE_ID)
        
        # Paramètres exacts selon tes derniers logs d'erreur
        result = client.predict(
            0.2,                    # param_0 : Expression (0.2 pour être léger)
            0.2,                    # param_1 : Mouvement (0.2)
            handle_file(AVATAR_PATH), # param_2 : Ton image
            True,                   # param_3 : LipSync activé
            api_name="/gpu_wrapped_execute_image"
        )
        
        # Extraction propre du chemin vidéo
        video_tmp = result[0] if isinstance(result, (list, tuple)) else result
        if isinstance(video_tmp, dict):
            video_tmp = video_tmp.get("video", video_tmp.get("path"))
            
        return video_tmp
    except Exception as e:
        print(f"❌ Erreur Hugging Face : {e}")
        return None

async def main():
    if not os.path.exists("video_metadata.json"):
        return

    with open("video_metadata.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Audio
    await generate_audio(data.get("voix_off", ""))

    # 2. Vidéo
    video_tmp = animate_character()

    if video_tmp:
        if os.path.exists("avatar_talking.mp4"): os.remove("avatar_talking.mp4")
        shutil.copy(video_tmp, "avatar_talking.mp4")
        print("✨ TERMINÉ : avatar_talking.mp4 créé.")
    else:
        print("⚠️ Échec de l'animation.")

if __name__ == "__main__":
    asyncio.run(main())

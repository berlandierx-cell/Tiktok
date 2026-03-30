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
    print(f"🎙️ Création de l'audio pour : {text[:40]}...")
    communicate = edge_tts.Communicate(text, "fr-FR-DeniseNeural")
    await communicate.save("voice.mp3")
    print("✅ Audio prêt.")

def animate_character():
    print(f"🚀 Animation sur Hugging Face ({HF_SPACE_ID})...")
    try:
        client = Client(HF_SPACE_ID)
        
        # Endpoint validé par tes logs précédents
        result = client.predict(
            0.1,                    # param_0 : Intensité
            0.1,                    # param_1 : Mouvement
            handle_file(AVATAR_PATH), # param_2 : Ton image
            True,                   # param_3 : LipSync ON
            api_name="/gpu_wrapped_execute_image"
        )
        
        # Extraction du fichier vidéo
        video_tmp = result[0] if isinstance(result, (list, tuple)) else result
        if isinstance(video_tmp, dict):
            video_tmp = video_tmp.get("video", video_tmp.get("path"))
            
        return video_tmp
    except Exception as e:
        print(f"❌ Erreur Hugging Face : {e}")
        return None

async def main():
    if not os.path.exists("video_metadata.json"):
        print("❌ Metadata absentes.")
        return

    with open("video_metadata.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Audio
    text_to_speak = data.get("voix_off", "Activez vos stop loss.")
    await generate_audio(text_to_speak)

    # 2. Vidéo
    video_tmp = animate_character()

    if video_tmp:
        final_name = "avatar_talking.mp4"
        if os.path.exists(final_name): os.remove(final_name)
        shutil.copy(video_tmp, final_name)
        print(f"✨ TERMINÉ : {final_name} est disponible !")
    else:
        print("⚠️ L'animation a échoué (quota GPU ou erreur serveur).")

if __name__ == "__main__":
    asyncio.run(main())

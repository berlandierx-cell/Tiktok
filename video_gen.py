import os
import json
import asyncio
import edge_tts
import shutil
from gradio_client import Client, handle_file

# On change pour un Space plus léger/rapide
HF_SPACE_ID = "Zunteng/Fast-LivePortrait" 
AVATAR_PATH = "assets/1774899221632.png"

async def generate_audio(text):
    print(f"🎙️ Création audio court...")
    # On force une seule phrase pour être ultra léger
    short_text = text.split('.')[0] + "."
    communicate = edge_tts.Communicate(short_text, "fr-FR-DeniseNeural")
    await communicate.save("voice.mp3")
    print("✅ Audio prêt.")

def animate_character():
    print(f"🚀 Tentative sur moteur Rapide (Gratuit)...")
    try:
        client = Client(HF_SPACE_ID)
        
        # Ce modèle est beaucoup plus rapide que l'original
        result = client.predict(
            input_image=handle_file(AVATAR_PATH),
            input_audio=handle_file('voice.mp3'),
            api_name="/fast_process" # L'endpoint optimisé
        )
        
        # Le résultat est souvent un chemin vers un mp4
        return result
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return None

async def main():
    if not os.path.exists("video_metadata.json"): return
    with open("video_metadata.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    await generate_audio(data.get("voix_off", "Succès."))
    video_tmp = animate_character()

    if video_tmp:
        if os.path.exists("avatar_talking.mp4"): os.remove("avatar_talking.mp4")
        shutil.copy(video_tmp, "avatar_talking.mp4")
        print("✨ VICTOIRE : avatar_talking.mp4 créé !")
    else:
        print("⚠️ Toujours bloqué par les quotas gratuits...")

if __name__ == "__main__":
    asyncio.run(main())

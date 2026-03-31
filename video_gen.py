import os
import json
import asyncio
import edge_tts
import shutil
from gradio_client import Client, handle_file

# Utilisation du moteur Fast (beaucoup moins gourmand en GPU)
HF_SPACE_ID = "Zunteng/Fast-LivePortrait" 
AVATAR_PATH = "assets/1774899221632.png"

async def generate_audio(text):
    print(f"🎙️ Création audio...")
    # On prend juste la première phrase pour rester sous les 5-10 secondes
    short_text = text.split('.')[0] + "."
    communicate = edge_tts.Communicate(short_text, "fr-FR-DeniseNeural")
    await communicate.save("voice.mp3")
    print("✅ Audio prêt.")

def animate_character():
    print(f"🚀 Connexion à {HF_SPACE_ID}...")
    try:
        client = Client(HF_SPACE_ID)
        
        # On envoie l'image et l'audio au moteur rapide
        result = client.predict(
            input_image_input=handle_file(AVATAR_PATH),
            input_audio_input=handle_file('voice.mp3'),
            api_name="/fast_process"
        )
        
        # Le résultat est le chemin vers la vidéo générée
        return result
    except Exception as e:
        print(f"❌ Erreur GPU Hugging Face : {e}")
        return None

async def main():
    if not os.path.exists("video_metadata.json"):
        print("❌ Erreur : Pas de JSON trouvé.")
        return

    with open("video_metadata.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Générer le son
    await generate_audio(data.get("voix_off", "Succès."))
    
    # 2. Générer l'animation
    video_tmp = animate_character()

    if video_tmp:
        if os.path.exists("avatar_talking.mp4"): os.remove("avatar_talking.mp4")
        shutil.copy(video_tmp, "avatar_talking.mp4")
        print("✨ VICTOIRE : avatar_talking.mp4 créé !")
    else:
        print("⚠️ Le serveur gratuit est surchargé. Retente dans quelques minutes.")

if __name__ == "__main__":
    asyncio.run(main())

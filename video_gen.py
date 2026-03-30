import os
import json
import asyncio
import edge_tts
import shutil
from gradio_client import Client, handle_file

# --- CONFIGURATION ---
HF_SPACE_ID = "KwaiVGI/LivePortrait" 
AVATAR_PATH = "assets/1774899221632.png" 

async def generate_audio(text):
    """Génère le fichier voice.mp3"""
    clean_text = text.replace('*', '').replace('#', '').strip()
    print(f"🎙️ Synthèse vocale : {clean_text[:100]}...")
    
    try:
        # On reste sur Denise qui a bien fonctionné au run précédent
        communicate = edge_tts.Communicate(clean_text, "fr-FR-DeniseNeural")
        await communicate.save("voice.mp3")
        print("✅ Fichier voice.mp3 généré.")
    except Exception as e:
        print(f"❌ Erreur Edge-TTS : {e}")
        raise

def animate_character():
    """Animation basée sur les endpoints détectés dans tes logs"""
    print(f"🚀 Connexion au moteur {HF_SPACE_ID}...")
    try:
        client = Client(HF_SPACE_ID)
        
        # On utilise l'endpoint /gpu_wrapped_execute_image trouvé dans tes logs
        # param_0: slider (0-0.8), param_1: slider (0-0.8), param_2: image, param_3: bool
        # Note: Si le LipSync ne bouge pas assez, on montera param_0 et param_1 à 0.5 plus tard
        
        result = client.predict(
            0.5,                    # param_0: Intensité (on met 0.5 pour voir le mouvement)
            0.5,                    # param_1: Intensité
            handle_file(AVATAR_PATH), # param_2: L'image de ton avatar
            True,                   # param_3: Checkbox (LipSync ON)
            api_name="/gpu_wrapped_execute_image"
        )
        
        # L'API renvoie (value_3, value_4), on récupère la première vidéo
        video_tmp_path = result[0] if isinstance(result, (list, tuple)) else result
        
        if video_tmp_path:
            # Si le résultat est un dictionnaire (courant sur Gradio 4/5)
            if isinstance(video_tmp_path, dict):
                video_tmp_path = video_tmp_path.get("video", video_tmp_path.get("path"))
            
            print(f"✅ Animation réussie !")
            return video_tmp_path
        return None
            
    except Exception as e:
        print(f"❌ Erreur lors de l'animation : {e}")
        return None

async def main():
    # 1. Vérifications
    if not os.path.exists("video_metadata.json"):
        print("❌ Erreur : video_metadata.json manquant.")
        return

    # 2. Lecture du JSON
    with open("video_metadata.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    script_text = data.get("voix_off", data.get("script", ""))
    
    # 3. Audio
    await generate_audio(script_text)

    # 4. Animation
    video_output = animate_character()

    if video_output:
        final_name = "avatar_talking.mp4"
        if os.path.exists(final_name):
            os.remove(final_name)
            
        # Déplacement du fichier final
        shutil.move(video_output, final_name)
        print(f"✨ SUCCÈS : {final_name} créé !")
    else:
        print("⚠️ L'animation a échoué.")

if __name__ == "__main__":
    asyncio.run(main())

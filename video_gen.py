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
    """Génère le fichier voice.mp3 à partir du texte de Gemini"""
    # Nettoyage des caractères spéciaux pour la synthèse vocale
    clean_text = text.replace('*', '').replace('#', '').strip()
    print(f"🎙️ Tentative de synthèse vocale pour : {clean_text[:100]}...")
    
    try:
        # Utilisation de Denise (voix très stable)
        communicate = edge_tts.Communicate(clean_text, "fr-FR-DeniseNeural")
        await communicate.save("voice.mp3")
        
        if os.path.exists("voice.mp3") and os.path.getsize("voice.mp3") > 0:
            print("✅ Fichier voice.mp3 généré avec succès.")
        else:
            raise Exception("Le fichier audio généré est vide.")
    except Exception as e:
        print(f"❌ Erreur Edge-TTS : {e}")
        raise

def animate_character():
    """Envoie l'image et l'audio à Hugging Face pour créer la vidéo"""
    print(f"🚀 Connexion au moteur {HF_SPACE_ID}...")
    try:
        client = Client(HF_SPACE_ID)
        
        # On ne spécifie plus api_name pour laisser le client choisir la fonction par défaut
        result = client.predict(
            input_image=handle_file(AVATAR_PATH),
            input_audio=handle_file("voice.mp3")
        )
        
        # Le résultat peut être une liste [video_path, json_data] ou juste le chemin
        video_tmp_path = result[0] if isinstance(result, (list, tuple)) else result
        
        if video_tmp_path and os.path.exists(video_tmp_path):
            print(f"✅ Animation réussie ! Fichier temporaire : {video_tmp_path}")
            return video_tmp_path
        else:
            print("❌ Le moteur n'a pas renvoyé de chemin de fichier valide.")
            return None
            
    except Exception as e:
        print(f"❌ Erreur lors de l'animation : {e}")
        # Optionnel : affiche l'aide de l'API en cas d'échec pour le debug
        try:
            client.view_api()
        except:
            pass
        return None

async def main():
    # 1. Vérifications de base
    if not os.path.exists("video_metadata.json"):
        print("❌ Erreur : video_metadata.json est introuvable.")
        return

    if not os.path.exists(AVATAR_PATH):
        print(f"❌ Erreur : L'image de l'avatar est introuvable dans {AVATAR_PATH}")
        return

    # 2. Lecture du script de Gemini
    with open("video_metadata.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # Récupération du texte (on gère plusieurs noms de clés possibles)
    script_text = data.get("voix_off", data.get("script", data.get("text", "")))
    
    if not script_text:
        print("❌ Erreur : Aucun texte trouvé dans le JSON.")
        return

    # 3. Étape Audio
    await generate_audio(script_text)

    # 4. Étape Animation (LipSync)
    video_output = animate_character()

    if video_output:
        # Nettoyage de l'ancienne vidéo si elle existe
        final_name = "avatar_talking.mp4"
        if os.path.exists(final_name):
            os.remove(final_name)
            
        # Déplacement du fichier généré vers la racine de ton repo
        shutil.move(video_output, final_name)
        print(f"✨ SUCCÈS : {final_name} est prêt dans ton dépôt !")
    else:
        print("⚠️ L'animation a échoué, vérifie les logs Hugging Face.")

if __name__ == "__main__":
    asyncio.run(main())

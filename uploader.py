import os
import json
from tiktok_uploader.upload import upload_video

def publish():
    # 1. Chargement des métadonnées pour la description
    metadata_path = "video_metadata.json"
    video_path = "final_video.mp4" # Vérifie bien que c'est le nom généré par composer.py

    if not os.path.exists(metadata_path):
        print("❌ Erreur : video_metadata.json introuvable.")
        return
    
    with open(metadata_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Construction de la légende TikTok
    description = f"{data.get('titre', 'Trading Tips')} 🚀 {data.get('tags', '#trading')}"

    # 2. Vérification des cookies
    if not os.path.exists('cookies.txt'):
        print("❌ Erreur : Le fichier cookies.txt est absent.")
        return

    print(f"📤 Tentative d'upload de {video_path}...")
    print(f"📝 Description : {description}")

    # 3. Upload via tiktok-uploader
    # On utilise headless=True car on est sur un serveur (GitHub Action)
    failed_videos = upload_video(
        video_path,
        description=description,
        cookies='cookies.txt',
        browser='chromium',
        headless=True
    )

    if not failed_videos:
        print("✅ SUCCESS : Cypher est en ligne sur TikTok !")
    else:
        print(f"❌ FAILED : L'upload a échoué pour {video_path}")

if __name__ == "__main__":
    publish()

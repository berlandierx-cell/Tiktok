import os
import json
from tiktok_uploader.upload import upload_video

def publish():
    # Configuration des noms de fichiers
    metadata_path = "video_metadata.json"
    video_path = "final_video.mp4" 

    if not os.path.exists(metadata_path):
        print(f"❌ Erreur : {metadata_path} introuvable.")
        return
    
    with open(metadata_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Construction de la légende TikTok
    description = f"{data.get('titre', 'Trading Tips')} 🚀 {data.get('tags', '#trading')}"

    # Vérification des fichiers nécessaires
    if not os.path.exists(video_path):
        print(f"❌ Erreur : La vidéo {video_path} n'a pas été générée par le composer.")
        return

    if not os.path.exists('cookies.txt'):
        print("❌ Erreur : Le fichier cookies.txt est absent (vérifie ton secret GitHub).")
        return

    print(f"📤 Tentative d'upload de {video_path}...")
    print(f"📝 Description : {description}")

    # Upload via tiktok-uploader
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

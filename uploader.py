import os
import json
from tiktok_uploader.upload import upload_video

def publish():
    metadata_path = "video_metadata.json"
    video_path = "final_video.mp4" 
    
    # On récupère le SessionID depuis les variables d'environnement GitHub
    session_id = os.environ.get('TIKTOK_SESSIONID')

    if not os.path.exists(metadata_path):
        print(f"❌ Erreur : {metadata_path} introuvable.")
        return
    
    with open(metadata_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    description = f"{data.get('titre', 'Trading Tips')} 🚀 {data.get('tags', '#trading')}"

    if not video_path or not os.path.exists(video_path):
        print(f"❌ Erreur : La vidéo {video_path} est introuvable.")
        return

    if not session_id:
        print("❌ Erreur : TIKTOK_SESSIONID est vide. Vérifie tes secrets GitHub.")
        return

    print(f"📤 Tentative d'upload via SessionID...")
    
    # On utilise l'argument 'sessionid' au lieu de 'cookies'
    failed_videos = upload_video(
        video_path,
        description=description,
        sessionid=session_id,
        browser='chromium',
        headless=True
    )

    if not failed_videos:
        print("✅ SUCCESS : Cypher est en ligne sur TikTok !")
    else:
        print(f"❌ FAILED : L'upload a échoué.")

if __name__ == "__main__":
    publish()

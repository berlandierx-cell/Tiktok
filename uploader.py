import os
import json
from tiktok_uploader.upload import upload_video

def publish():
    metadata_path = "video_metadata.json"
    video_path = "final_video.mp4" 
    session_id = os.environ.get('TIKTOK_SESSIONID')

    if not os.path.exists(metadata_path):
        print(f"❌ Erreur : {metadata_path} introuvable.")
        return
    
    with open(metadata_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    description = f"{data.get('titre', 'Trading Tips')} 🚀 {data.get('tags', '#trading')}"

    # On crée une structure de cookie que Playwright va comprendre
    auth_cookies = [
        {
            'name': 'sessionid',
            'value': session_id,
            'domain': '.tiktok.com',
            'path': '/',
            'secure': True,
            'httpOnly': True
        }
    ]

    print(f"📤 Tentative d'upload forcée pour Cypher...")

    failed_videos = upload_video(
        video_path,
        description=description,
        cookies=auth_cookies, # On passe la liste d'objets au lieu de la chaîne
        browser='chromium',
        headless=True
    )

    if not failed_videos:
        print("✅ SUCCESS : Cypher est enfin en ligne !")
    else:
        print(f"❌ FAILED : TikTok a encore bloqué la session.")

if __name__ == "__main__":
    publish()

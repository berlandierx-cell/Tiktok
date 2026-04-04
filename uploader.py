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

    if not session_id:
        print("❌ Erreur : TIKTOK_SESSIONID est vide.")
        return

    # Construction du fichier de cookies au format attendu par la lib
    cookies_data = [
        {
            "name": "sessionid",
            "value": session_id,
            "domain": ".tiktok.com",
            "path": "/",
            "secure": True,
            "httpOnly": True,
            "sameSite": "None"
        }
    ]

    # On écrit physiquement le fichier sur le disque
    cookie_file = "formatted_cookies.json"
    with open(cookie_file, 'w') as f:
        json.dump(cookies_data, f)

    print(f"📤 Tentative d'upload avec cookie formaté...")

    # On repasse le CHEMIN du fichier à la fonction
    failed_videos = upload_video(
        video_path,
        description=description,
        cookies=cookie_file, 
        browser='chromium',
        headless=True
    )

    # Nettoyage après tentative
    if os.path.exists(cookie_file):
        os.remove(cookie_file)

    if not failed_videos:
        print("✅ SUCCESS : Cypher est enfin en ligne !")
    else:
        print(f"❌ FAILED : L'upload a échoué (vérifie si ton compte n'est pas restreint).")

if __name__ == "__main__":
    publish()

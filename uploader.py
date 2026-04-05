import os
import json
import tempfile
from tiktok_uploader.upload import upload_video


def publish():
    metadata_path = "video_metadata.json"
    video_path    = "final_video.mp4"

    sessionid = os.getenv("TIKTOK_SESSION_ID")

    if not sessionid:
        print("❌ Erreur : TIKTOK_SESSION_ID est vide.")
        return

    if not os.path.exists(metadata_path):
        print(f"❌ {metadata_path} introuvable.")
        return

    if not os.path.exists(video_path):
        print(f"❌ {video_path} introuvable.")
        return

    with open(metadata_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    description = f"{data.get('titre', 'Trading')} 🚀 {data.get('tags', '#trading')}"

    # Format JSON attendu par tiktok_uploader
    cookies_data = [
        {
            "name": "sessionid",
            "value": sessionid,
            "domain": ".tiktok.com",
            "path": "/",
            "secure": True,
            "httpOnly": True,
            "sameSite": "None"
        }
    ]

    # Écrire dans un fichier temporaire
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json',
                                      delete=False, encoding='utf-8')
    json.dump(cookies_data, tmp)
    tmp.close()
    cookies_path = tmp.name

    print(f"📤 Upload TikTok en cours... (cookies: {cookies_path})")

    try:
        failed = upload_video(
            filename=video_path,
            description=description,
            cookies=cookies_path,
            browser='chromium',
            headless=True
        )

        if not failed:
            print("✅ Vidéo uploadée sur TikTok !")
        else:
            print(f"❌ Upload échoué : {failed}")

    except Exception as e:
        print(f"❌ Exception : {e}")

    finally:
        if os.path.exists(cookies_path):
            os.remove(cookies_path)
            print("🧹 Fichier temporaire supprimé.")


if __name__ == "__main__":
    publish()

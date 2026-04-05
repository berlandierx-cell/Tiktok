import os
import json
import tempfile
from tiktok_uploader.upload import upload_video


def publish():
    metadata_path = "video_metadata.json"
    video_path    = "final_video.mp4"

    cookies_content = os.getenv("TIKTOK_COOKIES")

    if not cookies_content:
        print("❌ Erreur : TIKTOK_COOKIES est vide.")
        return

    if not os.path.exists(metadata_path):
        print(f"❌ Erreur : {metadata_path} introuvable.")
        return

    if not os.path.exists(video_path):
        print(f"❌ Erreur : {video_path} introuvable.")
        return

    with open(metadata_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    description = f"{data.get('titre', 'Trading Tips')} 🚀 {data.get('tags', '#trading')}"

    # Écrire les cookies dans un fichier temporaire
    # (tiktok_uploader attend un chemin vers un fichier, pas le contenu brut)
    tmp_cookies = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json',
                                         delete=False, encoding='utf-8') as f:
            f.write(cookies_content)
            tmp_cookies = f.name

        print(f"📤 Upload en cours... (cookies → {tmp_cookies})")

        failed = upload_video(
            filename=video_path,
            description=description,
            cookies=tmp_cookies,
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
        # Nettoyage du fichier temporaire
        if tmp_cookies and os.path.exists(tmp_cookies):
            os.remove(tmp_cookies)
            print("🧹 Fichier cookies temporaire supprimé.")


if __name__ == "__main__":
    publish()

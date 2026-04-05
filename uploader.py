import os
import json
from tiktok_uploader.upload import upload_video


def publish():
    metadata_path = "video_metadata.json"
    video_path    = "final_video.mp4"

    cookies   = os.getenv("TIKTOK_COOKIES")
    sessionid = os.getenv("TIKTOK_SESSION_ID")

    if not os.path.exists(metadata_path):
        print(f"❌ {metadata_path} introuvable.")
        return

    if not os.path.exists(video_path):
        print(f"❌ {video_path} introuvable.")
        return

    with open(metadata_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    description = f"{data.get('titre', 'Trading')} 🚀 {data.get('tags', '#trading')}"

    print("📤 Upload TikTok en cours...")

    try:
        # 🔥 PRIORITÉ AUX COOKIES COMPLETS
        if cookies:
            print("🔐 Auth via cookies complets")
            failed = upload_video(
                filename=video_path,
                description=description,
                cookies=cookies,
                browser='chromium',
                headless=True
            )

        elif sessionid:
            print("⚠️ Fallback sessionid (moins fiable)")
            failed = upload_video(
                filename=video_path,
                description=description,
                sessionid=sessionid,
                browser='chromium',
                headless=True
            )

        else:
            print("❌ Aucun moyen d'auth trouvé")
            return

        if not failed:
            print("✅ Vidéo uploadée sur TikTok !")
        else:
            print(f"❌ Upload échoué : {failed}")

    except Exception as e:
        print(f"❌ Exception : {e}")


if __name__ == "__main__":
    publish()
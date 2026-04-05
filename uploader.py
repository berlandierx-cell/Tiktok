import os
import json
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

    print("📤 Upload TikTok en cours...")

    try:
        failed = upload_video(
            filename=video_path,
            description=description,
            sessionid=sessionid,
            browser='chromium',
            headless=True
        )

        if not failed:
            print("✅ Vidéo uploadée sur TikTok !")
        else:
            print(f"❌ Upload échoué : {failed}")

    except Exception as e:
        print(f"❌ Exception : {e}")


if __name__ == "__main__":
    publish()

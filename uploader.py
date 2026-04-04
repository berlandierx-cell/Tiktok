import os
import json
from tiktok_uploader.upload import upload_video

def publish():
    metadata_path = "video_metadata.json"
    video_path = "final_video.mp4"

    # 🔐 Nouveau secret (IMPORTANT)
    cookies = os.getenv("TIKTOK_COOKIES")

    if not cookies:
        print("❌ Erreur : TIKTOK_COOKIES est vide.")
        return

    if not os.path.exists(metadata_path):
        print(f"❌ Erreur : {metadata_path} introuvable.")
        return

    with open(metadata_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    description = f"{data.get('titre', 'Trading Tips')} 🚀 {data.get('tags', '#trading')}"

    print("📤 Upload en cours avec cookies complets...")

    try:
        failed_videos = upload_video(
            video=video_path,
            description=description,
            cookies=cookies,        # 🔥 LA CLÉ
            browser='chromium',
            headless=False          # 🔥 ULTRA IMPORTANT
        )

        if not failed_videos:
            print("✅ SUCCESS : Cypher est en ligne !")
        else:
            print(f"❌ FAILED : {failed_videos}")

    except Exception as e:
        print("❌ Exception pendant l'upload :", str(e))


if __name__ == "__main__":
    publish()
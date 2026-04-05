import os
import json
from tiktok_uploader.upload import upload_video


def parse_cookies(cookie_string):
    cookies = []
    for c in cookie_string.split(";"):
        if "=" in c:
            name, value = c.strip().split("=", 1)
            cookies.append({
                "name": name,
                "value": value,
                "domain": ".tiktok.com",
                "path": "/"
            })
    return cookies


def publish():
    metadata_path = "video_metadata.json"
    video_path    = "final_video.mp4"

    cookie_string = os.getenv("TIKTOK_COOKIES")
    sessionid     = os.getenv("TIKTOK_SESSION_ID")

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
        if cookie_string:
            print("🔐 Auth via cookies parsés")

            cookies = parse_cookies(cookie_string)

            failed = upload_video(
                filename=video_path,
                description=description,
                cookies=cookies,   # ✅ LISTE et plus string
                browser='chromium',
                headless=True
            )

        elif sessionid:
            print("⚠️ Fallback sessionid")

            failed = upload_video(
                filename=video_path,
                description=description,
                sessionid=sessionid,
                browser='chromium',
                headless=True
            )

        else:
            print("❌ Aucun moyen d'auth")
            return

        if not failed:
            print("✅ Vidéo uploadée sur TikTok !")
        else:
            print(f"❌ Upload échoué : {failed}")

    except Exception as e:
        print(f"❌ Exception : {e}")


if __name__ == "__main__":
    publish()
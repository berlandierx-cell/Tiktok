import os
import json
import requests


TIKTOK_ACCESS_TOKEN = os.environ.get("TIKTOK_ACCESS_TOKEN", "")


def publish(video_path="final.mp4", metadata_path="video_metadata.json"):
    """
    Publie la vidéo sur TikTok via l'API Content Posting.
    Nécessite TIKTOK_ACCESS_TOKEN dans les secrets GitHub.

    Doc : https://developers.tiktok.com/doc/content-posting-api-get-started
    """

    if not os.path.exists(video_path):
        print(f"❌ Vidéo introuvable : {video_path}")
        return False

    if not TIKTOK_ACCESS_TOKEN:
        print("⚠️ TIKTOK_ACCESS_TOKEN non défini — publication ignorée.")
        print("   → Crée un compte TikTok Developer et ajoute le token dans les secrets GitHub.")
        return False

    with open(metadata_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    titre = data.get("titre", "Trading Tips")
    tags = data.get("tags", "#trading")
    description = f"{titre}\n\n{tags}"

    file_size = os.path.getsize(video_path)

    # Étape 1 : Initialiser l'upload
    print("📤 Initialisation upload TikTok...")
    init_url = "https://open.tiktokapis.com/v2/post/publish/video/init/"
    headers = {
        "Authorization": f"Bearer {TIKTOK_ACCESS_TOKEN}",
        "Content-Type": "application/json; charset=UTF-8"
    }
    payload = {
        "post_info": {
            "title": description[:150],
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
            "video_cover_timestamp_ms": 1000
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": file_size,
            "chunk_size": file_size,
            "total_chunk_count": 1
        }
    }

    resp = requests.post(init_url, headers=headers, json=payload)
    if resp.status_code != 200:
        print(f"❌ Erreur init TikTok : {resp.status_code} - {resp.text}")
        return False

    resp_data = resp.json()
    publish_id = resp_data.get("data", {}).get("publish_id")
    upload_url = resp_data.get("data", {}).get("upload_url")

    if not upload_url:
        print(f"❌ Pas d'upload_url reçu : {resp_data}")
        return False

    # Étape 2 : Upload du fichier
    print("📤 Upload de la vidéo...")
    with open(video_path, 'rb') as f:
        video_data = f.read()

    upload_headers = {
        "Content-Type": "video/mp4",
        "Content-Range": f"bytes 0-{file_size - 1}/{file_size}",
        "Content-Length": str(file_size)
    }
    upload_resp = requests.put(upload_url, headers=upload_headers, data=video_data)

    if upload_resp.status_code in [200, 201, 204]:
        print(f"✅ Vidéo publiée sur TikTok ! publish_id : {publish_id}")
        return True
    else:
        print(f"❌ Erreur upload : {upload_resp.status_code} - {upload_resp.text}")
        return False


if __name__ == "__main__":
    publish()

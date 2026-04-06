import os
import json
import asyncio
from playwright.async_api import async_playwright


async def upload_tiktok(video_path, description, sessionid):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900}
        )

        await context.add_cookies([{
            "name": "sessionid",
            "value": sessionid,
            "domain": ".tiktok.com",
            "path": "/",
            "secure": True,
            "httpOnly": True,
            "sameSite": "None"
        }])

        page = await context.new_page()

        print("🌐 Ouverture TikTok Studio...")
        try:
            await page.goto(
                "https://www.tiktok.com/tiktokstudio/upload?from=upload",
                wait_until="domcontentloaded",
                timeout=90000
            )
        except Exception as e:
            print(f"❌ Impossible d'accéder à TikTok Studio : {e}")
            await browser.close()
            return False

        await page.wait_for_timeout(5000)

        current_url = page.url
        print(f"   URL : {current_url}")

        if "login" in current_url or "explore" in current_url:
            print("❌ Non authentifié — sessionid invalide ou expiré.")
            await browser.close()
            return False

        print("✅ TikTok Studio ouvert")

        # Input file est hidden → on le force avec set_input_files sans attendre visibilité
        print("📁 Upload du fichier vidéo...")
        try:
            # Attendre que l'élément existe dans le DOM (pas forcément visible)
            await page.wait_for_selector(
                "input[type='file']",
                state="attached",   # juste présent dans le DOM, pas visible
                timeout=30000
            )
            file_input = page.locator("input[type='file']").first
            # force=True bypass la vérification de visibilité
            await file_input.set_input_files(video_path)
            print("✅ Fichier envoyé")
        except Exception as e:
            print(f"❌ Erreur upload fichier : {e}")
            await page.screenshot(path="debug_upload.png")
            await browser.close()
            return False

        # Attendre le traitement de la vidéo par TikTok
        print("⏳ Traitement vidéo (40s)...")
        await page.wait_for_timeout(40000)

        # Description
        print("✍️ Description...")
        try:
            desc_box = page.locator("[contenteditable='true']").first
            await desc_box.click()
            await page.keyboard.press("Control+a")
            await page.keyboard.type(description[:150])
            await page.wait_for_timeout(2000)
        except Exception as e:
            print(f"   ⚠️ Description ignorée : {e}")

        # Publier
        print("🚀 Publication...")
        try:
            post_btn = page.locator(
                "button:has-text('Post'), button:has-text('Publier')"
            ).first
            await post_btn.wait_for(state="visible", timeout=20000)
            await post_btn.click()
            await page.wait_for_timeout(10000)
            print("✅ Vidéo publiée sur TikTok !")
        except Exception as e:
            print(f"❌ Bouton publier non trouvé : {e}")
            await page.screenshot(path="debug_publish.png")
            await browser.close()
            return False

        await browser.close()
        return True


def publish():
    metadata_path = "video_metadata.json"
    video_path    = os.path.abspath("final_video.mp4")
    sessionid     = os.getenv("TIKTOK_SESSION_ID")

    if not sessionid:
        print("❌ TIKTOK_SESSION_ID manquant.")
        return

    if not os.path.exists(video_path):
        print(f"❌ {video_path} introuvable.")
        return

    if not os.path.exists(metadata_path):
        print(f"❌ {metadata_path} introuvable.")
        return

    with open(metadata_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    description = f"{data.get('titre', 'Trading')} 🚀 {data.get('tags', '#trading')}"
    print(f"📤 Upload : {video_path}")
    print(f"   Description : {description[:80]}...")

    success = asyncio.run(upload_tiktok(video_path, description, sessionid))
    if not success:
        print("❌ Upload échoué.")


if __name__ == "__main__":
    publish()

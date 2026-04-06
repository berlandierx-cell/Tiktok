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

        await context.add_cookies([
            {
                "name": "sessionid",
                "value": sessionid,
                "domain": ".tiktok.com",
                "path": "/",
                "secure": True,
                "httpOnly": True,
                "sameSite": "None"
            }
        ])

        page = await context.new_page()

        print("🌐 Ouverture TikTok Studio...")
        try:
            # domcontentloaded bien plus rapide que networkidle
            await page.goto(
                "https://www.tiktok.com/tiktokstudio/upload?from=upload",
                wait_until="domcontentloaded",
                timeout=90000
            )
        except Exception as e:
            print(f"❌ Impossible d'accéder à TikTok Studio : {e}")
            await browser.close()
            return False

        # Attendre que la page soit vraiment chargée
        await page.wait_for_timeout(5000)

        current_url = page.url
        print(f"   URL : {current_url}")

        if "login" in current_url or "explore" in current_url:
            print("❌ Non authentifié — sessionid invalide ou expiré.")
            await browser.close()
            return False

        print("✅ TikTok Studio ouvert")

        # Attendre l'input file (jusqu'à 30s)
        print("📁 Recherche du champ upload...")
        try:
            await page.wait_for_selector("input[type='file']", timeout=30000)
            file_input = page.locator("input[type='file']").first
            await file_input.set_input_files(video_path)
            print("✅ Fichier uploadé")
        except Exception as e:
            print(f"❌ Champ upload non trouvé : {e}")
            await browser.close()
            return False

        # Attendre le traitement de la vidéo
        print("⏳ Traitement vidéo (30s)...")
        await page.wait_for_timeout(30000)

        # Description
        print("✍️ Description...")
        try:
            desc_box = page.locator("[contenteditable='true']").first
            await desc_box.click()
            await page.keyboard.press("Control+a")
            await page.keyboard.type(description[:150])
        except Exception as e:
            print(f"   ⚠️ Description ignorée : {e}")

        await page.wait_for_timeout(3000)

        # Publier
        print("🚀 Publication...")
        try:
            # TikTok peut avoir "Post" ou "Publier" selon la langue
            post_btn = page.locator(
                "button:has-text('Post'), button:has-text('Publier'), button:has-text('发布')"
            ).first
            await post_btn.wait_for(state="visible", timeout=15000)
            await post_btn.click()
            await page.wait_for_timeout(10000)
            print("✅ Vidéo publiée sur TikTok !")
        except Exception as e:
            print(f"❌ Bouton publier non trouvé : {e}")
            # Screenshot pour debug
            try:
                await page.screenshot(path="debug_tiktok.png")
                print("   📸 Screenshot sauvegardé : debug_tiktok.png")
            except:
                pass
            await browser.close()
            return False

        await browser.close()
        return True


def publish():
    metadata_path = "video_metadata.json"
    video_path    = os.path.abspath("final_video.mp4")

    sessionid = os.getenv("TIKTOK_SESSION_ID")

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

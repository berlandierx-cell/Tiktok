import os
import json
import asyncio
from playwright.async_api import async_playwright


async def upload_tiktok(video_path, description, sessionid):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # Injecter le sessionid
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
        await page.goto("https://www.tiktok.com/tiktokstudio/upload?from=upload",
                        wait_until="networkidle", timeout=60000)

        # Vérifier qu'on est bien connecté
        current_url = page.url
        print(f"   URL : {current_url}")
        if "login" in current_url or "explore" in current_url:
            print("❌ Non authentifié — sessionid invalide ou expiré.")
            await browser.close()
            return False

        print("✅ Connecté à TikTok Studio")

        # Uploader le fichier vidéo
        print("📁 Upload du fichier...")
        file_input = page.locator("input[type='file']")
        await file_input.set_input_files(video_path)

        # Attendre que la vidéo soit traitée
        print("⏳ Traitement vidéo en cours...")
        await page.wait_for_timeout(15000)

        # Remplir la description
        print("✍️ Ajout de la description...")
        try:
            desc_box = page.locator("[contenteditable='true']").first
            await desc_box.click()
            await desc_box.fill("")
            await desc_box.type(description[:150])
        except Exception as e:
            print(f"   ⚠️ Description non remplie : {e}")

        await page.wait_for_timeout(3000)

        # Cliquer sur Publier
        print("🚀 Publication...")
        try:
            post_btn = page.locator("button:has-text('Post'), button:has-text('Publier')")
            await post_btn.first.click()
            await page.wait_for_timeout(10000)
            print("✅ Vidéo publiée sur TikTok !")
        except Exception as e:
            print(f"❌ Bouton publier non trouvé : {e}")
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

import os
import json
import asyncio
from playwright.async_api import async_playwright


async def close_modals(page):
    """Ferme tous les modals/popups TikTok qui pourraient bloquer."""
    modal_closers = [
        "button[aria-label='Close']",
        "button[aria-label='Fermer']",
        "[data-e2e='modal-close-inner-button']",
        ".TUXModal button:has-text('OK')",
        ".TUXModal button:has-text('Got it')",
        ".TUXModal button:has-text('J\\'ai compris')",
        ".TUXModal button:has-text('Continuer')",
        ".TUXModal button:has-text('Continue')",
        ".TUXModal button:has-text('Confirm')",
        ".TUXModal button:has-text('Confirmer')",
        "[data-tux-modal] button",
    ]
    closed = 0
    for selector in modal_closers:
        try:
            btn = page.locator(selector).first
            if await btn.is_visible():
                await btn.click()
                await page.wait_for_timeout(1000)
                closed += 1
                print(f"   🔒 Modal fermé ({selector})")
        except:
            pass
    return closed


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

        # Fermer les modals initiaux
        await close_modals(page)

        # Upload fichier
        print("📁 Upload du fichier vidéo...")
        try:
            await page.wait_for_selector("input[type='file']", state="attached", timeout=30000)
            file_input = page.locator("input[type='file']").first
            await file_input.set_input_files(video_path)
            print("✅ Fichier envoyé")
        except Exception as e:
            print(f"❌ Erreur upload fichier : {e}")
            await page.screenshot(path="debug_upload.png")
            await browser.close()
            return False

        # Attendre le traitement + fermer modals qui apparaissent après l'upload
        print("⏳ Traitement vidéo (30s)...")
        for i in range(6):
            await page.wait_for_timeout(5000)
            closed = await close_modals(page)
            if closed:
                print(f"   🔒 {closed} modal(s) fermé(s) à t+{(i+1)*5}s")

        # Description — utiliser keyboard pour contourner les interceptions
        print("✍️ Description...")
        try:
            # Cliquer via JavaScript pour éviter l'interception
            desc_box = page.locator("[contenteditable='true']").first
            await desc_box.dispatch_event("click")
            await page.wait_for_timeout(1000)
            await page.keyboard.press("Control+a")
            await page.keyboard.type(description[:150])
            await page.wait_for_timeout(2000)
            print("✅ Description remplie")
        except Exception as e:
            print(f"   ⚠️ Description ignorée : {e}")

        # Fermer les modals une dernière fois avant de publier
        await close_modals(page)
        await page.wait_for_timeout(2000)

        # Publier via JavaScript pour éviter l'interception du modal overlay
        print("🚀 Publication...")
        try:
            # Chercher le bouton Post dans le formulaire principal (pas dans la sidebar)
            post_btn = page.locator(
                "div[class*='upload'] button:has-text('Post'),"
                "div[class*='upload'] button:has-text('Publier'),"
                "form button:has-text('Post'),"
                "form button:has-text('Publier'),"
                "button[data-e2e='post_video_button']"
            ).first

            # Fallback : chercher n'importe quel bouton Post visible
            if not await post_btn.is_visible():
                post_btn = page.locator(
                    "button:has-text('Post'), button:has-text('Publier')"
                ).last  # .last pour éviter la sidebar

            await post_btn.wait_for(state="visible", timeout=20000)

            # Cliquer via JS pour contourner l'overlay
            await post_btn.dispatch_event("click")
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

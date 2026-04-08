import os
import json
import asyncio
import datetime
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


async def _get_latest_video_url(page, sessionid) -> str:
    """Va sur TikTok Studio et récupère l'URL de la dernière vidéo postée."""
    try:
        print("🔍 Recherche de l'URL sur TikTok Studio...")
        await page.goto(
            "https://www.tiktok.com/tiktokstudio/content",
            wait_until="domcontentloaded",
            timeout=30000
        )
        await page.wait_for_timeout(4000)

        first_video = await page.locator("a[href*='/video/']").first.get_attribute("href")

        if first_video:
            if not first_video.startswith("http"):
                first_video = "https://www.tiktok.com" + first_video
            print(f"✅ URL trouvée : {first_video}")
            return first_video

    except Exception as e:
        print(f"⚠️ Fallback profil échoué : {e}")

    return None


def save_video_url(video_url: str, metadata: dict):
    """Ajoute la nouvelle vidéo dans videos.json"""
    videos_path = "videos.json"

    if os.path.exists(videos_path):
        with open(videos_path, "r", encoding="utf-8") as f:
            videos = json.load(f)
    else:
        videos = []

    existing_urls = [v["video_url"] for v in videos]
    if video_url in existing_urls:
        print("⚠️ Vidéo déjà dans videos.json")
        return

    videos.append({
        "video_url": video_url,
        "titre": metadata.get("titre", ""),
        "sujet": metadata.get("sujet", ""),
        "posted_at": datetime.datetime.now().isoformat(),
        "comments_processed_at": None,
        "comments_count": 0
    })

    with open(videos_path, "w", encoding="utf-8") as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)

    print(f"✅ Vidéo sauvegardée dans videos.json ({len(videos)} total)")


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

        await close_modals(page)

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

        print("⏳ Traitement vidéo (30s)...")
        for i in range(6):
            await page.wait_for_timeout(5000)
            closed = await close_modals(page)
            if closed:
                print(f"   🔒 {closed} modal(s) fermé(s) à t+{(i+1)*5}s")

        print("✍️ Description...")
        try:
            desc_box = page.locator("[contenteditable='true']").first
            await desc_box.dispatch_event("click")
            await page.wait_for_timeout(1000)
            await page.keyboard.press("Control+a")
            await page.keyboard.type(description[:150])
            await page.wait_for_timeout(2000)
            print("✅ Description remplie")
        except Exception as e:
            print(f"   ⚠️ Description ignorée : {e}")

        await close_modals(page)
        await page.wait_for_timeout(2000)

        print("🚀 Publication...")
        try:
            post_btn = page.locator(
                "div[class*='upload'] button:has-text('Post'),"
                "div[class*='upload'] button:has-text('Publier'),"
                "form button:has-text('Post'),"
                "form button:has-text('Publier'),"
                "button[data-e2e='post_video_button']"
            ).first

            if not await post_btn.is_visible():
                post_btn = page.locator(
                    "button:has-text('Post'), button:has-text('Publier')"
                ).last

            await post_btn.wait_for(state="visible", timeout=20000)
            await post_btn.dispatch_event("click")
            await page.wait_for_timeout(10000)
            print("✅ Vidéo publiée sur TikTok !")

        except Exception as e:
            print(f"❌ Bouton publier non trouvé : {e}")
            await page.screenshot(path="debug_publish.png")
            await browser.close()
            return False

        # ── Récupération de l'URL ──────────────────────────────
        print("🔍 Récupération de l'URL de la vidéo...")
        video_url = None
        try:
            await page.wait_for_timeout(5000)
            current_url = page.url
            if "/video/" in current_url:
                video_url = current_url
            else:
                link = await page.locator("a[href*='/video/']").first.get_attribute("href")
                if link:
                    video_url = link if link.startswith("http") else "https://www.tiktok.com" + link
        except Exception as e:
            print(f"⚠️ Récupération URL directe échouée : {e}")

        # Fallback : TikTok Studio content
        if not video_url:
            video_url = await _get_latest_video_url(page, sessionid)

        if video_url:
            metadata_path = "video_metadata.json"
            if os.path.exists(metadata_path):
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                metadata["video_url"] = video_url
                with open(metadata_path, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
            save_video_url(video_url, metadata)
        else:
            print("⚠️ URL introuvable, videos.json non mis à jour.")

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

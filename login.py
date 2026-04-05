from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir="tiktok_session",  # 📁 dossier où sera stockée la session
        headless=False,                  # ⚠️ obligatoire pour se connecter
        args=["--no-sandbox"]
    )

    page = browser.new_page()

    print("🌐 Ouverture de TikTok login...")
    page.goto("https://www.tiktok.com/login")

    print("👉 Connecte-toi à TikTok dans la fenêtre qui s'ouvre")
    print("👉 Puis reviens ici et appuie sur ENTER")

    input("⏳ En attente de validation...")

    print("💾 Session sauvegardée dans le dossier 'tiktok_session'")

    browser.close()
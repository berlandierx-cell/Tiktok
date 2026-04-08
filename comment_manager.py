import os
import json
import asyncio
import datetime
import re
from playwright.async_api import async_playwright
from google import genai

MODELS_PRIORITY = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest"]


# ─────────────────────────────────────────
# 1. RÉCUPÉRER LES COMMENTAIRES
# ─────────────────────────────────────────
async def get_comments(sessionid: str, video_url: str, max_comments: int = 30) -> list:
    """Récupère les commentaires d'une vidéo TikTok."""
    comments = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
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

        try:
            print(f"   🌐 Chargement : {video_url}")
            await page.goto(video_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)

            # Scroll pour charger les commentaires
            for _ in range(8):
                await page.mouse.wheel(0, 600)
                await page.wait_for_timeout(1200)

            # Extraire les commentaires
            comment_elements = await page.locator(
                "[data-e2e='comment-level-1'], "
                "div[class*='CommentItemWrapper'], "
                "div[class*='comment-item']"
            ).all()

            for el in comment_elements[:max_comments]:
                try:
                    text = await el.inner_text()
                    text = text.strip()
                    if text and len(text) > 2:
                        comments.append(text)
                except:
                    continue

        except Exception as e:
            print(f"   ⚠️ Erreur récupération commentaires : {e}")
        finally:
            await browser.close()

    print(f"   💬 {len(comments)} commentaire(s) récupéré(s)")
    return comments


# ─────────────────────────────────────────
# 2. ANALYSER ET GÉNÉRER LES RÉPONSES
# ─────────────────────────────────────────
def analyze_comments(comments: list, video_context: dict) -> tuple:
    """Analyse les commentaires via Gemini et génère des réponses."""
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    sujet  = video_context.get("sujet", "trading")
    niveau = video_context.get("niveau", "débutant")
    titre  = video_context.get("titre", "")

    comments_text = "\n".join([f"{i+1}. {c}" for i, c in enumerate(comments)])

    prompt = f"""Tu es un créateur TikTok expert en trading. Tu gères les commentaires de ta vidéo.

Vidéo : "{titre}" — Sujet : {sujet} — Niveau public : {niveau}

Commentaires à analyser :
{comments_text}

Pour chaque commentaire, réponds en JSON avec ce format :
{{
  "results": [
    {{
      "id": 1,
      "comment": "texte original du commentaire",
      "type": "question|compliment|spam|hors_sujet|negatif",
      "reply": "ta réponse en français (max 150 caractères) ou null si spam/haine"
    }}
  ]
}}

Règles :
- question → réponse pédagogique courte et utile
- compliment → remerciement chaleureux + invite à suivre
- spam/haine → reply = null (on ignore)
- hors_sujet → redirige poliment vers le sujet
- negatif/critique → réponse professionnelle et constructive
- Toujours en français, ton dynamique TikTok
- Maximum 150 caractères par réponse
- Réponds UNIQUEMENT en JSON pur, sans markdown"""

    for model_name in MODELS_PRIORITY:
        try:
            response = client.models.generate_content(model=model_name, contents=prompt)
            raw = response.text
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                data = json.loads(match.group())
                results  = [r for r in data["results"] if r.get("reply")]
                skipped  = len(data["results"]) - len(results)
                print(f"   🤖 Gemini ({model_name}) : {len(results)} réponses | {skipped} ignorés")
                return results, skipped
        except Exception as e:
            print(f"   ⚠️ {model_name} : {e}")
            continue

    return [], 0


# ─────────────────────────────────────────
# 3. POSTER LES RÉPONSES
# ─────────────────────────────────────────
async def post_reply(sessionid: str, video_url: str, comment_text: str, reply_text: str) -> bool:
    """Poste une réponse à un commentaire TikTok."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 900}
        )

        await context.add_cookies([{
            "name": "sessionid",
            

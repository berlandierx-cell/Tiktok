import os
import json
import re
import random
from google import genai

MODELS_PRIORITY = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest"]

NIVEAUX = ["débutant", "intermédiaire", "confirmé"]

SUJETS = [
    "les chandeliers japonais", "le RSI", "les moyennes mobiles", "le MACD",
    "les bandes de Bollinger", "le money management", "le risk/reward",
    "la psychologie du trader", "le scalping", "le swing trading",
    "le price action", "les supports et résistances", "les retracements de Fibonacci",
    "le volume en trading", "les divergences", "le trading de tendance",
    "la gestion des émotions", "le carnet d'ordres", "les gaps de marché",
    "l'analyse fondamentale vs technique", "les actualités macro en trading",
    "Bitcoin et les cycles de marché", "l'effet de levier", "les pièges à retail",
    "comment lire un graphique", "le trading en range", "les cassures de niveaux",
    "la corrélation entre actifs", "le DCA en crypto", "les liquidations en crypto"
]

ACTIFS_FOREX = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD"]
ACTIFS_CRYPTO = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT"]

def generate():
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    niveau = random.choice(NIVEAUX)
    sujet = random.choice(SUJETS)
    actif = random.choice(ACTIFS_FOREX + ACTIFS_CRYPTO)
    categorie = "crypto" if "/" in actif and "USDT" in actif else "forex"

    prompt = f"""Tu es un expert en trading qui crée du contenu TikTok éducatif.
Réponds UNIQUEMENT en JSON pur, sans markdown, sans backticks.

Contexte :
- Sujet : {sujet}
- Niveau du public : {niveau}
- Actif affiché en fond : {actif} ({categorie})

Génère un script de vidéo TikTok d'exactement 1 minute (environ 130-150 mots) en français.
Le script doit être pédagogique, dynamique, et adapté au niveau {niveau}.
Commence directement avec un hook accrocheur.

Format JSON strict :
{{
  "titre": "titre court et accrocheur pour TikTok (max 8 mots)",
  "sujet": "{sujet}",
  "niveau": "{niveau}",
  "actif": "{actif}",
  "categorie": "{categorie}",
  "voix_off": "le script complet de 130-150 mots ici",
  "sous_titres": ["phrase 1", "phrase 2", "phrase 3", "..."],
  "tags": "#trading #bourse #{categorie} #forex #apprendre"
}}

Règles pour sous_titres : découpe la voix_off en phrases courtes (5-8 mots max chacune), une par ligne."""

    for model_name in MODELS_PRIORITY:
        try:
            response = client.models.generate_content(model=model_name, contents=prompt)
            raw_text = response.text
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if match:
                data = json.loads(match.group())
                with open('video_metadata.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"✅ Brain : Script généré avec {model_name}")
                print(f"   📌 Sujet : {data.get('sujet')} | Niveau : {data.get('niveau')} | Actif : {data.get('actif')}")
                return
        except Exception as e:
            print(f"⚠️ {model_name} failed: {e}")
            continue

    # Backup
    backup = {
        "titre": "Le RSI expliqué simplement",
        "sujet": "le RSI",
        "niveau": "débutant",
        "actif": "BTC/USDT",
        "categorie": "crypto",
        "voix_off": "Le RSI, ou Relative Strength Index, est un indicateur de momentum utilisé en trading. Il mesure la vitesse et le changement des mouvements de prix sur une échelle de 0 à 100. Quand le RSI dépasse 70, l'actif est considéré suracheté, ce qui peut signaler une correction prochaine. Sous 30, il est survendu, potentielle opportunité d'achat. Mais attention, le RSI seul ne suffit pas. Combine-le toujours avec d'autres indicateurs comme les supports résistances ou les moyennes mobiles. En trading, aucun outil n'est parfait. La clé, c'est la confluence de signaux.",
        "sous_titres": ["Le RSI mesure le momentum", "Échelle de 0 à 100", "Au-dessus de 70 : suracheté", "En dessous de 30 : survendu", "Combine-le avec d'autres outils", "Aucun indicateur n'est parfait"],
        "tags": "#trading #rsi #crypto #apprendre #bourse"
    }
    with open('video_metadata.json', 'w', encoding='utf-8') as f:
        json.dump(backup, f, ensure_ascii=False, indent=2)
    print("⚠️ Brain : Backup utilisé")

if __name__ == "__main__":
    generate()

import os
import json
import re
import random
from google import genai

MODELS_PRIORITY = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest"]

NIVEAUX = ["débutant", "intermédiaire", "confirmé"]

SUJETS_PAR_FOND = {
    "chandeliers": [
        "les chandeliers japonais", "le price action", "les patterns de chandeliers",
        "le doji", "l'engulfing", "le marteau et le pendu"
    ],
    "indicateur_rsi": [
        "le RSI", "les divergences RSI", "le surachat et survente",
        "comment utiliser le RSI", "les faux signaux du RSI"
    ],
    "indicateur_macd": [
        "le MACD", "les croisements de moyennes", "la divergence MACD",
        "comment lire le MACD", "les signaux du MACD"
    ],
    "moyenne_mobile": [
        "les moyennes mobiles", "le golden cross", "le death cross",
        "MA20 vs MA50", "les moyennes mobiles exponentielles"
    ],
    "texte_cles": [
        "la psychologie du trader", "la gestion des émotions", "les erreurs du débutant",
        "les actualités macro en trading", "la corrélation entre actifs",
        "le trading de tendance", "le DCA en crypto", "les pièges à retail"
    ],
    "schema_risk_reward": [
        "le money management", "le risk/reward", "la gestion des pertes",
        "la taille de position", "le stop loss", "les règles du risk management"
    ]
}

ACTIFS_FOREX  = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD"]
ACTIFS_CRYPTO = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT"]


def generate():
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    niveau    = random.choice(NIVEAUX)
    fond_type = random.choice(list(SUJETS_PAR_FOND.keys()))
    sujet     = random.choice(SUJETS_PAR_FOND[fond_type])
    actif     = random.choice(ACTIFS_FOREX + ACTIFS_CRYPTO)
    categorie = "crypto" if "USDT" in actif else "forex"

    prompt = f"""Tu es un expert en trading qui crée du contenu TikTok éducatif en français.
Réponds UNIQUEMENT en JSON pur, sans markdown, sans backticks, sans commentaires.

Contexte :
- Sujet : {sujet}
- Niveau du public : {niveau}
- Actif affiché en fond : {actif} ({categorie})
- Type de fond visuel : {fond_type}

Génère un script TikTok d'exactement 1 minute (130-150 mots) en français.
Commence par un hook accrocheur (question ou affirmation forte).
Adapte le vocabulaire au niveau {niveau}.

Format JSON strict :
{{
  "titre": "titre court TikTok max 8 mots",
  "sujet": "{sujet}",
  "niveau": "{niveau}",
  "actif": "{actif}",
  "categorie": "{categorie}",
  "fond_type": "{fond_type}",
  "voix_off": "script complet 130-150 mots",
  "sous_titres": ["phrase courte 1", "phrase courte 2", "..."],
  "concepts_cles": ["concept 1", "concept 2", "concept 3", "concept 4", "concept 5"],
  "tags": "#trading #{categorie} #bourse #apprendre #finance"
}}"""

    for model_name in MODELS_PRIORITY:
        try:
            response = client.models.generate_content(model=model_name, contents=prompt)
            raw_text = response.text
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if match:
                data = json.loads(match.group())
                with open('video_metadata.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"✅ Brain OK ({model_name})")
                print(f"   📌 {data.get('sujet')} | {data.get('niveau')} | {data.get('fond_type')} | {data.get('actif')}")
                return
        except Exception as e:
            print(f"⚠️ {model_name} : {e}")
            continue

    print("⚠️ Brain : backup utilisé")
    backup = {
        "titre": "Le Risk/Reward expliqué",
        "sujet": "le risk/reward",
        "niveau": "débutant",
        "actif": "BTC/USDT",
        "categorie": "crypto",
        "fond_type": "schema_risk_reward",
        "voix_off": "Est-ce que tu sais vraiment ce qu'est le risk reward ? ...",
        "sous_titres": [
            "Tu connais le risk/reward ?",
            "C'est ton ratio gain / perte",
            "1 risqué pour 3 gagné",
            "Tu peux perdre et rester rentable",
            "C'est une question de maths",
            "Calcule avant chaque trade",
            "Ratio minimum : 1 pour 2",
            "C'est la base du trading pro"
        ],
        "concepts_cles": ["Risk/Reward", "Stop Loss", "Take Profit", "Ratio 1:2", "Money Management"],
        "tags": "#trading #riskmanagement #crypto #apprendre #bourse"
    }
    with open('video_metadata.json', 'w', encoding='utf-8') as f:
        json.dump(backup, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    generate()

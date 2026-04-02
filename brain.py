import os
import json
import re
import random
from google import genai

MODELS_PRIORITY = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest"]

NIVEAUX = ["débutant", "intermédiaire", "confirmé"]

SUJETS_PAR_FOND = {
    "chandeliers": [
        "les chandeliers japonais", "le pattern doji", "le marteau et le pendu",
        "l'engulfing haussier", "l'engulfing baissier", "le morning star",
        "l'étoile du soir", "le harami", "le spinning top", "le marubozu",
        "les bougies d'indécision", "lire un graphique en chandeliers",
        "le three white soldiers", "le three black crows", "le pin bar",
        "la bougie d'inversion", "le shooting star", "l'inverted hammer",
        "les patterns de continuation", "les patterns de retournement",
        "les zones de consolidation en chandeliers", "les gaps de marché",
        "les bougies longues vs courtes", "l'ombre des chandeliers",
        "les chandeliers hebdomadaires", "lire le contexte en chandeliers",
        "les faux signaux de chandeliers", "le tweezer top et bottom",
        "le dark cloud cover", "le piercing pattern",
        "les chandeliers en tendance haussière", "les chandeliers en tendance baissière",
        "le inside bar", "l'outside bar", "les niveaux clés en chandeliers",
    ],
    "indicateur_rsi": [
        "le RSI pour les débutants", "les divergences RSI", "le surachat et la survente",
        "comment paramétrer le RSI", "les faux signaux du RSI", "RSI et zones de prix",
        "le RSI en tendance", "combiner RSI et supports", "le RSI sur plusieurs timeframes",
        "RSI vs Stochastique", "le RSI période 9 vs 14", "lire les divergences cachées",
        "le RSI et les breakouts", "le RSI en range", "les extremes du RSI",
        "le RSI et le volume", "utiliser le RSI pour timer les entrées",
        "le RSI en scalping", "le RSI en swing trading", "RSI et price action",
        "les signaux RSI fiables vs faux", "le RSI et les news", "RSI multi-actifs",
        "améliorer le RSI avec d'autres indicateurs", "le RSI et les EMA",
        "le RSI et les bandes de Bollinger", "le RSI et le MACD",
        "interpréter le RSI en zone neutre", "les erreurs avec le RSI",
        "le RSI comme filtre de tendance",
        "RSI et gestion du risque", "divergence positive vs négative",
        "utiliser le RSI pour trouver des pivots", "le RSI et les retracements",
    ],
    "indicateur_macd": [
        "le MACD pour les débutants", "les croisements de lignes MACD",
        "la divergence MACD", "l'histogramme du MACD", "paramétrer le MACD",
        "MACD et tendance", "les faux signaux du MACD", "combiner MACD et RSI",
        "le MACD en scalping", "le MACD en swing", "le MACD et les niveaux clés",
        "MACD et price action", "lire les divergences MACD cachées",
        "MACD sur plusieurs timeframes", "MACD et EMA 200", "MACD et volume",
        "les erreurs classiques avec le MACD", "le signal line crossover",
        "MACD en zone de consolidation", "MACD et les breakouts",
        "améliorer le MACD avec d'autres outils", "MACD et gestion du risque",
        "le MACD zéro line crossover", "interpréter les pics d'histogramme",
        "MACD rapide vs lent", "MACD et Fibonacci", "MACD en crypto vs forex",
        "construire une stratégie avec le MACD", "les limites du MACD",
        "MACD et les retournements de tendance",
        "MACD et les gaps", "MACD et le momentum", "MACD comme filtre de tendance",
        "MACD et les moyennes mobiles",
    ],
    "moyenne_mobile": [
        "les moyennes mobiles simples", "les moyennes mobiles exponentielles",
        "le golden cross", "le death cross", "MA20 vs MA50 vs MA200",
        "choisir la bonne période de moyenne mobile", "les MA en tendance",
        "les MA comme support et résistance", "les MA en scalping",
        "les MA en swing trading", "le ribbon de moyennes mobiles",
        "croiser plusieurs MA", "MA et price action", "les faux croisements de MA",
        "MA et volume", "MA et RSI", "MA et MACD", "la EMA 200 en trading",
        "utiliser les MA pour trouver la tendance", "les MA en range",
        "MA dynamique vs niveaux statiques", "les erreurs avec les moyennes mobiles",
        "MA et gestion de position", "MA et trailing stop",
        "les MA en crypto vs forex", "MA et les grandes timeframes",
        "construire une stratégie simple avec les MA", "les MA en bourse",
        "MA et les news économiques", "MA et les retournements",
        "la déviation standard des MA", "MA rapide vs MA lente",
        "MA et les breakouts", "les limites des moyennes mobiles",
    ],
    "texte_cles": [
        "la psychologie du trader", "la gestion des émotions en trading",
        "les erreurs classiques du débutant", "les actualités macro en trading",
        "la corrélation entre actifs", "le trading de tendance",
        "le DCA en crypto", "les pièges à retail traders",
        "comment construire un plan de trading", "la routine du trader professionnel",
        "journal de trading : pourquoi et comment", "les biais cognitifs en trading",
        "la peur et la cupidité en trading", "le revenge trading",
        "l'overtrading : comment l'éviter", "le trading en temps de crise",
        "comment gérer une série de pertes", "la patience en trading",
        "trading et psychologie comportementale", "les règles d'or du trader",
        "comment rester discipliné", "le stress du trader",
        "trading et gestion du temps", "les fausses croyances sur le trading",
        "comment évaluer ses performances", "trading et gestion du capital",
        "le trading comme business", "les erreurs de mindset",
        "comment progresser rapidement en trading", "trading et vie personnelle",
        "la confiance en trading", "trading et addiction",
        "les meilleures lectures pour trader", "les communautés de trading",
    ],
    "schema_risk_reward": [
        "le money management", "le risk/reward ratio", "la gestion des pertes",
        "calculer la taille de position", "le stop loss intelligent",
        "le take profit : où le placer", "la règle des 1% de risque",
        "le trailing stop", "risque fixe vs risque variable",
        "comment calculer son lot en forex", "le levier et ses dangers",
        "la martingale : pourquoi l'éviter", "le pyramiding de position",
        "couper ses pertes rapidement", "laisser courir ses gains",
        "le ratio risque bénéfice en pratique", "la diversification du risque",
        "le drawdown : comprendre et gérer", "la règle des 2%",
        "gérer plusieurs positions simultanées", "le risque de corrélation",
        "position sizing avancé", "les stops trop serrés vs trop larges",
        "le risque en scalping vs swing", "le risk management en crypto",
        "calculer son espérance mathématique", "le risque sur news économiques",
        "comment définir son risque maximum journalier", "risk management et psychologie",
        "construire un système de trading rentable",
        "les erreurs de risk management", "risk/reward et win rate",
        "le ratio de Sharpe simplifié", "la gestion du capital à long terme",
    ],
}

ACTIFS_FOREX  = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD",
                 "EUR/GBP", "USD/CHF", "NZD/USD", "EUR/JPY", "GBP/JPY"]
ACTIFS_CRYPTO = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT",
                 "ADA/USDT", "DOGE/USDT", "AVAX/USDT", "MATIC/USDT", "DOT/USDT"]


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

Format JSON strict (respecte exactement ces clés) :
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
}}

Règles :
- sous_titres : 8 à 12 phrases de 5-7 mots maximum chacune
- concepts_cles : 5 termes clés du sujet, courts (1-3 mots)"""

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

    # Backup
    backup = {
        "titre": "Le Risk/Reward expliqué",
        "sujet": "le risk/reward",
        "niveau": "débutant",
        "actif": "BTC/USDT",
        "categorie": "crypto",
        "fond_type": "schema_risk_reward",
        "voix_off": "Est-ce que tu sais vraiment ce qu'est le risk reward ? C'est le ratio entre ce que tu risques et ce que tu peux gagner. Avec un ratio de 1 pour 3, tu peux perdre deux trades sur trois et rester rentable. Avant chaque trade, calcule ce ratio. En dessous de 1 pour 2, passe ton chemin.",
        "sous_titres": ["Tu connais le risk/reward ?", "Ratio gain contre perte", "1 risqué pour 3 gagné", "Perdre et rester rentable", "Calcule avant chaque trade", "Minimum 1 pour 2", "Base du trading pro"],
        "concepts_cles": ["Risk/Reward", "Stop Loss", "Take Profit", "Ratio 1:2", "Money Management"],
        "tags": "#trading #riskmanagement #crypto #apprendre #bourse"
    }
    with open('video_metadata.json', 'w', encoding='utf-8') as f:
        json.dump(backup, f, ensure_ascii=False, indent=2)
    print("⚠️ Brain : backup utilisé")


if __name__ == "__main__":
    generate()

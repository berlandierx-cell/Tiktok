import google.generativeai as genai
import os
import json
import re

# 1. Configuration de l'API avec ton Secret GitHub
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def get_model_name():
    """Trouve le nom exact du modèle Flash disponible sur ton compte"""
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods and 'flash' in m.name:
            return m.name
    return 'models/gemini-1.5-flash' # Fallback par défaut

def generate_viral_trading_content():
    model_name = get_model_name()
    print(f"Using model: {model_name}")
    model = genai.GenerativeModel(model_name)
    
    # Le Prompt optimisé pour éviter les erreurs de format JSON
    prompt = """
    Tu es un expert en trading crypto et bourse, spécialisé dans les vidéos virales TikTok.
    Ta mission : Choisir un concept de trading (ex: Order Blocks, RSI divergence, Psychologie de baleine).
    
    Structure de la vidéo (60 secondes) :
    1. Accroche choc (3s)
    2. Explication du problème (12s)
    3. La solution/stratégie (35s)
    4. Call to action (10s)

    Réponds UNIQUEMENT avec un objet JSON pur, sans texte avant ou après, suivant cette structure :
    {
      "sujet": "Nom du concept",
      "titre_video": "Accroche pour TikTok",
      "voix_off": "Texte complet à lire",
      "plan_de_montage": [
        {"temps": "0-5s", "visuel": "graphique_rouge", "texte_ecran": "STOP AUX PERTES"},
        {"temps": "5-60s", "visuel": "trading_view", "texte_ecran": "La méthode PRO"}
      ],
      "tags": "#trading #crypto #bourse"
    }
    """
    
    try:
        response = model.generate_content(prompt)
        
        # Nettoyage du Markdown si Gemini en ajoute (ex: ```json ... ```)
        clean_json = re.sub(r'```json|```', '', response.text).strip()
        
        # Validation du JSON
        data = json.loads(clean_json)
        
        # Sauvegarde locale pour les prochaines étapes du workflow
        with open('video_metadata.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print("✅ video_metadata.json généré avec succès !")
        print(f"Sujet du jour : {data['sujet']}")

    except Exception as e:
        print(f"❌ Erreur lors de la génération : {e}")
        # Petit hack : si ça rate, on crée un fichier vide pour éviter que le workflow plante sans explication
        exit(1)

if __name__ == "__main__":
    generate_viral_trading_content()

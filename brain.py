import google.generativeai as genai
import os
import json

# Configuration de l'API
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def generate_viral_trading_content():
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Le "Prompt Master" pour TikTok
    prompt = """
    Tu es un expert en trading viral sur TikTok. 
    Ton but est de créer un script de 50-60 secondes sur un sujet de trading (ex: RSI, Psychologie, Gestion du risque, Bull trap).
    
    Format de réponse attendu (STRICTEMENT JSON) :
    {
      "sujet": "Le nom du concept",
      "titre_video": "Accroche choc pour TikTok",
      "voix_off": "Le texte complet que le personnage va dire",
      "plan_de_montage": [
        {"temps": "0-5s", "visuel": "graphique_bourse_rouge", "texte_ecran": "STOP AUX PERTES"},
        {"temps": "5-20s", "visuel": "bougies_japonaises_zoom", "texte_ecran": "La stratégie RSI"},
        {"temps": "20-45s", "visuel": "trading_view_live", "texte_ecran": "Le signal d'achat"},
        {"temps": "45-60s", "visuel": "call_to_action", "texte_ecran": "Abonne-toi !"}
      ],
      "tags": "#trading #crypto #bourse #argent"
    }
    """
    
    response = model.generate_content(prompt)
    
    # On nettoie la réponse pour être sûr d'avoir du JSON pur
    json_text = response.text.replace('```json', '').replace('```', '').strip()
    
    with open('video_metadata.json', 'w', encoding='utf-8') as f:
        f.write(json_text)
    
    print("✅ Sujet et script générés dans video_metadata.json")

if __name__ == "__main__":
    generate_viral_trading_content()
    

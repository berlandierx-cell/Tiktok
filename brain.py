import os
import json
import re
from google import genai

# Ta liste de modèles qui fonctionnent
MODELS_PRIORITY = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-flash-latest",
    "gemini-2.5-pro",
]

def generate():
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    
    prompt = """Réponds UNIQUEMENT en JSON pur.
    Sujet : Un conseil de trading crypto percutant.
    Contrainte : La 'voix_off' doit faire MAXIMUM 40 mots.
    Format : {"titre": "...", "voix_off": "...", "tags": "..."}"""

    success = False
    for model_name in MODELS_PRIORITY:
        try:
            print(f"🤖 Tentative avec le modèle : {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            
            # Extraction et nettoyage du JSON
            raw_text = response.text
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if match:
                clean_json = match.group()
                with open('video_metadata.json', 'w', encoding='utf-8') as f:
                    f.write(clean_json)
                print(f"✅ Succès avec {model_name} !")
                success = True
                break
        except Exception as e:
            print(f"❌ Échec avec {model_name} : {e}")
            continue

    if not success:
        print("⚠️ Aucun modèle n'a fonctionné. Utilisation du backup manuel.")
        fallback = {"titre": "Trading Tip", "voix_off": "Ne tradez jamais sans stop loss.", "tags": "#trading"}
        with open('video_metadata.json', 'w', encoding='utf-8') as f:
            json.dump(fallback, f)

if __name__ == "__main__":
    generate()

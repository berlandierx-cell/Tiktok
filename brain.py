import os
import json
import re
from google import genai

MODELS_PRIORITY = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest"]

def generate():
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    
    # On demande une phrase unique (Punchline)
    prompt = """Réponds UNIQUEMENT en JSON pur.
    Sujet : Conseil trading crypto radical.
    Contrainte : Le texte 'voix_off' doit faire MAXIMUM 15 mots (une seule phrase).
    Format : {"titre": "...", "voix_off": "...", "tags": "..."}"""

    for model_name in MODELS_PRIORITY:
        try:
            response = client.models.generate_content(model=model_name, contents=prompt)
            raw_text = response.text
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if match:
                with open('video_metadata.json', 'w', encoding='utf-8') as f:
                    f.write(match.group())
                print(f"✅ Brain : Punchline générée avec {model_name}")
                return
        except:
            continue
    
    # Backup si tout rate
    with open('video_metadata.json', 'w', encoding='utf-8') as f:
        json.dump({"voix_off": "Arrête de trader avec tes émotions, suis ton plan."}, f)

if __name__ == "__main__":
    generate()

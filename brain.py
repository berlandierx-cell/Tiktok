import os
import json
import re
from google import genai

def generate():
    # Initialisation avec le nouveau SDK 2026
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    
    prompt = """Réponds UNIQUEMENT en JSON pur.
    Sujet : Un conseil de trading crypto percutant.
    Contrainte : La 'voix_off' doit faire MAXIMUM 40 mots (très court).
    Format : {"titre": "", "voix_off": "", "tags": ""}"""

    # Utilisation du modèle flash stable
    response = client.models.generate_content(
        model='gemini-1.5-flash',
        contents=prompt
    )

    # Nettoyage et sauvegarde
    text = response.text
    clean_json = re.sub(r'```json|```', '', text).strip()
    
    with open('video_metadata.json', 'w', encoding='utf-8') as f:
        f.write(clean_json)
    print("✅ Brain : Metadata générées (Format court validé)")

if __name__ == "__main__":
    generate()

import google.generativeai as genai
import os, json, re

# Configuration ancienne école
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def generate():
    # On utilise le modèle flash sans le préfixe models/
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = """Réponds UNIQUEMENT en JSON pur.
    Sujet : Un conseil de trading crypto ultra percutant.
    Contrainte : Le texte 'voix_off' doit faire MAXIMUM 45 mots.
    Format : {"titre": "", "voix_off": "", "tags": ""}"""
    
    response = model.generate_content(prompt)
    
    # Nettoyage du JSON
    clean_json = re.sub(r'```json|```', '', response.text).strip()
    
    with open('video_metadata.json', 'w', encoding='utf-8') as f:
        f.write(clean_json)
    print("✅ Brain : Metadata générées avec l'ancienne méthode.")

if __name__ == "__main__":
    generate()

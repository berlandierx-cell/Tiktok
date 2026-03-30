import google.generativeai as genai
import os, json, re

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def generate():
    model = genai.GenerativeModel('gemini-1.5-flash')
    # Prompt ultra direct pour un format TikTok percutant et court
    prompt = """Réponds UNIQUEMENT en JSON pur. 
    Sujet : Astuce de trading crypto/forex virale. 
    Contrainte : La 'voix_off' doit faire MAXIMUM 60 mots (environ 25 secondes). 
    Structure : {"sujet": "", "titre": "", "voix_off": "", "tags": ""}"""
    
    response = model.generate_content(prompt)
    # Nettoyage du JSON au cas où Gemini met des balises Markdown
    clean_json = re.sub(r'```json|```', '', response.text).strip()
    
    with open('video_metadata.json', 'w', encoding='utf-8') as f:
        f.write(clean_json)
    print("✅ Metadata générées (Format Court)")

if __name__ == "__main__":
    generate()

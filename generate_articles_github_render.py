
import os
import requests
import pandas as pd
from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI

# Charger les variables d'environnement
load_dotenv()

# Initialiser OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
LARAVEL_API = os.getenv("LARAVEL_API")

def categorie_to_id(name: str) -> int:
    mapping = {
        "Communication": 1,
        "Rédacteur": 2,
        "Politique": 3,
        "Immobilier": 4,
        "Rédacteur Santé": 5,
        "Cinema": 6,
        "Sport": 7,
        "Traduire": 9
    }
    return mapping.get(name.strip(), 2)

def generate_article(keyword):
    print(f"🧠 Génération article long SEO : {keyword}")
    prompt = f"""
Tu es un rédacteur web expert en SEO et UX. Rédige un article de blog de plus de 1000 mots, structuré pour le web, 
avec des titres H2 et H3 optimisés pour le référencement naturel. L’article doit être naturel, informatif, engageant 
(et ne jamais sembler écrit par une IA). Ajoute des paragraphes courts, des mots de transition, des titres attrayants 
et des expressions sémantiques pertinentes autour du sujet. Évite les introductions robotiques.
Thème : {keyword}
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Tu es un expert en rédaction humaine optimisée pour le SEO naturel."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.6
    )

    content = response.choices[0].message.content
    lines = content.strip().split("\n")
    title = lines[0]
    body = "\n".join(lines[1:])
    return title.strip(), body.strip()

def generate_image(prompt, filename):
    print(f"🖼️ Génération image : {filename}")
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        n=1,
        size="1024x1024"
    )

    url = response.data[0].url
    img_bytes = requests.get(url).content

    Path("images").mkdir(exist_ok=True)
    filepath = f"images/{filename}"
    with open(filepath, "wb") as f:
        f.write(img_bytes)
    return filepath

def send_to_laravel(title, content, keyword, category_id, cover_path, thumb_path):
    print(f"📤 Envoi à Laravel : {title}")
    try:
        with open(cover_path, "rb") as cover_file, open(thumb_path, "rb") as thumb_file:
            files = {
                "cover_image": cover_file,
                "thumbnail_image": thumb_file
            }
            data = {
                "title": title,
                "content": content,
                "keywords": keyword,
                "category_id": category_id
            }
            response = requests.post(LARAVEL_API, files=files, data=data)
            print(f"✅ Statut HTTP Laravel : {response.status_code}")
            try:
                print(response.json())
            except Exception:
                print("❌ Réponse brute Laravel :")
                print(response.text)
    except Exception as e:
        print("⚠️ Erreur lors de l'envoi à Laravel :", str(e))

def main():
    df = pd.read_excel("keywords.xlsx")
    for _, row in df.head(10).iterrows():  # Limite à 10 articles par jour
        keyword = row["mot_cle"]
        category = row["catégorie"]
        category_id = categorie_to_id(category)

        title, content = generate_article(keyword)
        slug = keyword.replace(" ", "_").lower()
        cover_img = generate_image(f"Image réaliste pour : {keyword}", f"{slug}_cover.jpg")
        thumb_img = generate_image(f"Miniature réaliste pour : {keyword}", f"{slug}_thumb.jpg")

        send_to_laravel(title, content, keyword, category_id, cover_img, thumb_img)

if __name__ == "__main__":
    main()

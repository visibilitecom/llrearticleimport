import os
import re
import requests
import pandas as pd
from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI

# Chargement des variables d’environnement
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
LARAVEL_API = os.getenv("LARAVEL_API")

# 🗂️ Mapping des catégories vers leur ID Laravel
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

# 🧠 Génère un article optimisé SEO
def generate_article(keyword):
    try:
        print(f"🧠 Génération article SEO : {keyword}")
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
        title = lines[0].strip("# ").strip()
        body = "\n".join(lines[1:]).strip()
        return title, body
    except Exception as e:
        print(f"❌ Erreur lors de la génération de l'article : {e}")
        return None, None

# ✅ Enregistrement dans storage/app/public/posts
def generate_image(prompt, filename):
    try:
        print(f"🖼️ Génération image : {filename}")
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        url = response.data[0].url
        img_bytes = requests.get(url).content

        # Chemin Laravel attendu
        storage_dir = Path("storage/app/public/posts")
        storage_dir.mkdir(parents=True, exist_ok=True)
        filepath = storage_dir / filename

        with open(filepath, "wb") as f:
            f.write(img_bytes)

        return str(filepath)
    except Exception as e:
        print(f"❌ Erreur lors de la génération d'image : {e}")
        return None

# 📤 Envoie à Laravel via API
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
                "key_words": keyword,
                "category_id": category_id
            }
            headers = {
                "Accept": "application/json",
                "User-Agent": "SEOArticleBot/1.0"
            }

            response = requests.post(LARAVEL_API, files=files, data=data, headers=headers, timeout=30)
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                print("✅ Réponse Laravel :", response.json())
            else:
                print("⚠️ Réponse non-JSON Laravel :")
                print(response.text[:1000])

    except requests.exceptions.HTTPError as e:
        print("❌ Erreur HTTP Laravel :", e.response.status_code, e.response.text[:500])
    except Exception as e:
        print("❌ Erreur générale lors de l’envoi à Laravel :", str(e))

# ▶️ Lancement du script
def main():
    try:
        df = pd.read_excel("keywords.xlsx")
    except Exception as e:
        print("❌ Fichier keywords.xlsx introuvable ou illisible :", e)
        return

    for _, row in df.head(10).iterrows():
        keyword = str(row.get("mot_cle", "")).strip()
        category = str(row.get("catégorie", "")).strip()

        if not keyword or not category:
            print("⚠️ Mot-clé ou catégorie manquant. Article ignoré.")
            continue

        category_id = categorie_to_id(category)

        title, content = generate_article(keyword)
        if not title or not content:
            print("⚠️ Article non généré. Passage au suivant.")
            continue

        slug = re.sub(r'\W+', '_', keyword.lower())
        cover_img = generate_image(f"Image réaliste pour : {keyword}", f"{slug}_cover.jpg")
        thumb_img = generate_image(f"Miniature réaliste pour : {keyword}", f"{slug}_thumb.jpg")

        if not cover_img or not thumb_img:
            print("⚠️ Images manquantes. Article ignoré.")
            continue

        send_to_laravel(title, content, keyword, category_id, cover_img, thumb_img)

        # Nettoyage facultatif si besoin
        # os.remove(cover_img)
        # os.remove(thumb_img)

if __name__ == "__main__":
    main()


import os
import openai
import requests
import pandas as pd
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
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
    print(f"🧠 Génération article : {keyword}")
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Tu es un expert en rédaction SEO."},
            {"role": "user", "content": f"Rédige un article de 300 mots optimisé SEO sur : {keyword}"}
        ],
        temperature=0.7
    )
    content = response["choices"][0]["message"]["content"]
    title = content.split("\n")[0]
    body = "\n".join(content.split("\n")[1:])
    return title.strip(), body.strip()

def generate_image(prompt, filename):
    print(f"🖼️ Génération image : {filename}")
    img = openai.Image.create(
        prompt=prompt,
        model="dall-e-3",
        n=1,
        size="1024x1024",
        response_format="url"
    )
    url = img["data"][0]["url"]
    img_bytes = requests.get(url).content

    Path("images").mkdir(exist_ok=True)
    filepath = f"images/{filename}"
    with open(filepath, "wb") as f:
        f.write(img_bytes)
    return filepath

def send_to_laravel(title, content, keyword, category_id, cover_path, thumb_path):
    print(f"📤 Envoi à Laravel : {title}")
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
        print(f"✅ Statut : {response.status_code}")
        print(response.json())

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

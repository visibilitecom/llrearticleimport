import os
import re
import sys
import subprocess
import requests
import pandas as pd
from dotenv import load_dotenv

# 📦 Vérifie et installe les modules nécessaires
required = ['openai', 'markdown', 'bs4', 'openpyxl']
for pkg in required:
    try:
        __import__(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

import markdown
from bs4 import BeautifulSoup
from openai import OpenAI

# 🔐 Chargement des variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
LARAVEL_API = os.getenv("LARAVEL_API")
IMAGE_PATH = "storage/photos/1/Google I/Google IO 2025.png"

# 🧠 Génération d'article long et SEO
def generate_article(keyword):
    print(f"🧠 Génération de contenu : {keyword}")
    prompt = f"""
Tu es un expert en rédaction humaine et SEO.

Rédige un article de blog HTML **de plus de 1000 mots** (au moins 6000 caractères), sans titre "Introduction". 
Structure : 
- 1 titre principal (utilisé comme <title>)
- **7 sections H2** minimum : <h2 class="section__title"><em>...</em></h2>
- Des sous-sections en <h3 class="section__title"><em>...</em></h3> si besoin
- Des <ul><li>...</li></ul> si pertinent
- Des <p> courts, lisibles, optimisés pour le web

Sujet : {keyword}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Tu écris comme un rédacteur humain SEO confirmé."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2500
        )
        html = response.choices[0].message.content
        title = extract_title_from_html(html)
        clean_html = sanitize_html(html)
        return title, clean_html
    except Exception as e:
        print(f"❌ Erreur GPT : {e}")
        return None, None

# 🔎 Extraction du premier H2 pour titre
def extract_title_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    h2 = soup.find('h2')
    return h2.get_text(strip=True) if h2 else "Article sans titre"

# 🧼 Nettoyage HTML (compatible Laravel/Tiny)
def sanitize_html(html):
    soup = BeautifulSoup(html, 'html.parser')

    # Mise en forme des H2 et H3
    for tag in soup.find_all(['h2', 'h3']):
        tag['class'] = 'section__title'
        text = tag.get_text(strip=True)
        tag.clear()
        em = soup.new_tag("em")
        em.string = text
        tag.append(em)

    return str(soup)

# 📤 Envoi à Laravel
def send_to_laravel(title, content, keyword):
    print(f"📤 Envoi à Laravel : {title}")
    try:
        data = {
            "title": title,
            "content": content,
            "key_words": keyword,
            "cover_image": IMAGE_PATH,
            "thumbnail_image": IMAGE_PATH
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "SEOArticleBot/1.0"
        }
        response = requests.post(LARAVEL_API, data=data, headers=headers, timeout=30)
        response.raise_for_status()
        if "application/json" in response.headers.get("Content-Type", ""):
            return True, response.json().get("post_id")
        print("⚠️ Réponse non-JSON :", response.text[:500])
        return False, None
    except Exception as e:
        print("❌ Erreur envoi Laravel :", str(e))
        return False, None

# ▶️ Script principal
def main():
    try:
        df = pd.read_excel("keywords.xlsx", engine='openpyxl')
    except Exception as e:
        print("❌ Erreur lecture Excel :", e)
        return

    if 'envoye' not in df.columns:
        df['envoye'] = 0
    if 'post_id' not in df.columns:
        df['post_id'] = None

    for idx, row in df.iterrows():
        if row.get("envoye", 0) == 1:
            continue

        keyword = str(row.get("mot_cle", "")).strip()
        if not keyword:
            continue

        title, content = generate_article(keyword)
        if not title or not content:
            continue

        success, post_id = send_to_laravel(title, content, keyword)
        if success:
            df.at[idx, 'envoye'] = 1
            df.at[idx, 'post_id'] = post_id
            print("✅ Article publié.\n")

    try:
        df.to_excel("keywords.xlsx", index=False, engine='openpyxl')
        print("💾 Excel mis à jour.")
    except Exception as e:
        print("❌ Erreur sauvegarde Excel :", e)

if __name__ == "__main__":
    main()
